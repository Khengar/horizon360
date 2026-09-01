from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import (
    EventSchema, RawEvent, Customer, Account, Role, UserRole, AuditLog,
    Workflow, WorkflowExecution, event_name_validator
)

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'domain', 'industry', 'tier', 'annual_revenue', 'attributes', 'created_at', 'updated_at']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'is_system_default', 'created_at']

class UserRoleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user_profile.user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user_profile', 'username', 'role', 'role_name', 'assigned_at']

class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'entity_type', 'entity_id', 'diff', 'ip_address', 'user', 'username', 'user_email', 'timestamp']

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
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'account', 'account_name', 'primary_email', 'primary_phone', 'attributes', 'timeline', 'consent', 'created_at', 'updated_at']

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'trigger_event', 'is_active', 'condition_field', 'condition_operator', 'condition_value', 'action_type', 'action_event_name', 'source_biom', 'destination_biom', 'created_at']

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    class Meta:
        model = WorkflowExecution
        fields = ['id', 'workflow', 'workflow_name', 'raw_event', 'status', 'error_message', 'created_at']

from .models import (
    EventSchema, RawEvent, Customer, Account, Role, UserRole, AuditLog,
    Workflow, WorkflowExecution, Segment, event_name_validator
)

class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segment
        fields = ['id', 'name', 'description', 'rules', 'is_active', 'created_at', 'updated_at']

class CustomerMergeSerializer(serializers.Serializer):
    secondary_customer_id = serializers.UUIDField(required=True, help_text="UUID of the secondary Customer to merge into this Customer")

class RawEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawEvent
        fields = ['id', 'event_name', 'raw_payload', 'processed', 'created_at']

