from rest_framework import serializers
from .models import Campaign, Lead, CampaignTransaction

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['company', 'created_at']


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

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
