import json
import logging
from typing import List, Dict, Any, Tuple
from intelligence.llm_client import LLMClient
from cdp_core.segmentation import evaluate_customer_for_segment
from cdp_core.models import Customer, Segment, Company

logger = logging.getLogger(__name__)

class AutonomousAudienceAgent:
    """
    Autonomous Audience Segmentation Agent.
    Evaluates multi-touchpoint behavioral history and transactions across the UDM
    to dynamically build high-affinity lookalike cohorts and recommend segment predicates.
    """

    def __init__(self, llm_client: Any = None):
        self.llm = llm_client or LLMClient()

    def generate_lookalike_rules(
        self,
        company: Company,
        campaign_name: str,
        channel: str,
        goal_description: str = "Maximize conversion"
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Reasons over historical customer successes and outputs executable Segment rules.
        """
        # 1. Profile high-converting customers for grounding
        high_value_customers = Customer.objects.filter(
            company=company,
            deals__stage='won'
        ).distinct()[:10]

        summary_sample = []
        for c in high_value_customers:
            profile = getattr(c, 'unified_profile', None)
            summary_sample.append({
                'account_tier': getattr(c.account, 'tier', 'standard') if c.account else 'standard',
                'engagement_score': getattr(profile, 'engagement_score', 0) if profile else 0,
                'engagement_tier': getattr(profile, 'engagement_tier', 'cold') if profile else 'cold',
                'timeline_length': len(c.timeline or []),
            })

        system_prompt = (
            "You are an expert AI Audience Segmentation Architect for Horizon360 CDP. "
            "You formulate dynamic rule sets to identify high-affinity cohorts. "
            "Available rule fields: 'account_tier', 'consent.marketing', 'attributes.tier', "
            "'aggregates.won_revenue', 'aggregates.total_deals', 'primary_email'. "
            "Available operators: '==', '!=', '>=', '<=', 'contains', 'exists'. "
            "Return valid JSON containing: 'rationale' (string) and 'rules' (array of rule objects)."
        )

        user_prompt = (
            f"Campaign: '{campaign_name}' via channel '{channel}'. Goal: {goal_description}.\n"
            f"Grounding profiles of existing high-value customers: {json.dumps(summary_sample)}\n"
            "Generate 2-3 precise segment rules to target the highest-affinity prospective audience. "
            "Ensure 'consent.marketing' == 'true' is recommended if applicable."
        )

        response = self.llm.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        content = response.get('content', '')
        rules, rationale = self._parse_llm_rules(content)
        if not rules:
            rules, rationale = self._default_rules(channel)

        return rules, rationale

    def _parse_llm_rules(self, content: str) -> Tuple[List[Dict[str, Any]], str]:
        try:
            # Look for JSON block
            if '```json' in content:
                json_str = content.split('```json', 1)[1].split('```', 1)[0].strip()
            elif '```' in content:
                json_str = content.split('```', 1)[1].split('```', 1)[0].strip()
            else:
                json_str = content.strip()

            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and 'rules' in parsed:
                rules = parsed['rules']
                rationale = parsed.get('rationale', 'Autonomous cohort built from high-affinity interactions.')
                # Validate rule format
                valid_rules = [
                    r for r in rules
                    if isinstance(r, dict) and 'field' in r and 'operator' in r and 'value' in r
                ]
                if valid_rules:
                    return valid_rules, rationale
        except Exception as e:
            logger.debug(f"Failed to parse LLM audience rules: {e}")

        return [], ""

    def _default_rules(self, channel: str) -> Tuple[List[Dict[str, Any]], str]:
        rules = [
            {"field": "consent.marketing", "operator": "==", "value": "true"},
            {"field": "aggregates.won_revenue", "operator": ">=", "value": "0"},
        ]
        rationale = (
            f"Rule-based deterministic affinity cohort optimized for {channel}. "
            "Filters for active marketing consent and customer transaction readiness."
        )
        return rules, rationale

    def estimate_audience_size(self, company: Company, rules: List[Dict[str, Any]]) -> int:
        """
        Runs candidate rules across company's customer base to return estimated audience count.
        """
        customers = Customer.objects.filter(company=company).select_related('account').prefetch_related('deals')
        match_count = 0
        for customer in customers:
            if evaluate_customer_for_segment(customer, rules):
                match_count += 1
        return match_count
