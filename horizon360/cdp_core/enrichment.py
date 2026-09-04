import logging
from collections import Counter
from django.utils.timezone import now
from .models import UnifiedProfile

logger = logging.getLogger(__name__)


def compute_engagement_score(profile):
    """
    Computes engagement score (0-100) based on:
    - Recency: days since last activity
    - Frequency: events per week
    - Depth: pages per session, event diversity
    - Monetary: total deal value
    """
    score = 0.0
    if profile.last_active_at:
        recency_days = (now() - profile.last_active_at).days
    else:
        recency_days = 999

    # Recency component (0-30 points)
    if recency_days <= 1:
        score += 30
    elif recency_days <= 7:
        score += 25
    elif recency_days <= 30:
        score += 15
    elif recency_days <= 90:
        score += 5

    # Frequency component (0-30 points)
    weeks = max(recency_days / 7, 1)
    events_per_week = profile.total_events / weeks
    score += min(events_per_week * 5, 30)

    # Depth component (0-20 points)
    score += min(profile.total_page_views * 0.5, 20)

    # Monetary component (0-20 points)
    try:
        deals = profile.customer.deals.filter(stage='won')
        total_value = sum(float(d.value) for d in deals)
        if total_value >= 10000:
            score += 20
        elif total_value >= 5000:
            score += 15
        elif total_value >= 1000:
            score += 10
        elif total_value > 0:
            score += 5
    except Exception:
        pass

    return min(score, 100)


def determine_lifecycle_stage(profile):
    """Determines lifecycle stage based on profile state."""
    customer = profile.customer
    if not customer.primary_email and not customer.primary_phone:
        return 'anonymous'
    if profile.total_events == 0:
        return 'known'
    try:
        has_won_deals = customer.deals.filter(stage='won').exists()
    except Exception:
        has_won_deals = False
    if profile.engagement_score >= 70:
        if has_won_deals:
            return 'customer'
        return 'qualified'
    if profile.engagement_score >= 40:
        return 'engaged'
    return 'known'


def determine_engagement_tier(score):
    """Maps engagement score to tier."""
    if score >= 80:
        return 'on_fire'
    if score >= 50:
        return 'hot'
    if score >= 25:
        return 'warm'
    return 'cold'


def compute_primary_interest(profile):
    """Determines primary interest category from most frequent event domain."""
    events = profile.customer.raw_events.values_list('event_name', flat=True)
    if events:
        categories = [e.split('.')[0] for e in events if '.' in e]
        if categories:
            most_common = Counter(categories).most_common(1)
            if most_common:
                return most_common[0][0]
    return ''


def enrich_firmographic(profile):
    """
    Syncs third-party firmographic/demographic data to the profile.
    Extracts from recent event payloads (IP geolocation, company domain).
    """
    customer = profile.customer
    recent_events = customer.raw_events.order_by('-created_at')[:5]
    for event in recent_events:
        payload = event.raw_payload or {}
        ip = payload.get('ip_address') or payload.get('ip')
        if ip:
            profile.location_city = payload.get('city', profile.location_city or '')
            profile.location_country = payload.get('country', profile.location_country or '')
            break

    # Domain-based company enrichment
    if customer.primary_email and '@' in customer.primary_email:
        domain = customer.primary_email.split('@')[1]
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']
        if domain not in free_domains:
            profile.enrichment_source = f"domain:{domain}"

    profile.save()


def enrich_profile(profile):
    """
    Master enrichment function: computes all derived metrics,
    sets lifecycle stage and engagement tier, syncs firmographic data.
    """
    profile.engagement_score = compute_engagement_score(profile)
    profile.lifecycle_stage = determine_lifecycle_stage(profile)
    profile.engagement_tier = determine_engagement_tier(profile.engagement_score)
    profile.primary_interest_category = compute_primary_interest(profile)
    profile.enriched_at = now()
    profile.save()

    # Firmographic enrichment
    enrich_firmographic(profile)

    return profile


def enrich_all_profiles(company):
    """
    Enriches all unified profiles for a company.
    """
    profiles = UnifiedProfile.objects.filter(company=company).select_related('customer')
    count = 0
    for profile in profiles:
        try:
            enrich_profile(profile)
            count += 1
        except Exception as e:
            logger.error(f"Error enriching profile {profile.id}: {e}")
    return count
