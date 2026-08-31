from rest_framework import viewsets, permissions
from .models import Invoice
from .serializers import InvoiceSerializer
from cdp_core.models import RawEvent

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.user.profile.company).select_related('customer', 'deal')

    def perform_create(self, serializer):
        invoice = serializer.save(company=self.request.user.profile.company)
        # Emit event
        event_name = f"invoice.{invoice.status}"
        RawEvent.objects.create(
            company=invoice.company,
            customer=invoice.customer,
            event_name=event_name,
            raw_payload={"invoice_id": invoice.id, "amount": float(invoice.amount), "deal_id": invoice.deal.id if invoice.deal else None},
            processed=False
        )

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        invoice = serializer.save()
        
        if old_status != invoice.status:
            event_name = f"invoice.{invoice.status}"
            RawEvent.objects.create(
                company=invoice.company,
                customer=invoice.customer,
                event_name=event_name,
                raw_payload={"invoice_id": invoice.id, "amount": float(invoice.amount), "deal_id": invoice.deal.id if invoice.deal else None},
                processed=False
            )
