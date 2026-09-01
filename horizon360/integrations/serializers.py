from rest_framework import serializers
from .models import Integration, IntegrationLog, WebhookSubscription, WebhookDeliveryLog

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ['id', 'name', 'provider', 'direction', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Redact config if included
        return ret

class IntegrationLogSerializer(serializers.ModelSerializer):
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    
    class Meta:
        model = IntegrationLog
        fields = ['id', 'integration', 'integration_name', 'direction', 'event_type', 'status', 'payload_metadata', 'error_message', 'correlation_id', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        fields = ['id', 'target_url', 'secret', 'subscribed_events', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WebhookDeliveryLogSerializer(serializers.ModelSerializer):
    target_url = serializers.CharField(source='subscription.target_url', read_only=True)

    class Meta:
        model = WebhookDeliveryLog
        fields = ['id', 'subscription', 'target_url', 'event_name', 'payload', 'response_status', 'response_body', 'success', 'delivered_at']
        read_only_fields = ['id', 'delivered_at']

