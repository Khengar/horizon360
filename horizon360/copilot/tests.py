from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, Customer, UserProfile
from crm.models import Contact, Deal
from intelligence.models import Insight
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class CopilotTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="alice@example.com")
        self.contact_a = Contact.objects.get(customer=self.customer_a)
        
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="bob@example.com")
        self.contact_b = Contact.objects.get(customer=self.customer_b)
        
        self.deal_a = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Enterprise License",
            value=150000,
            stage="negotiation"
        )
        # Set updated_at back a bit to simulate stalled deal (12 days)
        twelve_days_ago = timezone.now() - timedelta(days=12)
        Deal.objects.filter(id=self.deal_a.id).update(updated_at=twelve_days_ago)
        
        self.insight_a = Insight.objects.create(
            company=self.company_a,
            agent_type="sales",
            severity="high",
            title="High-value deal is stalled",
            description="Enterprise License is a $150,000 Negotiation deal with no recorded customer activity for 12 days.",
            recommendation="Schedule a follow-up with the customer.",
            entity_type="deal",
            entity_id=str(self.deal_a.id)
        )

        self.client = APIClient()

    def test_authenticated_copilot_request_succeeds(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "What deals are at risk?"}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "DEAL_RISK")

    def test_unauthenticated_request_rejected(self):
        response = self.client.post('/api/copilot/chat/', {"query": "What deals are at risk?"}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_company_a_cannot_retrieve_company_b_context(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.post('/api/copilot/chat/', {"query": "What deals are at risk?"}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Enterprise License", response.data["answer"])
        self.assertEqual(len(response.data["sources"]), 0)

    def test_deal_risk_returns_only_tenant_owned_data(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "What deals are at risk?"}, format='json')
        self.assertIn("Enterprise License", response.data["answer"])
        self.assertEqual(len(response.data["sources"]), 2) # deal and insight

    def test_pipeline_summary_returns_correct_metrics(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "What's our current pipeline?"}, format='json')
        self.assertEqual(response.data["intent"], "PIPELINE_SUMMARY")
        self.assertIn("$150,000", response.data["answer"])

    def test_customer_lookup_resolves_correct_customer(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "Tell me about alice@example.com"}, format='json')
        self.assertEqual(response.data["intent"], "CUSTOMER_LOOKUP")
        self.assertIn("alice@example.com", response.data["answer"])
        self.assertIn("$150,000", response.data["answer"])

    def test_deal_explanation_references_correct_deal(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "Why is Enterprise License at risk?"}, format='json')
        self.assertEqual(response.data["intent"], "DEAL_EXPLANATION")
        self.assertIn("Schedule a follow-up", response.data["answer"])

    def test_sales_recommendation_uses_existing_insights(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "What should sales focus on?"}, format='json')
        self.assertEqual(response.data["intent"], "SALES_RECOMMENDATION")
        self.assertIn("High-value deal is stalled", response.data["answer"])

    def test_unknown_question_returns_unsupported_response(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post('/api/copilot/chat/', {"query": "What's the weather?"}, format='json')
        self.assertEqual(response.data["intent"], "UNKNOWN")
        self.assertIn("unsupported", response.data["answer"])

    def test_empty_data_produces_graceful_response(self):
        self.client.force_authenticate(user=self.user_b)
        response = self.client.post('/api/copilot/chat/', {"query": "What deals are at risk?"}, format='json')
        self.assertIn("no high-value deals", response.data["answer"])
