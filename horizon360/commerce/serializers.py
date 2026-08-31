from rest_framework import serializers
from .models import Product, Order, OrderItem

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'customer' in data and data['customer'] and data['customer'].company != company:
            raise serializers.ValidationError({"customer": "Customer does not belong to this company."})

        return data

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

    def validate(self, data):
        request = self.context.get('request')
        company = request.user.profile.company

        if 'order' in data and data['order'] and data['order'].company != company:
            raise serializers.ValidationError({"order": "Order does not belong to this company."})
            
        if 'product' in data and data['product'] and data['product'].company != company:
            raise serializers.ValidationError({"product": "Product does not belong to this company."})

        return data
