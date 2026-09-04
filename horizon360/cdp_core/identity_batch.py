import logging
from difflib import SequenceMatcher
from celery import shared_task
from django.db.models import Q, Count
from django.utils.timezone import now
from .models import Customer, IdentityEdge, MergeSuggestion, Company
from .identity import merge_customers
from .audit import record_audit_log

logger = logging.getLogger(__name__)


def string_similarity(a, b):
    """Compute normalized string similarity using SequenceMatcher (0.0 - 1.0)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, str(a).lower().strip(), str(b).lower().strip()).ratio()


def email_domain_match(email_a, email_b):
    """Check if two emails share the same non-free domain."""
    free_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com'}
    if not email_a or not email_b or '@' not in email_a or '@' not in email_b:
        return 0.0
    domain_a = email_a.split('@')[1].lower()
    domain_b = email_b.split('@')[1].lower()
    if domain_a in free_domains or domain_b in free_domains:
        return 0.0
    return 1.0 if domain_a == domain_b else 0.0


def phone_similarity(phone_a, phone_b):
    """Compare phone numbers by last N digits."""
    import re
    if not phone_a or not phone_b:
        return 0.0
    digits_a = re.sub(r'\D', '', str(phone_a))
    digits_b = re.sub(r'\D', '', str(phone_b))
    if len(digits_a) < 5 or len(digits_b) < 5:
        return 0.0
    # Compare last 10 digits
    tail_a = digits_a[-10:]
    tail_b = digits_b[-10:]
    if tail_a == tail_b:
        return 1.0
    # Partial tail match
    if tail_a[-7:] == tail_b[-7:]:
        return 0.85
    return 0.0


import os
import pickle
import numpy as np

# Global cache for the loaded ML model
ML_MODEL = None
MODEL_LOADED = False

def get_ml_model():
    global ML_MODEL, MODEL_LOADED
    if not MODEL_LOADED:
        model_path = os.path.join(os.path.dirname(__file__), "ml_identity_model.pkl")
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    ML_MODEL = pickle.load(f)
                logger.info("Successfully loaded ml_identity_model.pkl")
            except Exception as e:
                logger.error(f"Failed to load ML identity model: {e}")
        MODEL_LOADED = True
    return ML_MODEL


def compute_match_score(customer_a, customer_b):
    """
    Computes a composite match score between two customers.
    If the ML model is trained and available, it uses the model's predict_proba for class 1.
    Otherwise, it falls back to a deterministic heuristic composite score.
    Returns (score, match_reasons) where score is 0.0 - 1.0.
    """
    reasons = []
    
    # 1. Feature Extraction
    name_a = (customer_a.attributes or {}).get('name', '') or (customer_a.attributes or {}).get('firstName', '')
    name_b = (customer_b.attributes or {}).get('name', '') or (customer_b.attributes or {}).get('firstName', '')
    name_sim = string_similarity(name_a, name_b)
    
    email_local_a = customer_a.primary_email.split('@')[0] if customer_a.primary_email and '@' in customer_a.primary_email else ''
    email_local_b = customer_b.primary_email.split('@')[0] if customer_b.primary_email and '@' in customer_b.primary_email else ''
    email_local_sim = string_similarity(email_local_a, email_local_b)
    
    domain_score = email_domain_match(customer_a.primary_email, customer_b.primary_email)
    
    ph1 = customer_a.primary_phone[-7:] if customer_a.primary_phone else ""
    ph2 = customer_b.primary_phone[-7:] if customer_b.primary_phone else ""
    if ph1 and ph2 and ph1 == ph2:
        phone_sim = 1.0
    else:
        # Must perfectly match train_identity_ml.py feature computation
        phone_sim = string_similarity(customer_a.primary_phone, customer_b.primary_phone)

    # 2. Compile Match Reasons for Dashboard
    if name_sim > 0.7:
        reasons.append({'field': 'name', 'score': round(name_sim, 3)})
    if email_local_sim > 0.6:
        reasons.append({'field': 'email_local', 'score': round(email_local_sim, 3)})
    if domain_score > 0:
        reasons.append({'field': 'email_domain', 'score': domain_score})
    if phone_sim > 0.7:
        reasons.append({'field': 'phone', 'score': round(phone_sim, 3)})

    # 3. ML Model Prediction (if available)
    model = get_ml_model()
    if model is not None:
        features = np.array([[name_sim, email_local_sim, domain_score, phone_sim]])
        # Get probability of class 1 (match)
        proba = model.predict_proba(features)[0]
        if len(proba) > 1:
            ml_score = proba[1]
        else:
            ml_score = float(model.predict(features)[0])
        return round(ml_score, 4), reasons

    # 4. Fallback Heuristics (if no model trained yet)
    weights = []
    if name_sim > 0.7: weights.append(name_sim * 0.20)
    if email_local_sim > 0.6: weights.append(email_local_sim * 0.35)
    if domain_score > 0: weights.append(domain_score * 0.15)
    if phone_sim > 0: weights.append(phone_sim * 0.30)

    if not weights:
        return 0.0, []

    composite_score = min(sum(weights) / max(sum(w for w in [0.35, 0.15, 0.30, 0.20] if w > 0), 0.01), 1.0)
    return round(composite_score, 4), reasons


def find_merge_candidates(company, limit=500):
    """
    Finds potential duplicate customer pairs within a company.
    Uses blocking strategy: groups by email domain or phone prefix.
    """
    candidates = []
    customers = list(
        Customer.objects.filter(company=company)
        .exclude(primary_email__isnull=True, primary_phone__isnull=True)
        .order_by('created_at')[:limit]
    )

    # Block by email domain
    domain_blocks = {}
    for c in customers:
        if c.primary_email and '@' in c.primary_email:
            domain = c.primary_email.split('@')[1].lower()
            free_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com'}
            if domain not in free_domains:
                domain_blocks.setdefault(domain, []).append(c)

    for domain, block_customers in domain_blocks.items():
        if len(block_customers) < 2 or len(block_customers) > 50:  # Hub suppression
            continue
        for i in range(len(block_customers)):
            for j in range(i + 1, len(block_customers)):
                score, reasons = compute_match_score(block_customers[i], block_customers[j])
                if score >= 0.70:
                    candidates.append((block_customers[i], block_customers[j], score, reasons))

    return candidates


@shared_task
def run_batch_identity_resolution(company_id=None):
    """
    Scheduled batch pipeline for identity resolution.
    Runs nightly or hourly via Celery Beat.
    
    Confidence thresholds:
    - >= 0.95: Auto-merge, re-point FKs, create AuditLog
    - 0.70-0.94: Create MergeSuggestion with 'pending' status
    - < 0.70: Keep separate
    """
    if company_id:
        companies = Company.objects.filter(id=company_id)
    else:
        companies = Company.objects.filter(is_active=True)

    total_auto_merged = 0
    total_suggested = 0

    for company in companies:
        try:
            candidates = find_merge_candidates(company)

            for primary, secondary, score, reasons in candidates:
                # Skip if already suggested or merged
                existing = MergeSuggestion.objects.filter(
                    Q(primary_customer=primary, secondary_customer=secondary) |
                    Q(primary_customer=secondary, secondary_customer=primary)
                ).exists()
                if existing:
                    continue

                if score >= 0.95:
                    # Auto-merge with confidence >= 95%
                    try:
                        merge_customers(primary, secondary)
                        MergeSuggestion.objects.create(
                            company=company,
                            primary_customer=primary,
                            secondary_customer=primary,  # secondary is deleted after merge
                            confidence_score=score,
                            match_reasons=reasons,
                            status='auto_merged',
                            reviewed_at=now()
                        )
                        total_auto_merged += 1
                        logger.info(f"Auto-merged customers {primary.id} <- {secondary.id} (score: {score})")
                    except Exception as e:
                        logger.error(f"Auto-merge failed for {primary.id} <- {secondary.id}: {e}")

                elif score >= 0.70:
                    # Flag for review (70-94%)
                    MergeSuggestion.objects.create(
                        company=company,
                        primary_customer=primary,
                        secondary_customer=secondary,
                        confidence_score=score,
                        match_reasons=reasons,
                        status='pending'
                    )
                    total_suggested += 1
                    logger.info(f"Created merge suggestion for {primary.id} <- {secondary.id} (score: {score})")

        except Exception as e:
            logger.error(f"Batch identity resolution failed for company {company.id}: {e}")

    logger.info(f"Batch identity resolution complete. Auto-merged: {total_auto_merged}, Suggested: {total_suggested}")
    return {'auto_merged': total_auto_merged, 'suggested': total_suggested}
