from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class AIResponse(BaseModel):
    provider: str
    model: str
    content: str
    parsed_json: Optional[Dict[str, Any]] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: float = 0.0
    is_fallback: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseAIProvider(ABC):
    """
    Abstract base class for all AI provider adapters (Groq, OpenAI, Anthropic, Gemini, Fallback).
    Guarantees standard execution interface across all editorial and research operations.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or ""
        self.model = model or ""
        self.base_url = base_url

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier of the provider."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Returns True if the provider has valid credentials and is reachable."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        """Generates plain text response."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs
    ) -> AIResponse:
        """Generates validated structured JSON output."""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Performs live ping/verification against provider API."""
        pass
