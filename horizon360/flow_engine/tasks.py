import logging
from celery import shared_task
from django.utils import timezone
import uuid

logger = logging.getLogger(__name__)

@shared_task(name='flow_engine.execute_node_task')
def execute_node_task(execution_id: str, canvas_node_id: str):
    """Executes a single node in a workflow DAG."""
    from .runtime import FlowRuntime
    try:
        runtime = FlowRuntime()
        runtime.execute_node(execution_id, canvas_node_id)
    except Exception as e:
        logger.exception(f"Failed to execute node {canvas_node_id} for execution {execution_id}: {e}")
        # In a robust system, we would mark the execution as failed if this outer wrapper crashes.


@shared_task(name='flow_engine.check_sla_timers')
def check_sla_timers():
    """Periodic task (e.g. every 60s) to check SLA warnings and breaches."""
    from .models import SLATimer, FlowExecution
    from .runtime import FlowRuntime
    from django.utils import timezone
    
    now = timezone.now()
    
    # 1. Process Breaches
    breached_timers = SLATimer.objects.filter(
        status__in=['active', 'warning'],
        breach_at__lte=now
    )
    
    for timer in breached_timers:
        logger.warning(f"SLA Breach for execution {timer.execution.id}")
        timer.status = 'breached'
        timer.save(update_fields=['status'])
        
        # Execute breach action
        action = timer.policy.breach_action
        if action:
            _handle_sla_action(timer, action)
            
    # 2. Process Warnings
    warning_timers = SLATimer.objects.filter(
        status='active',
        warning_at__lte=now
    )
    
    for timer in warning_timers:
        logger.info(f"SLA Warning for execution {timer.execution.id}")
        timer.status = 'warning'
        timer.save(update_fields=['status'])
        
        # Execute warning action
        action = timer.policy.warning_action
        if action:
            _handle_sla_action(timer, action)

def _handle_sla_action(timer, action):
    """Executes the action defined in the SLA policy (e.g. notify, jump to node)."""
    from .runtime import FlowRuntime
    action_type = action.get('type')
    
    if action_type == 'notify':
        # E.g. Send an email or in-app notification
        # For now, we simulate this via a log
        message = action.get('message', 'SLA Alert')
        logger.info(f"SLA Notification: {message} for execution {timer.execution.id}")
        
    elif action_type == 'jump':
        # Jump to a specific node in the current flow
        target_node_id = action.get('node_id')
        if target_node_id:
            logger.info(f"SLA Escalation: Jumping to node {target_node_id}")
            # Enqueue the node for execution
            execute_node_task.delay(str(timer.execution.id), target_node_id)
            
    elif action_type == 'cancel':
        # Terminate the execution
        timer.execution.status = 'failed'
        timer.execution.error_message = 'Terminated due to SLA breach'
        timer.execution.save(update_fields=['status', 'error_message'])

@shared_task(name='flow_engine.check_scheduled_flows')
def check_scheduled_flows():
    """Periodic task (every 60s) to trigger cron-based flows."""
    from .models import FlowDefinition
    from .runtime import FlowRuntime
    from croniter import croniter
    import datetime
    
    # We round down to the nearest minute to avoid skipping or double-triggering
    now = timezone.now().replace(second=0, microsecond=0)
    
    cron_flows = FlowDefinition.objects.filter(is_active=True, trigger_type='schedule')
    
    runtime = FlowRuntime()
    
    for flow in cron_flows:
        cron_expr = flow.trigger_schedule
        if not cron_expr:
            continue
            
        try:
            # croniter checks if the current datetime matches the cron expression
            if croniter.match(cron_expr, now):
                logger.info(f"Triggering scheduled flow: {flow.name} ({flow.id})")
                
                payload = {
                    '_scheduled_time': now.isoformat(),
                    '_cron_expression': cron_expr
                }
                
                runtime.start_execution(flow.id, trigger_payload=payload)
        except Exception as e:
            logger.error(f"Failed to process cron expression '{cron_expr}' for flow {flow.id}: {e}")

