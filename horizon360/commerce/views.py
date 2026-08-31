from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, Order, OrderItem, Cart, CartItem
from .serializers import (
    ProductSerializer, OrderSerializer, OrderItemSerializer,
    CartSerializer, CartItemSerializer
)
from cdp_core.models import RawEvent
from cdp_core.audit import AuditLoggingMixin
from cdp_core.idempotency import IdempotencyMixin

class ProductViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
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
        super().perform_create(serializer)


class OrderViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(company=self.request.user.profile.company).select_related('customer').prefetch_related('items')

    def perform_create(self, serializer):
        order = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=order.company,
            customer=order.customer,
            event_name='order.created',
            raw_payload={"order_id": order.id, "status": order.status, "total_amount": str(order.total_amount)},
            processed=False
        )
        super().perform_create(serializer)

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
        super().perform_update(serializer)


class OrderItemViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__company=self.request.user.profile.company)


class CartViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Cart.objects.filter(company=self.request.user.profile.company).prefetch_related('items')
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
        super().perform_create(serializer)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(cart=cart)
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='checkout')
    def checkout(self, request, pk=None):
        cart = self.get_object()
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            company=cart.company,
            customer=cart.customer,
            status='confirmed',
            total_amount=cart.total_amount
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.total_price
            )

        # Clear Cart
        cart.items.all().delete()

        # Emit event
        RawEvent.objects.create(
            company=order.company,
            customer=order.customer,
            event_name='order.checkout_completed',
            raw_payload={"order_id": order.id, "cart_id": str(cart.id), "total_amount": str(order.total_amount)},
            processed=False
        )

        return Response({
            "status": "checkout_completed",
            "order_id": order.id,
            "total_amount": float(order.total_amount)
        }, status=status.HTTP_201_CREATED)
