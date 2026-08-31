from rest_framework import serializers
from .models import Contact, Deal, PipelineStage, Quote, QuoteItem, Activity

class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'order', 'probability', 'is_won', 'is_lost', 'color_code', 'created_at']

class ContactSerializer(serializers.ModelSerializer):
    primary_email = serializers.ReadOnlyField()
    primary_phone = serializers.ReadOnlyField()
    account_name = serializers.CharField(source='account.name', read_only=True)

    class Meta:
        model = Contact
        fields = ['id', 'customer', 'account', 'account_name', 'owner', 'notes', 'primary_email', 'primary_phone', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            user_company = request.user.profile.company
            account = attrs.get('account')
            if account and account.company != user_company:
                raise serializers.ValidationError({"account": "Invalid account for this tenant."})
        return super().validate(attrs)

class DealSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    pipeline_stage_name = serializers.CharField(source='pipeline_stage.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    weighted_value = serializers.ReadOnlyField()

    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'account', 'account_name', 'customer', 'contact', 
            'pipeline_stage', 'pipeline_stage_name', 'owner', 'owner_username',
            'stage', 'probability', 'weighted_value', 'forecast_category',
            'value', 'health_score', 'stalled', 'lost_reason', 'expected_close_date',
            'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            user_company = request.user.profile.company
            customer = attrs.get('customer')
            contact = attrs.get('contact')
            account = attrs.get('account')
            
            if customer and customer.company != user_company:
                raise serializers.ValidationError({"customer": "Invalid customer."})
            if contact and contact.company != user_company:
                raise serializers.ValidationError({"contact": "Invalid contact."})
            if account and account.company != user_company:
                raise serializers.ValidationError({"account": "Invalid account for this tenant."})
                
        return super().validate(attrs)

class QuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteItem
        fields = ['id', 'product_name', 'sku', 'quantity', 'unit_price', 'discount_amount', 'total_price']
        read_only_fields = ['total_price']


class QuoteSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    deal_title = serializers.CharField(source='deal.title', read_only=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'deal', 'deal_title', 'account', 'account_name', 
            'customer', 'status', 'subtotal', 'discount_percent', 'tax_percent', 
            'total_amount', 'valid_until', 'notes', 'items', 'created_at', 'updated_at'
        ]

class ActivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'customer', 'account', 'deal', 'user', 'username',
            'activity_type', 'title', 'description', 'duration_minutes',
            'performed_at', 'metadata'
        ]



