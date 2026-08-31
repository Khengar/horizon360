from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from cdp_core.models import Company, UserProfile, Customer
from service.models import SLAPolicy, ServiceTicket, TicketComment, KnowledgeArticle

class Phase4ServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.company = Company.objects.create(name="Service Global Corp", plan="enterprise")
        self.agent = User.objects.create_user(username="support_agent", password="password123", email="agent@service.com")
        self.profile = UserProfile.objects.create(user=self.agent, company=self.company)

        self.customer = Customer.objects.create(
            company=self.company,
            primary_email="help@client.com"
        )
        self.client.force_authenticate(user=self.agent)

    def test_sla_policy_and_breach_calculation(self):
        # 1. Create Critical SLA Policy (4h resolution)
        sla_res = self.client.post('/api/v1/service/sla-policies/', {
            "name": "Mission Critical SLA",
            "priority": "critical",
            "response_time_hours": 1,
            "resolution_time_hours": 4
        }, format='json')
        self.assertEqual(sla_res.status_code, status.HTTP_201_CREATED)

        # 2. Create Ticket
        ticket_res = self.client.post('/api/v1/service/tickets/', {
            "customer": str(self.customer.id),
            "title": "Database connection timeout",
            "priority": "critical",
            "status": "open"
        }, format='json')
        self.assertEqual(ticket_res.status_code, status.HTTP_201_CREATED)
        ticket_id = ticket_res.data['id']

        ticket = ServiceTicket.objects.get(id=ticket_id)
        self.assertIsNotNone(ticket.sla_due_at)
        self.assertEqual(ticket.sla_policy.priority, 'critical')

        # 3. Add Agent Response Comment
        comment_res = self.client.post(f'/api/v1/service/tickets/{ticket_id}/add-comment/', {
            "message": "Investigating connection pool now.",
            "is_internal": False
        }, format='json')
        self.assertEqual(comment_res.status_code, status.HTTP_201_CREATED)

        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.first_responded_at)
        self.assertEqual(ticket.comments.count(), 1)

    def test_knowledge_base_articles(self):
        # 1. Create Article
        art_res = self.client.post('/api/v1/service/articles/', {
            "title": "Configuring SSO SAML 2.0",
            "slug": "configuring-sso-saml",
            "category": "Authentication",
            "content": "Follow these steps to configure Okta SSO...",
            "is_published": True
        }, format='json')
        self.assertEqual(art_res.status_code, status.HTTP_201_CREATED)
        slug = art_res.data['slug']

        # 2. Search Article
        search_res = self.client.get('/api/v1/service/articles/?search=SAML')
        self.assertEqual(search_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_res.data), 1)

        # 3. Increment View Counter
        view_res = self.client.post(f'/api/v1/service/articles/{art_res.data["id"]}/view/')
        self.assertEqual(view_res.status_code, status.HTTP_200_OK)
        self.assertEqual(view_res.data['view_count'], 1)
