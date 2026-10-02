from rest_framework import serializers
from cdp_core.models import Segment
from .models import (
    Campaign, CampaignSegment, CampaignContent, CampaignRecipient,
    CampaignEvent, CampaignPropensityScore, AttributionTouchpoint,
    Lead, CampaignTransaction
)

class CampaignContentSerializer(serializers.ModelSerializer):
    conversion_rate = serializers.SerializerMethodField()

    class Meta:
        model = CampaignContent
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_conversion_rate(self, obj):
        imp = obj.impressions or 0
        if imp == 0:
            return 0.0
        return round(((obj.successes or 0) / imp) * 100, 1)


class CampaignSegmentSerializer(serializers.ModelSerializer):
    segment_name = serializers.CharField(source='segment.name', read_only=True)
    rules = serializers.JSONField(source='segment.rules', read_only=True)

    class Meta:
        model = CampaignSegment
        fields = ['id', 'campaign', 'segment', 'segment_name', 'rules', 'is_exclusion', 'created_at']


class CampaignRecipientSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)
    customer_phone = serializers.CharField(source='customer.primary_phone', read_only=True)
    variant_name = serializers.CharField(source='content_variant.variant_name', read_only=True)

    class Meta:
        model = CampaignRecipient
        fields = '__all__'
        read_only_fields = ['company', 'queued_at']


class CampaignEventSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='recipient.customer.primary_email', read_only=True)

    class Meta:
        model = CampaignEvent
        fields = '__all__'
        read_only_fields = ['company', 'created_at']


class CampaignPropensityScoreSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)

    class Meta:
        model = CampaignPropensityScore
        fields = '__all__'
        read_only_fields = ['company', 'scored_at']


class AttributionTouchpointSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)

    class Meta:
        model = AttributionTouchpoint
        fields = '__all__'
        read_only_fields = ['company', 'created_at']


class CampaignSerializer(serializers.ModelSerializer):
    contents = CampaignContentSerializer(many=True, read_only=True)
    campaign_segments = CampaignSegmentSerializer(many=True, read_only=True)
    segment_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True, required=False)
    
    # Calculated KPIs
    open_rate = serializers.SerializerMethodField()
    click_rate = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    delivery_rate = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = [
            'company', 'created_at', 'updated_at', 'total_sent', 'total_delivered',
            'total_opened', 'total_clicked', 'total_converted', 'total_bounced',
            'total_unsubscribed', 'avg_propensity_score', 'churn_risk_count'
        ]

    def get_open_rate(self, obj):
        delivered = obj.total_delivered or 0
        if delivered == 0:
            return 0.0
        return round(((obj.total_opened or 0) / delivered) * 100, 1)

    def get_click_rate(self, obj):
        delivered = obj.total_delivered or 0
        if delivered == 0:
            return 0.0
        return round(((obj.total_clicked or 0) / delivered) * 100, 1)

    def get_conversion_rate(self, obj):
        sent = obj.total_sent or 0
        if sent == 0:
            return 0.0
        return round(((obj.total_converted or 0) / sent) * 100, 1)

    def get_delivery_rate(self, obj):
        sent = obj.total_sent or 0
        if sent == 0:
            return 0.0
        return round(((obj.total_delivered or 0) / sent) * 100, 1)

    def create(self, validated_data):
        segment_ids = validated_data.pop('segment_ids', [])
        campaign = super().create(validated_data)
        for seg_id in segment_ids:
            try:
                segment = Segment.objects.get(id=seg_id, company=campaign.company)
                CampaignSegment.objects.create(campaign=campaign, segment=segment)
            except Segment.DoesNotExist:
                pass
        return campaign

    def update(self, instance, validated_data):
        segment_ids = validated_data.pop('segment_ids', None)
        campaign = super().update(instance, validated_data)
        if segment_ids is not None:
            CampaignSegment.objects.filter(campaign=campaign).delete()
            for seg_id in segment_ids:
                try:
                    segment = Segment.objects.get(id=seg_id, company=campaign.company)
                    CampaignSegment.objects.create(campaign=campaign, segment=segment)
                except Segment.DoesNotExist:
                    pass
        return campaign


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = getattr(request.user.profile, 'company', None) if request and hasattr(request.user, 'profile') else None

        if company:
            if 'customer' in data and data['customer'] and data['customer'].company != company:
                raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

            if 'campaign' in data and data['campaign'] and data['campaign'].company != company:
                raise serializers.ValidationError({"campaign": "Campaign does not belong to this company."})

        return data


class CampaignTransactionSerializer(serializers.ModelSerializer):
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)

    class Meta:
        model = CampaignTransaction
        fields = '__all__'
        read_only_fields = ['company', 'created_at']
