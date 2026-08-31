from rest_framework import viewsets, permissions
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer
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
