from rest_framework import viewsets, permissions
from .models import Department, Employee, LeaveRequest
from .serializers import DepartmentSerializer, EmployeeSerializer, LeaveRequestSerializer
from cdp_core.models import RawEvent

class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Department.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.profile.company)

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Employee.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        employee = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=employee.company,
            event_name='employee.created',
            raw_payload={"employee_id": employee.id, "email": employee.email, "role": employee.role},
            processed=False
        )

    def perform_update(self, serializer):
        employee = serializer.save()
        RawEvent.objects.create(
            company=employee.company,
            event_name='employee.updated',
            raw_payload={"employee_id": employee.id, "email": employee.email, "status": employee.status},
            processed=False
        )

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LeaveRequest.objects.filter(company=self.request.user.profile.company)

    def perform_create(self, serializer):
        leave = serializer.save(company=self.request.user.profile.company)
        RawEvent.objects.create(
            company=leave.company,
            event_name='leave.requested',
            raw_payload={"leave_id": leave.id, "employee_id": leave.employee.id, "status": leave.status},
            processed=False
        )

    def perform_update(self, serializer):
        leave = serializer.save()
        event_name = 'leave.updated'
        if leave.status == 'approved':
            event_name = 'leave.approved'
        elif leave.status == 'rejected':
            event_name = 'leave.rejected'
            
        RawEvent.objects.create(
            company=leave.company,
            event_name=event_name,
            raw_payload={"leave_id": leave.id, "employee_id": leave.employee.id, "status": leave.status},
            processed=False
        )
