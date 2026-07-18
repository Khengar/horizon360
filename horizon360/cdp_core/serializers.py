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

