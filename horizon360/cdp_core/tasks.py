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

    if raw_event.processed:
        logger.info(f"RawEvent {raw_event_id} is already processed. Skipping.")
        return True

    # Normalization step on the event_name
    normalized_name = raw_event.event_name.strip().lower()
    raw_event.event_name = normalized_name
    
    payload = raw_event.raw_payload or {}
    # Treat traits as a dictionary, default to empty if not present
    traits = payload.get('traits')
    if not isinstance(traits, dict):
        traits = {}
    
    # 1. Extract and normalize identity keys (from root or traits)
    from .identity import normalize_email, normalize_phone
    raw_email = payload.get('email') or traits.get('email')
    raw_phone = payload.get('phone') or traits.get('phone')
    email = normalize_email(raw_email)
    phone = normalize_phone(raw_phone)
    
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

    customer = raw_event.customer
    if not customer and (email or phone):
        # 2. Query for match scoped to company
        query = Q(company=raw_event.company)
        identity_q = Q()
        if email:
            identity_q |= Q(primary_email=email)
        if phone:
            identity_q |= Q(primary_phone=phone)
            
        customer = Customer.objects.filter(query & identity_q).first()
        
        # 3. Create if no match exists
        if not customer:
            customer = Customer.objects.create(
                company=raw_event.company,
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
        
        # Minimal Workflow Execution
        if normalized_name in ['order.completed', 'shopez.checkout.completed']:
            from crm.models import Contact, Deal
            # Automatically create a Contact if none exists so we can map the Deal
            contact = Contact.objects.filter(customer=customer).first()
            if not contact:
                contact = Contact.objects.create(
                    company=raw_event.company,
                    customer=customer,
                    email=email,
                    first_name=traits.get('firstName', payload.get('firstName', 'ShopEZ Customer'))
                )
            
            amount = payload.get('amount') or payload.get('totalAmount', 0.0)
            Deal.objects.create(
                company=raw_event.company,
                contact=contact,
                customer=customer,
                title=f"ShopEZ Online Order: {payload.get('orderId', 'New')}",
                stage='won',
                value=amount
            )
    
    # Mark as processed and save
    raw_event.processed = True
    raw_event.save()
    
    # 5. Execute Workflows
    from .workflow_service import execute_workflows
    execute_workflows(raw_event)
    
    # 6. Stream event to Outbound Webhooks
    try:
        from integrations.webhooks import dispatch_webhook
        dispatch_webhook(
            company=raw_event.company,
            event_name=normalized_name,
            payload={
                "event_name": normalized_name,
                "event_id": raw_event.id,
                "customer_id": str(customer.id) if customer else None,
                "payload": payload,
                "timestamp": raw_event.created_at.isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error triggering webhooks for event {raw_event_id}: {e}")

    logger.info(f"Successfully processed RawEvent {raw_event_id} (normalized to: {normalized_name})")
    return True

