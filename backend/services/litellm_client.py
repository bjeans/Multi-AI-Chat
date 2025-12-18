import httpx
import json
import os
from typing import List, AsyncGenerator, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")


class LiteLLMClient:
    """Client for interacting with LiteLLM proxy"""

    def __init__(self, base_url: str = LITELLM_PROXY_URL, api_key: str = LITELLM_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers including authorization if API key is set"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_available_models(self) -> List[Dict[str, any]]:
        """Fetch available models from LiteLLM proxy"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                # LiteLLM proxy returns models in OpenAI format
                if "data" in data:
                    return [
                        {
                            "id": model.get("id"),
                            "name": model.get("id"),
                            "available": True,
                            "provider": model.get("owned_by", "unknown"),
                        }
                        for model in data["data"]
                    ]
                return []
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    async def get_model_info(self) -> dict:
        """Fetch detailed model info from /v1/model/info endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/v1/model/info",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return {"data": []}

    async def get_health_status(self) -> dict:
        """Fetch health status from /health/latest endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/health/latest",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching health status: {e}")
            return {"latest_health_checks": {}, "total_models": 0}

    async def test_model(self, model_id: str) -> bool:
        """Test if a model is available and responding"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": model_id,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5,
                    },
                )
                return response.status_code == 200
        except Exception:
            return False

    async def stream_chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from LiteLLM proxy
        Yields individual token chunks as they arrive
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                }
                if max_tokens:
                    payload["max_tokens"] = max_tokens

                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            if data_str.strip() == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            yield f"\n[Error: HTTP {e.response.status_code}]"
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def get_chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get complete chat response (non-streaming)
        Used for chairman synthesis
        """
        full_response = ""
        async for chunk in self.stream_chat_completion(
            model_id, messages, temperature, max_tokens
        ):
            full_response += chunk
        return full_response
