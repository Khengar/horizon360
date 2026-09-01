from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_views import RegisterView, LoginView, LogoutView
from .views import (
    EventIngestionView, EventSchemaViewSet, CustomerViewSet, SegmentView, 
    WorkflowViewSet, WorkflowExecutionViewSet, RawEventViewSet,
    AccountViewSet, RoleViewSet, UserRoleViewSet, AuditLogViewSet,
    SegmentViewSet
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'schemas', EventSchemaViewSet, basename='schema')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='userrole')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'segments-manage', SegmentViewSet, basename='segment-manage')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-executions', WorkflowExecutionViewSet, basename='workflowexecution')
router.register(r'events-history', RawEventViewSet, basename='rawevent')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('events/', EventIngestionView.as_view(), name='event-ingest'),
    path('segments/<str:segment_name>/', SegmentView.as_view(), name='segment-detail'),
    path('', include(router.urls)),
]


