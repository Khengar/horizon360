from rest_framework import serializers
from .models import Contact, Deal

class ContactSerializer(serializers.ModelSerializer):
    primary_email = serializers.ReadOnlyField()
    primary_phone = serializers.ReadOnlyField()

    class Meta:
        model = Contact
        fields = ['id', 'customer', 'owner', 'notes', 'primary_email', 'primary_phone', 'created_at', 'updated_at']

class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = ['id', 'title', 'customer', 'contact', 'stage', 'value', 'expected_close_date', 'created_at', 'updated_at']

    def validate(self, attrs):
        user_company = self.context['request'].user.profile.company
        customer = attrs.get('customer')
        contact = attrs.get('contact')
        
        if customer and customer.company != user_company:
            raise serializers.ValidationError({"customer": "Invalid customer."})
        if contact and contact.company != user_company:
            raise serializers.ValidationError({"contact": "Invalid contact."})
            
        return super().validate(attrs)

