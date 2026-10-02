from rest_framework import serializers
from .models import (
    FlowDefinition, FlowVersion, FlowNode, FlowEdge,
    FlowExecution, StepExecution, ApprovalRequest, FlowMarketplaceTemplate,
    FlowAuditLog, FlowSLAPolicy
)

class FlowAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowAuditLog
        fields = '__all__'

class FlowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowNode
        fields = '__all__'

class FlowEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowEdge
        fields = '__all__'

class FlowVersionSerializer(serializers.ModelSerializer):
    nodes = FlowNodeSerializer(many=True, read_only=True)
    edges = FlowEdgeSerializer(many=True, read_only=True)
    
    class Meta:
        model = FlowVersion
        fields = '__all__'

class FlowDefinitionSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    
    class Meta:
        model = FlowDefinition
        fields = '__all__'
        
    def get_latest_version(self, obj):
        version = obj.versions.first()
        return FlowVersionSerializer(version).data if version else None

class StepExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepExecution
        fields = '__all__'

class FlowExecutionSerializer(serializers.ModelSerializer):
    steps = StepExecutionSerializer(many=True, read_only=True)
    version_data = FlowVersionSerializer(source='version', read_only=True)
    
    class Meta:
        model = FlowExecution
        fields = '__all__'

class ApprovalRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        
class FlowMarketplaceTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowMarketplaceTemplate
        fields = '__all__'

class FlowSLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowSLAPolicy
        fields = '__all__'


