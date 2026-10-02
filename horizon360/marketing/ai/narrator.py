import json
import logging
from typing import Dict, Any, Optional
from intelligence.llm_client import LLMClient
from intelligence.models import Insight
from .attribution import AttributionCalculator

logger = logging.getLogger(__name__)

class AttributionNarrator:
    """
    Equips the Marketing Agent with reasoning loops to analyze multi-touch attribution data,
    evaluate spend-to-revenue efficiency, and narrate strategic executive briefings.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_briefing(self, campaign: Any) -> Dict[str, Any]:
        """
        Synthesizes campaign metrics and attribution breakdowns into a narrative briefing.
        """
        company = campaign.company
        channel_data = AttributionCalculator.get_campaign_channel_breakdown(campaign)

        budget_val = float(campaign.budget or 0)
        sent_val = campaign.total_sent or 0
        delivered_val = campaign.total_delivered or 0
        opened_val = campaign.total_opened or 0
        clicked_val = campaign.total_clicked or 0
        converted_val = campaign.total_converted or 0

        # Calculate actual spend and ROI from CampaignTransaction
        spend_txs = campaign.transactions.filter(transaction_type='spend')
        roi_txs = campaign.transactions.filter(transaction_type='roi')
        total_spend = sum(float(t.amount) for t in spend_txs) or budget_val
        total_roi = sum(float(t.amount) for t in roi_txs) or float(campaign.goal_value or 0)

        roi_percent = round(((total_roi - total_spend) / total_spend * 100), 1) if total_spend > 0 else 0.0

        stats_summary = {
            'campaign_name': campaign.name,
            'channel': campaign.channel,
            'status': campaign.status,
            'total_sent': sent_val,
            'open_rate': round((opened_val / delivered_val * 100), 1) if delivered_val > 0 else 0.0,
            'click_rate': round((clicked_val / delivered_val * 100), 1) if delivered_val > 0 else 0.0,
            'conversion_rate': round((converted_val / max(sent_val, 1) * 100), 1),
            'total_spend': total_spend,
            'attributed_revenue': total_roi,
            'roi_percentage': roi_percent,
            'channels_breakdown': channel_data.get('channels', []),
        }

        system_prompt = (
            "You are an executive marketing strategist and attribution intelligence officer. "
            "Analyze campaign performance data and craft a concise, authoritative 3-part briefing:\n"
            "1. Executive Summary & Conversion Velocity\n"
            "2. Channel Attribution Breakdown & Journey Insights\n"
            "3. Actionable Budget & Channel Reallocation Recommendations\n"
            "Format the response cleanly in clear markdown paragraphs."
        )

        user_prompt = (
            f"Campaign Performance & Attribution Data:\n"
            f"{json.dumps(stats_summary, indent=2)}\n"
            "Write the attribution insight briefing now."
        )

        response = self.llm.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        narration = response.get('content', '')
        if not narration or len(narration.strip()) < 50:
            narration = self._generate_fallback_narration(stats_summary)

        # Persist as cross-BIOM intelligence insight
        try:
            Insight.objects.create(
                company=company,
                agent_type='marketing',
                severity='medium' if roi_percent >= 0 else 'high',
                title=f"Campaign Attribution Briefing: {campaign.name}",
                description=narration[:1000],
                entity_type='campaign',
                entity_id=str(campaign.id),
                confidence=0.92,
                recommendation=f"Current ROI is {roi_percent}%. Allocate higher impression weight to top performing channels.",
                status='new'
            )
        except Exception as e:
            logger.warning(f"Could not persist Insight: {e}")

        return {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'stats': stats_summary,
            'narrative_briefing': narration,
        }

    def _generate_fallback_narration(self, stats: Dict[str, Any]) -> str:
        name = stats['campaign_name']
        spend = stats['total_spend']
        rev = stats['attributed_revenue']
        roi = stats['roi_percentage']
        conv_rate = stats['conversion_rate']

        return (
            f"### Executive Summary\n"
            f"Campaign **{name}** achieved a conversion rate of **{conv_rate}%** on total spend of **${spend:,.2f}**, "
            f"generating **${rev:,.2f}** in attributed revenue (Net ROI: **{roi}%**).\n\n"
            f"### Journey & Channel Attribution\n"
            f"The primary channel `{stats['channel']}` drove key outbound momentum. Multi-touch interactions "
            f"indicate healthy prospect engagement with an open rate of {stats['open_rate']}% and click-through of {stats['click_rate']}%.\n\n"
            f"### Strategic Recommendations\n"
            f"- Optimize low-performing creative variants using Thompson Sampling contextual bandits.\n"
            f"- Reallocate 15-20% of unspent budget into high-intent inbound retargeting segments."
        )
