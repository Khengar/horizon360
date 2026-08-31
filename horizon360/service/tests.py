from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, RawEvent, UserProfile
from service.models import ServiceTicket
from django.contrib.auth.models import User

class ServiceTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="alice@example.com")
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="bob@example.com")
        
        self.client = APIClient()

    def test_ticket_creation_tenant_isolation(self):
        self.client.force_authenticate(user=self.user_a)
        
        # Cross-company customer rejected
        response = self.client.post('/api/service/tickets/', {
            "customer": self.customer_b.id,
            "title": "Help!",
            "priority": "high"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))
        
        # Valid creation
        response = self.client.post('/api/service/tickets/', {
            "customer": self.customer_a.id,
            "title": "Help!",
            "priority": "high"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ServiceTicket.objects.filter(company=self.company_a).count(), 1)
        
        # Verify event
        self.assertEqual(RawEvent.objects.filter(event_name="ticket.created").count(), 1)

    def test_ticket_retrieval_tenant_isolation(self):
        ServiceTicket.objects.create(company=self.company_a, customer=self.customer_a, title="Ticket A")
        ServiceTicket.objects.create(company=self.company_b, customer=self.customer_b, title="Ticket B")
        
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/service/tickets/')
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Ticket A")

    def test_ticket_update_resolution_events(self):
        ticket = ServiceTicket.objects.create(company=self.company_a, customer=self.customer_a, title="Ticket A", priority="low", status="open")
        self.client.force_authenticate(user=self.user_a)
        
        response = self.client.patch(f'/api/service/tickets/{ticket.id}/', {
            "priority": "high",
            "status": "resolved"
        })
        self.assertEqual(response.status_code, 200)
        
        # Should create ticket.priority_changed and ticket.resolved events
        self.assertEqual(RawEvent.objects.filter(event_name="ticket.priority_changed").count(), 1)
        self.assertEqual(RawEvent.objects.filter(event_name="ticket.resolved").count(), 1)
        
        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.resolved_at)
