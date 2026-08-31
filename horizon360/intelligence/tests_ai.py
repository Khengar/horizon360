from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from cdp_core.models import Company, Customer, RawEvent, UserProfile, Workflow
from crm.models import Contact, Deal
from intelligence.models import Insight
from intelligence.agents import (
    SalesIntelligenceAgent,
    CustomerHealthAgent,
    MarketingIntelligenceAgent,
    ServiceIntelligenceAgent,
    FinanceIntelligenceAgent,
    ExecutiveSynthesisAgent,
    MeshRunner
)
from intelligence.llm_client import LLMClient
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from cdp_core.workflow_service import execute_workflows

class AIAgentIntegrationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="AI Test Corp")
        self.user = User.objects.create_user(username="ai_user", password="password")
        UserProfile.objects.create(user=self.user, company=self.company)

        self.customer = Customer.objects.create(
            company=self.company,
            primary_email="charlie@enterprise.com",
            timeline=[
                {"event_name": "user.identified", "time": "2026-08-01"},
                {"event_name": "pricing.viewed", "time": "2026-08-02", "payload": {"url": "/pricing"}},
                {"event_name": "pricing.viewed", "time": "2026-08-03", "payload": {"url": "/pricing"}},
                {"event_name": "demo.requested", "time": "2026-08-03"},
                {"event_name": "trial.started", "time": "2026-08-04"},
                {"event_name": "login", "time": "2026-08-05"}
            ]
        )
        self.contact = Contact.objects.get(customer=self.customer)
        self.deal = Deal.objects.create(
            company=self.company,
            customer=self.customer,
            contact=self.contact,
            title="Enterprise Cloud Deal",
            value=120000,
            stage="negotiation"
        )
        # Backdate deal and events so agents trigger stalled/churn detection
        past_time = timezone.now() - timedelta(days=20)
        Deal.objects.filter(id=self.deal.id).update(created_at=past_time, updated_at=past_time)
        RawEvent.objects.filter(company=self.company).update(created_at=past_time)
        
        self.client = APIClient()

    def test_llm_client_fallback_mode(self):
        client = LLMClient(provider='fallback')
        self.assertEqual(client.provider, 'fallback')
        res = client.chat_completion([{"role": "user", "content": "Hello"}])
        self.assertTrue(res['success'])
        self.assertTrue(len(res['content']) > 0)

    def test_customer_health_agent_churn_detection(self):
        agent = CustomerHealthAgent()
        insights = agent.run(self.company)
        self.assertTrue(any(i.agent_type == 'customer_success' for i in insights))
        churn_insight = next((i for i in insights if 'Churn Warning' in i.title), None)
        self.assertIsNotNone(churn_insight)
        self.assertEqual(churn_insight.severity, 'high')

    def test_marketing_intelligence_agent(self):
        # Create prospective customer with pricing views but no deal
        prospect = Customer.objects.create(
            company=self.company,
            primary_email="prospect@acme.com",
            timeline=[
                {"event_name": "pricing.viewed", "payload": {"url": "/pricing"}},
                {"event_name": "pricing.viewed", "payload": {"url": "/pricing/enterprise"}}
            ]
        )
        agent = MarketingIntelligenceAgent()
        insights = agent.run(self.company)
        self.assertTrue(any(i.agent_type == 'marketing' for i in insights))
        mkt_insight = next((i for i in insights if 'prospect@acme.com' in i.title), None)
        self.assertIsNotNone(mkt_insight)

    def test_service_intelligence_agent(self):
        RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name="support.ticket_created",
            raw_payload={"subject": "SSO Login Failure", "priority": "high"}
        )
        agent = ServiceIntelligenceAgent()
        insights = agent.run(self.company)
        self.assertTrue(any(i.agent_type == 'service' for i in insights))
        svc_insight = next((i for i in insights if i.agent_type == 'service'), None)
        self.assertIsNotNone(svc_insight)
        self.assertEqual(svc_insight.severity, 'critical')

    def test_finance_intelligence_agent(self):
        # Deal won without payment event
        won_deal = Deal.objects.create(
            company=self.company,
            customer=self.customer,
            contact=self.contact,
            title="Unbilled Won Project",
            value=85000,
            stage="won"
        )
        agent = FinanceIntelligenceAgent()
        insights = agent.run(self.company)
        self.assertTrue(any(i.agent_type == 'finance' for i in insights))
        fin_insight = next((i for i in insights if 'Unbilled Revenue' in i.title), None)
        self.assertIsNotNone(fin_insight)

    def test_executive_synthesis_agent(self):
        agent = ExecutiveSynthesisAgent()
        insights = agent.run(self.company)
        self.assertTrue(len(insights) > 0)
        exec_insight = insights[0]
        self.assertEqual(exec_insight.agent_type, 'executive')
        self.assertIn("$120,000", exec_insight.description)

    def test_mesh_runner_runs_all_6_agents(self):
        result = MeshRunner.run_mesh_for_company(self.company)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['agents_executed'], 6)
        self.assertTrue(result['total_insights_generated'] >= 2)

    def test_execute_action_api_endpoint(self):
        self.client.force_authenticate(user=self.user)
        
        # Test 1: Apply Tag
        res_tag = self.client.post('/api/intelligence/action/', {
            "action_type": "apply_tag",
            "entity_type": "customer",
            "entity_id": str(self.customer.id),
            "payload": {"tag": "AI_VIP_TIER"}
        }, format='json')
        self.assertEqual(res_tag.status_code, 200)
        self.customer.refresh_from_db()
        self.assertIn("AI_VIP_TIER", self.customer.attributes.get('tags', []))

        # Test 2: Draft Email
        res_email = self.client.post('/api/intelligence/action/', {
            "action_type": "draft_email",
            "entity_type": "customer",
            "entity_id": str(self.customer.id),
            "payload": {"message": "Custom AI SDR follow-up email draft"}
        }, format='json')
        self.assertEqual(res_email.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.attributes.get('latest_ai_email_draft'), "Custom AI SDR follow-up email draft")

    def test_ai_workflow_actions(self):
        wf_insight = Workflow.objects.create(
            company=self.company,
            name="AI High Value Alert",
            trigger_event="order.completed",
            condition_field="amount",
            condition_operator=">=",
            condition_value="5000",
            action_type="ai_generate_insight",
            action_event_name="insight.generated"
        )
        event = RawEvent.objects.create(
            company=self.company,
            customer=self.customer,
            event_name="order.completed",
            raw_payload={"amount": 7500, "item": "Enterprise Addon"}
        )
        execute_workflows(event)
        self.assertTrue(Insight.objects.filter(company=self.company, agent_type="workflow_ai").exists())
