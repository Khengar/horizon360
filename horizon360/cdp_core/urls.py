from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_views import RegisterView, LoginView, LogoutView
from .views import EventIngestionView, EventSchemaViewSet, CustomerViewSet, SegmentView

router = DefaultRouter()
router.register(r'schemas', EventSchemaViewSet, basename='schema')
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('events/', EventIngestionView.as_view(), name='event-ingest'),
    path('segments/<str:segment_name>/', SegmentView.as_view(), name='segment-detail'),
    path('', include(router.urls)),
]
