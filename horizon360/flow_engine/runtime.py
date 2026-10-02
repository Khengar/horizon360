import logging
from uuid import UUID
from django.utils import timezone
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import FlowDefinition, FlowExecution, StepExecution, FlowAuditLog
from .handlers import get_handler

logger = logging.getLogger(__name__)

def broadcast_execution_update(execution_id, payload):
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'execution_{str(execution_id)}',
            {
                'type': 'execution_update',
                'message': payload
            }
        )

class FlowRuntime:
    """DAG-based workflow executor."""
    
    def start_execution(self, flow_id: UUID, trigger_payload: dict, triggered_by: User = None) -> FlowExecution:
        """Create a new execution and begin processing."""
        flow = FlowDefinition.objects.get(id=flow_id, is_active=True)
        version = flow.versions.filter(status='published').first()
        
        if not version:
            raise ValueError(f"No published version found for flow {flow_id}")
            
        # Build idempotency key (e.g. flow_id:event_id)
        event_id = trigger_payload.get('event_id', None)
        idem_key = f"{flow_id}:{event_id}" if event_id else f"{flow_id}:{timezone.now().timestamp()}"
        
        execution, created = FlowExecution.objects.get_or_create(
            idempotency_key=idem_key,
            defaults={
                'flow': flow,
                'version': version,
                'company': flow.company,
                'status': 'running',
                'trigger_payload': trigger_payload,
                'triggered_by': triggered_by,
                'context': {
                    'trigger': {'payload': trigger_payload},
                    'variables': {},
                    'node_outputs': {},
                },
            }
        )
        
        if not created:
            logger.info(f"Execution already exists for idempotency key {idem_key}")
            return execution
            
        # Find the trigger node and start execution
        trigger_node = version.nodes.filter(node_type='trigger').first()
        if trigger_node:
            execution.started_at = timezone.now()
            execution.save()
            
            FlowAuditLog.objects.create(
                company=flow.company,
                event_type='execution.started',
                actor=triggered_by,
                actor_type='user' if triggered_by else 'system',
                flow_id=flow.id,
                execution_id=execution.id,
                description=f"Flow execution {execution.id} started via trigger.",
                metadata={'trigger_payload': trigger_payload}
            )
            
            # --- Initialize flow-level SLAs ---
            for policy in flow.sla_policies.filter(is_active=True, scope='flow'):
                from datetime import timedelta
                from .models import SLATimer
                SLATimer.objects.create(
                    execution=execution,
                    policy=policy,
                    warning_at=execution.started_at + timedelta(minutes=policy.warning_threshold_minutes),
                    breach_at=execution.started_at + timedelta(minutes=policy.breach_threshold_minutes),
                )
            
            # Import inline to avoid circular imports
            from .tasks import execute_node_task
            execute_node_task.delay(str(execution.id), trigger_node.canvas_node_id)
            
        return execution
        
    def execute_node(self, execution_id: str, canvas_node_id: str):
        """Execute a single node and advance the DAG."""
        execution = FlowExecution.objects.select_for_update().get(id=execution_id)
        
        if execution.status not in ['running', 'pending']:
            logger.warning(f"Execution {execution_id} is in status {execution.status}, skipping node {canvas_node_id}")
            return
            
        node = execution.version.nodes.get(canvas_node_id=canvas_node_id)
        
        # Create step execution record
        step = StepExecution.objects.create(
            execution=execution, 
            node=node, 
            canvas_node_id=canvas_node_id,
            status='running', 
            started_at=timezone.now(),
            input_data={'context': execution.context} # Snapshot of current state
        )
        
        broadcast_execution_update(execution.id, {
            'event': 'step_started',
            'node_id': canvas_node_id,
            'status': 'running'
        })
        
        try:
            handler = get_handler(node.node_type)
            result = handler.execute(node, step, execution)
            
            if result.status == 'waiting':
                # E.g. Approval node - pause execution branch
                step.status = 'waiting'
                step.save()
                
                broadcast_execution_update(execution.id, {
                    'event': 'step_waiting',
                    'node_id': canvas_node_id,
                    'status': 'waiting'
                })
                
                # --- Initialize node-level SLAs ---
                for policy in execution.flow.sla_policies.filter(is_active=True, scope='node', target_node_id=canvas_node_id):
                    from datetime import timedelta
                    from .models import SLATimer
                    SLATimer.objects.create(
                        execution=execution,
                        policy=policy,
                        step_execution=step,
                        warning_at=timezone.now() + timedelta(minutes=policy.warning_threshold_minutes),
                        breach_at=timezone.now() + timedelta(minutes=policy.breach_threshold_minutes),
                    )
                
                execution.status = result.execution_status 
                execution.current_node_id = canvas_node_id
                execution.save()
                return
                
            # Node completed successfully
            step.status = 'completed'
            step.output_data = result.output
            step.completed_at = timezone.now()
            if step.started_at:
                step.duration_ms = int((step.completed_at - step.started_at).total_seconds() * 1000)
            step.save()
            
            # Broadcast WebSocket event
            broadcast_execution_update(execution.id, {
                'event': 'step_completed',
                'node_id': canvas_node_id,
                'status': 'completed',
                'output': step.output_data
            })
            
            # Resolve Node-Level SLA Timers
            from .models import SLATimer
            SLATimer.objects.filter(step_execution=step, status__in=['active', 'warning']).update(
                status='resolved',
                resolved_at=timezone.now()
            )
            
            # Update shared execution context
            execution.context['node_outputs'][canvas_node_id] = result.output
            if result.variables:
                execution.context['variables'].update(result.variables)
            execution.save()
            
            # Find and schedule next nodes
            next_nodes = self._resolve_next_nodes(node, result, execution)
            
            if not next_nodes:
                # Reached an end node or a node with no outgoing edges
                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.save()
                
                # Resolve Flow-Level SLA Timers
                SLATimer.objects.filter(execution=execution, status__in=['active', 'warning']).update(
                    status='resolved',
                    resolved_at=timezone.now()
                )
                
                FlowAuditLog.objects.create(
                    company=execution.company,
                    event_type='execution.completed',
                    actor_type='system',
                    flow_id=execution.flow.id,
                    execution_id=execution.id,
                    description=f"Flow execution {execution.id} completed successfully."
                )
                
                return
                
            from .tasks import execute_node_task
            for next_node_id in next_nodes:
                target_node = execution.version.nodes.get(canvas_node_id=next_node_id)
                
                if target_node.node_type == 'parallel_join':
                    # Parallel AND-Join: Wait for all incoming edges to complete
                    incoming_edges = execution.version.edges.filter(target_node=next_node_id)
                    source_ids = [e.source_node for e in incoming_edges]
                    
                    completed_sources = execution.steps.filter(
                        canvas_node_id__in=source_ids,
                        status='completed'
                    ).values_list('canvas_node_id', flat=True)
                    
                    if len(set(completed_sources)) >= len(set(source_ids)):
                        logger.info(f"Join node {next_node_id} conditions met. Firing.")
                        execute_node_task.delay(str(execution.id), next_node_id)
                    else:
                        logger.info(f"Join node {next_node_id} waiting on other branches. ({len(set(completed_sources))}/{len(set(source_ids))})")
                else:
                    # Normal XOR-Join or single incoming edge behavior
                    execute_node_task.delay(str(execution.id), next_node_id)
                
        except Exception as e:
            self._handle_failure(step, execution, node, e)
            
    def _resolve_next_nodes(self, node, result, execution):
        """Determine which nodes to execute next based on edges and conditions."""
        edges = execution.version.edges.filter(source_node=node.canvas_node_id)
        
        if node.node_type == 'condition':
            # Route based on condition result (true/false handle)
            condition_met = result.output.get('condition_met', False)
            handle = 'true' if condition_met else 'false'
            edges = edges.filter(source_handle=handle)
            
        elif node.node_type == 'switch':
            # Route based on matched case
            matched_case = result.output.get('matched_case', 'default')
            edges = edges.filter(source_handle=matched_case)
            
        return [edge.target_node for edge in edges]
        
    def _handle_failure(self, step, execution, node, error):
        """Handle node failure with retry logic."""
        logger.error(f"Node {node.canvas_node_id} failed: {error}")
        step.error_message = str(error)
        step.status = 'failed'
        step.save()
        
        broadcast_execution_update(execution.id, {
            'event': 'step_failed',
            'node_id': node.canvas_node_id,
            'status': 'failed',
            'error': str(error)
        })
        
        if step.attempt_number < node.max_retries:
            # Retry with exponential backoff
            delay = node.retry_delay_seconds * (2 ** (step.attempt_number - 1))
            logger.info(f"Retrying node {node.canvas_node_id} in {delay}s (Attempt {step.attempt_number + 1})")
            
            from .tasks import execute_node_task
            execute_node_task.apply_async(
                args=[str(execution.id), node.canvas_node_id],
                countdown=delay
            )
            step.attempt_number += 1
            step.status = 'pending'
            step.save()
        else:
            # Max retries exceeded
            execution.status = 'failed'
            execution.error_message = f"Node {node.canvas_node_id} failed: {str(error)}"
            execution.save()
            
            FlowAuditLog.objects.create(
                company=execution.company,
                event_type='execution.failed',
                actor_type='system',
                flow_id=execution.flow.id,
                execution_id=execution.id,
                step_id=step.id,
                description=f"Flow execution failed at node {node.canvas_node_id}.",
                metadata={'error': str(error)}
            )
            
            # Resolve Flow-Level SLA Timers
            from .models import SLATimer
            SLATimer.objects.filter(execution=execution, status__in=['active', 'warning']).update(
                status='resolved',
                resolved_at=timezone.now()
            )
