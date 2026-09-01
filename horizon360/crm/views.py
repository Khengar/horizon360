from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Contact, Deal, PipelineStage, Quote, QuoteItem, Activity
from .serializers import (
    ContactSerializer, DealSerializer, PipelineStageSerializer,
    QuoteSerializer, QuoteItemSerializer, ActivitySerializer
)
from cdp_core.models import Company, UserProfile, Customer, Account
from cdp_core.audit import AuditLoggingMixin, record_audit_log
from cdp_core.idempotency import IdempotencyMixin
from .scoring import calculate_deal_health
from .search import perform_universal_search

def get_or_create_user_company(user):
    if hasattr(user, 'profile') and user.profile and user.profile.company:
        return user.profile.company
    company = Company.objects.first()
    if not company:
        company = Company.objects.create(name='Default Corp')
    if user and user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'company': company})
        if not profile.company:
            profile.company = company
            profile.save()
    return company


class PipelineStageViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = PipelineStageSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return PipelineStage.objects.none()
        company = get_or_create_user_company(self.request.user)
        return PipelineStage.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)


class ContactViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = ContactSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Contact.objects.none()
        company = get_or_create_user_company(self.request.user)
        queryset = Contact.objects.filter(company=company)
        account_id = self.request.query_params.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        return queryset

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)


class DealViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = DealSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Deal.objects.none()
        company = get_or_create_user_company(self.request.user)
        queryset = Deal.objects.filter(company=company).select_related('account', 'customer', 'contact', 'pipeline_stage', 'owner')
        account_id = self.request.query_params.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        stage = self.request.query_params.get('stage')
        if stage:
            queryset = queryset.filter(stage=stage)
        stalled = self.request.query_params.get('stalled')
        if stalled is not None:
            queryset = queryset.filter(stalled=stalled.lower() == 'true')
        return queryset

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        deal = serializer.save(company=company)
        calculate_deal_health(deal, persist=True)
        super().perform_create(serializer)

    def perform_update(self, serializer):
        deal = serializer.save()
        calculate_deal_health(deal, persist=True)
        super().perform_update(serializer)

    @action(detail=True, methods=['post'], url_path='recalculate-health')
    def recalculate_health(self, request, pk=None):
        deal = self.get_object()
        score = calculate_deal_health(deal, persist=True)
        return Response({
            "deal_id": deal.id,
            "health_score": score,
            "stalled": deal.stalled,
            "weighted_value": deal.weighted_value
        }, status=status.HTTP_200_OK)


class QuoteViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = QuoteSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Quote.objects.none()
        company = get_or_create_user_company(self.request.user)
        queryset = Quote.objects.filter(company=company).prefetch_related('items').select_related('deal', 'account', 'customer')
        deal_id = self.request.query_params.get('deal')
        if deal_id:
            queryset = queryset.filter(deal_id=deal_id)
        return queryset

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)

    @action(detail=True, methods=['post'], url_path='add-item')
    def add_item(self, request, pk=None):
        quote = self.get_object()
        serializer = QuoteItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(quote=quote)
        quote.refresh_from_db()
        quote.recalculate_totals()
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)


    @action(detail=True, methods=['post'], url_path='convert-to-invoice')
    def convert_to_invoice(self, request, pk=None):
        quote = self.get_object()
        try:
            from finance.models import Invoice
            invoice = Invoice.objects.create(
                company=quote.company,
                customer=quote.customer,
                deal=quote.deal,
                invoice_number=f"INV-{quote.quote_number}",
                amount=quote.total_amount,
                status='issued'
            )
            quote.status = 'converted'
            quote.save(update_fields=['status'])

            record_audit_log(
                company=quote.company,
                action='create',
                entity_type='Invoice',
                entity_id=str(invoice.id),
                user=request.user,
                diff={"source_quote": quote.quote_number, "amount": float(quote.total_amount)}
            )

            return Response({
                "status": "converted",
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "amount": float(invoice.amount)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ActivityViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Activity.objects.none()
        company = get_or_create_user_company(self.request.user)
        queryset = Activity.objects.filter(company=company).select_related('customer', 'account', 'deal', 'user')
        
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        account_id = self.request.query_params.get('account')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        deal_id = self.request.query_params.get('deal')
        if deal_id:
            queryset = queryset.filter(deal_id=deal_id)
            
        activity_type = self.request.query_params.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
            
        return queryset

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        user = self.request.user if self.request.user.is_authenticated else None
        activity = serializer.save(company=company, user=user)
        
        # If activity is linked to a deal, recalculate deal health
        if activity.deal:
            calculate_deal_health(activity.deal, persist=True)
            
        super().perform_create(serializer)


class UniversalSearchView(APIView):
    """
    Unified multi-entity search endpoint across Accounts, Contacts, Customers, Deals, Quotes, Invoices, Tickets.
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        company = get_or_create_user_company(request.user)
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        results = perform_universal_search(company=company, query_text=query, limit=limit)
        return Response(results, status=status.HTTP_200_OK)


