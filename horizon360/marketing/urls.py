from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet, CampaignContentViewSet, CampaignRecipientViewSet,
    CampaignEventViewSet, AttributionTouchpointViewSet, TemplateViewSet,
    LeadViewSet, CampaignTransactionViewSet, MarketingDashboardView
)
from .webhooks import campaign_event_webhook

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'contents', CampaignContentViewSet, basename='campaign-content')
router.register(r'recipients', CampaignRecipientViewSet, basename='campaign-recipient')
router.register(r'events', CampaignEventViewSet, basename='campaign-event')
router.register(r'touchpoints', AttributionTouchpointViewSet, basename='attribution-touchpoint')
router.register(r'templates', TemplateViewSet, basename='campaign-template')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'transactions', CampaignTransactionViewSet, basename='campaign-transaction')

urlpatterns = [
    path('dashboard/', MarketingDashboardView.as_view(), name='marketing-dashboard'),
    path('webhooks/campaign-events/', campaign_event_webhook, name='campaign-webhook'),
    path('', include(router.urls)),
]
