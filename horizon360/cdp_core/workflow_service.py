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
            defaults={'status': 'failed'} # We will update this immediately
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
        # Simple operator parsing
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
        # Avoid infinite loops by not letting invoice.requested trigger itself
        # This is handled naturally if trigger_event != action_event_name
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
    else:
        raise ValueError(f"Unknown action_type: {workflow.action_type}")
