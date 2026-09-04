from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_deal_won_orchestration(deal_id):
    """
    Celery task that triggers cross-BIOM orchestration when a Deal is won.
    Called asynchronously from Deal.save() when the stage transitions to 'won'.
    """
    from crm.orchestration import orchestrate_deal_won

    logger.info(f"Starting deal-won orchestration for Deal {deal_id}")
    try:
        result = orchestrate_deal_won(deal_id)
        logger.info(f"Orchestration result for Deal {deal_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Orchestration failed for Deal {deal_id}: {exc}", exc_info=True)
        raise
