from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationViewSet, IntegrationLogViewSet, 
    WebhookSubscriptionViewSet, WebhookDeliveryLogViewSet,
    inbound_webhook
)

router = DefaultRouter()
router.register(r'integrations', IntegrationViewSet, basename='integration')
router.register(r'integration-logs', IntegrationLogViewSet, basename='integrationlog')
router.register(r'webhook-subscriptions', WebhookSubscriptionViewSet, basename='webhook-subscription')
router.register(r'webhook-logs', WebhookDeliveryLogViewSet, basename='webhook-log')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/<uuid:integration_id>/', inbound_webhook, name='inbound_webhook'),
]

