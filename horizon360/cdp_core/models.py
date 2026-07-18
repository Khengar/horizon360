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
        unique=True,
        validators=[event_name_validator],
        help_text="Enforces domain.action naming convention (e.g., user.logged_in)"
    )
    json_schema = models.JSONField(
        help_text="JSON schema validating raw payload for this event type"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.event_name


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    primary_email = models.EmailField(null=True, blank=True, unique=True)
    primary_phone = models.CharField(max_length=50, null=True, blank=True, unique=True)
    attributes = models.JSONField(default=dict, blank=True)
    timeline = models.JSONField(default=list, blank=True)
    consent = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def __str__(self):
        return f"{self.event_name} (ID: {self.id}, processed={self.processed})"
