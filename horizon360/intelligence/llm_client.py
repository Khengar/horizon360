import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_local_env():
    """
    Search and load key-value pairs from .env files in standard project directories
    into os.environ if not already present.
    """
    search_paths = [
        Path(__file__).resolve().parent / '.env', # intelligence/.env
        Path(__file__).resolve().parent.parent / '.env', # horizon360/.env
        Path(__file__).resolve().parent.parent.parent / '.env', # workspace root .env
    ]
    for p in search_paths:
        if p.exists() and p.is_file():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k:
                                os.environ[k] = v
            except Exception as e:
                logger.warning(f"Failed to parse .env at {p}: {e}")

# Load environment on module import
load_local_env()


class LLMClient:
    """
    Unified LLM Client supporting Groq, NVIDIA NIM, OpenAI, Ollama, 
    and a robust Deterministic Fallback Engine with Zero External Dependencies.
    """
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        load_local_env()
        self.provider = (provider or os.environ.get('LLM_PROVIDER', 'auto')).lower()
        self.timeout = timeout
        
        groq_key = os.environ.get('GROQ_API_KEY')
        nvidia_key = os.environ.get('NVIDIA_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        if self.provider == 'auto':
            if nvidia_key:
                self.provider = 'nvidia'
            elif groq_key:
                self.provider = 'groq'
            elif openai_key:
                self.provider = 'openai'
            elif os.environ.get('OLLAMA_HOST'):
                self.provider = 'ollama'
            else:
                self.provider = 'fallback'

        # Configure endpoints & models based on provider
        if self.provider == 'groq':
            self.api_key = api_key or groq_key
            self.base_url = base_url or 'https://api.groq.com/openai/v1'
            self.model = model or os.environ.get('LLM_MODEL', 'llama-3.3-70b-versatile')
        elif self.provider == 'nvidia':
            self.api_key = api_key or nvidia_key
            self.base_url = base_url or 'https://integrate.api.nvidia.com/v1'
            self.model = model or os.environ.get('LLM_MODEL', 'nvidia/nemotron-3-ultra-550b-a55b')
        elif self.provider == 'openai':
            self.api_key = api_key or openai_key
            self.base_url = base_url or 'https://api.openai.com/v1'
            self.model = model or os.environ.get('LLM_MODEL', 'gpt-4o-mini')
        elif self.provider == 'ollama':
            self.api_key = api_key or 'ollama'
            ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
            self.base_url = f"{ollama_host.rstrip('/')}/v1"
            self.model = model or os.environ.get('LLM_MODEL', 'llama3')
        else:
            self.provider = 'fallback'
            self.api_key = None
            self.base_url = None
            self.model = 'horizon-deterministic-v1'

    def get_provider_name(self) -> str:
        if self.provider == 'groq':
            return f"Groq ({self.model})"
        elif self.provider == 'nvidia':
            return f"NVIDIA NIM ({self.model})"
        elif self.provider == 'openai':
            return f"OpenAI ({self.model})"
        elif self.provider == 'ollama':
            return f"Ollama ({self.model})"
        return "Horizon Intelligence Engine"

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Executes a chat completion. If provider is fallback or if API call fails,
        falls back gracefully to internal rule reasoning.
        """
        if self.provider == 'fallback' or not self.api_key:
            return self._fallback_completion(messages, tools)

        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if tools and self.provider != 'nvidia':
            # Some NIM models do not support custom tools schema parameter
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        if response_format and self.provider in ['groq', 'openai']:
            payload["response_format"] = response_format

        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            endpoint,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Horizon360-AI-Engine/1.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_json = json.loads(resp.read().decode('utf-8'))
                choice = resp_json.get("choices", [{}])[0]
                message = choice.get("message", {})
                return {
                    "success": True,
                    "provider": self.get_provider_name(),
                    "message": message,
                    "content": message.get("content", ""),
                    "tool_calls": message.get("tool_calls", [])
                }
        except Exception as e:
            logger.warning(f"LLM request to {self.provider} failed: {e}. Falling back to deterministic engine.")
            return self._fallback_completion(messages, tools)

    def _fallback_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Deterministic internal fallback engine when no external API key is active.
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        query_lower = last_user_msg.lower()

        # Check if tools are provided and should be called
        if tools:
            tool_names = [t.get("function", {}).get("name") for t in tools if "function" in t]
            
            if ("pipeline" in query_lower or "summary" in query_lower or "revenue" in query_lower) and "get_pipeline_summary" in tool_names:
                return {
                    "success": True,
                    "provider": self.get_provider_name(),
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_fallback_pipe_1",
                            "type": "function",
                            "function": {
                                "name": "get_pipeline_summary",
                                "arguments": "{}"
                            }
                        }]
                    },
                    "content": "",
                    "tool_calls": [{
                        "id": "call_fallback_pipe_1",
                        "type": "function",
                        "function": {
                            "name": "get_pipeline_summary",
                            "arguments": "{}"
                        }
                    }]
                }

            if ("risk" in query_lower or "stalled" in query_lower or "attention" in query_lower or "why" in query_lower) and "get_stalled_deals" in tool_names:
                return {
                    "success": True,
                    "provider": self.get_provider_name(),
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_fallback_deals_1",
                            "type": "function",
                            "function": {
                                "name": "get_stalled_deals",
                                "arguments": json.dumps({"min_value": 0, "days": 0})
                            }
                        }]
                    },
                    "content": "",
                    "tool_calls": [{
                        "id": "call_fallback_deals_1",
                        "type": "function",
                        "function": {
                            "name": "get_stalled_deals",
                            "arguments": json.dumps({"min_value": 0, "days": 0})
                        }
                    }]
                }

            if ("tell me about" in query_lower or "customer" in query_lower or "@" in query_lower) and "lookup_customer" in tool_names:
                import re
                match = re.search(r'[\w\.-]+@[\w\.-]+', last_user_msg)
                identifier = match.group(0) if match else "alice@example.com"
                return {
                    "success": True,
                    "provider": self.get_provider_name(),
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_fallback_cust_1",
                            "type": "function",
                            "function": {
                                "name": "lookup_customer",
                                "arguments": json.dumps({"identifier": identifier})
                            }
                        }]
                    },
                    "content": "",
                    "tool_calls": [{
                        "id": "call_fallback_cust_1",
                        "type": "function",
                        "function": {
                            "name": "lookup_customer",
                            "arguments": json.dumps({"identifier": identifier})
                        }
                    }]
                }

        # Direct text completion fallback
        return {
            "success": True,
            "provider": self.get_provider_name(),
            "message": {
                "role": "assistant",
                "content": "Horizon 360 AI is monitoring all real-time events across your unified data model. How can I assist with your pipeline, customers, or workflows?"
            },
            "content": "Horizon 360 AI is monitoring all real-time events across your unified data model. How can I assist with your pipeline, customers, or workflows?",
            "tool_calls": []
        }
