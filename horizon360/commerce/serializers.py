from rest_framework import serializers
from .models import Product, Order, OrderItem, Cart, CartItem

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['company', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_name', 'quantity', 'price']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            company = request.user.profile.company
            if 'order' in data and data['order'] and data['order'].company != company:
                raise serializers.ValidationError({"order": "Order does not belong to this company."})
            if 'product' in data and data['product'] and data['product'].company != company:
                raise serializers.ValidationError({"product": "Product does not belong to this company."})
        return data

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_email', 'status', 'total_amount', 'items', 'created_at']
        read_only_fields = ['company', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request.user, 'profile') and request.user.profile.company:
            company = request.user.profile.company
            if 'customer' in data and data['customer'] and data['customer'].company != company:
                raise serializers.ValidationError({"customer": "Customer does not belong to this company."})
        return data

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'created_at', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.ReadOnlyField()
    customer_email = serializers.CharField(source='customer.primary_email', read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'customer_email', 'total_amount', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_amount']

