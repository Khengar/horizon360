from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
from crm.models import Deal, Contact
from cdp_core.models import Company, Customer, RawEvent
from .models import Insight
from .llm_client import LLMClient
import logging

logger = logging.getLogger(__name__)

class BaseIntelligenceAgent(ABC):
    """
    Base Agent implementing the OODA (Observe -> Orient -> Decide -> Act) loop.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Domain type: 'sales', 'customer_success', 'service', 'marketing', 'finance', 'executive'."""
        pass

    @abstractmethod
    def observe(self, company: Company) -> List[Dict[str, Any]]:
        """1. OBSERVE: Gather raw domain signals from Universal Data Model."""
        pass

    @abstractmethod
    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """2. ORIENT & DECIDE: Reason over signals and produce structured insights."""
        pass

    def act(self, company: Company, insights_data: List[Dict[str, Any]]) -> List[Insight]:
        """3. ACT: Persist insights, deduplicate, and trigger downstream remediations."""
        created_insights = []
        for data in insights_data:
            entity_type = data.get('entity_type')
            entity_id = str(data.get('entity_id')) if data.get('entity_id') is not None else None
            title = data.get('title')

            # Prevent duplicate insights within a 24-hour window
            recent = Insight.objects.filter(
                company=company,
                agent_type=self.agent_type,
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                created_at__gte=timezone.now() - timedelta(days=1)
            ).first()

            if not recent:
                insight = Insight.objects.create(
                    company=company,
                    agent_type=self.agent_type,
                    severity=data.get('severity', 'medium'),
                    title=title,
                    description=data.get('description', ''),
                    entity_type=entity_type,
                    entity_id=entity_id,
                    confidence=data.get('confidence', 0.85),
                    recommendation=data.get('recommendation', ''),
                    status='new'
                )
                created_insights.append(insight)
            else:
                created_insights.append(recent)
        return created_insights

    def run(self, company: Company) -> List[Insight]:
        signals = self.observe(company)
        insights_data = self.analyze(company, signals)
        return self.act(company, insights_data)


class SalesIntelligenceAgent(BaseIntelligenceAgent):
    """
    Monitors sales pipeline velocity, identifies stalled deals,
    calculates win probability factors, and drafts SDR playbooks.
    """
    @property
    def agent_type(self) -> str:
        return 'sales'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        signals = []
        candidate_deals = Deal.objects.filter(
            company=company,
            stage='negotiation',
            value__gte=100000
        )
        seven_days_ago = timezone.now() - timedelta(days=7)

        for deal in candidate_deals:
            customer = deal.customer or (deal.contact.customer if deal.contact else None)
            last_activity = None
            if customer:
                last_activity = RawEvent.objects.filter(
                    company=company,
                    customer=customer
                ).order_by('-created_at').first()

            last_date = last_activity.created_at if last_activity else deal.created_at
            if last_date < seven_days_ago:
                days_stalled = (timezone.now() - last_date).days
                signals.append({
                    'type': 'stalled_high_value_deal',
                    'deal': deal,
                    'days_stalled': days_stalled,
                    'severity': 'high'
                })

        return signals

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        insights = []
        for signal in signals:
            deal = signal['deal']
            val = float(deal.value)
            days = signal.get('days_stalled', 0)

            if signal['type'] == 'stalled_high_value_deal':
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


class CustomerHealthAgent(BaseIntelligenceAgent):
    """
    Evaluates customer event streams, identifies churn risk, 
    computes engagement metrics, and triggers retention playbooks.
    """
    @property
    def agent_type(self) -> str:
        return 'customer_success'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        signals = []
        customers = Customer.objects.filter(company=company)
        two_weeks_ago = timezone.now() - timedelta(days=14)

        for customer in customers:
            recent_events = RawEvent.objects.filter(
                company=company,
                customer=customer,
                created_at__gte=two_weeks_ago
            ).count()

            total_events = len(customer.timeline) if isinstance(customer.timeline, list) else 0
            deals_count = Deal.objects.filter(company=company, customer=customer).count()

            if total_events >= 4 and recent_events == 0:
                signals.append({
                    'type': 'churn_risk_inactivity',
                    'customer': customer,
                    'total_events': total_events,
                    'recent_events': recent_events,
                    'deals_count': deals_count
                })
            elif recent_events >= 8:
                signals.append({
                    'type': 'high_engagement_upsell',
                    'customer': customer,
                    'recent_events': recent_events
                })

        return signals

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        insights = []
        for s in signals:
            cust = s['customer']
            ident = cust.primary_email or cust.primary_phone or f"Customer {cust.id}"

            if s['type'] == 'churn_risk_inactivity':
                insights.append({
                    'severity': 'high',
                    'title': f"Churn Warning: Inactivity detected for {ident}",
                    'description': f"Customer had {s['total_events']} historical interactions but zero touchpoints over the past 14 days.",
                    'entity_type': 'customer',
                    'entity_id': str(cust.id),
                    'confidence': 0.85,
                    'recommendation': 'Trigger Customer Success outreach with product usage review and survey.'
                })
            elif s['type'] == 'high_engagement_upsell':
                insights.append({
                    'severity': 'low',
                    'title': f"Expansion Opportunity: High activity from {ident}",
                    'description': f"Recorded {s['recent_events']} events in the last 14 days. Strong product adoption signal.",
                    'entity_type': 'customer',
                    'entity_id': str(cust.id),
                    'confidence': 0.92,
                    'recommendation': 'Qualify for premium tier upgrade or add-on modules.'
                })
        return insights


class MarketingIntelligenceAgent(BaseIntelligenceAgent):
    """
    Analyzes multi-touchpoint visitor intent, identifies high-intent buying signals,
    and creates dynamic audience segmentation campaigns.
    """
    @property
    def agent_type(self) -> str:
        return 'marketing'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        signals = []
        customers = Customer.objects.filter(company=company)
        
        for customer in customers:
            timeline = customer.timeline or []
            pricing_views = sum(1 for e in timeline if isinstance(e, dict) and ('pricing' in str(e.get('payload', {})).lower() or 'pricing' in e.get('event_name', '').lower()))
            has_deal = Deal.objects.filter(company=company, customer=customer).exists()
            
            # High Intent: Multiple pricing views but no sales opportunity yet
            if pricing_views >= 2 and not has_deal:
                signals.append({
                    'type': 'high_intent_unassigned_lead',
                    'customer': customer,
                    'pricing_views': pricing_views
                })

        return signals

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        insights = []
        for s in signals:
            cust = s['customer']
            ident = cust.primary_email or cust.primary_phone or f"Customer {cust.id}"
            insights.append({
                'severity': 'medium',
                'title': f"High Intent Lead: {ident} viewed pricing {s['pricing_views']} times",
                'description': f"Prospective customer {ident} demonstrates strong purchase intent with {s['pricing_views']} pricing page interactions, but has no active deal.",
                'entity_type': 'customer',
                'entity_id': str(cust.id),
                'confidence': 0.89,
                'recommendation': 'Auto-create Qualified Opportunity and assign SDR outreach sequence.'
            })
        return insights


class ServiceIntelligenceAgent(BaseIntelligenceAgent):
    """
    Monitors support interactions, assesses SLA breach risk, 
    evaluates ticket sentiment, and drafts grounded KB answers.
    """
    @property
    def agent_type(self) -> str:
        return 'service'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        signals = []
        # Look for support or error events in RawEvents
        support_events = RawEvent.objects.filter(
            company=company,
            event_name__in=['support.ticket_created', 'ticket.opened', 'error.occurred', 'customer.complaint']
        ).order_by('-created_at')[:20]

        for ev in support_events:
            customer = ev.customer
            customer_deals_val = 0.0
            if customer:
                deals = Deal.objects.filter(company=company, customer=customer)
                customer_deals_val = sum(float(d.value or 0) for d in deals)

            signals.append({
                'type': 'support_ticket_triage',
                'raw_event': ev,
                'customer': customer,
                'customer_value': customer_deals_val
            })

        return signals

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        insights = []
        for s in signals:
            ev = s['raw_event']
            val = s['customer_value']
            cust_ident = ev.customer.primary_email if ev.customer else "Anonymous User"

            severity = 'critical' if val >= 50000 else 'high'
            insights.append({
                'severity': severity,
                'title': f"Priority Support Ticket: {cust_ident} (${val:,.0f} LTV)",
                'description': f"Support event '{ev.event_name}' received from high-value account. Requires accelerated SLA triage.",
                'entity_type': 'customer' if ev.customer else 'event',
                'entity_id': str(ev.customer.id) if ev.customer else str(ev.id),
                'confidence': 0.94,
                'recommendation': 'Assign Senior Support Engineer and send personalized reassurance update.'
            })
        return insights


class FinanceIntelligenceAgent(BaseIntelligenceAgent):
    """
    Monitors revenue recognition, detects payment anomalies, 
    evaluates deal-to-cash conversion, and triggers dunning workflows.
    """
    @property
    def agent_type(self) -> str:
        return 'finance'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        signals = []
        # Check won deals without payment events
        won_deals = Deal.objects.filter(company=company, stage='won')
        for d in won_deals:
            customer = d.customer or (d.contact.customer if d.contact else None)
            if customer:
                has_order = RawEvent.objects.filter(
                    company=company,
                    customer=customer,
                    event_name__in=['order.completed', 'invoice.paid', 'payment.success']
                ).exists()
                if not has_order and float(d.value or 0) > 0:
                    signals.append({
                        'type': 'unbilled_won_deal',
                        'deal': d,
                        'customer': customer
                    })

        return signals

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        insights = []
        for s in signals:
            deal = s['deal']
            val = float(deal.value or 0)
            insights.append({
                'severity': 'medium',
                'title': f"Unbilled Revenue Signal: Deal '{deal.title}' ($ {val:,.0f})",
                'description': f"Deal is marked as Closed Won, but no corresponding order.completed or payment event has been registered in the UDM.",
                'entity_type': 'deal',
                'entity_id': str(deal.id),
                'confidence': 0.91,
                'recommendation': 'Generate invoice via Finance BIOM and send secure payment link.'
            })
        return insights


class ExecutiveSynthesisAgent(BaseIntelligenceAgent):
    """
    Synthesizes cross-BIOM metrics into an executive briefing with strategic action recommendations.
    """
    @property
    def agent_type(self) -> str:
        return 'executive'

    def observe(self, company: Company) -> List[Dict[str, Any]]:
        total_customers = Customer.objects.filter(company=company).count()
        deals = Deal.objects.filter(company=company)
        total_pipe = sum(float(d.value or 0) for d in deals)
        won_rev = sum(float(d.value or 0) for d in deals.filter(stage='won'))
        open_deals = deals.exclude(stage__in=['won', 'lost']).count()
        high_severity_insights = Insight.objects.filter(company=company, severity__in=['high', 'critical']).count()

        return [{
            'type': 'executive_summary',
            'total_customers': total_customers,
            'total_pipeline': total_pipe,
            'won_revenue': won_rev,
            'open_deals': open_deals,
            'risk_count': high_severity_insights
        }]

    def analyze(self, company: Company, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not signals:
            return []
        s = signals[0]
        pipe_val = s['total_pipeline']
        won_val = s['won_revenue']
        risks = s['risk_count']

        recommendations = []
        if risks > 0:
            recommendations.append(f"Remediate {risks} high-risk pipeline deals and accounts.")
        if s['open_deals'] > 0 and won_val == 0:
            recommendations.append("Accelerate mid-stage proposals to close Q3 revenue.")
        if not recommendations:
            recommendations.append("Continue current execution; expand inbound marketing cadence.")

        return [{
            'severity': 'medium' if risks == 0 else 'high',
            'title': "Executive Briefing: Pipeline Health & Strategy",
            'description': (
                f"Horizon 360 unified overview: {s['total_customers']} unified customer profiles, "
                f"${pipe_val:,.2f} total pipeline across {s['open_deals']} open deals, "
                f"${won_val:,.2f} recognized won revenue. "
                f"{risks} critical alert(s) requiring executive attention."
            ),
            'entity_type': 'company',
            'entity_id': str(company.id),
            'confidence': 0.95,
            'recommendation': " | ".join(recommendations)
        }]


class MeshRunner:
    """
    Orchestrates the entire Federated Multi-Agent Intelligence Mesh for a company.
    """
    @classmethod
    def get_all_agents(cls) -> List[BaseIntelligenceAgent]:
        return [
            SalesIntelligenceAgent(),
            CustomerHealthAgent(),
            MarketingIntelligenceAgent(),
            ServiceIntelligenceAgent(),
            FinanceIntelligenceAgent(),
            ExecutiveSynthesisAgent()
        ]

    @classmethod
    def run_mesh_for_company(cls, company: Company) -> Dict[str, Any]:
        agents = cls.get_all_agents()
        all_created = []
        agent_summaries = {}

        for agent in agents:
            try:
                insights = agent.run(company)
                all_created.extend(insights)
                agent_summaries[agent.agent_type] = len(insights)
            except Exception as e:
                logger.exception(f"Error running agent {agent.agent_type} for company {company.id}: {e}")
                agent_summaries[agent.agent_type] = 0

        return {
            "status": "success",
            "company_id": company.id,
            "company_name": company.name,
            "agents_executed": len(agents),
            "agent_summaries": agent_summaries,
            "total_insights_generated": len(all_created)
        }
