from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceTicketViewSet

router = DefaultRouter()
router.register(r'tickets', ServiceTicketViewSet, basename='serviceticket')

urlpatterns = [
    path('', include(router.urls)),
]
