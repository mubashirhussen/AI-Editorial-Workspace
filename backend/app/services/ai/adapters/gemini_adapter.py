import json
import time
import logging
import httpx
from typing import Dict, Any, Optional
from backend.app.services.ai.base import BaseAIProvider, AIResponse

logger = logging.getLogger("editorial_workspace.ai.gemini")

class GeminiAdapter(BaseAIProvider):
    """
    Adapter for Google Gemini REST API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or "",
            model=model or "gemini-1.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta"
        )

    @property
    def provider_name(self) -> str:
        return "google_gemini"

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
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        duration_ms = (time.perf_counter() - start_t) * 1000
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)

        return AIResponse(
            provider="google_gemini",
            model=self.model,
            content=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
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
        sys_p = (system_prompt or "") + "\nRespond with valid JSON object only."
        res = await self.generate_text(prompt, system_prompt=sys_p, temperature=temperature, max_tokens=max_tokens)
        try:
            clean = res.content.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.endswith("```"):
                clean = clean[:-3]
            res.parsed_json = json.loads(clean.strip())
        except Exception as e:
            logger.warning(f"Failed to parse Gemini JSON: {e}")
            res.parsed_json = {"error": "Invalid JSON returned", "raw": res.content}
        return res

    async def check_health(self) -> Dict[str, Any]:
        start_t = time.perf_counter()
        if not self.api_key:
            return {"status": "unconfigured", "provider": "google_gemini"}
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "connected",
                "provider": "google_gemini",
                "model": self.model,
                "latency_ms": round(duration_ms, 2)
            }
        except Exception as e:
            duration_ms = (time.perf_counter() - start_t) * 1000
            return {
                "status": "error",
                "provider": "google_gemini",
                "error": str(e),
                "latency_ms": round(duration_ms, 2)
            }

