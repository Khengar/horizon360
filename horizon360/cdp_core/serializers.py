from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import EventSchema, RawEvent, Customer, event_name_validator

class EventSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSchema
        fields = ['id', 'event_name', 'json_schema', 'created_at', 'updated_at']

class EventIngestionSerializer(serializers.Serializer):
    event_name = serializers.CharField(
        max_length=255,
        validators=[event_name_validator]
    )
    raw_payload = serializers.JSONField()

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'primary_email', 'primary_phone', 'attributes', 'timeline', 'created_at', 'updated_at']

from .models import Workflow, WorkflowExecution

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'trigger_event', 'is_active', 'condition_field', 'condition_operator', 'condition_value', 'action_type', 'action_event_name', 'source_biom', 'destination_biom', 'created_at']

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    class Meta:
        model = WorkflowExecution
        fields = ['id', 'workflow', 'workflow_name', 'raw_event', 'status', 'error_message', 'created_at']

