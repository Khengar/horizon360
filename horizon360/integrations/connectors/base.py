class BaseConnector:
    def __init__(self, integration):
        self.integration = integration
        self.company = integration.company
        self.config = integration.config

    def authenticate(self, request_headers=None, request_payload=None):
        """Validate inbound request."""
        raise NotImplementedError

    def health_check(self):
        """Check outbound credentials/connectivity."""
        raise NotImplementedError

    def receive(self, raw_payload, request_headers):
        """Process inbound data and normalize it for Horizon."""
        raise NotImplementedError

    def send(self, action_payload, raw_event):
        """Process outbound data to external system."""
        raise NotImplementedError

    def normalize(self, external_event_type, payload):
        """Convert external event to canonical event dictionary."""
        raise NotImplementedError
