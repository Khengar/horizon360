from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .intents import IntentResolver, Intent
from .context import ContextBuilder
from cdp_core.models import Company

class ModelProvider(ABC):
    @abstractmethod
    def generate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class DeterministicProvider(ModelProvider):
    def generate(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        intent_name = context.get('intent')
        
        response = {
            "status": "success",
            "intent": intent_name,
            "answer": "",
            "sources": [],
            "actions": []
        }
        
        if intent_name == "UNKNOWN":
            response["answer"] = "I'm sorry, I don't understand that request or it is currently unsupported."
            
        elif intent_name == "DEAL_RISK":
            insights = context.get("insights", [])
            deals = context.get("deals", [])
            if not insights:
                response["answer"] = "There are currently no high-value deals flagged as at risk."
            else:
                count = len(insights)
                response["answer"] = f"{count} high-value deal{'s' if count != 1 else ''} currently require{'s' if count == 1 else ''} attention.\n\n"
                for ins in insights:
                    # Find matching deal
                    matching_deal = next((d for d in deals if str(d['id']) == str(ins['entity_id'])), None)
                    if matching_deal:
                        response["answer"] += f"{matching_deal['title']} — ${matching_deal['value']:,.0f}\n"
                        response["answer"] += f"Stage: {matching_deal['stage'].capitalize()}\n"
                        response["answer"] += f"Stalled: {matching_deal['days_stalled']} days\n\n"
                    
                    response["answer"] += f"Recommendation:\n{ins['recommendation']}\n\n"
                    
                    if ins['entity_id']:
                        response["sources"].append({"type": "deal", "id": int(ins['entity_id'])})
                        response["sources"].append({"type": "insight", "id": ins['id']})
                        
        elif intent_name == "PIPELINE_SUMMARY":
            pipe = context.get("pipeline", {})
            response["answer"] = (
                f"Current Pipeline Summary:\n"
                f"- Total Pipeline Value: ${pipe.get('total_value', 0):,.2f} ({pipe.get('total_deals', 0)} deals)\n"
                f"- Open Pipeline Value: ${pipe.get('open_value', 0):,.2f} ({pipe.get('open_deals', 0)} deals)\n"
                f"- Closed Won Revenue: ${pipe.get('won_value', 0):,.2f}\n"
            )
            
        elif intent_name == "CUSTOMER_LOOKUP":
            cust = context.get("customer")
            if not cust:
                response["answer"] = "I could not find a customer matching that description."
            else:
                response["answer"] = (
                    f"Customer details for {cust['email']}:\n"
                    f"- Total Deals: {cust['deals_count']}\n"
                    f"- Total Deal Value: ${cust['total_value']:,.2f}\n"
                )
                response["sources"].append({"type": "customer", "id": cust['id']})
                
        elif intent_name == "DEAL_EXPLANATION":
            deal = context.get("deal")
            ins = context.get("insight")
            if not deal:
                response["answer"] = "I could not find a deal matching that name."
            elif not ins:
                response["answer"] = f"Deal '{deal['title']}' is currently in stage '{deal['stage']}' with a value of ${deal['value']:,.2f}, and it is not flagged with any specific insights."
                response["sources"].append({"type": "deal", "id": deal['id']})
            else:
                response["answer"] = (
                    f"{deal['title']} is a ${deal['value']:,.2f} {deal['stage'].capitalize()} deal.\n"
                    f"Risk: {ins['description']}\n"
                    f"Recommendation: {ins['recommendation']}"
                )
                response["sources"].append({"type": "deal", "id": deal['id']})
                response["sources"].append({"type": "insight", "id": ins['id']})
                
        elif intent_name == "SALES_RECOMMENDATION":
            insights = context.get("insights", [])
            if not insights:
                response["answer"] = "There are no critical recommendations for sales at this time."
            else:
                response["answer"] = "Here are the top focus areas for sales based on recent insights:\n\n"
                for ins in insights:
                    response["answer"] += f"- {ins['title']}: {ins['recommendation']}\n"
                    response["sources"].append({"type": "insight", "id": ins['id']})

        return response

class CopilotService:
    def __init__(self, provider: ModelProvider = None):
        self.provider = provider or DeterministicProvider()
        
    def handle(self, company: Company, query: str) -> Dict[str, Any]:
        intent = IntentResolver.resolve(query)
        context = ContextBuilder.build_context(company, intent)
        return self.provider.generate(query, context)
