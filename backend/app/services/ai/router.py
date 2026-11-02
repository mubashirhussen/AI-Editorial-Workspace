import asyncio
import logging
import random
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.encryption import decrypt_secret
from backend.app.models.base import AiProviderConfig, ProviderUsageRecord
from backend.app.services.monitoring_service import monitoring_service
from backend.app.services.ai.base import BaseAIProvider, AIResponse
from backend.app.services.ai.adapters.groq_adapter import GroqAdapter
from backend.app.services.ai.adapters.openai_adapter import OpenAIAdapter
from backend.app.services.ai.adapters.anthropic_adapter import AnthropicAdapter
from backend.app.services.ai.adapters.gemini_adapter import GeminiAdapter
from backend.app.services.ai.adapters.fallback_adapter import FallbackAdapter

logger = logging.getLogger("editorial_workspace.ai.router")

class AIRouter:
    """
    Intelligent AI Provider Router supporting dynamic provider selection,
    credential encryption, bounded exponential retries, and usage accounting.
    """

    def __init__(self):
        self.fallback_adapter = FallbackAdapter()

    def get_adapter(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ) -> BaseAIProvider:
        """
        Resolves the appropriate AI provider adapter based on database configs,
        environment variables, and requested preferences.
        """
        prov_name = (provider or settings.DEFAULT_AI_PROVIDER).lower()
        key = None
        custom_model = model

        # 1. Check database for organization-specific or global provider config
        if db:
            query = db.query(AiProviderConfig).filter(
                AiProviderConfig.is_active == True
            )
            if organization_id:
                query = query.filter(AiProviderConfig.organization_id == organization_id)
            if provider:
                query = query.filter(AiProviderConfig.provider == prov_name)
            
            db_config = query.order_by(AiProviderConfig.is_default.desc()).first()
            if db_config:
                prov_name = db_config.provider.lower()
                custom_model = custom_model or db_config.model_name
                if db_config.encrypted_api_key:
                    key = decrypt_secret(db_config.encrypted_api_key)

        # 2. Fall back to environment credentials
        if not key:
            if prov_name == "groq":
                key = settings.GROQ_API_KEY
                custom_model = custom_model or settings.DEFAULT_AI_MODEL
            elif prov_name == "openai":
                key = settings.OPENAI_API_KEY or settings.AI_API_KEY
                custom_model = custom_model or settings.AI_MODEL
            elif prov_name == "anthropic":
                key = settings.ANTHROPIC_API_KEY
                custom_model = custom_model or "claude-3-5-sonnet-latest"
            elif prov_name in ("google_gemini", "gemini"):
                key = settings.GOOGLE_AI_API_KEY
                custom_model = custom_model or "gemini-1.5-flash"
                prov_name = "google_gemini"

        # 3. Instantiate corresponding adapter
        if prov_name == "groq" and key:
            return GroqAdapter(api_key=key, model=custom_model)
        elif prov_name == "openai" and key:
            return OpenAIAdapter(api_key=key, model=custom_model, base_url=settings.AI_BASE_URL)
        elif prov_name == "anthropic" and key:
            return AnthropicAdapter(api_key=key, model=custom_model)
        elif prov_name in ("google_gemini", "gemini") and key:
            return GeminiAdapter(api_key=key, model=custom_model)

        # 4. If requested provider key is unavailable, check if Groq has an env key
        if settings.GROQ_API_KEY:
            return GroqAdapter(api_key=settings.GROQ_API_KEY, model=settings.DEFAULT_AI_MODEL)
        elif settings.OPENAI_API_KEY or settings.AI_API_KEY:
            return OpenAIAdapter(api_key=settings.OPENAI_API_KEY or settings.AI_API_KEY, model=settings.AI_MODEL)

        # 5. Deterministic offline engine fallback
        return self.fallback_adapter

    async def execute_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation_name: str = "structured_synthesis",
        db: Optional[Session] = None,
        organization_id: Optional[str] = None,
        max_retries: int = 2
    ) -> AIResponse:
        adapter = self.get_adapter(provider, model, db=db, organization_id=organization_id)
        last_error = None

        # Execute with bounded exponential backoff
        for attempt in range(max_retries + 1):
            try:
                res = await adapter.generate_structured(prompt, system_prompt=system_prompt, schema=schema)
                # Record successful usage
                self._record_telemetry(res, operation_name, status="success", db=db, organization_id=organization_id)
                return res
            except Exception as e:
                last_error = e
                logger.warning(f"AI Provider '{adapter.provider_name}' attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    # Bounded jitter backoff (0.5s - 1.5s)
                    backoff = (0.5 * (2 ** attempt)) + random.uniform(0.1, 0.4)
                    await asyncio.sleep(backoff)

        # Fallback on failure
        logger.warning(f"All {max_retries + 1} attempts failed on '{adapter.provider_name}'. Triggering deterministic fallback engine.")
        res = await self.fallback_adapter.generate_structured(prompt, system_prompt=system_prompt, schema=schema)
        self._record_telemetry(res, operation_name, status="fallback", provider_error=str(last_error), db=db, organization_id=organization_id)
        return res

    async def execute_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation_name: str = "text_generation",
        db: Optional[Session] = None,
        organization_id: Optional[str] = None,
        max_retries: int = 2
    ) -> AIResponse:
        adapter = self.get_adapter(provider, model, db=db, organization_id=organization_id)
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                res = await adapter.generate_text(prompt, system_prompt=system_prompt)
                self._record_telemetry(res, operation_name, status="success", db=db, organization_id=organization_id)
                return res
            except Exception as e:
                last_error = e
                logger.warning(f"AI Provider '{adapter.provider_name}' attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    backoff = (0.5 * (2 ** attempt)) + random.uniform(0.1, 0.4)
                    await asyncio.sleep(backoff)

        res = await self.fallback_adapter.generate_text(prompt, system_prompt=system_prompt)
        self._record_telemetry(res, operation_name, status="fallback", provider_error=str(last_error), db=db, organization_id=organization_id)
        return res

    def _record_telemetry(
        self,
        res: AIResponse,
        operation: str,
        status: str,
        provider_error: Optional[str] = None,
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ):
        # 1. In-memory monitoring
        monitoring_service.record_ai_operation(
            operation_type=operation,
            duration_ms=res.duration_ms,
            status=status,
            provider_error=provider_error,
            prompt_tokens=res.prompt_tokens,
            completion_tokens=res.completion_tokens
        )

        # 2. Database persistent accounting (if Session is provided)
        if db:
            try:
                record = ProviderUsageRecord(
                    organization_id=organization_id,
                    provider=res.provider,
                    model=res.model,
                    operation=operation,
                    prompt_tokens=res.prompt_tokens,
                    completion_tokens=res.completion_tokens,
                    total_tokens=res.total_tokens,
                    duration_ms=res.duration_ms,
                    status=status,
                    error_message=provider_error
                )
                db.add(record)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to record provider usage to DB: {e}")
                db.rollback()

ai_router = AIRouter()

