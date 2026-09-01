import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from cdp_core.models import Company, UserProfile
from cdp_core.throttling import TenantRateThrottle
from integrations.models import WebhookSubscription, WebhookDeliveryLog
from integrations.webhooks import generate_signature, dispatch_webhook

class Phase5PlatformPolishTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Tenant 1 (Enterprise)
        self.company1 = Company.objects.create(name="Enterprise Global", plan="enterprise")
        self.user1 = User.objects.create_user(username="ent_admin", password="password123", email="admin@enterprise.com")
        self.profile1 = UserProfile.objects.create(user=self.user1, company=self.company1)

        # Tenant 2 (Starter)
        self.company2 = Company.objects.create(name="Starter Small", plan="starter")
        self.user2 = User.objects.create_user(username="start_user", password="password123", email="user@starter.com")
        self.profile2 = UserProfile.objects.create(user=self.user2, company=self.company2)

        self.client.force_authenticate(user=self.user1)

    def test_webhook_subscription_crud(self):
        # 1. Create Webhook Subscription
        sub_res = self.client.post('/api/v1/integrations/webhook-subscriptions/', {
            "target_url": "https://api.external-crm.com/webhooks/horizon",
            "subscribed_events": ["deal.won", "payment.completed"],
            "is_active": True
        }, format='json')
        self.assertEqual(sub_res.status_code, status.HTTP_201_CREATED)
        sub_id = sub_res.data['id']
        self.assertIsNotNone(sub_res.data['secret'])

        # 2. Query Subscriptions
        list_res = self.client.get('/api/v1/integrations/webhook-subscriptions/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    def test_hmac_signature_generation(self):
        payload = json.dumps({"deal_id": 101, "amount": 50000})
        secret = "secret_key_12345"
        sig = generate_signature(payload, secret)

        self.assertTrue(sig.startswith("sha256="))
        # Verify deterministic output
        self.assertEqual(sig, generate_signature(payload, secret))

    @patch('urllib.request.urlopen')
    def test_webhook_dispatch_and_delivery_logging(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'{"received": true}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        sub = WebhookSubscription.objects.create(
            company=self.company1,
            target_url="https://api.example.com/events",
            secret="test_secret",
            subscribed_events=["payment.completed"]
        )

        event_payload = {"payment_id": "pay_999", "amount": 1000.00}
        logs = dispatch_webhook(self.company1, "payment.completed", event_payload)

        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertTrue(log.success)
        self.assertEqual(log.response_status, 200)
        self.assertEqual(log.event_name, "payment.completed")

        # Verify Delivery Log API
        log_res = self.client.get('/api/v1/integrations/webhook-logs/')
        self.assertEqual(log_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(log_res.data), 1)

    @patch('urllib.request.urlopen')
    def test_webhook_ping_action(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b'OK'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        sub = WebhookSubscription.objects.create(
            company=self.company1,
            target_url="https://api.example.com/ping-test",
            secret="secret_ping"
        )

        ping_res = self.client.post(f'/api/v1/integrations/webhook-subscriptions/{sub.id}/ping/')
        self.assertEqual(ping_res.status_code, status.HTTP_200_OK)
        self.assertTrue(ping_res.data['success'])
        self.assertEqual(ping_res.data['response_status'], 200)

    def test_tenant_rate_throttling_tiers(self):
        throttle = TenantRateThrottle()

        # Enterprise User
        mock_request_ent = MagicMock()
        mock_request_ent.user = self.user1
        throttle.request = mock_request_ent
        self.assertEqual(throttle.get_rate(), '2000/min')

        # Starter User
        mock_request_start = MagicMock()
        mock_request_start.user = self.user2
        throttle.request = mock_request_start
        self.assertEqual(throttle.get_rate(), '100/min')
