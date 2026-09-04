from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet, DealViewSet, PipelineStageViewSet, 
    QuoteViewSet, ActivityViewSet, UniversalSearchView
)
from cdp_core.views import AccountViewSet
from .api_orchestration import OrchestrationStatusView

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='crm-account')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'pipeline-stages', PipelineStageViewSet, basename='pipeline-stage')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'activities', ActivityViewSet, basename='activity')

urlpatterns = [
    path('orchestration/', OrchestrationStatusView.as_view(), name='orchestration-status'),
    path('search/', UniversalSearchView.as_view(), name='universal-search'),
    path('', include(router.urls)),
]


