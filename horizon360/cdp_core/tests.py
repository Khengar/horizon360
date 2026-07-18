from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from .models import EventSchema, RawEvent
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
        self.schema = EventSchema.objects.create(
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
        response = self.client.post('/api/events/', payload, format='json')
        
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
        response = self.client.post('/api/events/', payload, format='json')
        
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
        response = self.client.post('/api/events/', payload, format='json')
        
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
        response = self.client.post('/api/events/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("event_name", response.data)


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
