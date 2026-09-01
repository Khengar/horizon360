from django.db import models
from cdp_core.models import Company
import uuid

class Integration(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error')
    ]
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('bi_directional', 'Bi-Directional')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='integrations')
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=100) # e.g. stripe_demo, hubspot_demo
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='bi_directional')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    config = models.JSONField(default=dict, blank=True) # stores webhook_secret, api_key, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"

class IntegrationLog(models.Model):
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('processing', 'Processing')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='integration_logs')
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, related_name='logs')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    event_type = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payload_metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    correlation_id = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['integration', 'direction', 'correlation_id'], name='unique_integration_correlation')
        ]

    def __str__(self):
        return f"{self.direction} | {self.integration.name} | {self.status}"


import secrets

def default_webhook_secret():
    return secrets.token_hex(20)

class WebhookSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='webhook_subscriptions')
    target_url = models.URLField(max_length=500)
    secret = models.CharField(max_length=100, default=default_webhook_secret)
    subscribed_events = models.JSONField(default=list, help_text="List of event names or ['*'] for wildcard")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook: {self.target_url} ({'Active' if self.is_active else 'Inactive'})"


class WebhookDeliveryLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(WebhookSubscription, on_delete=models.CASCADE, related_name='delivery_logs')
    event_name = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-delivered_at']

    def __str__(self):
        return f"[{'SUCCESS' if self.success else 'FAILED'}] {self.event_name} -> {self.subscription.target_url} ({self.response_status})"

