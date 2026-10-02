import logging
from celery import shared_task
from django.utils import timezone
from .models import Campaign, CampaignRecipient, CampaignContent, CampaignPropensityScore
from .services import CampaignExecutionService
from .ai.propensity import PropensityScorer
from .ai.bandit import ThompsonSamplingBandit
from .ai.attribution import AttributionCalculator

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_campaign(self, campaign_id: int):
    """
    Main background task for executing an outbound campaign.
    Evaluates audience, snapshots target criteria, scores propensity,
    generates recipient batches, and dispatches delivery.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} does not exist.")
        return

    service = CampaignExecutionService()
    propensity_engine = PropensityScorer()

    # 1. Resolve audience from Universal Data Model
    audience = service.resolve_audience(campaign)
    campaign.estimated_audience = len(audience)
    campaign.status = 'sending'
    campaign.started_at = timezone.now()

    # Snapshot audience configuration
    segment_names = [cs.segment.name for cs in campaign.campaign_segments.select_related('segment').all()]
    campaign.audience_snapshot = {
        'total_resolved': len(audience),
        'segments': segment_names,
        'resolved_at': timezone.now().isoformat(),
        'channel': campaign.channel,
    }
    campaign.save()

    service.emit_campaign_lifecycle_event(campaign, 'campaign.sending', {'total_recipients': len(audience)})

    # 2. Get content variants
    contents = list(campaign.contents.all())
    if not contents:
        # Create a default variant if none exists
        default_variant = CampaignContent.objects.create(
            campaign=campaign,
            variant_name='Default',
            subject=f"Update regarding {campaign.name}",
            body_html=f"<p>Hello {{ customer.name }},</p><p>We have an exciting announcement for you.</p>",
            body_plain=f"Hello {{ customer.name }},\n\nWe have an exciting announcement for you.",
            message_text=f"Hello {{ customer.name }}, check out {campaign.name}!",
        )
        contents = [default_variant]

    # 3. Create recipients & score propensity
    recipient_ids = []
    propensity_sum = 0.0
    churn_count = 0

    for customer in audience:
        variant = service.assign_variant(campaign, contents)
        addr = customer.primary_email if campaign.channel == 'email' else customer.primary_phone or ''

        # Propensity scoring
        prop_score = 0.5
        is_churn = False
        opt_hour = None
        if campaign.ai_send_time_enabled:
            score_data = propensity_engine.score_customer(customer, campaign)
            prop_score = score_data['conversion_probability']
            is_churn = score_data.get('churn_risk', False)
            opt_hour = score_data.get('optimal_send_hour')

            CampaignPropensityScore.objects.update_or_create(
                campaign=campaign,
                customer=customer,
                defaults={
                    'company': campaign.company,
                    'conversion_probability': prop_score,
                    'churn_probability': score_data.get('churn_probability', 0.0),
                    'optimal_send_hour': opt_hour,
                    'model_version': score_data.get('model_version', 'v1'),
                    'features_snapshot': score_data.get('features_snapshot', {}),
                }
            )

        propensity_sum += prop_score
        if is_churn:
            churn_count += 1

        recip, _ = CampaignRecipient.objects.update_or_create(
            campaign=campaign,
            customer=customer,
            defaults={
                'company': campaign.company,
                'content_variant': variant,
                'channel_address': addr,
                'status': 'queued',
                'propensity_score': prop_score,
                'churn_risk': is_churn,
            }
        )
        recipient_ids.append(recip.id)

    if audience:
        campaign.avg_propensity_score = round(propensity_sum / len(audience), 3)
        campaign.churn_risk_count = churn_count
        campaign.save()

    # 4. Dispatch batches (e.g. 50 per batch)
    batch_size = 50
    for i in range(0, len(recipient_ids), batch_size):
        chunk = recipient_ids[i:i + batch_size]
        send_campaign_batch.delay(campaign_id, chunk)

    # 5. Mark campaign as active/completed when dispatch finishes
    if not recipient_ids:
        campaign.status = 'completed'
        campaign.completed_at = timezone.now()
        campaign.save()
        service.emit_campaign_lifecycle_event(campaign, 'campaign.completed')


@shared_task
def send_campaign_batch(campaign_id: int, recipient_ids: list):
    """
    Sends messages to a batch of recipients, rendering personalized content
    and tracking send & delivery status.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return

    service = CampaignExecutionService()
    recipients = CampaignRecipient.objects.filter(id__in=recipient_ids).select_related('customer', 'content_variant')

    for recipient in recipients:
        try:
            # 1. Render message
            if recipient.content_variant:
                rendered = service.render_content(recipient.content_variant, recipient.customer)

            # 2. Record Sent event
            service.record_recipient_event(campaign, recipient, 'sent')

            # 3. Simulate instant delivery (or handle through ESP connector)
            service.record_recipient_event(campaign, recipient, 'delivered')

        except Exception as e:
            logger.error(f"Error sending campaign {campaign_id} to recipient {recipient.id}: {e}")
            recipient.status = 'failed'
            recipient.error_message = str(e)
            recipient.save()

    # Check if all queued items for the campaign are processed
    pending_count = campaign.recipients.filter(status='queued').count()
    if pending_count == 0:
        campaign.status = 'active'
        campaign.completed_at = timezone.now()
        campaign.save()
        service.emit_campaign_lifecycle_event(campaign, 'campaign.completed')


@shared_task
def evaluate_bandit_winner(campaign_id: int):
    """
    Evaluates arm parameters for a campaign running the Contextual Multi-Armed Bandit.
    If a variant has demonstrated statistical dominance, assigns bandit_winner_content.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return

    if not campaign.bandit_enabled:
        return

    contents = list(campaign.contents.all())
    if len(contents) < 2:
        return

    # Check impressions threshold
    eligible = [c for c in contents if (c.impressions or 0) >= 30]
    if len(eligible) >= 2:
        best_variant = max(eligible, key=lambda c: (c.successes or 0) / max(1, c.impressions or 1))
        campaign.bandit_winner_content = best_variant
        campaign.save(update_fields=['bandit_winner_content'])
        logger.info(f"Bandit winner declared for campaign {campaign.id}: Variant {best_variant.variant_name}")


@shared_task
def recalculate_attribution(campaign_id: int):
    """
    Recalculates multi-touch attribution weights across all touchpoints for a campaign.
    """
    try:
        campaign = Campaign.objects.get(id=campaign_id)
    except Campaign.DoesNotExist:
        return

    touchpoints = list(campaign.touchpoints.all().order_by('occurred_at'))
    AttributionCalculator.calculate_attribution_weights(touchpoints, campaign.goal_value)
