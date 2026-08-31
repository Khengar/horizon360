from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Integration, IntegrationLog
from .serializers import IntegrationSerializer, IntegrationLogSerializer
from cdp_core.views import get_or_create_user_company
from cdp_core.models import RawEvent, Customer
from .connectors.factory import get_connector
import uuid
import logging

logger = logging.getLogger(__name__)

from rest_framework.decorators import action
from .models import Integration, IntegrationLog, WebhookSubscription, WebhookDeliveryLog
from .serializers import (
    IntegrationSerializer, IntegrationLogSerializer,
    WebhookSubscriptionSerializer, WebhookDeliveryLogSerializer
)
from .webhooks import send_single_webhook
from cdp_core.views import get_or_create_user_company
from cdp_core.models import RawEvent, Customer
from cdp_core.audit import AuditLoggingMixin
from cdp_core.idempotency import IdempotencyMixin

class IntegrationViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company = get_or_create_user_company(self.request.user)
        return Integration.objects.filter(company=company)
        
    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        secret = str(uuid.uuid4())
        config = {'webhook_secret': secret}
        serializer.save(company=company, config=config)
        super().perform_create(serializer)


class IntegrationLogViewSet(AuditLoggingMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = IntegrationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company = get_or_create_user_company(self.request.user)
        return IntegrationLog.objects.filter(company=company).order_by('-timestamp')


class WebhookSubscriptionViewSet(IdempotencyMixin, AuditLoggingMixin, viewsets.ModelViewSet):
    serializer_class = WebhookSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company = get_or_create_user_company(self.request.user)
        return WebhookSubscription.objects.filter(company=company)

    def perform_create(self, serializer):
        company = get_or_create_user_company(self.request.user)
        serializer.save(company=company)
        super().perform_create(serializer)

    @action(detail=True, methods=['post'], url_path='ping')
    def ping(self, request, pk=None):
        subscription = self.get_object()
        ping_payload = {
            "event": "webhook.ping",
            "message": "Horizon 360 test webhook ping",
            "timestamp": str(uuid.uuid4())
        }
        log = send_single_webhook(subscription, "webhook.ping", ping_payload)
        return Response({
            "status": "ping_sent",
            "success": log.success,
            "response_status": log.response_status,
            "log_id": str(log.id)
        }, status=status.HTTP_200_OK)


class WebhookDeliveryLogViewSet(AuditLoggingMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = WebhookDeliveryLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company = get_or_create_user_company(self.request.user)
        queryset = WebhookDeliveryLog.objects.filter(subscription__company=company).select_related('subscription')
        subscription_id = self.request.query_params.get('subscription')
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)
        return queryset


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def inbound_webhook(request, integration_id):
    """
    Public webhook endpoint for receiving external events.
    """
    integration = get_object_or_404(Integration, id=integration_id)
    
    # 1. Authenticate
    connector = get_connector(integration)
    if not connector.authenticate(request.META, request.data):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
    # 2. Prevent duplicate processing (idempotency)
    # Use an external ID or fallback to a hash/timestamp
    external_id = str(request.data.get('id', uuid.uuid4()))
    
    log, created = IntegrationLog.objects.get_or_create(
        integration=integration,
        direction='inbound',
        correlation_id=external_id,
        defaults={
            'company': integration.company,
            'event_type': request.data.get('type', 'unknown'),
            'status': 'processing',
            'payload_metadata': request.data
        }
    )
    
    if not created and log.status == 'success':
        return Response({'status': 'already_processed'}, status=status.HTTP_200_OK)

    try:
        # 3. Normalize
        normalized_data = connector.receive(request.data, request.META)
        
        # Resolve customer if email provided
        customer = None
        email = normalized_data.get('customer_identifier')
        if email:
            customer = Customer.objects.filter(company=integration.company, primary_email=email).first()
            if not customer:
                customer = Customer.objects.create(company=integration.company, primary_email=email)
        
        # 4. Generate RawEvent
        raw_event = RawEvent.objects.create(
            company=integration.company,
            customer=customer,
            event_name=normalized_data.get('event_name'),
            raw_payload=normalized_data.get('payload'),
            processed=False
        )
        
        # 5. Trigger Horizon Flow
        from cdp_core.tasks import process_event_task
        process_event_task.delay(raw_event.id)
        
        # 6. Record Success
        log.status = 'success'
        log.save()
        
        return Response({'status': 'accepted', 'raw_event_id': raw_event.id}, status=status.HTTP_202_ACCEPTED)
        
    except Exception as e:
        logger.exception("Inbound webhook failed")
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
