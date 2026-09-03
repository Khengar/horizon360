from rest_framework import viewsets, permissions, status, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Invoice, Payment, JournalEntry, Expense, Product, LineItem, Transaction
from .serializers import InvoiceSerializer, PaymentSerializer, JournalEntrySerializer, ExpenseSerializer, ProductSerializer, LineItemSerializer, TransactionSerializer
from cdp_core.models import RawEvent
from cdp_core.audit import AuditLoggingMixin, record_audit_log
from cdp_core.idempotency import IdempotencyMixin

class InvoiceViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Invoice.objects.filter(company=self.request.user.profile.company).select_related('customer', 'deal').prefetch_related('payments')
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        invoice = serializer.save(company=self.request.user.profile.company)
        # Record initial Journal Entry
        JournalEntry.objects.create(
            company=invoice.company,
            entry_type='debit',
            account_code='1200_ACCOUNTS_RECEIVABLE',
            amount=invoice.amount,
            currency=invoice.currency,
            reference_type='invoice',
            reference_id=str(invoice.id),
            description=f"AR created for Invoice {invoice.invoice_number}"
        )
        JournalEntry.objects.create(
            company=invoice.company,
            entry_type='credit',
            account_code='4010_SALES_REVENUE',
            amount=invoice.amount,
            currency=invoice.currency,
            reference_type='invoice',
            reference_id=str(invoice.id),
            description=f"Revenue recognized for Invoice {invoice.invoice_number}"
        )

        # Emit event
        event_name = f"invoice.{invoice.status}"
        RawEvent.objects.create(
            company=invoice.company,
            customer=invoice.customer,
            event_name=event_name,
            raw_payload={"invoice_id": invoice.id, "amount": float(invoice.amount), "deal_id": invoice.deal.id if invoice.deal else None},
            processed=False
        )
        super().perform_create(serializer)

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
        super().perform_update(serializer)

    @action(detail=True, methods=['post'], url_path='record-payment')
    def record_payment(self, request, pk=None):
        invoice = self.get_object()
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payment = serializer.save(company=invoice.company, invoice=invoice, customer=invoice.customer)
        invoice.refresh_from_db()
        return Response({
            "status": "payment_recorded",
            "payment_id": str(payment.id),
            "invoice_status": invoice.status,
            "amount_paid": float(invoice.amount_paid),
            "balance_due": float(invoice.balance_due)
        }, status=status.HTTP_201_CREATED)


class PaymentViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.filter(company=self.request.user.profile.company).select_related('invoice', 'customer')
        invoice_id = self.request.query_params.get('invoice')
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
        super().perform_create(serializer)


class JournalEntryViewSet(AuditLoggingMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(company=self.request.user.profile.company)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)

class ProductViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)


class TransactionPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination

    def get_queryset(self):
        return Transaction.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
