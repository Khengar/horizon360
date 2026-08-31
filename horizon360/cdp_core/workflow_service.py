import logging
from django.db import IntegrityError
from .models import Workflow, WorkflowExecution, RawEvent

logger = logging.getLogger(__name__)

def execute_workflows(raw_event):
    """
    Finds and executes all active workflows that match the raw_event's event_name.
    """
    workflows = Workflow.objects.filter(
        company=raw_event.company,
        is_active=True,
        trigger_event=raw_event.event_name
    )

    for workflow in workflows:
        # Check idempotency
        execution, created = WorkflowExecution.objects.get_or_create(
            workflow=workflow,
            raw_event=raw_event,
            defaults={'status': 'failed'}
        )
        if not created:
            logger.info(f"WorkflowExecution already exists for workflow {workflow.id} and event {raw_event.id}. Skipping.")
            continue

        try:
            # Evaluate Condition
            condition_met = evaluate_condition(workflow, raw_event)
            
            if not condition_met:
                execution.status = 'skipped'
                execution.save()
                continue
                
            # Execute Action
            execute_action(workflow, raw_event)
            
            # Mark Success
            execution.status = 'success'
            execution.save()

        except Exception as e:
            logger.exception(f"Error executing workflow {workflow.id} for event {raw_event.id}")
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.save()


def evaluate_condition(workflow, raw_event):
    if not workflow.condition_field:
        return True # No condition
        
    payload = raw_event.raw_payload or {}
    actual_value = payload.get(workflow.condition_field)
    
    if actual_value is None:
        return False
        
    try:
        if workflow.condition_operator == '>=':
            return float(actual_value) >= float(workflow.condition_value)
        elif workflow.condition_operator == '<=':
            return float(actual_value) <= float(workflow.condition_value)
        elif workflow.condition_operator == '==':
            return str(actual_value) == str(workflow.condition_value)
    except (ValueError, TypeError):
        return False
        
    return False


def execute_action(workflow, raw_event):
    if workflow.action_type == 'create_event':
        # Create a new RawEvent
        if workflow.trigger_event == workflow.action_event_name:
            raise ValueError("Workflow trigger and action cannot be the same event to avoid infinite loops.")
            
        new_payload = dict(raw_event.raw_payload)
        new_payload['source_workflow'] = workflow.name
        new_payload['trigger_event_id'] = raw_event.id
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            event_name=workflow.action_event_name,
            raw_payload=new_payload,
            processed=False
        )
        
        # Trigger Celery processing for the new event
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'ai_generate_insight':
        from intelligence.models import Insight
        payload = raw_event.raw_payload or {}
        Insight.objects.create(
            company=raw_event.company,
            agent_type='workflow_ai',
            severity='medium',
            title=f"Automated Insight from {workflow.name}",
            description=f"Triggered by event '{raw_event.event_name}' with payload: {payload}",
            entity_type='customer' if raw_event.customer else 'event',
            entity_id=str(raw_event.customer.id) if raw_event.customer else str(raw_event.id),
            confidence=0.90,
            recommendation='Review workflow execution details and engage customer.'
        )

    elif workflow.action_type == 'ai_classify':
        if raw_event.customer:
            customer = raw_event.customer
            if not isinstance(customer.attributes, dict):
                customer.attributes = {}
            customer.attributes['ai_classification'] = workflow.action_event_name or 'classified'
            customer.save()

    elif workflow.action_type == 'ai_draft_outreach':
        if raw_event.customer:
            customer = raw_event.customer
            if not isinstance(customer.attributes, dict):
                customer.attributes = {}
            ident = customer.primary_email or customer.primary_phone or 'Customer'
            customer.attributes['ai_draft_message'] = (
                f"Hello {ident}, we noticed your recent activity regarding {raw_event.event_name}. "
                f"Our team is here to assist you with next steps!"
            )
            customer.save()

    elif workflow.action_type == 'create_invoice':
        from finance.models import Invoice
        payload = raw_event.raw_payload or {}
        
        deal_id = payload.get('deal_id')
        if not deal_id:
            # Maybe the event is deal.won, the deal is in payload? Wait, the RawEvent payload has deal details.
            # Let's extract from payload.
            deal_id = payload.get('id')
        
        amount = payload.get('value', 0)
        
        from crm.models import Deal
        deal = None
        if deal_id:
            try:
                deal = Deal.objects.get(id=deal_id, company=raw_event.company)
            except Deal.DoesNotExist:
                pass
                
        # Idempotency check: Don't create if invoice for this deal exists. 
        # But maybe the workflow execution table handles idempotency? Yes it does.
        
        invoice = Invoice.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            deal=deal,
            invoice_number=f"INV-{raw_event.id}",
            amount=amount,
            status='requested'
        )
        
        # Emit invoice.requested event
        new_payload = dict(raw_event.raw_payload)
        new_payload['invoice_id'] = invoice.id
        new_payload['amount'] = float(amount)
        new_payload['source_workflow'] = workflow.name
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            event_name='invoice.requested',
            raw_payload=new_payload,
            processed=False
        )
        
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'create_project':
        from projects.models import Project
        payload = raw_event.raw_payload or {}
        
        # When invoice.paid -> Project creation, we need customer and deal?
        # Typically the event contains the raw entity details if it comes from an object,
        # but the raw_event itself has the `customer` field which we can use.
        # Idempotency is guarded by WorkflowExecution.
        
        name_base = "Project for " + (raw_event.customer.primary_email if raw_event.customer else "Unknown")
        
        project = Project.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            name=name_base,
            status='planned'
        )
        
        # Emit project.created event
        new_payload = dict(raw_event.raw_payload)
        new_payload['project_id'] = project.id
        new_payload['source_workflow'] = workflow.name
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            event_name='project.created',
            raw_payload=new_payload,
            processed=False
        )
        
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'create_ticket':
        from service.models import ServiceTicket
        name_base = "Onboarding for " + (raw_event.customer.primary_email if raw_event.customer else "Unknown")
        ticket = ServiceTicket.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            title=name_base,
            description="Automated ticket created from Project",
            priority='high',
            status='open'
        )
        new_payload = dict(raw_event.raw_payload or {})
        new_payload['ticket_id'] = ticket.id
        new_payload['source_workflow'] = workflow.name
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            event_name='ticket.created',
            raw_payload=new_payload,
            processed=False
        )
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'create_opportunity':
        from crm.models import Deal
        payload = raw_event.raw_payload or {}
        name = "Opportunity from Lead " + str(payload.get('lead_id', 'Unknown'))
        deal = Deal.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            name=name,
            value=0.00,
            stage='prospecting'
        )
        new_payload = dict(raw_event.raw_payload or {})
        new_payload['deal_id'] = deal.id
        new_payload['source_workflow'] = workflow.name
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=raw_event.customer,
            event_name='deal.created',
            raw_payload=new_payload,
            processed=False
        )
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'create_onboarding_project':
        from projects.models import Project
        payload = raw_event.raw_payload or {}
        name = "Employee Onboarding for " + str(payload.get('email', 'Unknown'))
        project = Project.objects.create(
            company=raw_event.company,
            customer=None, # Employee doesn't have a customer necessarily
            name=name,
            status='planned'
        )
        new_payload = dict(raw_event.raw_payload or {})
        new_payload['project_id'] = project.id
        new_payload['source_workflow'] = workflow.name
        
        new_event = RawEvent.objects.create(
            company=raw_event.company,
            customer=None,
            event_name='project.created',
            raw_payload=new_payload,
            processed=False
        )
        from .tasks import process_event_task
        process_event_task.delay(new_event.id)

    elif workflow.action_type == 'send_integration_event':
        from integrations.models import Integration, IntegrationLog
        from integrations.connectors.factory import get_connector
        
        # Action payload contains integration selection
        provider = workflow.action_event_name
        integration = Integration.objects.filter(company=raw_event.company, provider=provider, status='active').first()
        
        if not integration:
            raise ValueError(f"No active integration found for provider: {provider}")
            
        connector = get_connector(integration)
        
        # Idempotency
        external_id = f"out_{raw_event.id}_{workflow.id}"
        
        log, created = IntegrationLog.objects.get_or_create(
            integration=integration,
            direction='outbound',
            correlation_id=external_id,
            defaults={
                'company': integration.company,
                'event_type': raw_event.event_name,
                'status': 'processing'
            }
        )
        
        if not created and log.status == 'success':
            return # already sent
            
        try:
            result = connector.send(raw_event.raw_payload, raw_event)
            log.status = 'success'
            log.payload_metadata = result
            log.save()
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            raise e

    else:
        raise ValueError(f"Unknown action_type: {workflow.action_type}")
