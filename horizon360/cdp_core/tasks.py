from celery import shared_task
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

@shared_task
def process_event_task(raw_event_id):
    """
    Asynchronously processes a raw event: normalizes event_name, 
    resolves identity, updates customer profile, and marks as processed.
    """
    from .models import RawEvent, Customer
    try:
        raw_event = RawEvent.objects.get(id=raw_event_id)
    except RawEvent.DoesNotExist:
        logger.error(f"RawEvent with id {raw_event_id} does not exist.")
        return False

    # Normalization step on the event_name
    normalized_name = raw_event.event_name.strip().lower()
    raw_event.event_name = normalized_name
    
    payload = raw_event.raw_payload or {}
    # Treat traits as a dictionary, default to empty if not present
    traits = payload.get('traits')
    if not isinstance(traits, dict):
        traits = {}
    
    # 1. Extract identity keys (from root or traits)
    email = payload.get('email') or traits.get('email')
    phone = payload.get('phone') or traits.get('phone')
    
    # Extract non-identity properties (exclude email/phone, traits container, and consent)
    consent = payload.get('consent', {})
    if not isinstance(consent, dict):
        consent = {}

    properties_to_merge = {}
    for key, value in payload.items():
        if key not in ['email', 'phone', 'traits', 'consent']:
            properties_to_merge[key] = value
    for key, value in traits.items():
        if key not in ['email', 'phone']:
            properties_to_merge[key] = value

    customer = None
    if email or phone:
        # 2. Query for exact match
        query = Q()
        if email:
            query |= Q(primary_email=email)
        if phone:
            query |= Q(primary_phone=phone)
            
        # For simplicity, we just pick the first match (if duplicates existed somehow)
        customer = Customer.objects.filter(query).first()
        
        # 3. Create if no match exists
        if not customer:
            customer = Customer.objects.create(
                primary_email=email,
                primary_phone=phone
            )
            
    if customer:
        # Link RawEvent to Customer
        raw_event.customer = customer
        
        # 4. Profile Construction
        # Append to chronological timeline
        event_summary = {
            'event_name': normalized_name,
            'received_at': raw_event.created_at.isoformat(),
            'payload': payload
        }
        
        if not isinstance(customer.timeline, list):
            customer.timeline = []
        customer.timeline.append(event_summary)
        
        # Merge attributes (standard dict update to keep latest state)
        if not isinstance(customer.attributes, dict):
            customer.attributes = {}
        customer.attributes.update(properties_to_merge)
        
        # Merge consent flags
        if not isinstance(customer.consent, dict):
            customer.consent = {}
        if consent:
            customer.consent.update(consent)
        
        # Save updated Customer
        customer.save()
    
    # Mark as processed and save
    raw_event.processed = True
    raw_event.save()
    
    logger.info(f"Successfully processed RawEvent {raw_event_id} (normalized to: {normalized_name})")
    return True
