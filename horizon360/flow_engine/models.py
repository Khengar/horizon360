import uuid
from django.db import models
from django.contrib.auth.models import User
from cdp_core.models import Company, RawEvent

class FlowDefinition(models.Model):
    """Top-level workflow definition. Immutable once published via versions."""
    
    CATEGORY_CHOICES = [
        ('cross_biom', 'Cross-BIOM Automation'),
        ('approval', 'Approval Workflow'),
        ('onboarding', 'Onboarding'),
        ('escalation', 'Escalation'),
        ('notification', 'Notification'),
        ('ai_triggered', 'AI-Triggered'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='flow_definitions')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='custom')
    is_active = models.BooleanField(default=False)
    is_template = models.BooleanField(default=False)  # Marketplace template
    
    # Trigger configuration
    trigger_type = models.CharField(max_length=50, choices=[
        ('event', 'Domain Event'),
        ('schedule', 'Cron Schedule'),
        ('manual', 'Manual Trigger'),
        ('ai', 'AI Agent Trigger'),
        ('webhook', 'Inbound Webhook'),
    ])
    trigger_event = models.CharField(max_length=255, blank=True)  # e.g. "deal.won"
    trigger_schedule = models.CharField(max_length=100, blank=True)  # cron expression
    trigger_config = models.JSONField(default=dict, blank=True)  # extra trigger params
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)  # ["finance", "approval", "urgent"]
    icon = models.CharField(max_length=50, default='zap')  # Lucide icon name
    color = models.CharField(max_length=7, default='#6366f1')  # Hex color
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class FlowVersion(models.Model):
    """Immutable snapshot of a flow definition. Executions always reference a version."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # The full canvas state (React Flow serialization)
    canvas_data = models.JSONField(default=dict)  # {viewport, nodes_layout}
    
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('flow', 'version_number')
        ordering = ['-version_number']


class FlowNode(models.Model):
    """Single node in the workflow DAG."""
    
    NODE_TYPES = [
        # Control flow
        ('trigger', 'Trigger'),
        ('condition', 'Condition (If/Else)'),
        ('switch', 'Switch (Multi-Branch)'),
        ('delay', 'Delay / Timer'),
        ('parallel_fork', 'Parallel Fork'),
        ('parallel_join', 'Parallel Join'),
        ('loop', 'Loop / Iterator'),
        ('end', 'End'),
        
        # Actions
        ('action', 'BIOM Action'),
        ('ai_action', 'AI Action'),
        ('http_request', 'HTTP Request'),
        ('transform', 'Data Transform'),
        ('notification', 'Send Notification'),
        
        # Human-in-the-loop
        ('approval', 'Approval Gate'),
        ('manual_task', 'Manual Task'),
        ('form_input', 'Form Input'),
        
        # Integration
        ('integration', 'Integration Action'),
        ('webhook_out', 'Outbound Webhook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(FlowVersion, on_delete=models.CASCADE, related_name='nodes')
    canvas_node_id = models.CharField(max_length=100)  # React Flow node ID (e.g. "node-1")
    node_type = models.CharField(max_length=50, choices=NODE_TYPES)
    label = models.CharField(max_length=255)
    
    # Position on canvas
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    
    # Node-specific configuration (varies by type)
    config = models.JSONField(default=dict)
    
    # Retry configuration
    max_retries = models.PositiveIntegerField(default=3)
    retry_delay_seconds = models.PositiveIntegerField(default=60)
    
    # Compensation (saga pattern) - action to execute on rollback
    compensation_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ('version', 'canvas_node_id')
        ordering = ['position_y', 'position_x']


class FlowEdge(models.Model):
    """Directed edge connecting two nodes in the DAG."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.ForeignKey(FlowVersion, on_delete=models.CASCADE, related_name='edges')
    edge_id = models.CharField(max_length=100)  # React Flow edge ID
    source_node = models.CharField(max_length=100)  # source node_id
    target_node = models.CharField(max_length=100)  # target node_id
    source_handle = models.CharField(max_length=50, blank=True)  # e.g. "true", "false"
    label = models.CharField(max_length=255, blank=True)  # Edge label
    condition = models.JSONField(default=dict, blank=True)  # Optional edge-level condition
    
    class Meta:
        unique_together = ('version', 'edge_id')


# ─── Execution Models ─────────────────────────────────────────────

class FlowExecution(models.Model):
    """One run of a workflow."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('waiting_approval', 'Waiting for Approval'),
        ('waiting_input', 'Waiting for Input'),
        ('waiting_delay', 'Waiting (Delayed)'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('compensating', 'Compensating (Rollback)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name='executions')
    version = models.ForeignKey(FlowVersion, on_delete=models.CASCADE, related_name='executions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    
    # Trigger context
    trigger_event = models.ForeignKey(RawEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name='flow_executions')
    trigger_payload = models.JSONField(default=dict)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Execution context - shared state across all nodes
    context = models.JSONField(default=dict)
    
    # Idempotency
    idempotency_key = models.CharField(max_length=255, unique=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Current position in DAG
    current_node_id = models.CharField(max_length=100, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['flow', '-created_at']),
        ]


class StepExecution(models.Model):
    """Execution record for a single node within a flow run."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('waiting', 'Waiting'),
        ('compensated', 'Compensated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(FlowExecution, on_delete=models.CASCADE, related_name='steps')
    node = models.ForeignKey(FlowNode, on_delete=models.CASCADE)
    canvas_node_id = models.CharField(max_length=100)  # Denormalized for fast lookup
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Input/output for this step
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error & retry
    error_message = models.TextField(blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['execution', 'node_id']),
        ]


# ─── Approval Models ──────────────────────────────────────────────

class ApprovalRequest(models.Model):
    """A pending approval tied to a workflow step execution."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('escalated', 'Escalated'),
        ('delegated', 'Delegated'),
        ('expired', 'Expired'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step_execution = models.OneToOneField(StepExecution, on_delete=models.CASCADE, related_name='approval')
    execution = models.ForeignKey(FlowExecution, on_delete=models.CASCADE, related_name='approvals')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # What is being approved
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    context_data = models.JSONField(default=dict)  # Approval form data to display
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Approver chain
    current_approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                          related_name='pending_approvals')
    approver_role = models.CharField(max_length=100, blank=True)  # Role-based assignment
    approval_level = models.PositiveIntegerField(default=1)  # Current level in chain
    max_levels = models.PositiveIntegerField(default=1)  # Total approval levels
    
    # SLA / Escalation
    deadline = models.DateTimeField(null=True, blank=True)
    escalation_role = models.CharField(max_length=100, blank=True)
    escalation_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='escalation_approvals')
    
    # Delegation
    delegated_from = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='delegated_approvals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['current_approver', 'status']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['deadline']),
        ]


class ApprovalAction(models.Model):
    """Audit record for every action taken on an approval."""
    
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delegated', 'Delegated'),
        ('escalated', 'Escalated'),
        ('commented', 'Commented'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    approval = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name='actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # e.g. delegation target
    created_at = models.DateTimeField(auto_now_add=True)


# ─── SLA Models ────────────────────────────────────────────────────

class FlowSLAPolicy(models.Model):
    """SLA policy attached to a flow or specific node."""
    
    SCOPE_CHOICES = [
        ('flow', 'Entire Flow'),
        ('node', 'Specific Node'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(FlowDefinition, on_delete=models.CASCADE, related_name='sla_policies')
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    target_node_id = models.CharField(max_length=100, blank=True)  # For node-scoped SLAs
    
    name = models.CharField(max_length=255)
    
    # Time limits
    warning_threshold_minutes = models.PositiveIntegerField(default=60)
    breach_threshold_minutes = models.PositiveIntegerField(default=240)
    
    # Escalation actions
    warning_action = models.JSONField(default=dict)
    breach_action = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SLATimer(models.Model):
    """Active timer tracking SLA compliance for a running execution."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('warning', 'Warning Sent'),
        ('breached', 'Breached'),
        ('resolved', 'Resolved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(FlowExecution, on_delete=models.CASCADE, related_name='sla_timers')
    policy = models.ForeignKey(FlowSLAPolicy, on_delete=models.CASCADE)
    step_execution = models.ForeignKey(StepExecution, on_delete=models.CASCADE, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    started_at = models.DateTimeField(auto_now_add=True)
    warning_at = models.DateTimeField()
    breach_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'warning_at']),
            models.Index(fields=['status', 'breach_at']),
        ]


# ─── Marketplace Models ───────────────────────────────────────────

class FlowMarketplaceTemplate(models.Model):
    """Curated workflow template available in the marketplace."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50)
    
    # The full serialized flow definition for import
    template_data = models.JSONField()
    
    # Metadata
    source_bioms = models.JSONField(default=list)  # ["Sales", "Finance"]
    target_bioms = models.JSONField(default=list)  # ["Finance", "Projects"]
    tags = models.JSONField(default=list)
    icon = models.CharField(max_length=50, default='zap')
    
    # Usage stats
    install_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0)
    
    is_official = models.BooleanField(default=True)  # Horizon-provided vs community
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-install_count']


class FlowAuditLog(models.Model):
    """Immutable audit record for every flow engine action."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # What
    event_type = models.CharField(max_length=100)  
    
    # Who
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_type = models.CharField(max_length=20)  # user, system, ai_agent, scheduler
    
    # Where
    flow_id = models.UUIDField(null=True, blank=True)
    execution_id = models.UUIDField(null=True, blank=True)
    step_id = models.UUIDField(null=True, blank=True)
    
    # Details
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    # Immutable timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['flow_id', '-created_at']),
            models.Index(fields=['execution_id', '-created_at']),
        ]
