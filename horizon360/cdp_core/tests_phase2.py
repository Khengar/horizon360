import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from cdp_core.models import Company, UserProfile, Account, Customer, RawEvent, Segment, AuditLog
from cdp_core.identity import normalize_email, normalize_phone, merge_customers
from cdp_core.segmentation import evaluate_rule, get_segment_audience
from crm.models import Deal, Contact
from finance.models import Invoice
from service.models import ServiceTicket

class Phase2CDPHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tenant 1
        self.company1 = Company.objects.create(name="Enterprise Tech Corp", plan="enterprise")
        self.user1 = User.objects.create_user(username="admin_user", password="password123", email="admin@corp.com")
        self.profile1 = UserProfile.objects.create(user=self.user1, company=self.company1)

        # Tenant 2
        self.company2 = Company.objects.create(name="Startup Inc", plan="starter")
        self.user2 = User.objects.create_user(username="other_user", password="password123", email="other@startup.com")
        self.profile2 = UserProfile.objects.create(user=self.user2, company=self.company2)

    def test_identity_normalization(self):
        # Email normalization
        self.assertEqual(normalize_email("  John.DOE@Example.COM  "), "john.doe@example.com")
        self.assertIsNone(normalize_email("invalid-email"))
        self.assertIsNone(normalize_email(""))
        self.assertIsNone(normalize_email(None))

        # Phone normalization
        self.assertEqual(normalize_phone(" +1 (555) 123-4567 "), "+15551234567")
        self.assertEqual(normalize_phone("098-765-4321"), "0987654321")
        self.assertIsNone(normalize_phone("123"))
        self.assertIsNone(normalize_phone(""))

    def test_customer_merge_and_biom_cascade(self):
        self.client.force_authenticate(user=self.user1)

        account = Account.objects.create(company=self.company1, name="Apex Holdings", tier="enterprise")

        # Primary Customer
        primary = Customer.objects.create(
            company=self.company1,
            account=account,
            primary_email="primary@apex.com",
            primary_phone="+1111111111",
            attributes={"tier": "enterprise", "country": "USA"},
            consent={"marketing": True},
            timeline=[{"event_name": "user.signup", "received_at": "2026-01-01T00:00:00Z"}]
        )

        # Secondary Customer (e.g. created via web lead)
        secondary = Customer.objects.create(
            company=self.company1,
            primary_email="secondary@apex.com",
            attributes={"annual_spend": 25000, "country": "US"},
            consent={"analytics": True},
            timeline=[{"event_name": "page.viewed", "received_at": "2026-01-02T00:00:00Z"}]
        )

        # Attach deals, invoices, and raw events to secondary customer
        deal1 = Deal.objects.create(
            company=self.company1,
            customer=secondary,
            title="Expansion Deal",
            stage="qualified",
            value=50000.00
        )
        invoice1 = Invoice.objects.create(
            company=self.company1,
            customer=secondary,
            deal=deal1,
            invoice_number="INV-SEC-01",
            amount=50000.00,
            status="issued"
        )
        ticket1 = ServiceTicket.objects.create(
            company=self.company1,
            customer=secondary,
            title="Integration help",
            status="open"
        )
        event1 = RawEvent.objects.create(
            company=self.company1,
            customer=secondary,
            event_name="checkout.started",
            raw_payload={"amount": 50000}
        )

        # Execute Merge API
        res = self.client.post(f'/api/v1/cdp/customers/{primary.id}/merge/', {
            "secondary_customer_id": str(secondary.id)
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'success')

        # Verify Secondary Customer is deleted
        self.assertFalse(Customer.objects.filter(id=secondary.id).exists())

        # Verify Primary Customer has merged data
        primary.refresh_from_db()
        self.assertEqual(primary.attributes['country'], 'USA')  # primary overrides
        self.assertEqual(primary.attributes['annual_spend'], 25000)  # secondary filled missing
        self.assertTrue(primary.consent['marketing'])
        self.assertTrue(primary.consent['analytics'])
        self.assertEqual(len(primary.timeline), 2)

        # Verify Related entities now point to primary customer
        deal1.refresh_from_db()
        invoice1.refresh_from_db()
        ticket1.refresh_from_db()
        event1.refresh_from_db()

        self.assertEqual(deal1.customer, primary)
        self.assertEqual(invoice1.customer, primary)
        self.assertEqual(ticket1.customer, primary)
        self.assertEqual(event1.customer, primary)

        # Verify Audit Log was written
        merge_log = AuditLog.objects.filter(company=self.company1, action="merge", entity_id=str(primary.id)).first()
        self.assertIsNotNone(merge_log)
        self.assertIn("merged_secondary_customer", merge_log.diff)

    def test_dynamic_rule_based_segmentation(self):
        self.client.force_authenticate(user=self.user1)

        # Create Customers with various attributes
        c1 = Customer.objects.create(
            company=self.company1,
            primary_email="vip@acme.com",
            attributes={"tier": "enterprise", "nps_score": 9}
        )
        Deal.objects.create(company=self.company1, customer=c1, stage="won", value=15000.00)

        c2 = Customer.objects.create(
            company=self.company1,
            primary_email="regular@acme.com",
            attributes={"tier": "standard", "nps_score": 6}
        )
        Deal.objects.create(company=self.company1, customer=c2, stage="won", value=2000.00)

        # Create Dynamic Segment via API
        seg_res = self.client.post('/api/v1/cdp/segments-manage/', {
            "name": "High-Value Champions",
            "description": "Enterprise tier with won revenue >= 10,000",
            "rules": [
                {"field": "attributes.tier", "operator": "==", "value": "enterprise"},
                {"field": "aggregates.won_revenue", "operator": ">=", "value": "10000"}
            ]
        }, format='json')

        self.assertEqual(seg_res.status_code, status.HTTP_201_CREATED)
        seg_id = seg_res.data['id']

        # Evaluate Segment Customers endpoint
        cust_res = self.client.get(f'/api/v1/cdp/segments-manage/{seg_id}/customers/')
        self.assertEqual(cust_res.status_code, status.HTTP_200_OK)
        self.assertEqual(cust_res.data['match_count'], 1)
        self.assertEqual(cust_res.data['customers'][0]['primary_email'], "vip@acme.com")

    def test_gdpr_dsar_export_and_anonymization(self):
        self.client.force_authenticate(user=self.user1)

        customer = Customer.objects.create(
            company=self.company1,
            primary_email="user_to_erase@domain.com",
            primary_phone="+1234567890",
            attributes={"full_name": "John Doe", "tier": "enterprise"},
            consent={"marketing": True}
        )

        # 1. DSAR Export Endpoint
        export_res = self.client.get(f'/api/v1/cdp/customers/{customer.id}/export-data/')
        self.assertEqual(export_res.status_code, status.HTTP_200_OK)
        self.assertEqual(export_res.data['identity']['primary_email'], "user_to_erase@domain.com")

        # Verify export audit log
        export_log = AuditLog.objects.filter(company=self.company1, action="export", entity_id=str(customer.id)).first()
        self.assertIsNotNone(export_log)

        # 2. RTBF Anonymization Endpoint
        erase_res = self.client.post(f'/api/v1/cdp/customers/{customer.id}/anonymize/')
        self.assertEqual(erase_res.status_code, status.HTTP_200_OK)
        self.assertEqual(erase_res.data['status'], 'anonymized')

        # Verify in DB
        customer.refresh_from_db()
        self.assertTrue(customer.primary_email.startswith("anonymized_"))
        self.assertIsNone(customer.primary_phone)
        self.assertNotIn("full_name", customer.attributes)
        self.assertEqual(customer.attributes.get("tier"), "enterprise")  # business classification retained

        # Verify anonymize audit log
        anonymize_log = AuditLog.objects.filter(company=self.company1, action="anonymize", entity_id=str(customer.id)).first()
        self.assertIsNotNone(anonymize_log)

    def test_idempotency_key_prevents_duplicate_creation(self):
        self.client.force_authenticate(user=self.user1)
        idemp_key = f"key-{uuid.uuid4()}"

        payload = {
            "name": "Idempotent Account",
            "domain": "idemp.com",
            "tier": "standard"
        }

        # First request
        res1 = self.client.post(
            '/api/v1/cdp/accounts/',
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=idemp_key
        )
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        first_id = res1.data['id']

        # Duplicate second request with same Idempotency-Key
        res2 = self.client.post(
            '/api/v1/cdp/accounts/',
            payload,
            format='json',
            HTTP_IDEMPOTENCY_KEY=idemp_key
        )
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        second_id = res2.data['id']

        # Must return the exact same cached object ID
        self.assertEqual(first_id, second_id)

        # Verify in DB that only 1 record exists
        count = Account.objects.filter(company=self.company1, name="Idempotent Account").count()
        self.assertEqual(count, 1)
