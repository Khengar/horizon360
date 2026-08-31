from django.test import TestCase
from rest_framework.test import APIClient
from cdp_core.models import Company, UserProfile, RawEvent, Workflow
from integrations.models import Integration, IntegrationLog
from django.contrib.auth.models import User
import uuid

class IntegrationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Integration Corp")
        self.user = User.objects.create_user(username="intadmin", password="password")
        UserProfile.objects.create(user=self.user, company=self.company)
        self.client = APIClient()

        self.other_company = Company.objects.create(name="Other Corp")
        
        self.secret = str(uuid.uuid4())
        self.integration = Integration.objects.create(
            company=self.company,
            name="Stripe Demo",
            provider="stripe_demo",
            direction="bi_directional",
            config={'webhook_secret': self.secret}
        )
        
        self.hubspot = Integration.objects.create(
            company=self.company,
            name="HubSpot Demo",
            provider="hubspot_demo",
            direction="bi_directional",
            config={'webhook_secret': self.secret}
        )

    def test_inbound_webhook_auth_and_normalization(self):
        url = f'/api/nexus/webhooks/{self.integration.id}/'
        
        # Unauthenticated
        resp = self.client.post(url, {'type': 'payment_received', 'id': 'ev_123', 'customer_email': 'test@example.com'}, format='json')
        self.assertEqual(resp.status_code, 401)
        
        # Authenticated
        resp = self.client.post(
            url, 
            {'type': 'payment_received', 'id': 'ev_123', 'customer_email': 'test@example.com'}, 
            HTTP_X_STRIPE_DEMO_SIG=self.secret, 
            format='json'
        )
        self.assertEqual(resp.status_code, 202)
        
        # Verify RawEvent created
        event = RawEvent.objects.filter(company=self.company, event_name='external.payment_received').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.customer.primary_email, 'test@example.com')
        
        # Idempotency
        resp2 = self.client.post(
            url, 
            {'type': 'payment_received', 'id': 'ev_123', 'customer_email': 'test@example.com'}, 
            HTTP_X_STRIPE_DEMO_SIG=self.secret, 
            format='json'
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['status'], 'already_processed')

    def test_outbound_workflow(self):
        # Setup workflow
        Workflow.objects.create(
            company=self.company,
            name="Test Outbound",
            trigger_event="deal.won",
            action_type="send_integration_event",
            action_event_name="hubspot_demo"
        )
        
        # Trigger event
        from cdp_core.workflow_service import execute_workflows
        event = RawEvent.objects.create(company=self.company, event_name='deal.won', raw_payload={}, processed=False)
        execute_workflows(event)
        
        # Check log
        log = IntegrationLog.objects.filter(company=self.company, direction='outbound').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'success')
