from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, UserProfile, RawEvent
from hrms.models import Department, Employee, LeaveRequest
from django.contrib.auth.models import User

class HRMSTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.dept_a = Department.objects.create(company=self.company_a, name="Engineering A")
        self.dept_b = Department.objects.create(company=self.company_b, name="Engineering B")
        
        self.client = APIClient()

    def test_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Try to assign cross-tenant department to employee
        response = self.client.post('/api/hrms/employees/', {
            "department": self.dept_b.id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "role": "Developer"
        })
        self.assertEqual(response.status_code, 400)
        
        # Valid assignment
        response = self.client.post('/api/hrms/employees/', {
            "department": self.dept_a.id,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "role": "Developer"
        })
        self.assertEqual(response.status_code, 201)
        
        emp_id = response.data['id']
        
        # LeaveRequest creation
        response = self.client.post('/api/hrms/leave-requests/', {
            "employee": emp_id,
            "start_date": "2024-01-01",
            "end_date": "2024-01-05",
            "reason": "Vacation"
        })
        self.assertEqual(response.status_code, 201)
        leave_id = response.data['id']
        
        # Events emitted
        events = RawEvent.objects.filter(company=self.company_a)
        self.assertEqual(events.count(), 2)
        event_names = [e.event_name for e in events]
        self.assertIn("employee.created", event_names)
        self.assertIn("leave.requested", event_names)
        
        # LeaveRequest approval
        response = self.client.patch(f'/api/hrms/leave-requests/{leave_id}/', {
            "status": "approved"
        })
        self.assertEqual(response.status_code, 200)
        
        # Approved event emitted
        events = RawEvent.objects.filter(company=self.company_a, event_name="leave.approved")
        self.assertEqual(events.count(), 1)
