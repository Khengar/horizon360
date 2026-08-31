from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, Workflow, WorkflowExecution, RawEvent, UserProfile
from crm.models import Contact, Deal
from finance.models import Invoice
from django.contrib.auth.models import User
from cdp_core.workflow_service import execute_workflows

class FinanceTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="alice@example.com")
        self.deal_a = Deal.objects.create(company=self.company_a, customer=self.customer_a, title="Deal A", value=150000, stage="won")
        
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="bob@example.com")
        self.deal_b = Deal.objects.create(company=self.company_b, customer=self.customer_b, title="Deal B", value=150000, stage="won")
        
        self.client = APIClient()

    def test_invoice_creation_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Cross-company customer rejected
        response = self.client.post('/api/finance/invoices/', {
            "customer": self.customer_b.id,
            "invoice_number": "INV-001",
            "amount": 500
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))
        
        # Valid creation
        response = self.client.post('/api/finance/invoices/', {
            "customer": self.customer_a.id,
            "deal": self.deal_a.id,
            "invoice_number": "INV-002",
            "amount": 500
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Invoice.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(RawEvent.objects.filter(event_name="invoice.draft").count(), 1)

    def test_invoice_retrieval_tenant_isolation(self):
        Invoice.objects.create(company=self.company_a, customer=self.customer_a, invoice_number="INV-A", amount=100)
        Invoice.objects.create(company=self.company_b, customer=self.customer_b, invoice_number="INV-B", amount=200)
        
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/finance/invoices/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], "INV-A")

    def test_workflow_creates_exactly_one_invoice(self):
        # Create workflow
        workflow = Workflow.objects.create(
            company=self.company_a,
            name="Create Invoice on Won",
            trigger_event="deal.won",
            condition_field="value",
            condition_operator=">=",
            condition_value="100000",
            action_type="create_invoice"
        )
        
        # Create event
        event = RawEvent.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            event_name="deal.won",
            raw_payload={"id": self.deal_a.id, "value": 150000}
        )
        
        # Execute workflow
        execute_workflows(event)
        
        # Assert invoice created
        self.assertEqual(Invoice.objects.count(), 1)
        invoice = Invoice.objects.first()
        self.assertEqual(invoice.amount, 150000)
        self.assertEqual(invoice.deal, self.deal_a)
        self.assertEqual(invoice.status, 'requested')
        
        # Assert event created
        self.assertEqual(RawEvent.objects.filter(event_name="invoice.requested").count(), 1)
        
        # Idempotency check: Process again, no duplicate invoice
        execute_workflows(event)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(WorkflowExecution.objects.count(), 1) # Only 1 success

    def test_invoice_status_update_creates_event(self):
        invoice = Invoice.objects.create(company=self.company_a, customer=self.customer_a, invoice_number="INV-A", amount=100)
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(f'/api/finance/invoices/{invoice.id}/', {"status": "paid"})
        self.assertEqual(response.status_code, 200)
        
        # Should create invoice.paid event
        self.assertEqual(RawEvent.objects.filter(event_name="invoice.paid").count(), 1)
