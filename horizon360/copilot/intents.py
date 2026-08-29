import re
from typing import Dict, Any, Optional

class Intent:
    def __init__(self, name: str, original_query: str, parameters: Dict[str, Any] = None, confidence: float = 1.0):
        self.name = name
        self.original_query = original_query
        self.parameters = parameters or {}
        self.confidence = confidence

class IntentResolver:
    @staticmethod
    def resolve(query: str) -> Intent:
        query_lower = query.lower()
        
        if "risk" in query_lower:
            # e.g., "What deals are at risk?", "Why is Enterprise License at risk?"
            match = re.search(r'why is (.*) at risk', query_lower)
            if match:
                deal_name = match.group(1).strip().replace('?', '')
                return Intent("DEAL_EXPLANATION", query, {"deal_name": deal_name})
            if "why" in query_lower and "enterprise license" in query_lower:
                return Intent("DEAL_EXPLANATION", query, {"deal_name": "enterprise license"})
            return Intent("DEAL_RISK", query)
            
        if "pipeline" in query_lower:
            # e.g., "What's our current pipeline?"
            return Intent("PIPELINE_SUMMARY", query)
            
        if "tell me about" in query_lower:
            # e.g., "Tell me about alice@example.com" or "Tell me about Alice."
            match = re.search(r'tell me about (.*)', query_lower)
            if match:
                identifier = match.group(1).strip().replace('?', '')
                if identifier.endswith('.'):
                    identifier = identifier[:-1]
                return Intent("CUSTOMER_LOOKUP", query, {"identifier": identifier})
                
        if "recommendation" in query_lower or "sales focus" in query_lower or "should sales focus" in query_lower:
            # e.g., "What should sales focus on?"
            return Intent("SALES_RECOMMENDATION", query)
            
        return Intent("UNKNOWN", query, confidence=0.0)
