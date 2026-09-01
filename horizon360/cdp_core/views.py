from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
import jsonschema
from jsonschema.exceptions import ValidationError
from .models import (
    EventSchema, RawEvent, Customer, Company, UserProfile, Account, 
    Role, UserRole, AuditLog, Workflow, WorkflowExecution, Segment
)
from .serializers import (
    EventSchemaSerializer, CustomerSerializer, AccountSerializer, 
    RoleSerializer, UserRoleSerializer, AuditLogSerializer,
    WorkflowSerializer, WorkflowExecutionSerializer, RawEventSerializer,
    SegmentSerializer, CustomerMergeSerializer
)
from .tasks import process_event_task
from .audit import AuditLoggingMixin, record_audit_log
from .permissions import HasTenantRolePermission, IsTenantAdmin
from .identity import merge_customers
from .segmentation import get_segment_audience
from .idempotency import IdempotencyMixin

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


class AccountViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows B2B Accounts to be viewed, created, or edited.
    """
    serializer_class = AccountSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Account.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Account.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)


class RoleViewSet(AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing Tenant RBAC Roles.
    """
    serializer_class = RoleSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Role.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Role.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)


class UserRoleViewSet(AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint for assigning RBAC Roles to Users in a Tenant.
    """
    serializer_class = UserRoleSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return UserRole.objects.none()
        company = get_or_create_user_company(self.request.user)
        return UserRole.objects.filter(user_profile__company=company)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for viewing tenant immutable audit logs.
    """
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return AuditLog.objects.none()
        company = get_or_create_user_company(self.request.user)
        queryset = AuditLog.objects.filter(company=company)
        
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type__iexact=entity_type)
            
        action_name = self.request.query_params.get('action')
        if action_name:
            queryset = queryset.filter(action__iexact=action_name)
            
        return queryset


class EventSchemaViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows EventSchemas to be viewed or edited.
    """
    serializer_class = EventSchemaSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return EventSchema.objects.none()
        company = get_or_create_user_company(self.request.user)
        return EventSchema.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)


class EventIngestionView(APIView):
    """
    Ingests event data, validates against registered schema,
    stores raw event, and schedules processing.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return Response({"error": "X-API-Key header is missing"}, status=status.HTTP_401_UNAUTHORIZED)
            
        company = Company.objects.filter(api_token=api_key).first()
        if not company or not company.is_active:
            return Response({"error": "Invalid or Inactive API Key"}, status=status.HTTP_401_UNAUTHORIZED)

        event_name = request.data.get('event_name')
        raw_payload = request.data.get('raw_payload')
        
        # Look up schema
        try:
            schema_obj = EventSchema.objects.get(event_name=event_name, company=company)
        except EventSchema.DoesNotExist:
            return Response(
                {"error": f"Schema for event '{event_name}' not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate raw_payload against the schema
        try:
            jsonschema.validate(instance=raw_payload, schema=schema_obj.json_schema)
        except ValidationError as e:
            return Response(
                {"error": f"Schema validation failed: {e.message}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save RawEvent (with processed=False)
        raw_event = RawEvent.objects.create(
            event_name=event_name,
            raw_payload=raw_payload,
            company=company,
            processed=False
        )
        
        # Trigger Celery task asynchronously
        process_event_task.delay(raw_event.id)
        
        return Response(
            {"status": "accepted", "event_id": raw_event.id},
            status=status.HTTP_202_ACCEPTED
        )


class CustomerViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows Customers to be viewed, created, or edited.
    """
    serializer_class = CustomerSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Customer.objects.none()
            
        company = get_or_create_user_company(self.request.user)
        queryset = Customer.objects.filter(company=company)
        email = self.request.query_params.get('email', None)
        if email is not None:
            queryset = queryset.filter(primary_email=email)
        account_id = self.request.query_params.get('account', None)
        if account_id is not None:
            queryset = queryset.filter(account_id=account_id)
        return queryset

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)

    @action(detail=True, methods=['get'], url_path='360')
    def customer_360(self, request, pk=None):
        customer = self.get_queryset().prefetch_related('deals').select_related('contact', 'company', 'account').filter(pk=pk).first()
        if not customer:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        
        deals = list(customer.deals.all())
        total_deal_value = sum((d.value for d in deals), 0)
        open_deals = [d for d in deals if d.stage not in ['won', 'lost']]
        won_deals = [d for d in deals if d.stage == 'won']
        lost_deals = [d for d in deals if d.stage == 'lost']
        open_pipeline_value = sum((d.value for d in open_deals), 0)
        won_revenue = sum((d.value for d in won_deals), 0)

        contact_data = None
        if hasattr(customer, 'contact') and customer.contact:
            contact_data = {
                "id": customer.contact.id,
                "notes": customer.contact.notes,
                "created_at": customer.contact.created_at,
            }

        deals_data = [
            {
                "id": d.id,
                "stage": d.stage,
                "value": d.value,
                "created_at": d.created_at,
                "status": d.get_stage_display()
            } for d in deals
        ]
        
        events = customer.raw_events.all().order_by('-created_at')
        events_data = [
            {
                "id": e.id,
                "event_name": e.event_name,
                "created_at": e.created_at,
                "payload": e.raw_payload
            } for e in events
        ]

        data = {
            "identity": {
                "id": customer.id,
                "primary_email": customer.primary_email,
                "primary_phone": customer.primary_phone,
                "account_id": customer.account_id,
                "account_name": customer.account.name if customer.account else None,
                "attributes": customer.attributes,
                "consent": customer.consent,
                "created_at": customer.created_at,
                "updated_at": customer.updated_at
            },
            "company": {
                "id": customer.company.id if customer.company else 1,
                "name": customer.company.name if customer.company else "Default Corp"
            },
            "contact": contact_data,
            "deals": deals_data,
            "aggregates": {
                "total_deal_value": total_deal_value,
                "open_pipeline_value": open_pipeline_value,
                "won_revenue": won_revenue,
                "open_deals_count": len(open_deals),
                "won_deals_count": len(won_deals),
                "lost_deals_count": len(lost_deals)
            },
            "timeline": events_data
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='merge')
    def merge(self, request, pk=None):
        """
        Merges a secondary customer record into this primary customer.
        Re-points all BIOM entities (Deals, Invoices, ServiceTickets, Orders, Projects, Leads, RawEvents)
        and leaves an immutable audit trail.
        """
        primary_customer = self.get_object()
        serializer = CustomerMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        secondary_id = serializer.validated_data['secondary_customer_id']

        try:
            secondary_customer = Customer.objects.get(
                id=secondary_id,
                company=primary_customer.company
            )
        except Customer.DoesNotExist:
            return Response(
                {"error": "Secondary customer not found in this tenant."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            result = merge_customers(primary_customer, secondary_customer, user=request.user)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='export-data')
    def export_data(self, request, pk=None):
        """
        GDPR/CCPA Data Subject Access Request (DSAR) export endpoint.
        Returns the entire data packet for this customer across all BIOMs.
        """
        customer = self.get_object()
        user = getattr(request, 'user', None)

        record_audit_log(
            company=customer.company,
            action='export',
            entity_type='Customer',
            entity_id=str(customer.id),
            user=user,
            diff={"dsar_export": True}
        )

        return self.customer_360(request, pk=pk)

    @action(detail=True, methods=['post'], url_path='anonymize')
    def anonymize(self, request, pk=None):
        """
        GDPR/CCPA Right to be Forgotten (RTBF) erasure endpoint.
        Anonymizes PII while preserving aggregate financial / historical data integrity.
        """
        customer = self.get_object()
        old_identity = {
            "email": customer.primary_email,
            "phone": customer.primary_phone,
            "attributes": customer.attributes
        }

        # Anonymize identifiers
        customer.primary_email = f"anonymized_{customer.id.hex[:8]}@erased.local"
        customer.primary_phone = None
        
        # Clear personal attribute keys
        sanitized_attrs = {}
        for k, v in (customer.attributes or {}).items():
            if k in ['plan', 'tier', 'account_type']:
                sanitized_attrs[k] = v
        customer.attributes = sanitized_attrs

        # Clear consent flags
        customer.consent = {"status": "erased", "marketing_consent": False}
        customer.save()

        # Update associated contact if present
        if hasattr(customer, 'contact') and customer.contact:
            customer.contact.notes = "[PII Erased per GDPR/CCPA request]"
            customer.contact.save()

        record_audit_log(
            company=customer.company,
            action='anonymize',
            entity_type='Customer',
            entity_id=str(customer.id),
            user=request.user,
            diff={
                "before": old_identity,
                "after": {"primary_email": customer.primary_email, "erased": True}
            }
        )

        return Response({
            "status": "anonymized",
            "customer_id": customer.id,
            "anonymized_email": customer.primary_email
        }, status=status.HTTP_200_OK)


class SegmentViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    """
    API endpoint for Dynamic Rule-Based Segments.
    """
    serializer_class = SegmentSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Segment.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Segment.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)

    @action(detail=True, methods=['get'], url_path='customers')
    def customers(self, request, pk=None):
        """
        Evaluates the dynamic segment rules in real-time and returns matching customers.
        """
        segment = self.get_object()
        limit = request.query_params.get('limit')
        limit_int = int(limit) if limit and limit.isdigit() else None
        
        audience = get_segment_audience(segment, limit=limit_int)
        serializer = CustomerSerializer(audience, many=True)
        return Response({
            "segment_id": segment.id,
            "segment_name": segment.name,
            "match_count": len(audience),
            "customers": serializer.data
        }, status=status.HTTP_200_OK)


class SegmentView(APIView):
    """
    Legacy API endpoint for backwards compatibility.
    """
    def get(self, request, segment_name, *args, **kwargs):
        company = get_or_create_user_company(request.user)
        base_qs = Customer.objects.filter(company=company)

        if segment_name == 'free-tier':
            queryset = base_qs.filter(attributes__account_type='free_tier')
        elif segment_name == 'high-value-cart':
            queryset = base_qs.filter(attributes__cart_value__gte=100)
        elif segment_name == 'active-shopper':
            queryset = base_qs.filter(timeline__contains=[{'event_name': 'cart.updated'}])
        else:
            # Fallback to database Segment by name
            seg = Segment.objects.filter(company=company, name__iexact=segment_name).first()
            if seg:
                audience = get_segment_audience(seg)
                serializer = CustomerSerializer(audience, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkflowViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Workflow.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Workflow.objects.filter(company=company)
        
    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)

    @action(detail=False, methods=['get'])
    def templates(self, request):
        templates = [
            {"group": "Sales", "name": "Deal Won → Invoice", "trigger_event": "deal.won", "action_type": "create_invoice", "source_biom": "Sales", "destination_biom": "Finance"},
            {"group": "Sales", "name": "Deal Won → Project", "trigger_event": "deal.won", "action_type": "create_project", "source_biom": "Sales", "destination_biom": "Projects"},
            {"group": "Sales", "name": "Stalled Deal → Follow-up", "trigger_event": "deal.stalled", "action_type": "create_ticket", "source_biom": "Sales", "destination_biom": "Service"},
            {"group": "Marketing", "name": "Lead Qualified → Sales Opportunity", "trigger_event": "lead.qualified", "action_type": "create_opportunity", "source_biom": "Marketing", "destination_biom": "Sales"},
            {"group": "Marketing", "name": "Lead Converted → Customer Onboarding", "trigger_event": "lead.converted", "action_type": "create_onboarding_project", "source_biom": "Marketing", "destination_biom": "Projects"},
            {"group": "Finance", "name": "Invoice Paid → Project", "trigger_event": "invoice.paid", "action_type": "create_project", "source_biom": "Finance", "destination_biom": "Projects"},
            {"group": "Finance", "name": "Invoice Overdue → Service Escalation", "trigger_event": "invoice.overdue", "action_type": "create_ticket", "source_biom": "Finance", "destination_biom": "Service"},
            {"group": "Projects", "name": "Project Created → Service Onboarding", "trigger_event": "project.created", "action_type": "create_ticket", "source_biom": "Projects", "destination_biom": "Service"},
            {"group": "Service", "name": "Critical Ticket → Executive Escalation", "trigger_event": "ticket.critical", "action_type": "ai_generate_insight", "source_biom": "Service", "destination_biom": "Intelligence"},
            {"group": "HRMS", "name": "Employee Created → Onboarding Project", "trigger_event": "employee.created", "action_type": "create_onboarding_project", "source_biom": "HRMS", "destination_biom": "Projects"},
            {"group": "Commerce", "name": "Order Fulfilled → Customer Success Follow-up", "trigger_event": "order.fulfilled", "action_type": "create_ticket", "source_biom": "Commerce", "destination_biom": "Service"},
            {"group": "Partner", "name": "Partner Opportunity Won → Sales Workflow", "trigger_event": "partner_opportunity.won", "action_type": "create_opportunity", "source_biom": "Partner", "destination_biom": "Sales"},
            {"group": "Vendor", "name": "Purchase Order Approved → Finance Event", "trigger_event": "purchase_order.approved", "action_type": "ai_generate_insight", "source_biom": "Vendor", "destination_biom": "Finance"}
        ]
        return Response(templates)


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WorkflowExecutionSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return WorkflowExecution.objects.none()
        company = get_or_create_user_company(self.request.user)
        return WorkflowExecution.objects.filter(workflow__company=company).order_by('-created_at')


class RawEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RawEventSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return RawEvent.objects.none()
        company = get_or_create_user_company(self.request.user)
        return RawEvent.objects.filter(company=company).order_by('-created_at')


