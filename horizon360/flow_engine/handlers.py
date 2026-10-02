import requests
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .template_resolver import TemplateResolver
from .models import FlowNode, StepExecution, FlowExecution, ApprovalRequest

@dataclass
class NodeResult:
    status: str  # 'completed', 'waiting', 'failed'
    output: Dict[str, Any]
    variables: Dict[str, Any] = None
    execution_status: str = 'running'  # If 'waiting', what should the execution status be?

class NodeHandler:
    """Base class for all node execution handlers."""
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        raise NotImplementedError

class TriggerHandler(NodeHandler):
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        # Trigger is just a pass-through node that emits the initial payload
        return NodeResult(
            status='completed',
            output={'trigger_payload': execution.trigger_payload}
        )

class ConditionHandler(NodeHandler):
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        config = node.config
        
        # New Rule Tree logic
        if 'rule_tree' in config:
            condition_met = self._evaluate_rule_node(config['rule_tree'], execution.context)
            return NodeResult(
                status='completed',
                output={'condition_met': condition_met, 'evaluated_tree': True}
            )
            
        # Legacy fallback
        field = config.get('field', '')
        operator = config.get('operator', '==')
        target_value = config.get('value', '')
        
        actual_value = TemplateResolver.resolve(f"{{{{{field}}}}}", execution.context)
        condition_met = self._evaluate_single(actual_value, operator, target_value)
                
        return NodeResult(
            status='completed',
            output={'condition_met': condition_met, 'evaluated_value': actual_value}
        )
        
    def _evaluate_rule_node(self, node_data: dict, context: dict) -> bool:
        node_type = node_data.get('type', 'condition')
        
        if node_type == 'group':
            logic = node_data.get('logic', 'AND')
            rules = node_data.get('rules', [])
            if not rules:
                return True
                
            results = [self._evaluate_rule_node(r, context) for r in rules]
            if logic == 'AND':
                return all(results)
            else: # OR
                return any(results)
                
        else: # condition
            field = node_data.get('field', '')
            operator = node_data.get('operator', '==')
            target_value = node_data.get('value', '')
            
            # Use TemplateResolver to dynamically look up from context
            actual_value = TemplateResolver.resolve(f"{{{{{field}}}}}", context)
            return self._evaluate_single(actual_value, operator, target_value)
            
    def _evaluate_single(self, actual_value, operator, target_value) -> bool:
        if operator == '==':
            return str(actual_value) == str(target_value)
        elif operator == '!=':
            return str(actual_value) != str(target_value)
        elif operator == '>':
            try:
                return float(actual_value) > float(target_value)
            except ValueError:
                return False
        elif operator == '<':
            try:
                return float(actual_value) < float(target_value)
            except ValueError:
                return False
        elif operator == '>=':
            try:
                return float(actual_value) >= float(target_value)
            except ValueError:
                return False
        elif operator == '<=':
            try:
                return float(actual_value) <= float(target_value)
            except ValueError:
                return False
        elif operator == 'contains':
            return str(target_value).lower() in str(actual_value).lower()
        return False

class ActionHandler(NodeHandler):
    """Executes a BIOM-specific action (e.g. create_invoice, create_project)."""
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        config = node.config
        action_type = config.get('action_type')
        
        # Resolve any templates in the params
        raw_params = config.get('params', {})
        params = TemplateResolver.resolve_dict(raw_params, execution.context)
        
        # Here we would typically dispatch to the respective BIOM service (finance, projects, etc.)
        # For MVP/architecture, we mock the creation and return dummy IDs.
        
        result_data = {'action_type': action_type, 'status': 'success'}
        
        if action_type == 'create_invoice':
            result_data['invoice_id'] = f"INV-{execution.id.hex[:6]}"
            result_data['amount'] = params.get('amount')
        elif action_type == 'create_project':
            result_data['project_id'] = f"PRJ-{execution.id.hex[:6]}"
            
        return NodeResult(
            status='completed',
            output=result_data
        )

class ApprovalHandler(NodeHandler):
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        config = node.config
        title_template = config.get('title', 'Approval Required')
        title = TemplateResolver.resolve(title_template, execution.context)
        
        # In a real scenario, we'd lookup the approver by role or specific user ID
        # For now, if not provided, just pick the first superuser as fallback
        approver = User.objects.filter(is_superuser=True).first()
        
        # Create the approval request
        ApprovalRequest.objects.create(
            step_execution=step,
            execution=execution,
            company=execution.company,
            title=title,
            description=config.get('description', ''),
            context_data=execution.context,
            status='pending',
            current_approver=approver
        )
        
        # Node pauses execution until approval is resolved
        return NodeResult(
            status='waiting',
            output={'message': 'Waiting for human approval'},
            execution_status='waiting_approval'
        )

class AIActionHandler(NodeHandler):
    """Executes AI inference via NVIDIA NIM API."""
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        config = node.config
        prompt_template = config.get('prompt_template', '')
        prompt = TemplateResolver.resolve(prompt_template, execution.context)
        
        model = config.get('model', getattr(settings, 'LLM_MODEL', 'nvidia/nemotron-3-ultra-550b-a55b'))
        api_key = getattr(settings, 'NVIDIA_API_KEY', None)
        
        if not api_key:
            raise ValueError("NVIDIA_API_KEY is not configured in settings.")
            
        try:
            response = requests.post(
                'https://integrate.api.nvidia.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': config.get('max_tokens', 1024),
                    'temperature': config.get('temperature', 0.3),
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            ai_content = data['choices'][0]['message']['content']
            
            return NodeResult(
                status='completed',
                output={
                    'ai_response': ai_content,
                    'model': data.get('model')
                },
                variables={config.get('output_variable', 'ai_output'): ai_content}
            )
        except Exception as e:
            raise Exception(f"AI Action failed: {str(e)}")

class EndHandler(NodeHandler):
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        return NodeResult(
            status='completed',
            output={'message': 'Flow reached end node'}
        )

class JoinHandler(NodeHandler):
    def execute(self, node: FlowNode, step: StepExecution, execution: FlowExecution) -> NodeResult:
        return NodeResult(
            status='completed',
            output={'message': 'All parallel branches joined successfully'}
        )

def get_handler(node_type: str) -> NodeHandler:
    """Factory to return the appropriate handler for a node type."""
    handlers = {
        'trigger': TriggerHandler(),
        'condition': ConditionHandler(),
        'action': ActionHandler(),
        'ai_action': AIActionHandler(),
        'approval': ApprovalHandler(),
        'end': EndHandler(),
        'parallel_join': JoinHandler(),
    }
    return handlers.get(node_type, ActionHandler())
