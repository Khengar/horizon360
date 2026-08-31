from rest_framework import serializers
from .models import Partner, PartnerOpportunity

class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'customer' in data and data['customer'] and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        return data

class PartnerOpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerOpportunity
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'partner' in data and data['partner'] and data['partner'].company != company:
            raise serializers.ValidationError({"partner": "Partner does not belong to this company."})
            
        if 'customer' in data and data['customer'] and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        return data
