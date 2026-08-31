from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartnerViewSet, PartnerOpportunityViewSet

router = DefaultRouter()
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'opportunities', PartnerOpportunityViewSet, basename='partneropportunity')

urlpatterns = [
    path('', include(router.urls)),
]
