import logging
from collections import Counter
from django.utils.timezone import now
from .models import Customer, UnifiedProfile

logger = logging.getLogger(__name__)


def build_unified_profile(customer):
    """
    Collects all distributed events, cross-device sessions, and
    omnichannel interactions into a single UnifiedProfile record.
    Merges them into one master record within the Level 3 Unified Database.
    """
    profile, created = UnifiedProfile.objects.get_or_create(
        customer=customer,
        defaults={'company': customer.company}
    )

    # Aggregate from RawEvents
    events = customer.raw_events.all()
    profile.total_events = events.count()
    profile.total_sessions = events.filter(event_name__contains='session').count()
    profile.total_page_views = events.filter(event_name__contains='page').count()

    # Timestamps
    first_event = events.order_by('created_at').first()
    last_event = events.order_by('-created_at').first()
    profile.first_seen_at = first_event.created_at if first_event else None
    profile.last_active_at = last_event.created_at if last_event else None

    # Channels from identity edges
    channels = set()
    if hasattr(customer, 'identity_edges'):
        for edge in customer.identity_edges.all():
            if edge.identity_type == 'device_id':
                channels.add('mobile')
            elif edge.identity_type == 'cookie_id':
                channels.add('web')
            elif edge.identity_type == 'email':
                channels.add('email')
            elif edge.identity_type == 'phone':
                channels.add('phone')
    if customer.primary_email:
        channels.add('email')
    if customer.primary_phone:
        channels.add('phone')
    profile.channels_active = list(channels)

    # Consent sync from Customer.consent
    consent = customer.consent or {}
    profile.marketing_consent = consent.get('marketing_consent', False)
    profile.analytics_consent = consent.get('analytics_consent', False)
    profile.consent_status = consent.get('status', 'unknown')

    profile.save()
    return profile


def build_all_unified_profiles(company):
    """
    Builds or refreshes unified profiles for all customers in a company.
    """
    customers = Customer.objects.filter(company=company)
    count = 0
    for customer in customers:
        try:
            build_unified_profile(customer)
            count += 1
        except Exception as e:
            logger.error(f"Error building unified profile for customer {customer.id}: {e}")
    return count
