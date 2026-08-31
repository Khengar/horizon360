from rest_framework import serializers
from .models import Vendor, PurchaseOrder

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'vendor' in data and data['vendor'] and data['vendor'].company != company:
            raise serializers.ValidationError({"vendor": "Vendor does not belong to this company."})

        return data
