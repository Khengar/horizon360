from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, RawEvent, UserProfile, Workflow, WorkflowExecution
from crm.models import Deal
from finance.models import Invoice
from projects.models import Project, Task
from django.contrib.auth.models import User
from cdp_core.workflow_service import execute_workflows

class ProjectTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="alice@example.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="bob@example.com")
        
        self.deal_a = Deal.objects.create(company=self.company_a, customer=self.customer_a, title="Deal A", value=150000, stage="won")
        
        self.client = APIClient()

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Cross-tenant customer rejected
        response = self.client.post('/api/projects/projects/', {
            "customer": self.customer_b.id,
            "name": "Invalid Project"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))
        
        # Valid creation
        response = self.client.post('/api/projects/projects/', {
            "customer": self.customer_a.id,
            "name": "Valid Project"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.filter(company=self.company_a).count(), 1)
        
    def test_multi_biom_workflow(self):
        # 1. Setup Workflows
        wf_finance = Workflow.objects.create(
            company=self.company_a,
            name="Deal to Invoice",
            trigger_event="deal.won",
            condition_field="value",
            condition_operator=">=",
            condition_value="100000",
            action_type="create_invoice"
        )
        
        wf_project = Workflow.objects.create(
            company=self.company_a,
            name="Invoice Paid to Project",
            trigger_event="invoice.paid",
            action_type="create_project"
        )
        
        # 2. Trigger deal.won
        event1 = RawEvent.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            event_name="deal.won",
            raw_payload={"id": self.deal_a.id, "value": 150000}
        )
        execute_workflows(event1)
        
        # Finance Invoice created
        self.assertEqual(Invoice.objects.count(), 1)
        invoice = Invoice.objects.first()
        self.assertEqual(invoice.status, 'requested')
        
        # 3. Mark Invoice Paid (which emits invoice.paid)
        self.client.force_authenticate(user=self.user_a)
        response = self.client.patch(f'/api/finance/invoices/{invoice.id}/', {"status": "paid"})
        self.assertEqual(response.status_code, 200)
        
        event2 = RawEvent.objects.get(event_name="invoice.paid")
        execute_workflows(event2)
        
        # 4. Project created
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.first()
        self.assertEqual(project.company, self.company_a)
        self.assertEqual(project.customer, self.customer_a)
        
        # 5. Prevent duplicate Project creation when invoice.paid is reprocessed
        execute_workflows(event2)
        self.assertEqual(Project.objects.count(), 1)
