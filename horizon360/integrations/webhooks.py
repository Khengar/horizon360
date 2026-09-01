import json
import hmac
import hashlib
import logging
from typing import List, Optional
from django.core.serializers.json import DjangoJSONEncoder
import urllib.request
import urllib.error
from .models import WebhookSubscription, WebhookDeliveryLog

logger = logging.getLogger(__name__)

def generate_signature(payload_json: str, secret: str) -> str:
    """
    Computes an HMAC-SHA256 signature for payload verification.
    """
    digest = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={digest}"


def send_single_webhook(subscription: WebhookSubscription, event_name: str, payload: dict, timeout: int = 5) -> WebhookDeliveryLog:
    """
    Sends a signed JSON HTTP POST request to a webhook subscription and logs the attempt.
    """
    payload_str = json.dumps(payload, cls=DjangoJSONEncoder)
    signature = generate_signature(payload_str, subscription.secret)

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Horizon360-Webhook/1.0',
        'X-Horizon-Event': event_name,
        'X-Horizon-Signature': signature,
    }

    req = urllib.request.Request(
        subscription.target_url,
        data=payload_str.encode('utf-8'),
        headers=headers,
        method='POST'
    )

    response_status = None
    response_body = ""
    success = False

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_status = response.getcode()
            response_body = response.read().decode('utf-8', errors='ignore')[:1000]
            success = 200 <= response_status < 300
    except urllib.error.HTTPError as e:
        response_status = e.code
        response_body = e.read().decode('utf-8', errors='ignore')[:1000]
        success = False
    except Exception as e:
        response_status = 599  # Connection / Network error
        response_body = str(e)[:1000]
        success = False

    log = WebhookDeliveryLog.objects.create(
        subscription=subscription,
        event_name=event_name,
        payload=payload,
        response_status=response_status,
        response_body=response_body,
        success=success
    )
    return log


def dispatch_webhook(company, event_name: str, payload: dict, timeout: int = 5) -> List[WebhookDeliveryLog]:
    """
    Dispatches an event to all active matching webhook subscriptions for the company.
    """
    subscriptions = WebhookSubscription.objects.filter(company=company, is_active=True)
    logs = []

    for sub in subscriptions:
        events = sub.subscribed_events or []
        if '*' in events or event_name in events:
            try:
                log = send_single_webhook(sub, event_name, payload, timeout=timeout)
                logs.append(log)
            except Exception as e:
                logger.error(f"Error dispatching webhook to {sub.target_url}: {e}")

    return logs
