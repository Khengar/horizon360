from typing import Dict, Any
from cdp_core.models import Company, Customer
from crm.models import Deal
from intelligence.models import Insight
from django.db.models import Sum, Q
from django.utils import timezone

class ContextBuilder:
    @staticmethod
    def build_context(company: Company, intent: 'Intent') -> Dict[str, Any]:
        context = {
            "intent": intent.name,
            "company": {
                "id": company.id,
                "name": company.name
            }
        }
        
        if intent.name == "DEAL_RISK":
            deals = Deal.objects.filter(company=company, stage='negotiation', value__gte=100000)
            insights = Insight.objects.filter(company=company, entity_type='deal', severity__in=['high', 'critical'])
            
            context["deals"] = []
            for d in deals:
                context["deals"].append({
                    "id": d.id,
                    "title": d.title,
                    "value": float(d.value) if d.value else 0,
                    "stage": d.stage,
                    "days_stalled": (timezone.now() - d.updated_at).days if getattr(d, 'updated_at', None) else 0
                })
            
            context["insights"] = [
                {
                    "id": i.id,
                    "severity": i.severity,
                    "title": i.title,
                    "recommendation": i.recommendation,
                    "entity_id": i.entity_id
                } for i in insights
            ]
            
        elif intent.name == "PIPELINE_SUMMARY":
            all_deals = Deal.objects.filter(company=company)
            open_deals = all_deals.exclude(stage__in=['won', 'lost'])
            
            context["pipeline"] = {
                "total_deals": all_deals.count(),
                "open_deals": open_deals.count(),
                "total_value": float(all_deals.aggregate(total=Sum('value'))['total'] or 0),
                "open_value": float(open_deals.aggregate(total=Sum('value'))['total'] or 0),
                "won_value": float(all_deals.filter(stage='won').aggregate(total=Sum('value'))['total'] or 0),
            }
            
        elif intent.name == "CUSTOMER_LOOKUP":
            identifier = intent.parameters.get("identifier", "").lower()
            customer = Customer.objects.filter(
                Q(primary_email__icontains=identifier) | Q(primary_phone__icontains=identifier),
                company=company
            ).first()
            
            if customer:
                deals = Deal.objects.filter(company=company, customer=customer)
                context["customer"] = {
                    "id": customer.id,
                    "email": customer.primary_email,
                    "phone": customer.primary_phone,
                    "deals_count": deals.count(),
                    "total_value": float(deals.aggregate(total=Sum('value'))['total'] or 0)
                }
            else:
                context["customer"] = None
                
        elif intent.name == "DEAL_EXPLANATION":
            deal_name = intent.parameters.get("deal_name", "").lower()
            deal = Deal.objects.filter(company=company, title__icontains=deal_name).first()
            if deal:
                insight = Insight.objects.filter(company=company, entity_type='deal', entity_id=str(deal.id)).first()
                context["deal"] = {
                    "id": deal.id,
                    "title": deal.title,
                    "value": float(deal.value) if deal.value else 0,
                    "stage": deal.stage
                }
                if insight:
                    context["insight"] = {
                        "id": insight.id,
                        "title": insight.title,
                        "description": insight.description,
                        "recommendation": insight.recommendation
                    }
                else:
                    context["insight"] = None
            else:
                context["deal"] = None
                
        elif intent.name == "SALES_RECOMMENDATION":
            insights = Insight.objects.filter(company=company, severity__in=['high', 'critical'])
            context["insights"] = [
                {
                    "id": i.id,
                    "severity": i.severity,
                    "title": i.title,
                    "recommendation": i.recommendation
                } for i in insights
            ]

        return context
