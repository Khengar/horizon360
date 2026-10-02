import re
from functools import reduce

class TemplateResolver:
    """Resolves {{variable.path}} references against the execution context."""
    
    @staticmethod
    def resolve(template: str, context: dict) -> str:
        """
        Replaces {{path.to.var}} with values from context.
        Example: "Invoice for {{trigger.payload.company}}" -> "Invoice for Acme"
        """
        if not template or not isinstance(template, str):
            return template
            
        def replacer(match):
            path = match.group(1).strip()
            keys = path.split('.')
            try:
                # Traverse the dictionary using the keys
                value = reduce(lambda d, key: d.get(key, '') if isinstance(d, dict) else getattr(d, key, ''), keys, context)
                return str(value) if value is not None and value != '' else ''
            except Exception:
                return ''
                
        return re.sub(r'\{\{(.+?)\}\}', replacer, template)
        
    @staticmethod
    def resolve_dict(data: dict, context: dict) -> dict:
        """Recursively resolves templates within a dictionary's string values."""
        resolved = {}
        for k, v in data.items():
            if isinstance(v, str):
                resolved[k] = TemplateResolver.resolve(v, context)
            elif isinstance(v, dict):
                resolved[k] = TemplateResolver.resolve_dict(v, context)
            elif isinstance(v, list):
                resolved[k] = [
                    TemplateResolver.resolve_dict(i, context) if isinstance(i, dict) 
                    else TemplateResolver.resolve(i, context) if isinstance(i, str) 
                    else i 
                    for i in v
                ]
            else:
                resolved[k] = v
        return resolved
