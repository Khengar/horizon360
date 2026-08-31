from django.test import TestCase
from cdp_core.models import Company, Customer, Workflow, RawEvent, WorkflowExecution
from crm.models import Deal
from finance.models import Invoice
from projects.models import Project
from service.models import ServiceTicket
from cdp_core.workflow_service import execute_workflows

class WorkflowChainTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Demo Corp")
        self.customer = Customer.objects.create(company=self.company, primary_email="demo@example.com")
        self.deal = Deal.objects.create(
            company=self.company,
            customer=self.customer,
            title="Big Deal",
            value=15000.00,
            stage='lead'
        )

        # 1. Deal Won -> Create Invoice
        Workflow.objects.create(
            company=self.company,
            name="Deal Won to Invoice",
            trigger_event="deal.won",
            action_type="create_invoice",
            source_biom="Sales",
            destination_biom="Finance"
        )
        
        # 2. Invoice Paid -> Create Project
        Workflow.objects.create(
            company=self.company,
            name="Invoice Paid to Project",
            trigger_event="invoice.paid",
            action_type="create_project",
            source_biom="Finance",
            destination_biom="Projects"
        )
        
        # 3. Project Created -> Create Ticket
        Workflow.objects.create(
            company=self.company,
            name="Project to Onboarding Ticket",
            trigger_event="project.created",
            action_type="create_ticket",
            source_biom="Projects",
            destination_biom="Service"
        )

    def test_complete_workflow_chain(self):
        # 1. Trigger deal.won
        event1 = RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name='deal.won',
            raw_payload={'id': self.deal.id, 'value': str(self.deal.value)},
            processed=False
        )
        execute_workflows(event1)
        
        # Verify invoice created and event generated
        self.assertTrue(Invoice.objects.filter(company=self.company, deal=self.deal).exists())
        invoice = Invoice.objects.get(company=self.company, deal=self.deal)
        event2 = RawEvent.objects.filter(company=self.company, event_name='invoice.requested').first()
        self.assertIsNotNone(event2)
        
        # 2. Trigger invoice.paid
        event3 = RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name='invoice.paid',
            raw_payload={'invoice_id': invoice.id, 'amount': float(invoice.amount)},
            processed=False
        )
        execute_workflows(event3)
        
        # Verify project created and event generated
        self.assertTrue(Project.objects.filter(company=self.company, customer=self.customer).exists())
        project = Project.objects.get(company=self.company, customer=self.customer)
        event4 = RawEvent.objects.filter(company=self.company, event_name='project.created').first()
        self.assertIsNotNone(event4)
        
        # 3. Trigger project.created
        execute_workflows(event4)
        
        # Verify service ticket created and event generated
        self.assertTrue(ServiceTicket.objects.filter(company=self.company, customer=self.customer).exists())
        event5 = RawEvent.objects.filter(company=self.company, event_name='ticket.created').first()
        self.assertIsNotNone(event5)
