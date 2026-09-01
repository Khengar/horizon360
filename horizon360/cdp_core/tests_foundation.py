from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from cdp_core.models import Company, UserProfile, Account, Customer, Role, UserRole, AuditLog
from crm.models import Contact, Deal
from cdp_core.audit import record_audit_log

class FoundationArchitectureTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tenant 1
        self.company1 = Company.objects.create(name="Acme Corp", plan="enterprise")
        self.user1 = User.objects.create_user(username="alice", password="password123", email="alice@acme.com")
        self.profile1 = UserProfile.objects.create(user=self.user1, company=self.company1)

        # Tenant 2
        self.company2 = Company.objects.create(name="Beta LLC", plan="starter")
        self.user2 = User.objects.create_user(username="bob", password="password123", email="bob@beta.com")
        self.profile2 = UserProfile.objects.create(user=self.user2, company=self.company2)

    def test_account_creation_and_tenant_isolation(self):
        self.client.force_authenticate(user=self.user1)

        # Create account in Tenant 1 via API
        response = self.client.post('/api/v1/cdp/accounts/', {
            "name": "Global Tech Corp",
            "domain": "globaltech.com",
            "industry": "Software",
            "tier": "enterprise",
            "annual_revenue": "5000000.00"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account_id = response.data['id']

        # Verify Tenant 1 can see it
        get_res1 = self.client.get(f'/api/v1/cdp/accounts/{account_id}/')
        self.assertEqual(get_res1.status_code, status.HTTP_200_OK)

        # Verify Tenant 2 CANNOT see it (tenant isolation)
        self.client.force_authenticate(user=self.user2)
        get_res2 = self.client.get(f'/api/v1/cdp/accounts/{account_id}/')
        self.assertEqual(get_res2.status_code, status.HTTP_404_NOT_FOUND)

        # Verify Tenant 2's list does not contain Tenant 1's account
        list_res2 = self.client.get('/api/v1/cdp/accounts/')
        self.assertEqual(len(list_res2.data), 0)

    def test_account_customer_contact_deal_hierarchy(self):
        # Create Account
        account = Account.objects.create(
            company=self.company1,
            name="MegaCorp",
            domain="megacorp.com",
            tier="enterprise"
        )

        # Create Customer linked to Account
        customer = Customer.objects.create(
            company=self.company1,
            account=account,
            primary_email="lead@megacorp.com",
            primary_phone="+1234567890"
        )

        # Contact is auto-created by signal and linked to Customer & Account
        contact = Contact.objects.get(customer=customer)
        self.assertEqual(contact.account, account)
        self.assertEqual(contact.company, self.company1)

        # Create Deal linked to Account & Contact
        deal = Deal.objects.create(
            company=self.company1,
            account=account,
            customer=customer,
            contact=contact,
            title="Mega Enterprise License",
            stage="qualified",
            value=120000.00
        )
        self.assertEqual(deal.account.name, "MegaCorp")
        self.assertEqual(deal.customer.primary_email, "lead@megacorp.com")

    def test_audit_logging_engine(self):
        self.client.force_authenticate(user=self.user1)

        # 1. Action creates an audit log
        res = self.client.post('/api/v1/cdp/accounts/', {
            "name": "Audit Tracked Inc",
            "domain": "audited.com"
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        acc_id = res.data['id']

        # Verify audit log was recorded
        logs = AuditLog.objects.filter(company=self.company1, entity_type="Account", entity_id=acc_id)
        self.assertTrue(logs.exists())
        self.assertEqual(logs.first().action, "create")
        self.assertEqual(logs.first().user, self.user1)

        # 2. Update logs diff
        update_res = self.client.patch(f'/api/v1/cdp/accounts/{acc_id}/', {
            "tier": "enterprise"
        }, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)

        update_logs = AuditLog.objects.filter(company=self.company1, entity_type="Account", entity_id=acc_id, action="update")
        self.assertTrue(update_logs.exists())

        # 3. Read audit logs via API
        audit_res = self.client.get('/api/v1/cdp/audit-logs/')
        self.assertEqual(audit_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(audit_res.data), 2)

    def test_rbac_roles_and_assignment(self):
        self.client.force_authenticate(user=self.user1)

        # Create custom role
        role_res = self.client.post('/api/v1/cdp/roles/', {
            "name": "Sales Manager",
            "description": "Can manage deals and view all customer records",
            "permissions": ["crm.read", "crm.write", "deals.manage"]
        }, format='json')
        self.assertEqual(role_res.status_code, status.HTTP_201_CREATED)
        role_id = role_res.data['id']

        # Assign role to user profile
        assign_res = self.client.post('/api/v1/cdp/user-roles/', {
            "user_profile": self.profile1.id,
            "role": role_id
        }, format='json')
        self.assertEqual(assign_res.status_code, status.HTTP_201_CREATED)

        # Verify assignment in DB
        role = Role.objects.get(id=role_id)
        self.assertTrue(UserRole.objects.filter(user_profile=self.profile1, role=role).exists())
        self.assertIn("crm.write", role.permissions)
