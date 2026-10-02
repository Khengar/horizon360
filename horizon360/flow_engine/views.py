from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, fields
from datetime import timedelta
from .models import (
    FlowDefinition, FlowVersion, FlowNode, FlowEdge,
    FlowExecution, ApprovalRequest, FlowMarketplaceTemplate,
    SLATimer, FlowAuditLog, FlowSLAPolicy
)
from .serializers import (
    FlowDefinitionSerializer, FlowVersionSerializer, 
    FlowExecutionSerializer, ApprovalRequestSerializer,
    FlowMarketplaceTemplateSerializer, FlowAuditLogSerializer,
    FlowSLAPolicySerializer
)
from .runtime import FlowRuntime

class FlowAnalyticsView(APIView):
    """API endpoint for fetching execution and SLA analytics."""
    
    def get(self, request, *args, **kwargs):
        # 1. Overall Execution Metrics
        total_executions = FlowExecution.objects.count()
        completed = FlowExecution.objects.filter(status='completed').count()
        failed = FlowExecution.objects.filter(status='failed').count()
        
        success_rate = round((completed / total_executions * 100) if total_executions > 0 else 0, 1)
        failure_rate = round((failed / total_executions * 100) if total_executions > 0 else 0, 1)
        
        # Calculate Average Execution Time (only for completed)
        completed_execs = FlowExecution.objects.filter(status='completed', completed_at__isnull=False)
        avg_time = completed_execs.annotate(
            duration=ExpressionWrapper(F('completed_at') - F('started_at'), output_field=fields.DurationField())
        ).aggregate(Avg('duration'))['duration__avg']
        
        avg_time_seconds = avg_time.total_seconds() if avg_time else 0
        
        # 2. SLA Metrics
        total_slas = SLATimer.objects.count()
        breached = SLATimer.objects.filter(status='breached').count()
        warnings = SLATimer.objects.filter(status='warning').count()
        
        sla_breach_rate = round((breached / total_slas * 100) if total_slas > 0 else 0, 1)
        
        # 3. Executions Over Time (Last 7 Days)
        today = timezone.now().date()
        executions_over_time = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_execs = FlowExecution.objects.filter(started_at__date=day)
            executions_over_time.append({
                'date': day.strftime('%b %d'),
                'total': day_execs.count(),
                'success': day_execs.filter(status='completed').count(),
                'failed': day_execs.filter(status='failed').count()
            })
            
        return Response({
            'total_executions': total_executions,
            'success_rate': success_rate,
            'failure_rate': failure_rate,
            'avg_execution_seconds': round(avg_time_seconds, 1),
            'sla_metrics': {
                'total_monitored': total_slas,
                'breaches': breached,
                'warnings': warnings,
                'breach_rate': sla_breach_rate
            },
            'executions_over_time': executions_over_time
        })

class FlowDefinitionViewSet(viewsets.ModelViewSet):
    """API endpoint that allows workflows to be viewed or edited."""
    serializer_class = FlowDefinitionSerializer
    
    def get_queryset(self):
        # In a real app we filter by request.user.company
        return FlowDefinition.objects.all()
        
    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """Manually trigger a workflow execution."""
        flow = self.get_object()
        payload = request.data.get('payload', {})
        
        try:
            runtime = FlowRuntime()
            execution = runtime.start_execution(
                flow_id=flow.id, 
                trigger_payload=payload, 
                triggered_by=request.user if request.user.is_authenticated else None
            )
            return Response({
                'execution_id': execution.id, 
                'status': execution.status
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'])
    def update_trigger(self, request, pk=None):
        """Update the trigger configuration for the flow."""
        flow = self.get_object()
        trigger_type = request.data.get('trigger_type')
        if trigger_type:
            flow.trigger_type = trigger_type
        
        if 'trigger_schedule' in request.data:
            flow.trigger_schedule = request.data.get('trigger_schedule')
        if 'trigger_event' in request.data:
            flow.trigger_event = request.data.get('trigger_event')
        
        trigger_config = request.data.get('trigger_config')
        if isinstance(trigger_config, dict):
            flow.trigger_config = trigger_config
            
        flow.save()
        return Response(FlowDefinitionSerializer(flow).data)
        
class FlowVersionViewSet(viewsets.ModelViewSet):
    """API endpoint for managing specific flow versions and canvas state."""
    serializer_class = FlowVersionSerializer
    queryset = FlowVersion.objects.all()
    
    @action(detail=True, methods=['put'])
    def canvas(self, request, pk=None):
        """Save nodes and edges from the React Flow designer."""
        version = self.get_object()
        nodes_data = request.data.get('nodes', [])
        edges_data = request.data.get('edges', [])
        
        # Clear existing
        version.nodes.all().delete()
        version.edges.all().delete()
        
        # Recreate nodes
        for n in nodes_data:
            FlowNode.objects.create(
                version=version,
                canvas_node_id=n.get('id'),
                node_type=n.get('type', 'action'),
                label=n.get('data', {}).get('label', 'Node'),
                position_x=n.get('position', {}).get('x', 0),
                position_y=n.get('position', {}).get('y', 0),
                config=n.get('data', {}).get('config', {})
            )
            
        # Recreate edges
        for e in edges_data:
            FlowEdge.objects.create(
                version=version,
                edge_id=e.get('id'),
                source_node=e.get('source'),
                target_node=e.get('target'),
                source_handle=e.get('sourceHandle', ''),
                label=e.get('label', '')
            )
            
        return Response({'status': 'canvas saved successfully'})

class FlowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view for tracking executions and step traces."""
    serializer_class = FlowExecutionSerializer
    queryset = FlowExecution.objects.all()
    
class ApprovalRequestViewSet(viewsets.ModelViewSet):
    """Endpoint for human-in-the-loop tasks."""
    serializer_class = ApprovalRequestSerializer
    queryset = ApprovalRequest.objects.all()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        approval = self.get_object()
        comment = request.data.get('comment', '')
        
        # We would typically call an ApprovalEngine here
        approval.status = 'approved'
        approval.resolved_at = timezone.now()
        approval.save()
        
        # Resume the DAG execution
        from .tasks import execute_node_task
        step = approval.step_execution
        step.status = 'completed'
        step.output_data = {'action': 'approved', 'comment': comment}
        step.save()
        
        # Advance DAG to next node
        runtime = FlowRuntime()
        execution = step.execution
        execution.context['node_outputs'][step.canvas_node_id] = step.output_data
        execution.save()
        
        next_nodes = runtime._resolve_next_nodes(step.node, type('obj', (object,), {'output': step.output_data}), execution)
        for next_id in next_nodes:
            execute_node_task.delay(str(execution.id), next_id)
            
        return Response({'status': 'approved'})
        
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        approval = self.get_object()
        approval.status = 'rejected'
        approval.resolved_at = timezone.now()
        approval.save()
        
        step = approval.step_execution
        step.status = 'failed'
        step.error_message = f"Approval rejected by {request.user.username if request.user.is_authenticated else 'system'}"
        step.save()
        
        execution = step.execution
        execution.status = 'failed'
        execution.error_message = step.error_message
        execution.save()
        
        return Response({'status': 'rejected'})
        
class FlowMarketplaceTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Browse pre-built cross-BIOM automation templates."""
    serializer_class = FlowMarketplaceTemplateSerializer
    queryset = FlowMarketplaceTemplate.objects.all()

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class WebhookReceiverView(APIView):
    """Receive external webhook events and trigger the associated flow."""
    permission_classes = [AllowAny]
    
    def post(self, request, flow_id):
        try:
            flow = FlowDefinition.objects.get(id=flow_id, is_active=True, trigger_type='webhook')
        except FlowDefinition.DoesNotExist:
            return Response({'error': 'Active webhook flow not found.'}, status=404)
            
        # Optional: Validate secret token if configured
        secret = flow.trigger_config.get('secret')
        if secret:
            auth_header = request.headers.get('Authorization', '')
            if auth_header != f"Bearer {secret}":
                return Response({'error': 'Unauthorized webhook.'}, status=401)
                
        # Trigger the flow
        from .runtime import FlowRuntime
        runtime = FlowRuntime()
        payload = request.data
        if not isinstance(payload, dict):
            payload = {'data': payload}
            
        # Inject standard webhook metadata
        payload['_webhook_metadata'] = {
            'method': request.method,
            'headers': dict(request.headers),
            'query_params': request.query_params.dict()
        }
        
        execution = runtime.start_execution(flow.id, trigger_payload=payload)
        return Response({'status': 'accepted', 'execution_id': str(execution.id)}, status=202)

class FlowAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FlowAuditLogSerializer
    queryset = FlowAuditLog.objects.all().order_by('-created_at')

class FlowSLAPolicyViewSet(viewsets.ModelViewSet):
    serializer_class = FlowSLAPolicySerializer
    
    def get_queryset(self):
        qs = FlowSLAPolicy.objects.all()
        flow_id = self.request.query_params.get('flow')
        if flow_id:
            qs = qs.filter(flow_id=flow_id)
        return qs


