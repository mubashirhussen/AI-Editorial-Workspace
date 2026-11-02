import json
import time
import logging
import httpx
from typing import Dict, Any, Optional
from backend.app.services.ai.base import BaseAIProvider, AIResponse

logger = logging.getLogger("editorial_workspace.ai.anthropic")

class AnthropicAdapter(BaseAIProvider):
    """
    Adapter for Anthropic Claude (Messages API via Async HTTP).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or "",
            model=model or "claude-3-5-sonnet-latest",
            base_url="https://api.anthropic.com/v1"
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        start_t = time.perf_counter()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        duration_ms = (time.perf_counter() - start_t) * 1000
        content = data.get("content", [{}])[0].get("text", "")
        usage = data.get("usage", {})

        return AIResponse(
            provider="anthropic",
            model=self.model,
            content=content,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            duration_ms=round(duration_ms, 2)
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        sys_p = (system_prompt or "") + "\nRespond with valid JSON object only. Do not wrap in markdown or prose."
        res = await self.generate_text(prompt, system_prompt=sys_p, temperature=temperature, max_tokens=max_tokens)
        try:
            clean = res.content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            res.parsed_json = json.loads(clean.strip())
        except Exception as e:
            logger.warning(f"Failed to parse Claude JSON response: {e}")
            res.parsed_json = {"error": "Invalid JSON returned", "raw": res.content}
        return res

    async def check_health(self) -> Dict[str, Any]:
        start_t = time.perf_counter()
        if not self.api_key:
            return {"status": "unconfigured", "provider": "anthropic"}
        try:
            # Send minimal 1-token test probe
            res = await self.generate_text("ping", max_tokens=1)
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "connected",
                "provider": "anthropic",
                "model": self.model,
                "latency_ms": round(duration_ms, 2)
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "error",
                "provider": "anthropic",
                "error": str(e),
                "latency_ms": round(duration_ms, 2)
            }
