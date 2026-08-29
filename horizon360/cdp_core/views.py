from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
import jsonschema
from jsonschema.exceptions import ValidationError
from .models import EventSchema, RawEvent, Customer, Company
from .serializers import EventSchemaSerializer, CustomerSerializer
from .tasks import process_event_task

class EventSchemaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows EventSchemas to be viewed or edited.
    """
    serializer_class = EventSchemaSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, 'profile'):
            return EventSchema.objects.none()
        return EventSchema.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'profile'):
            serializer.save(company=self.request.user.profile.company)
        else:
            serializer.save()


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
        if not hasattr(self.request.user, 'profile'):
            return Customer.objects.none()
            
        queryset = Customer.objects.filter(company=self.request.user.profile.company)
        email = self.request.query_params.get('email', None)
        if email is not None:
            queryset = queryset.filter(primary_email=email)
        return queryset

class SegmentView(APIView):
    """
    API endpoint that returns hardcoded dynamic segments.
    """
    def get(self, request, segment_name, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        company = request.user.profile.company
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
