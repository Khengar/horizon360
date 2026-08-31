from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from cdp_core.models import Company, UserProfile, Account, Customer
from crm.models import PipelineStage, Contact, Deal, Quote, QuoteItem, Activity
from crm.scoring import calculate_deal_health
from crm.search import perform_universal_search
from finance.models import Invoice
from service.models import ServiceTicket

class Phase3CRMCoreTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tenant 1
        self.company1 = Company.objects.create(name="Enterprise Tech Corp", plan="enterprise")
        self.user1 = User.objects.create_user(username="sales_rep", password="password123", email="rep@corp.com")
        self.profile1 = UserProfile.objects.create(user=self.user1, company=self.company1)

        # Tenant 2
        self.company2 = Company.objects.create(name="Acme Global", plan="starter")
        self.user2 = User.objects.create_user(username="other_rep", password="password123", email="other@acme.com")
        self.profile2 = UserProfile.objects.create(user=self.user2, company=self.company2)

        self.client.force_authenticate(user=self.user1)

    def test_configurable_pipeline_stages(self):
        # Create custom stages
        res1 = self.client.post('/api/v1/crm/pipeline-stages/', {
            "name": "Discovery Call",
            "order": 1,
            "probability": 20,
            "color_code": "#60A5FA"
        }, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        stage1_id = res1.data['id']

        res2 = self.client.post('/api/v1/crm/pipeline-stages/', {
            "name": "Executive Demo",
            "order": 2,
            "probability": 50,
            "color_code": "#34D399"
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        # Query pipeline stages
        stages_res = self.client.get('/api/v1/crm/pipeline-stages/')
        self.assertEqual(stages_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(stages_res.data), 2)

    def test_deal_weighted_value_and_health_scoring(self):
        account = Account.objects.create(company=self.company1, name="Titan Corp", tier="enterprise")
        customer = Customer.objects.create(company=self.company1, primary_email="buyer@titan.com", account=account)

        # Create Deal
        deal_res = self.client.post('/api/v1/crm/deals/', {
            "title": "Titan Cloud Migration",
            "account": str(account.id),
            "customer": str(customer.id),
            "stage": "proposal",
            "probability": 60,
            "value": "100000.00",
            "forecast_category": "commit"
        }, format='json')
        self.assertEqual(deal_res.status_code, status.HTTP_201_CREATED)
        deal_id = deal_res.data['id']
        self.assertEqual(deal_res.data['weighted_value'], 60000.00)

        # Add an Activity
        act_res = self.client.post('/api/v1/crm/activities/', {
            "deal": deal_id,
            "customer": str(customer.id),
            "account": str(account.id),
            "activity_type": "call",
            "title": "Discovery call with VP of Engineering",
            "duration_minutes": 30
        }, format='json')
        self.assertEqual(act_res.status_code, status.HTTP_201_CREATED)

        # Test recalculate health
        recalc_res = self.client.post(f'/api/v1/crm/deals/{deal_id}/recalculate-health/')
        self.assertEqual(recalc_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(recalc_res.data['health_score'], 80)
        self.assertFalse(recalc_res.data['stalled'])

    def test_cpq_quote_creation_and_conversion(self):
        account = Account.objects.create(company=self.company1, name="Starlight Inc")
        customer = Customer.objects.create(company=self.company1, primary_email="buyer@starlight.com", account=account)
        deal = Deal.objects.create(company=self.company1, account=account, customer=customer, title="Platform License", value=50000.00)

        # 1. Create Quote
        quote_res = self.client.post('/api/v1/crm/quotes/', {
            "quote_number": "Q-2026-001",
            "deal": deal.id,
            "account": str(account.id),
            "customer": str(customer.id),
            "discount_percent": "10.00",
            "tax_percent": "5.00"
        }, format='json')
        self.assertEqual(quote_res.status_code, status.HTTP_201_CREATED)
        quote_id = quote_res.data['id']

        # 2. Add Line Items
        item1_res = self.client.post(f'/api/v1/crm/quotes/{quote_id}/add-item/', {
            "product_name": "Horizon 360 Enterprise Core",
            "sku": "H360-CORE",
            "quantity": 1,
            "unit_price": "40000.00",
            "discount_amount": "0.00"
        }, format='json')
        self.assertEqual(item1_res.status_code, status.HTTP_201_CREATED)

        item2_res = self.client.post(f'/api/v1/crm/quotes/{quote_id}/add-item/', {
            "product_name": "Premium Support Add-on",
            "sku": "H360-SUPP",
            "quantity": 2,
            "unit_price": "5000.00",
            "discount_amount": "0.00"
        }, format='json')
        self.assertEqual(item2_res.status_code, status.HTTP_201_CREATED)

        # Verify Totals: Subtotal = 40000 + 10000 = 50000, 10% discount = 45000, 5% tax = 47250
        quote = Quote.objects.get(id=quote_id)
        self.assertEqual(float(quote.subtotal), 50000.00)
        self.assertEqual(float(quote.total_amount), 47250.00)

        # 3. Convert Quote to Invoice
        conv_res = self.client.post(f'/api/v1/crm/quotes/{quote_id}/convert-to-invoice/')
        self.assertEqual(conv_res.status_code, status.HTTP_200_OK)
        self.assertEqual(conv_res.data['status'], 'converted')

        # Verify Invoice in DB
        invoice = Invoice.objects.get(id=conv_res.data['invoice_id'])
        self.assertEqual(invoice.invoice_number, "INV-Q-2026-001")
        self.assertEqual(float(invoice.amount), 47250.00)
        self.assertEqual(invoice.status, 'issued')

    def test_universal_search(self):
        # Seed records for search
        acc = Account.objects.create(company=self.company1, name="Cyberdyne Systems", domain="cyberdyne.com")
        cust = Customer.objects.create(company=self.company1, primary_email="sarah@cyberdyne.com", account=acc)
        deal = Deal.objects.create(company=self.company1, account=acc, customer=cust, title="Cyberdyne AI Framework", value=200000.00)
        inv = Invoice.objects.create(company=self.company1, customer=cust, deal=deal, invoice_number="INV-CYBER-01", amount=200000.00, status="issued")
        ticket = ServiceTicket.objects.create(company=self.company1, customer=cust, title="Cyberdyne Firewall Request", status="open")

        # Execute Search
        search_res = self.client.get('/api/v1/crm/search/?q=Cyberdyne')
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(search_res.data['total_matches'], 4)

        results = search_res.data['results']
        self.assertTrue(any(a['name'] == "Cyberdyne Systems" for a in results['accounts']))
        self.assertTrue(any(c['email'] == "sarah@cyberdyne.com" for c in results['customers']))
        self.assertTrue(any(d['title'] == "Cyberdyne AI Framework" for d in results['deals']))
        self.assertTrue(any(i['invoice_number'] == "INV-CYBER-01" for i in results['invoices']))
        self.assertTrue(any(t['title'] == "Cyberdyne Firewall Request" for t in results['tickets']))
