from rest_framework import viewsets, permissions
from .models import Product, Order, OrderItem
from .serializers import ProductSerializer, OrderSerializer, OrderItemSerializer
from cdp_core.models import RawEvent

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        product = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=product.company,
            event_name='product.created',
            raw_payload={"product_id": product.id, "name": product.name, "price": str(product.price)},
            processed=False
        )

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        order = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=order.company,
            customer=order.customer,
            event_name='order.created',
            raw_payload={"order_id": order.id, "status": order.status, "total_amount": str(order.total_amount)},
            processed=False
        )

    def perform_update(self, serializer):
        order = serializer.save()
        event_name = 'order.updated'
        if order.status == 'confirmed':
            event_name = 'order.confirmed'
        elif order.status == 'fulfilled':
            event_name = 'order.fulfilled'
        elif order.status == 'cancelled':
            event_name = 'order.cancelled'
            
        RawEvent.objects.create(
            company=order.company,
            customer=order.customer,
            event_name=event_name,
            raw_payload={"order_id": order.id, "status": order.status, "total_amount": str(order.total_amount)},
            processed=False
        )

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__company=self.request.user.profile.company)
