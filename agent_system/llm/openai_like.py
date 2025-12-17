import httpx
from typing import List, Dict
from .base import LLMProvider

class OpenAILikeProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages
        }
        payload.update(kwargs)
        
        try:
            response = httpx.post(url, headers=self.headers, json=payload, timeout=60.0)
            response.raise_for_status() 
            result = response.json()['choices'][0]['message']['content']
            return result
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Error communicating with LLM provider: {str(e)}")
