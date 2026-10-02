import os
os.environ['LLM_PROVIDER'] = 'fallback'
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User

from cdp_core.models import Company, Customer, RawEvent, UserProfile, Segment, UnifiedProfile
from marketing.models import (
    Campaign, CampaignSegment, CampaignContent, CampaignRecipient,
    CampaignEvent, AttributionTouchpoint, Lead, CampaignTransaction
)
from marketing.services import CampaignExecutionService
from marketing.ai.bandit import ThompsonSamplingBandit
from marketing.ai.propensity import PropensityScorer
from marketing.ai.audience_agent import AutonomousAudienceAgent
from marketing.ai.attribution import AttributionCalculator

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class MarketingTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")

        self.user_a = User.objects.create_user(username="usera", password="password")
        UserProfile.objects.create(user=self.user_a, company=self.company_a)

        self.user_b = User.objects.create_user(username="userb", password="password")
        UserProfile.objects.create(user=self.user_b, company=self.company_b)

        self.customer_a = Customer.objects.create(
            company=self.company_a, primary_email="alice@example.com", primary_phone="+1234567890",
            attributes={"first_name": "Alice", "tier": "enterprise"}
        )
        self.customer_b = Customer.objects.create(
            company=self.company_b, primary_email="bob@example.com", primary_phone="+1987654321"
        )
        UnifiedProfile.objects.create(
            customer=self.customer_a, company=self.company_a,
            marketing_consent=True, engagement_score=85.0, engagement_tier='on_fire'
        )

        self.campaign_a = Campaign.objects.create(
            company=self.company_a, name="Campaign A", status="active", budget=1000, channel="email"
        )
        self.campaign_b = Campaign.objects.create(
            company=self.company_b, name="Campaign B", status="active", budget=2000, channel="email"
        )

        self.client = APIClient()

    def test_tenant_isolation_creation(self):
        self.client.force_authenticate(user=self.user_a)

        # Cross-company customer rejected
        response = self.client.post('/api/marketing/leads/', {
            "customer": self.customer_b.id,
            "name": "Invalid Lead",
            "email": "invalid@example.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))

        # Cross-company campaign rejected
        response = self.client.post('/api/marketing/leads/', {
            "campaign": self.campaign_b.id,
            "name": "Invalid Lead",
            "email": "invalid@example.com"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not belong to this company", str(response.data))

        # Valid lead creation
        response = self.client.post('/api/marketing/leads/', {
            "customer": self.customer_a.id,
            "campaign": self.campaign_a.id,
            "name": "Valid Lead",
            "email": "valid@example.com"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Lead.objects.filter(company=self.company_a).count(), 1)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.created").count(), 1)

    def test_lead_status_events(self):
        lead = Lead.objects.create(company=self.company_a, name="Lead A", email="a@example.com", status="new")
        self.client.force_authenticate(user=self.user_a)

        # Update to qualified
        response = self.client.patch(f'/api/marketing/leads/{lead.id}/', {"status": "qualified"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.qualified").count(), 1)

        # Update to converted
        response = self.client.patch(f'/api/marketing/leads/{lead.id}/', {"status": "converted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="lead.converted").count(), 1)

    def test_campaign_status_events(self):
        self.client.force_authenticate(user=self.user_a)

        # Create draft campaign
        response = self.client.post('/api/marketing/campaigns/', {
            "name": "New Campaign",
            "status": "draft"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(RawEvent.objects.filter(event_name="campaign.created").count(), 1)

        campaign_id = response.data['id']

        # Update to active
        response = self.client.patch(f'/api/marketing/campaigns/{campaign_id}/', {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawEvent.objects.filter(event_name="campaign.active").count(), 1)

    def test_campaign_audience_resolution_and_preview(self):
        self.client.force_authenticate(user=self.user_a)

        # Create a Segment in Company A
        segment = Segment.objects.create(
            company=self.company_a,
            name="Enterprise Tier",
            rules=[{"field": "attributes.tier", "operator": "==", "value": "enterprise"}]
        )

        campaign = Campaign.objects.create(
            company=self.company_a,
            name="Q4 Enterprise Push",
            channel="email",
            budget=5000.00
        )
        CampaignSegment.objects.create(campaign=campaign, segment=segment)

        response = self.client.post(f'/api/marketing/campaigns/{campaign.id}/preview-audience/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['estimated_audience'], 1)
        self.assertEqual(response.data['channel'], 'email')
        self.assertEqual(len(response.data['sample_recipients']), 1)

    def test_campaign_execution_service_lifecycle(self):
        service = CampaignExecutionService()
        campaign = self.campaign_a

        # 1. Resolve audience
        audience = service.resolve_audience(campaign)
        self.assertIn(self.customer_a, audience)

        # 2. Assign variant & render
        content = CampaignContent.objects.create(
            campaign=campaign,
            variant_name='A',
            subject="Hello {{ customer.name }}",
            body_html="<p>Special deal for {{ account.name }}</p>"
        )
        rendered = service.render_content(content, self.customer_a)
        self.assertEqual(rendered['subject'], "Hello Alice")

        # 3. Create recipient and track events
        recipient = CampaignRecipient.objects.create(
            campaign=campaign,
            customer=self.customer_a,
            company=self.company_a,
            content_variant=content,
            status='queued'
        )

        # Track Sent
        service.record_recipient_event(campaign, recipient, 'sent')
        self.assertEqual(recipient.status, 'sent')
        self.assertIsNotNone(recipient.sent_at)

        # Track Delivered
        service.record_recipient_event(campaign, recipient, 'delivered')
        self.assertEqual(recipient.status, 'delivered')

        # Track Clicked
        service.record_recipient_event(campaign, recipient, 'clicked')
        self.assertEqual(recipient.status, 'clicked')

        # Track Converted
        service.record_recipient_event(campaign, recipient, 'converted', revenue=Decimal('250.00'))
        self.assertEqual(recipient.status, 'converted')
        self.assertEqual(recipient.conversion_value, Decimal('250.00'))

        # Check metrics updated on Campaign
        campaign.refresh_from_db()
        self.assertEqual(campaign.total_sent, 1)
        self.assertEqual(campaign.total_delivered, 1)
        self.assertEqual(campaign.total_clicked, 1)
        self.assertEqual(campaign.total_converted, 1)

        # Check attribution touchpoint created
        self.assertTrue(AttributionTouchpoint.objects.filter(campaign=campaign, customer=self.customer_a).exists())

    def test_contextual_multi_armed_bandit(self):
        bandit = ThompsonSamplingBandit()
        c1 = CampaignContent.objects.create(campaign=self.campaign_a, variant_name='Arm 1')
        c2 = CampaignContent.objects.create(campaign=self.campaign_a, variant_name='Arm 2')

        # Feed arm 1 positive rewards, arm 2 negative rewards
        for _ in range(10):
            bandit.record_feedback(c1, reward=True)
            bandit.record_feedback(c2, reward=False)

        c1.refresh_from_db()
        c2.refresh_from_db()

        self.assertGreater(c1.bandit_alpha, c2.bandit_alpha)
        self.assertGreater(c2.bandit_beta, c1.bandit_beta)

        stats = bandit.get_distribution_stats([c1, c2])
        self.assertEqual(len(stats), 2)
        # Arm 1 should have much higher traffic weight allocated
        arm1_stat = next(s for s in stats if s['id'] == c1.id)
        arm2_stat = next(s for s in stats if s['id'] == c2.id)
        self.assertGreater(arm1_stat['traffic_weight'], arm2_stat['traffic_weight'])

    def test_propensity_scorer(self):
        scorer = PropensityScorer()
        score = scorer.score_customer(self.customer_a, self.campaign_a)

        self.assertIn('conversion_probability', score)
        self.assertIn('churn_probability', score)
        self.assertIn('optimal_send_hour', score)
        self.assertGreater(score['conversion_probability'], 0.5)

    def test_multi_touch_attribution_calculator(self):
        now = timezone.now()
        tp1 = AttributionTouchpoint.objects.create(
            company=self.company_a, campaign=self.campaign_a, customer=self.customer_a,
            touchpoint_type='impression', channel='email', occurred_at=now
        )
        tp2 = AttributionTouchpoint.objects.create(
            company=self.company_a, campaign=self.campaign_a, customer=self.customer_a,
            touchpoint_type='email_click', channel='email', occurred_at=now
        )
        tp3 = AttributionTouchpoint.objects.create(
            company=self.company_a, campaign=self.campaign_a, customer=self.customer_a,
            touchpoint_type='conversion', channel='email', occurred_at=now
        )

        results = AttributionCalculator.calculate_attribution_weights([tp1, tp2, tp3], Decimal('1000.00'))
        self.assertEqual(len(results), 3)

        tp1.refresh_from_db()
        tp2.refresh_from_db()
        tp3.refresh_from_db()

        self.assertEqual(tp1.first_touch_weight, 1.0)
        self.assertEqual(tp3.last_touch_weight, 1.0)
        self.assertAlmostEqual(tp1.linear_weight, 1.0 / 3.0, places=2)
        self.assertEqual(tp1.position_based_weight, 0.40)
        self.assertEqual(tp3.position_based_weight, 0.40)
        self.assertEqual(tp2.position_based_weight, 0.20)

    def test_campaign_webhook_callback(self):
        recipient = CampaignRecipient.objects.create(
            campaign=self.campaign_a,
            customer=self.customer_a,
            company=self.company_a,
            status='delivered'
        )

        response = self.client.post('/api/marketing/webhooks/campaign-events/', {
            "recipient_id": recipient.id,
            "event_type": "opened",
            "metadata": {"user_agent": "Mozilla"}
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        recipient.refresh_from_db()
        self.assertEqual(recipient.status, 'opened')
        self.assertIsNotNone(recipient.opened_at)

    def test_campaign_actions_api(self):
        self.client.force_authenticate(user=self.user_a)

        # 1. Schedule
        resp = self.client.post(f'/api/marketing/campaigns/{self.campaign_a.id}/schedule/', {
            "scheduled_at": "2026-11-01T10:00:00Z",
            "timezone": "UTC"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'scheduled')

        # 2. Duplicate
        resp = self.client.post(f'/api/marketing/campaigns/{self.campaign_a.id}/duplicate/')
        self.assertEqual(resp.status_code, 201)
        self.assertIn("Copy of", resp.data['name'])

        # 3. Analytics
        resp = self.client.get(f'/api/marketing/campaigns/{self.campaign_a.id}/analytics/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('kpis', resp.data)
        self.assertIn('financials', resp.data)
        self.assertIn('bandit_variants', resp.data)

        # 4. Generate Audience (Autonomous Cohort Agent)
        resp = self.client.post(f'/api/marketing/campaigns/{self.campaign_a.id}/generate-audience/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('recommended_rules', resp.data)

        # 5. Generate Copy (RAG Copy Generation)
        resp = self.client.post(f'/api/marketing/campaigns/{self.campaign_a.id}/generate-copy/', {
            "tone": "enthusiastic"
        })
        self.assertEqual(resp.status_code, 201)
        self.assertIn('subject', resp.data)

        # 6. Attribution Briefing
        resp = self.client.get(f'/api/marketing/campaigns/{self.campaign_a.id}/attribution-briefing/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('narrative_briefing', resp.data)

    def test_marketing_dashboard_view(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get('/api/marketing/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_campaigns_count', response.data)
        self.assertIn('total_spend', response.data)
        self.assertIn('total_attributed_roi', response.data)
