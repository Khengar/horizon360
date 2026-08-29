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
        fields = ['id', 'contact', 'stage', 'value', 'created_at', 'updated_at']
