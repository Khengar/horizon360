from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntegrationViewSet, IntegrationLogViewSet, inbound_webhook

router = DefaultRouter()
router.register(r'integrations', IntegrationViewSet, basename='integration')
router.register(r'integration-logs', IntegrationLogViewSet, basename='integrationlog')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/<uuid:integration_id>/', inbound_webhook, name='inbound_webhook'),
]
