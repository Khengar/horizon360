from .stripe import StripeDemoConnector
from .hubspot import HubSpotDemoConnector

def get_connector(integration):
    if integration.provider == 'stripe_demo':
        return StripeDemoConnector(integration)
    elif integration.provider == 'hubspot_demo':
        return HubSpotDemoConnector(integration)
    raise ValueError(f"Unknown provider: {integration.provider}")
