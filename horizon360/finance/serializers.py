from rest_framework import serializers
from .models import Invoice

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['company', 'created_at', 'updated_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        # Validate customer belongs to same company
        if 'customer' in data and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        # Validate deal belongs to same company and matches customer
        if 'deal' in data and data['deal']:
            if data['deal'].company != company:
                raise serializers.ValidationError({"deal": "Deal does not belong to this company."})
            if data['deal'].customer != data.get('customer', self.instance.customer if self.instance else None):
                raise serializers.ValidationError({"deal": "Deal customer does not match invoice customer."})
        
        return data
