from rest_framework import viewsets, permissions
from .models import Vendor, PurchaseOrder
from .serializers import VendorSerializer, PurchaseOrderSerializer
from cdp_core.models import RawEvent

class VendorViewSet(viewsets.ModelViewSet):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Vendor.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        vendor = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=vendor.company,
            event_name='vendor.created',
            raw_payload={"vendor_id": vendor.id, "name": vendor.name, "status": vendor.status},
            processed=False
        )

    def perform_update(self, serializer):
        vendor = serializer.save()
        RawEvent.objects.create(
            company=vendor.company,
            event_name='vendor.updated',
            raw_payload={"vendor_id": vendor.id, "name": vendor.name, "status": vendor.status},
            processed=False
        )

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PurchaseOrder.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        po = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=po.company,
            event_name='purchase_order.created',
            raw_payload={"po_id": po.id, "vendor_id": po.vendor.id, "status": po.status, "amount": str(po.amount)},
            processed=False
        )

    def perform_update(self, serializer):
        po = serializer.save()
        event_name = 'purchase_order.updated'
        if po.status == 'approved':
            event_name = 'purchase_order.approved'
        elif po.status == 'received':
            event_name = 'purchase_order.received'
        elif po.status == 'cancelled':
            event_name = 'purchase_order.cancelled'
            
        RawEvent.objects.create(
            company=po.company,
            event_name=event_name,
            raw_payload={"po_id": po.id, "vendor_id": po.vendor.id, "status": po.status, "amount": str(po.amount)},
            processed=False
        )
