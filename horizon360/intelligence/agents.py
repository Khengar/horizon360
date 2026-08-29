from abc import ABC, abstractmethod
from typing import List, Any
from django.utils import timezone
from datetime import timedelta
from crm.models import Deal
from .models import Insight
from cdp_core.models import Company

class IntelligenceAgent(ABC):
    @property
    @abstractmethod
    def agent_type(self) -> str:
        pass

    @abstractmethod
    def observe(self, company: Company) -> List[Any]:
        """Gather relevant signals for this agent type."""
        pass

    @abstractmethod
    def analyze(self, signals: List[Any]) -> List[dict]:
        """Analyze signals and determine insights."""
        pass

    def run(self, company: Company):
        signals = self.observe(company)
        insights_data = self.analyze(signals)
        
        for data in insights_data:
            # Check if this exact insight was already created recently to prevent spam
            recent = Insight.objects.filter(
                company=company,
                agent_type=self.agent_type,
                entity_type=data.get('entity_type'),
                entity_id=data.get('entity_id'),
                title=data.get('title'),
                created_at__gte=timezone.now() - timedelta(days=1)
            ).exists()
            
            if not recent:
                Insight.objects.create(
                    company=company,
                    agent_type=self.agent_type,
                    **data
                )


class SalesIntelligenceAgent(IntelligenceAgent):
    @property
    def agent_type(self) -> str:
        return 'sales'

    def observe(self, company: Company) -> List[Any]:
        signals = []
        
        # Candidate deals: stage is Negotiation, value >= 100000
        candidate_deals = Deal.objects.filter(
            company=company,
            stage='negotiation',
            value__gte=100000
        )
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        for deal in candidate_deals:
            # Determine last relevant activity for this customer
            # "no recorded customer activity for X days"
            from cdp_core.models import RawEvent
            last_activity = RawEvent.objects.filter(
                company=company,
                customer=deal.customer
            ).order_by('-created_at').first()
            
            last_activity_date = last_activity.created_at if last_activity else deal.created_at
            
            if last_activity_date < seven_days_ago:
                days_stalled = (timezone.now() - last_activity_date).days
                signals.append({
                    'type': 'stalled_high_value_deal',
                    'deal': deal,
                    'days_stalled': days_stalled
                })
            
        return signals

    def analyze(self, signals: List[Any]) -> List[dict]:
        insights = []
        for signal in signals:
            if signal['type'] == 'stalled_high_value_deal':
                deal = signal['deal']
                days = signal['days_stalled']
                val = float(deal.value)
                insights.append({
                    'severity': 'high',
                    'title': 'High-value deal is stalled',
                    'description': f"{deal.title} is a ${val:,.0f} Negotiation deal with no recorded customer activity for {days} days.",
                    'entity_type': 'deal',
                    'entity_id': str(deal.id),
                    'confidence': 0.8,
                    'recommendation': 'Schedule a follow-up with the customer.'
                })
        return insights
