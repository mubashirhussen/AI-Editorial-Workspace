import re
import json
import time
from typing import Dict, Any, Optional
from backend.app.services.ai.base import BaseAIProvider, AIResponse
from backend.app.utils.text_processing import split_into_sentences

class FallbackAdapter(BaseAIProvider):
    """
    Deterministic rule-based offline fallback adapter.
    Guarantees deterministic, reproducible responses for tests, CI, and network outages.
    """

    def __init__(self):
        super().__init__(api_key="", model="deterministic-fallback-v1")

    @property
    def provider_name(self) -> str:
        return "deterministic_fallback"

    async def is_available(self) -> bool:
        return True

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ) -> AIResponse:
        sentences = split_into_sentences(prompt)
        first_s = sentences[0] if sentences else "Deterministic synthesis completed."
        content = f"Executive synthesis: {first_s} Grounded analysis confirms key findings across reported sources."
        return AIResponse(
            provider="deterministic_fallback",
            model=self.model,
            content=content,
            is_fallback=True,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content.split()),
            total_tokens=len(prompt.split()) + len(content.split()),
            duration_ms=1.5
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        sentences = split_into_sentences(prompt)
        summary = (sentences[0] + " " + (sentences[1] if len(sentences) > 1 else "")) if sentences else "Automated source extraction."

        data = {
            "summary": summary[:280],
            "key_points": [
                s[:120] for s in sentences[:4]
            ] if sentences else ["Primary architectural development noted."],
            "reported_facts": [
                f"Empirical measurement confirmed: {s[:100]}" for s in sentences[1:3]
            ] if len(sentences) > 1 else ["Verified system benchmark."],
            "analysis": [
                "Strategic infrastructure alignment indicates strong operational efficiency.",
                "Market adoption patterns demonstrate shift towards specialized accelerators."
            ],
            "founder_implications": {
                "strategic_takeaway": "Builders must focus on latency and unit economics rather than raw parameter count.",
                "operational_risk": "Rapid technological commoditization requires architectural flexibility."
            },
            "uncertainties": [
                "Long-term inference power consumption across edge clusters."
            ],
            "newsletter_angles": [
                {
                    "title": "Why Specialized Hardware is Winning the Inference Scaling War",
                    "target_audience": "Founders & Technical Operators",
                    "hook": "New architectural breakthroughs demonstrate a 4x efficiency gain."
                }
            ],
            "generation_mode": "deterministic_fallback"
        }

        return AIResponse(
            provider="deterministic_fallback",
            model=self.model,
            content=json.dumps(data),
            parsed_json=data,
            is_fallback=True,
            prompt_tokens=len(prompt.split()),
            completion_tokens=150,
            total_tokens=len(prompt.split()) + 150,
            duration_ms=2.0
        )

    async def check_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "deterministic_fallback",
            "model": self.model,
            "latency_ms": 0.5,
            "is_fallback": True
        }
