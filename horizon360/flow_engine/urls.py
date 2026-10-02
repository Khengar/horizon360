from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FlowDefinitionViewSet, FlowVersionViewSet, 
    FlowExecutionViewSet, ApprovalRequestViewSet,
    FlowMarketplaceTemplateViewSet, WebhookReceiverView,
    FlowAnalyticsView, FlowAuditLogViewSet, FlowSLAPolicyViewSet
)

router = DefaultRouter()
router.register(r'flows', FlowDefinitionViewSet, basename='flow')
router.register(r'flow-versions', FlowVersionViewSet, basename='flowversion')
router.register(r'executions', FlowExecutionViewSet, basename='execution')
router.register(r'approvals', ApprovalRequestViewSet, basename='approval')
router.register(r'flow-templates', FlowMarketplaceTemplateViewSet, basename='template')
router.register(r'flow-audit', FlowAuditLogViewSet, basename='flowaudit')
router.register(r'sla-policies', FlowSLAPolicyViewSet, basename='slapolicy')

urlpatterns = [
    path('flow-analytics/dashboard/', FlowAnalyticsView.as_view(), name='flow_analytics'),
    path('', include(router.urls)),
    path('webhooks/<uuid:flow_id>/', WebhookReceiverView.as_view(), name='webhook_receiver'),
]
