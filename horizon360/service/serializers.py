from rest_framework import serializers
from .models import ServiceTicket, SLAPolicy, TicketComment, KnowledgeArticle, ServiceEntitlement

class SLAPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SLAPolicy
        fields = ['id', 'name', 'priority', 'response_time_hours', 'resolution_time_hours', 'is_active', 'created_at']


class TicketCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'author', 'author_username', 'message', 'is_internal', 'created_at']
        read_only_fields = ['id', 'created_at', 'author', 'ticket']



class KnowledgeArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = ['id', 'title', 'slug', 'category', 'content', 'is_published', 'view_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'view_count']


class ServiceTicketSerializer(serializers.ModelSerializer):
    comments = TicketCommentSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)
    sla_policy_name = serializers.CharField(source='sla_policy.name', read_only=True)

    class Meta:
        model = ServiceTicket
        fields = [
            'id', 'customer', 'customer_email', 'sla_policy', 'sla_policy_name',
            'title', 'description', 'status', 'priority', 'is_sla_breached',
            'first_responded_at', 'sla_due_at', 'resolved_at', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['company', 'created_at', 'updated_at', 'resolved_at', 'first_responded_at', 'sla_due_at', 'is_sla_breached']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            company = request.user.profile.company
            if 'customer' in data and data['customer'].company != company:
                raise serializers.ValidationError({"customer": "Customer does not belong to this company."})
            if 'sla_policy' in data and data['sla_policy'] and data['sla_policy'].company != company:
                raise serializers.ValidationError({"sla_policy": "SLA Policy does not belong to this company."})
        return data


class ServiceEntitlementSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)
    class Meta:
        model = ServiceEntitlement
        fields = '__all__'
