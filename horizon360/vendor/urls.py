from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')

urlpatterns = [
    path('', include(router.urls)),
]
