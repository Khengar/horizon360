import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Company(models.Model):
    name = models.CharField(max_length=255)
    api_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    plan = models.CharField(max_length=50, default='growth', help_text="Tenant subscription plan (starter, growth, enterprise)")
    config = models.JSONField(default=dict, blank=True, help_text="Tenant-level system and UI configuration")
    is_active = models.BooleanField(default=True, help_text="Uncheck to revoke API access.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tenant_id(self):
        return self.id

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"

class Role(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of permission codes e.g. ['crm.view', 'crm.edit', 'finance.admin']"
    )
    is_system_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class UserRole(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='assigned_users')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'role')

    def __str__(self):
        return f"{self.user_profile.user.username} -> {self.role.name}"

class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    tier = models.CharField(max_length=50, default='standard')
    annual_revenue = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.company.name})"

# Regex validator for event_name: domain.action
# Must contain at least one dot, use lowercase letters, and have no spaces.
event_name_validator = RegexValidator(
    regex=r'^[a-z0-9_]+(?:\.[a-z0-9_]+)+$',
    message='Event name must contain at least one dot, use lowercase letters, and have no spaces.'
)

class EventSchema(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    event_name = models.CharField(
        max_length=255,
        validators=[event_name_validator],
        help_text="Enforces domain.action naming convention (e.g., user.logged_in)"
    )
    json_schema = models.JSONField(
        help_text="JSON schema validating raw payload for this event type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'event_name')

    def __str__(self):
        return self.event_name


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    primary_email = models.EmailField(null=True, blank=True)
    primary_phone = models.CharField(max_length=50, null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    timeline = models.JSONField(default=list, blank=True)
    consent = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'primary_email'], name='unique_company_email'),
            models.UniqueConstraint(fields=['company', 'primary_phone'], name='unique_company_phone')
        ]

    def __str__(self):
        return f"Customer {self.id} ({self.primary_email or self.primary_phone or 'Anonymous'})"


class RawEvent(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    event_name = models.CharField(max_length=255)
    raw_payload = models.JSONField()
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='raw_events')
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.company and self.customer and self.customer.company != self.company:
            raise ValidationError("RawEvent company must match Customer company.")

    def save(self, *args, **kwargs):
        if not self.company and self.customer:
            self.company = self.customer.company
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_name} (ID: {self.id}, processed={self.processed})"

class Workflow(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='workflows')
    name = models.CharField(max_length=255)
    trigger_event = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    condition_field = models.CharField(max_length=255, blank=True)
    condition_operator = models.CharField(max_length=50, blank=True)
    condition_value = models.CharField(max_length=255, blank=True)
    action_type = models.CharField(max_length=255)
    action_event_name = models.CharField(max_length=255)
    source_biom = models.CharField(max_length=50, blank=True)
    destination_biom = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class WorkflowExecution(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    raw_event = models.ForeignKey(RawEvent, on_delete=models.CASCADE, related_name='workflow_executions')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workflow', 'raw_event')

    def __str__(self):
        return f"{self.workflow.name} on {self.raw_event.id} - {self.status}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('merge', 'Merge'),
        ('export', 'Export'),
        ('access', 'Access'),
        ('anonymize', 'Anonymize'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=255, db_index=True)
    diff = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.action.upper()}] {self.entity_type} ({self.entity_id}) by {self.user or 'System'}"

class Segment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='segments')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rules = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of rules e.g. [{'field': 'attributes.tier', 'operator': '==', 'value': 'enterprise'}]"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.company.name})"


