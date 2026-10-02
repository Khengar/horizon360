import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Campaign, CampaignRecipient
from .services import CampaignExecutionService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def campaign_event_webhook(request):
    """
    Inbound webhook callback receiver for ESP / SMS delivery and engagement events.
    Supports standard event payloads:
    {
        "campaign_id": 1,
        "recipient_id": 123,
        "customer_id": "uuid-...",
        "event_type": "opened" | "clicked" | "converted" | "bounced" | "unsubscribed",
        "metadata": { "link_url": "...", "user_agent": "..." },
        "revenue": 150.00
    }
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception as e:
        return JsonResponse({"error": f"Invalid JSON payload: {e}"}, status=400)

    campaign_id = body.get('campaign_id')
    recipient_id = body.get('recipient_id')
    customer_id = body.get('customer_id')
    event_type = body.get('event_type')
    metadata = body.get('metadata', {})
    revenue = Decimal(str(body.get('revenue', 0.0)))

    if not event_type:
        return JsonResponse({"error": "event_type is required"}, status=400)

    recipient = None
    if recipient_id:
        recipient = CampaignRecipient.objects.filter(id=recipient_id).select_related('campaign', 'customer').first()
    elif campaign_id and customer_id:
        recipient = CampaignRecipient.objects.filter(
            campaign_id=campaign_id,
            customer_id=customer_id
        ).select_related('campaign', 'customer').first()

    if not recipient:
        return JsonResponse({"error": "CampaignRecipient not found"}, status=404)

    service = CampaignExecutionService()
    try:
        event = service.record_recipient_event(
            campaign=recipient.campaign,
            recipient=recipient,
            event_type=event_type,
            metadata=metadata,
            revenue=revenue
        )
        return JsonResponse({
            "status": "success",
            "event_id": event.id,
            "campaign_id": recipient.campaign_id,
            "event_type": event_type,
            "recipient_status": recipient.status
        }, status=200)
    except Exception as e:
        logger.error(f"Error processing campaign webhook: {e}")
        return JsonResponse({"error": str(e)}, status=500)
