from rest_framework import serializers
from .models import ServiceTicket

class ServiceTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceTicket
        fields = '__all__'
        read_only_fields = ['company', 'created_at', 'updated_at', 'resolved_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        # Validate customer belongs to same company
        if 'customer' in data and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        return data
