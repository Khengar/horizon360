import logging
from celery import shared_task
from .models import Company
from .unification import build_all_unified_profiles
from .enrichment import enrich_all_profiles

logger = logging.getLogger(__name__)


@shared_task
def enrich_all_company_profiles(company_id=None):
    """
    Periodic task: builds unified profiles and enriches them.
    Runs on Celery Beat schedule (e.g., every 2 hours).
    """
    if company_id:
        companies = Company.objects.filter(id=company_id)
    else:
        companies = Company.objects.filter(is_active=True)

    total_unified = 0
    total_enriched = 0

    for company in companies:
        try:
            unified = build_all_unified_profiles(company)
            total_unified += unified
            enriched = enrich_all_profiles(company)
            total_enriched += enriched
        except Exception as e:
            logger.error(f"Enrichment failed for company {company.id}: {e}")

    logger.info(f"Enrichment sweep complete. Unified: {total_unified}, Enriched: {total_enriched}")
    return {'unified': total_unified, 'enriched': total_enriched}

@shared_task
def update_single_profile_task(customer_id):
    """
    Real-time task: incrementally updates unification and enrichment for a single customer.
    Triggered by process_event_task immediately after an event is attached.
    """
    from .models import Customer
    from .unification import build_unified_profile
    from .enrichment import enrich_profile
    
    try:
        customer = Customer.objects.get(id=customer_id)
        profile = build_unified_profile(customer)
        enrich_profile(profile)
        logger.info(f"Real-time unification and enrichment complete for Customer {customer_id}")
    except Customer.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Real-time profile update failed for Customer {customer_id}: {e}")
