import logging
from typing import List, Dict, Any, Optional
from .models import Customer, Segment

logger = logging.getLogger(__name__)

def extract_field_value(customer: Customer, field_path: str) -> Any:
    """
    Extracts nested values from a Customer instance.
    Examples:
    - 'attributes.tier' -> customer.attributes.get('tier')
    - 'consent.marketing' -> customer.consent.get('marketing')
    - 'primary_email' -> customer.primary_email
    - 'primary_phone' -> customer.primary_phone
    - 'account_name' -> customer.account.name if customer.account else None
    - 'timeline.event_name' -> boolean (True if event exists in timeline)
    - 'aggregates.won_revenue' -> computes sum of won deals
    - 'aggregates.total_deals' -> computes deal count
    """
    if not field_path:
        return None

    field_path = field_path.strip()

    # Timeline event check
    if field_path.startswith('timeline.'):
        target_event = field_path.split('timeline.', 1)[1]
        timeline = customer.timeline or []
        for ev in timeline:
            if isinstance(ev, dict) and ev.get('event_name') == target_event:
                return True
        return False

    # Financial / deal aggregates check
    if field_path.startswith('aggregates.'):
        agg_key = field_path.split('aggregates.', 1)[1]
        deals = list(customer.deals.all())
        if agg_key == 'won_revenue':
            return sum((float(d.value) for d in deals if d.stage == 'won'), 0.0)
        elif agg_key == 'open_pipeline_value':
            return sum((float(d.value) for d in deals if d.stage not in ['won', 'lost']), 0.0)
        elif agg_key == 'total_deals':
            return len(deals)
        elif agg_key == 'won_deals':
            return len([d for d in deals if d.stage == 'won'])

    # Attributes check
    if field_path.startswith('attributes.'):
        attr_key = field_path.split('attributes.', 1)[1]
        attrs = customer.attributes or {}
        return attrs.get(attr_key)

    # Consent check
    if field_path.startswith('consent.'):
        consent_key = field_path.split('consent.', 1)[1]
        consent = customer.consent or {}
        return consent.get(consent_key)

    # Account properties
    if field_path == 'account_name':
        return customer.account.name if customer.account else None
    if field_path == 'account_tier':
        return customer.account.tier if customer.account else None

    # Direct model fields
    return getattr(customer, field_path, None)


def evaluate_rule(customer: Customer, rule: Dict[str, Any]) -> bool:
    """
    Evaluates a single rule dictionary against a Customer.
    Example rule: {"field": "attributes.tier", "operator": "==", "value": "enterprise"}
    """
    field = rule.get('field')
    op = rule.get('operator', '==')
    target_val = rule.get('value')

    actual_val = extract_field_value(customer, field)

    if op == 'exists':
        return actual_val is not None and actual_val != ''
    if op == 'is_null':
        return actual_val is None or actual_val == ''

    if actual_val is None:
        return False

    try:
        if op == '==':
            return str(actual_val).lower() == str(target_val).lower()
        elif op == '!=':
            return str(actual_val).lower() != str(target_val).lower()
        elif op == '>=':
            return float(actual_val) >= float(target_val)
        elif op == '<=':
            return float(actual_val) <= float(target_val)
        elif op == '>':
            return float(actual_val) > float(target_val)
        elif op == '<':
            return float(actual_val) < float(target_val)
        elif op == 'contains':
            return str(target_val).lower() in str(actual_val).lower()
        elif op == 'in':
            if isinstance(target_val, list):
                return str(actual_val).lower() in [str(x).lower() for x in target_val]
            return str(actual_val).lower() in str(target_val).lower()
        elif op == 'starts_with':
            return str(actual_val).lower().startswith(str(target_val).lower())
    except (ValueError, TypeError) as e:
        logger.debug(f"Rule evaluation type error: {e}")
        return False

    return False


def evaluate_customer_for_segment(customer: Customer, rules: List[Dict[str, Any]]) -> bool:
    """
    Evaluates whether a customer satisfies all rules in a segment (AND logic).
    """
    if not rules:
        return True
    for rule in rules:
        if not evaluate_rule(customer, rule):
            return False
    return True


def get_segment_audience(segment: Segment, limit: Optional[int] = None) -> List[Customer]:
    """
    Returns the list of customers that match the segment's dynamic rules.
    """
    base_qs = Customer.objects.filter(company=segment.company).select_related('account').prefetch_related('deals', 'raw_events')
    matching_customers = []
    rules = segment.rules or []

    for customer in base_qs:
        if evaluate_customer_for_segment(customer, rules):
            matching_customers.append(customer)
            if limit and len(matching_customers) >= limit:
                break

    return matching_customers
