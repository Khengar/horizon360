from .base import BaseConnector

class HubSpotDemoConnector(BaseConnector):
    def authenticate(self, request_headers=None, request_payload=None):
        expected_secret = self.config.get('webhook_secret')
        actual_secret = request_headers.get('HTTP_X_HUBSPOT_DEMO_SIG') if request_headers else None
        return expected_secret and actual_secret == expected_secret

    def receive(self, raw_payload, request_headers):
        event_type = raw_payload.get('type')
        return self.normalize(event_type, raw_payload)

    def normalize(self, external_event_type, payload):
        # Maps hubspot events to canonical Horizon events
        mapped_event = 'external.lead_updated'
        
        email = payload.get('email')
        
        return {
            'event_name': mapped_event,
            'source': 'hubspot_demo',
            'external_id': payload.get('id'),
            'customer_identifier': email,
            'payload': payload
        }

    def send(self, action_payload, raw_event):
        # Demo send
        return {
            'status': 'success',
            'external_id': f"out_{raw_event.id}",
            'message': 'Demo HubSpot Send Successful'
        }
