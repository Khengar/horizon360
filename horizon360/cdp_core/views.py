from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
import jsonschema
from jsonschema.exceptions import ValidationError
from .models import EventSchema, RawEvent, Customer, Company, UserProfile
from .serializers import EventSchemaSerializer, CustomerSerializer
from .tasks import process_event_task

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

class EventSchemaViewSet(viewsets.ModelViewSet):
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

class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Customers to be viewed.
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
        return queryset

    @action(detail=True, methods=['get'], url_path='360')
    def customer_360(self, request, pk=None):
        customer = self.get_queryset().prefetch_related('deals').select_related('contact', 'company').filter(pk=pk).first()
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
                "attributes": customer.attributes,
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

class SegmentView(APIView):
    """
    API endpoint that returns hardcoded dynamic segments.
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
            return Response({"error": "Segment not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from .models import Workflow, WorkflowExecution
from .serializers import WorkflowSerializer, WorkflowExecutionSerializer

from rest_framework.decorators import action
from rest_framework.response import Response

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Workflow.objects.none()
        company = get_or_create_user_company(self.request.user)
        return Workflow.objects.filter(company=company)
        
    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)

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

from .serializers import serializers

class RawEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawEvent
        fields = ['id', 'event_name', 'raw_payload', 'processed', 'created_at']

class RawEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RawEventSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return RawEvent.objects.none()
        company = get_or_create_user_company(self.request.user)
        return RawEvent.objects.filter(company=company).order_by('-created_at')
