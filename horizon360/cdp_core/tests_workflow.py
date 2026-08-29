from django.test import TestCase
from cdp_core.models import Company, Customer, RawEvent, Workflow, WorkflowExecution
from crm.models import Contact, Deal
from cdp_core.tasks import process_event_task
from cdp_core.workflow_service import execute_workflows

class WorkflowKernelTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@test.com")
        self.contact_a = Contact.objects.get(customer=self.customer_a)
        
        self.workflow = Workflow.objects.create(
            company=self.company_a,
            name="High Value Won Deal -> Invoice Request",
            trigger_event="deal.won",
            condition_field="value",
            condition_operator=">=",
            condition_value="100000",
            action_type="create_event",
            action_event_name="invoice.requested"
        )

    def test_qualifying_deal_produces_invoice_requested(self):
        # 1. workflow triggers on deal.won
        # 2. qualifying deal passes condition
        # 4. qualifying deal produces invoice.requested
        # 5. execution record is created
        # 6. successful execution is marked success
        deal = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Big Deal",
            value=150000,
            stage="negotiation"
        )
        
        initial_events_count = RawEvent.objects.count()
        
        # This will trigger deal.won RawEvent which then triggers process_event_task
        deal.stage = "won"
        deal.save()
        
        # The save() method creates the deal.won event, but we need to manually process it since Celery delay is mocked/not running inline unless configured
        # Let's find the deal.won event and process it
        deal_won_event = RawEvent.objects.get(event_name="deal.won", raw_payload__deal_id=deal.id)
        
        # process_event_task will call execute_workflows at the end
        process_event_task(deal_won_event.id)
        
        # Check WorkflowExecution
        execution = WorkflowExecution.objects.get(workflow=self.workflow, raw_event=deal_won_event)
        self.assertEqual(execution.status, 'success')
        
        # Check invoice.requested was created
        # 10. invoice.requested retains correct company/deal/customer context
        invoice_event = RawEvent.objects.get(event_name="invoice.requested")
        self.assertEqual(invoice_event.company, self.company_a)
        self.assertEqual(invoice_event.customer, self.customer_a)
        self.assertEqual(invoice_event.raw_payload['deal_id'], deal.id)
        self.assertEqual(invoice_event.raw_payload['source_workflow'], self.workflow.name)

    def test_non_qualifying_deal_is_skipped(self):
        # 3. non-qualifying deal is skipped
        deal = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Small Deal",
            value=50000,
            stage="negotiation"
        )
        
        deal.stage = "won"
        deal.save()
        
        deal_won_event = RawEvent.objects.get(event_name="deal.won", raw_payload__deal_id=deal.id)
        process_event_task(deal_won_event.id)
        
        execution = WorkflowExecution.objects.get(workflow=self.workflow, raw_event=deal_won_event)
        self.assertEqual(execution.status, 'skipped')
        
        # Ensure no invoice.requested
        with self.assertRaises(RawEvent.DoesNotExist):
            RawEvent.objects.get(event_name="invoice.requested")

    def test_idempotency_same_event_cannot_execute_twice(self):
        # 8. same RawEvent cannot execute same workflow twice
        deal = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Idempotent Deal",
            value=150000,
            stage="won"
        )
        deal_won_event = RawEvent.objects.get(event_name="deal.won", raw_payload__deal_id=deal.id)
        process_event_task(deal_won_event.id)
        
        # Second time
        process_event_task(deal_won_event.id)
        
        # Should only be 1 execution
        executions = WorkflowExecution.objects.filter(workflow=self.workflow, raw_event=deal_won_event)
        self.assertEqual(executions.count(), 1)
        
        # Should only be 1 invoice.requested event
        invoice_events = RawEvent.objects.filter(event_name="invoice.requested")
        self.assertEqual(invoice_events.count(), 1)

    def test_tenant_isolation(self):
        # 9. workflow for Company A cannot run on Company B event
        customer_b = Customer.objects.create(company=self.company_b, primary_email="b@test.com")
        contact_b = Contact.objects.get(customer=customer_b)
        
        deal = Deal.objects.create(
            company=self.company_b,
            customer=customer_b,
            contact=contact_b,
            title="Company B Big Deal",
            value=150000,
            stage="won"
        )
        deal_won_event = RawEvent.objects.get(event_name="deal.won", raw_payload__deal_id=deal.id)
        process_event_task(deal_won_event.id)
        
        # Ensure Company A workflow didn't run on Company B event
        executions = WorkflowExecution.objects.filter(workflow=self.workflow, raw_event=deal_won_event)
        self.assertEqual(executions.count(), 0)
        
        # No invoice.requested generated
        self.assertEqual(RawEvent.objects.filter(event_name="invoice.requested").count(), 0)

    def test_failed_execution(self):
        # 7. failed execution is recorded as failed
        # Make the workflow action invalid
        self.workflow.action_type = "unknown_action"
        self.workflow.save()
        
        deal = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Failed Deal",
            value=150000,
            stage="won"
        )
        deal_won_event = RawEvent.objects.get(event_name="deal.won", raw_payload__deal_id=deal.id)
        process_event_task(deal_won_event.id)
        
        execution = WorkflowExecution.objects.get(workflow=self.workflow, raw_event=deal_won_event)
        self.assertEqual(execution.status, 'failed')
        self.assertIn("Unknown action_type", execution.error_message)

    def test_recursive_trigger_prevention(self):
        # 11. invoice.requested does not recursively trigger the same workflow
        # Make workflow trigger on invoice.requested creating another invoice.requested
        recursive_workflow = Workflow.objects.create(
            company=self.company_a,
            name="Recursive",
            trigger_event="invoice.requested",
            action_type="create_event",
            action_event_name="invoice.requested"
        )
        
        raw_event = RawEvent.objects.create(
            company=self.company_a,
            event_name="invoice.requested",
            raw_payload={"value": 1000},
            processed=False
        )
        process_event_task(raw_event.id)
        
        execution = WorkflowExecution.objects.get(workflow=recursive_workflow, raw_event=raw_event)
        self.assertEqual(execution.status, 'failed')
        self.assertIn("Workflow trigger and action cannot be the same event", execution.error_message)
