from rest_framework import viewsets, permissions
from .models import Project, Task, Target
from .serializers import ProjectSerializer, TaskSerializer, TargetSerializer
from rest_framework.pagination import PageNumberPagination
from cdp_core.models import RawEvent

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(company=self.request.user.profile.company).select_related('customer')

    def perform_create(self, serializer):
        project = serializer.save(company=self.request.user.profile.company)
        
        RawEvent.objects.create(
            company=project.company,
            customer=project.customer,
            event_name='project.created',
            raw_payload={"project_id": project.id, "name": project.name, "status": project.status},
            processed=False
        )

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(project__company=self.request.user.profile.company).select_related('project')

class TargetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

class TargetViewSet(viewsets.ModelViewSet):
    serializer_class = TargetSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TargetPagination

    def get_queryset(self):
        return Target.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)
