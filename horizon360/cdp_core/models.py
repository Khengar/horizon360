import uuid
import uuid
from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    name = models.CharField(max_length=255)
    api_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True, help_text="Uncheck to revoke API access.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"
from django.core.validators import RegexValidator

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
