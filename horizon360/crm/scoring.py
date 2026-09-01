import logging
from django.utils import timezone
from .models import Deal, Activity

logger = logging.getLogger(__name__)

def calculate_deal_health(deal: Deal, persist: bool = False) -> int:
    """
    Computes a deterministic health score (0-100) and stalled flag for a Deal
    based on activity recency, stage velocity, and expected close date.
    """
    if deal.stage == 'won':
        deal.health_score = 100
        deal.stalled = False
        if persist:
            deal.save(update_fields=['health_score', 'stalled'])
        return 100

    if deal.stage == 'lost':
        deal.health_score = 0
        deal.stalled = False
        if persist:
            deal.save(update_fields=['health_score', 'stalled'])
        return 0

    now = timezone.now()
    score = 100

    # 1. Activity Recency
    latest_activity = Activity.objects.filter(deal=deal).order_by('-performed_at').first()
    if latest_activity:
        days_since_activity = (now - latest_activity.performed_at).days
        if days_since_activity > 30:
            score -= 50
        elif days_since_activity > 14:
            score -= 25
    else:
        days_since_creation = (now - deal.created_at).days if deal.created_at else 0
        if days_since_creation > 7:
            score -= 20

    # 2. Expected Close Date Overdue
    if deal.expected_close_date and deal.expected_close_date < now.date():
        days_overdue = (now.date() - deal.expected_close_date).days
        if days_overdue > 14:
            score -= 35
        else:
            score -= 20

    # 3. Stage Velocity Stagnation
    days_in_stage = (now - deal.updated_at).days if deal.updated_at else 0
    if deal.stage == 'lead' and days_in_stage > 14:
        score -= 20
    elif deal.stage == 'proposal' and days_in_stage > 30:
        score -= 15
    elif deal.stage == 'negotiation' and days_in_stage > 45:
        score -= 20

    final_score = max(0, min(100, score))
    deal.health_score = final_score
    deal.stalled = final_score < 50

    if persist:
        deal.save(update_fields=['health_score', 'stalled'])

    return final_score
