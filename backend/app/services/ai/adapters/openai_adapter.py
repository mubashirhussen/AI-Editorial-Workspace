import json
import time
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from backend.app.services.ai.base import BaseAIProvider, AIResponse

logger = logging.getLogger("editorial_workspace.ai.openai")

class OpenAIAdapter(BaseAIProvider):
    """
    Adapter for standard OpenAI API models (gpt-4o, gpt-4o-mini).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            api_key=api_key or "",
            model=model or "gpt-4o-mini",
            base_url=base_url or "https://api.openai.com/v1"
        )
        self._client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=30.0)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def is_available(self) -> bool:
        return bool(self._client and len(self.api_key.strip()) > 10)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        start_t = time.perf_counter()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        duration_ms = (time.perf_counter() - start_t) * 1000
        content = response.choices[0].message.content or ""
        usage = response.usage

        return AIResponse(
            provider="openai",
            model=self.model,
            content=content,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
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
        start_t = time.perf_counter()
        sys_p = (system_prompt or "You are an analytical AI editorial assistant. Output valid JSON only.")
        messages = [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": prompt}
        ]

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=max_tokens
        )
        duration_ms = (time.perf_counter() - start_t) * 1000
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)
        usage = response.usage

        return AIResponse(
            provider="openai",
            model=self.model,
            content=raw_content,
            parsed_json=parsed,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            duration_ms=round(duration_ms, 2)
        )

    async def check_health(self) -> Dict[str, Any]:
        start_t = time.perf_counter()
        try:
            models = await self._client.models.list()
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "connected",
                "provider": "openai",
                "model": self.model,
                "latency_ms": round(duration_ms, 2),
                "is_model_available": True
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "error",
                "provider": "openai",
                "error": str(e),
                "latency_ms": round(duration_ms, 2)
            }
