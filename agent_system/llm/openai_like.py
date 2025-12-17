import httpx
import random
import time
from typing import List, Dict, Optional
from .base import LLMProvider

class OpenAILikeProvider(LLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        timeout_s: float = 60.0,
        max_retries: int = 3,
        backoff_base_s: float = 0.5,
        backoff_max_s: float = 6.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.max_retries = max(1, int(max_retries))
        self.backoff_base_s = float(backoff_base_s)
        self.backoff_max_s = float(backoff_max_s)
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._client = httpx.Client(
            headers=self.headers,
            timeout=httpx.Timeout(timeout_s),
        )

    def _retry_delay(self, attempt: int, retry_after_s: Optional[float] = None) -> float:
        if retry_after_s is not None:
            return max(0.0, min(self.backoff_max_s, float(retry_after_s)))
        base = self.backoff_base_s * (2 ** max(0, attempt - 1))
        jitter = random.uniform(0.0, 0.25)
        return max(0.0, min(self.backoff_max_s, base + jitter))

    def generate(self, messages: List[Dict[str, str]], model: str, **kwargs) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages
        }
        payload.update(kwargs)
        
        retryable_statuses = {408, 429, 500, 502, 503, 504}
        last_err: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                body = e.response.text

                retry_after = None
                if "retry-after" in e.response.headers:
                    try:
                        retry_after = float(e.response.headers["retry-after"])
                    except Exception:
                        retry_after = None

                last_err = Exception(f"HTTP error {status}: {body}")
                if status in retryable_statuses and attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt, retry_after_s=retry_after))
                    continue
                raise last_err
            except (httpx.TimeoutException, httpx.RequestError) as e:
                last_err = Exception(f"Error communicating with LLM provider: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self._retry_delay(attempt))
                    continue
                raise last_err
            except Exception as e:
                raise Exception(f"Error communicating with LLM provider: {str(e)}")

        raise last_err or Exception("Error communicating with LLM provider: unknown error")
