from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceTicketViewSet, SLAPolicyViewSet, KnowledgeArticleViewSet, ServiceEntitlementViewSet

router = DefaultRouter()
router.register(r'tickets', ServiceTicketViewSet, basename='serviceticket')
router.register(r'sla-policies', SLAPolicyViewSet, basename='sla-policy')
router.register(r'articles', KnowledgeArticleViewSet, basename='knowledge-article')

urlpatterns = [
    path('', include(router.urls)),
]

