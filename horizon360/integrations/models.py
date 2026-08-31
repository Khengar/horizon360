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
