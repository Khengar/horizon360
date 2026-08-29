from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from .models import EventSchema, RawEvent, Company
from .tasks import process_event_task


class EventSchemaModelTest(TestCase):
    """
    Tests the EventSchema model constraints, specifically the event_name regex validation.
    """
    def test_valid_event_names(self):
        valid_names = ['user.logged_in', 'product.viewed', 'order.completed.success', 'a.b']
        schema = {
            "type": "object",
            "properties": {"user_id": {"type": "integer"}},
            "required": ["user_id"]
        }
        for name in valid_names:
            event_schema = EventSchema(event_name=name, json_schema=schema)
            # Should not raise ValidationError
            event_schema.full_clean()
            event_schema.save()
            self.assertEqual(EventSchema.objects.filter(event_name=name).count(), 1)

    def test_invalid_event_names(self):
        invalid_names = [
            'user',              # no dot
            'User.logged_in',    # uppercase letter
            'user.logged in',    # contains space
            'user.LOGGED_IN',    # uppercase letter
            '.user.logged_in',   # starts with dot
            'user.logged_in.',   # ends with dot
        ]
        schema = {
            "type": "object"
        }
        for name in invalid_names:
            event_schema = EventSchema(event_name=name, json_schema=schema)
            with self.assertRaises(ValidationError):
                event_schema.full_clean()


class EventIngestionViewTest(APITestCase):
    """
    Tests the POST /api/events/ endpoint.
    """
    def setUp(self):
        # Create a sample schema for testing
        self.schema_data = {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["user_id"]
        }
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile
        self.company = Company.objects.create(name="Test Corp")
        self.user = User.objects.create_user(username='testadmin', password='password')
        UserProfile.objects.create(user=self.user, company=self.company)
        self.api_key = str(self.company.api_token)
        self.schema = EventSchema.objects.create(
            company=self.company,
            event_name="user.logged_in",
            json_schema=self.schema_data
        )

    @patch('cdp_core.views.process_event_task.delay')
    def test_ingestion_success(self, mock_task):
        payload = {
            "event_name": "user.logged_in",
            "raw_payload": {
                "user_id": 42,
                "email": "test@example.com"
            }
        }
        response = self.client.post('/api/events/', payload, format='json', HTTP_X_API_KEY=self.api_key)
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('event_id', response.data)
        self.assertEqual(response.data['status'], 'accepted')
        
        # Verify RawEvent was created with processed=False
        raw_event = RawEvent.objects.get(id=response.data['event_id'])
        self.assertEqual(raw_event.event_name, "user.logged_in")
        self.assertEqual(raw_event.raw_payload, payload['raw_payload'])
        self.assertFalse(raw_event.processed)
        
        # Verify task was triggered
        mock_task.assert_called_once_with(raw_event.id)

    def test_ingestion_schema_missing(self):
        payload = {
            "event_name": "product.viewed",
            "raw_payload": {
                "product_id": 99
            }
        }
        response = self.client.post('/api/events/', payload, format='json', HTTP_X_API_KEY=self.api_key)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Schema for event 'product.viewed' not found", response.data['error'])

    def test_ingestion_validation_fails(self):
        # user_id is missing, which is a required field in our test schema
        payload = {
            "event_name": "user.logged_in",
            "raw_payload": {
                "email": "invalid-email-format"
            }
        }
        response = self.client.post('/api/events/', payload, format='json', HTTP_X_API_KEY=self.api_key)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("Schema validation failed", response.data['error'])

    def test_ingestion_invalid_event_name_in_payload(self):
        payload = {
            "event_name": "INVALID_NAME",
            "raw_payload": {
                "user_id": 42
            }
        }
        response = self.client.post('/api/events/', payload, format='json', HTTP_X_API_KEY=self.api_key)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)


class CeleryNormalizationTaskTest(TestCase):
    """
    Tests the process_event_task Celery task.
    """
    def test_process_event_task_success(self):
        # Create a raw event with spaces and uppercase in the name to verify normalization
        raw_event = RawEvent.objects.create(
            event_name="  User.Logged_In  ",
            raw_payload={"some": "data"},
            processed=False
        )
        
        result = process_event_task(raw_event.id)
        self.assertTrue(result)
        
        # Reload raw event and check normalized name and processed state
        raw_event.refresh_from_db()
        self.assertEqual(raw_event.event_name, "user.logged_in")
        self.assertTrue(raw_event.processed)

    def test_process_event_task_nonexistent_id(self):
        result = process_event_task(999999)
        self.assertFalse(result)

class Customer360ViewTest(APITestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from cdp_core.models import UserProfile, Customer, Company
        from crm.models import Contact, Deal
        
        self.company_a = Company.objects.create(name="Company A")
        self.company_b = Company.objects.create(name="Company B")
        
        self.user_a = User.objects.create_user(username='usera', password='password')
        UserProfile.objects.create(user=self.user_a, company=self.company_a)
        
        self.user_b = User.objects.create_user(username='userb', password='password')
        UserProfile.objects.create(user=self.user_b, company=self.company_b)
        
        self.customer_a = Customer.objects.create(company=self.company_a, primary_email="a@test.com")
        self.contact_a = Contact.objects.get(customer=self.customer_a)
        Deal.objects.create(company=self.company_a, customer=self.customer_a, contact=self.contact_a, value=100, stage='won')
        Deal.objects.create(company=self.company_a, customer=self.customer_a, contact=self.contact_a, value=50, stage='new')
        RawEvent.objects.create(company=self.company_a, customer=self.customer_a, event_name='test.event', raw_payload={'k':'v'})
        
        self.customer_b = Customer.objects.create(company=self.company_b, primary_email="b@test.com")
        
    def test_unauthenticated_request_rejected(self):
        res = self.client.get(f'/api/customers/{self.customer_a.id}/360/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_authenticated_can_retrieve_own(self):
        self.client.force_authenticate(user=self.user_a)
        res = self.client.get(f'/api/customers/{self.customer_a.id}/360/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(str(res.data['identity']['id']), str(self.customer_a.id))
        self.assertEqual(res.data['contact']['id'], self.contact_a.id)
        self.assertEqual(len(res.data['deals']), 2)
        self.assertEqual(res.data['aggregates']['total_deal_value'], 150)
        self.assertEqual(res.data['aggregates']['won_revenue'], 100)
        self.assertEqual(res.data['aggregates']['open_pipeline_value'], 50)
        self.assertEqual(len(res.data['timeline']), 3)
        event_names = [e['event_name'] for e in res.data['timeline']]
        self.assertIn('test.event', event_names)
        
    def test_cannot_retrieve_other_company(self):
        self.client.force_authenticate(user=self.user_a)
        res = self.client.get(f'/api/customers/{self.customer_b.id}/360/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_customer_with_no_events_or_deals(self):
        self.client.force_authenticate(user=self.user_b)
        res = self.client.get(f'/api/customers/{self.customer_b.id}/360/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['deals']), 0)
        self.assertEqual(len(res.data['timeline']), 0)
        self.assertEqual(res.data['aggregates']['total_deal_value'], 0)
