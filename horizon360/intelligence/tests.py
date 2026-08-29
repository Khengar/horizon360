from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from cdp_core.models import Company, Customer, RawEvent
from crm.models import Contact, Deal
from .models import Insight
from .agents import SalesIntelligenceAgent
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from cdp_core.models import UserProfile
from unittest import mock

class IntelligenceTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@test.com")
        self.contact_a = Contact.objects.get(customer=self.customer_a)
        
        self.customer_b = Customer.objects.create(company=self.company_a, primary_email="b@test.com")
        self.contact_b = Contact.objects.get(customer=self.customer_b)
        
        self.customer_c = Customer.objects.create(company=self.company_a, primary_email="c@test.com")
        self.contact_c = Contact.objects.get(customer=self.customer_c)
        
        # Deal A: $150,000, Negotiation, last activity > 7 days (stalled)
        self.deal_a = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_a,
            contact=self.contact_a,
            title="Deal A",
            value=150000,
            stage="negotiation"
        )
        
        # Deal B: $150,000, Negotiation, last activity = 1 day (recent activity)
        self.deal_b = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_b,
            contact=self.contact_b,
            title="Deal B",
            value=150000,
            stage="negotiation"
        )
        
        # Deal C: $50,000, Negotiation, last activity > 7 days (low value)
        self.deal_c = Deal.objects.create(
            company=self.company_a,
            customer=self.customer_c,
            contact=self.contact_c,
            title="Deal C",
            value=50000,
            stage="negotiation"
        )
        
        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)

    def test_high_value_stalled_deal(self):
        base_time = timezone.now()
        twelve_days_ago = base_time - timedelta(days=12)
        Deal.objects.update(created_at=twelve_days_ago)
        
        # When deals are created, they auto-generate deal.stage_changed RawEvents with current timestamp.
        # We must backdate these events too.
        RawEvent.objects.filter(company=self.company_a).update(created_at=twelve_days_ago)
        
        # Add recent activity for Deal B's customer (1 day ago)
        event = RawEvent.objects.create(
            company=self.company_a,
            customer=self.customer_b,
            event_name='page_view',
            raw_payload={},
            processed=True
        )
        # Fix created_at for the RawEvent to be 1 day ago
        RawEvent.objects.filter(id=event.id).update(created_at=base_time - timedelta(days=1))
        
        agent = SalesIntelligenceAgent()
        
        # 1, 2, 3: High value stalled produces insight, recent suppresses, low value suppresses
        agent.run(self.company_a)
        
        insights = Insight.objects.filter(company=self.company_a)
        
        self.assertEqual(insights.count(), 1)
        
        insight = insights.first()
        
        # 4. Correct customer/deal/company references
        self.assertEqual(insight.entity_type, 'deal')
        self.assertEqual(insight.entity_id, str(self.deal_a.id))
        self.assertEqual(insight.company, self.company_a)
        
        # 5. Recommendation content exists
        self.assertEqual(insight.title, 'High-value deal is stalled')
        self.assertTrue('no recorded customer activity for' in insight.description)
        self.assertTrue(len(insight.recommendation) > 0)
        
        # 6. Repeated analysis does not produce duplicate active insights
        agent.run(self.company_a)
        self.assertEqual(Insight.objects.filter(company=self.company_a).count(), 1)

    def test_tenant_isolation(self):
        # 7. Tenant isolation
        agent = SalesIntelligenceAgent()
        
        # Force a generic insight manually to test API isolation
        Insight.objects.create(
            company=self.company_a,
            agent_type='sales',
            title='Test Insight A',
            description='Test A'
        )
        
        client = APIClient()
        
        # User A checks
        client.force_authenticate(user=self.user_a)
        response_a = client.get('/api/intelligence/insights/')
        self.assertEqual(response_a.status_code, 200)
        self.assertEqual(len(response_a.data), 1)
        self.assertEqual(response_a.data[0]['title'], 'Test Insight A')
        
        # User B checks
        client.force_authenticate(user=self.user_b)
        response_b = client.get('/api/intelligence/insights/')
        self.assertEqual(response_b.status_code, 200)
        self.assertEqual(len(response_b.data), 0)
