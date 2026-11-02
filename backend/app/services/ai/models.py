from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ModelMetadata(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    context_window: int
    max_output_tokens: int
    capabilities: List[str]  # "text", "structured_json", "summarization", "rewrite", "editorial_analysis", "embeddings"
    is_default: bool = False
    is_available: bool = True
    input_cost_per_million: Optional[float] = None
    output_cost_per_million: Optional[float] = None

class ProviderMetadata(BaseModel):
    id: str
    name: str
    description: str
    website: str
    docs_url: str
    auth_header_type: str  # "Bearer", "x-api-key", "query_param"
    default_model: str
    models: List[ModelMetadata]

MODEL_REGISTRY: Dict[str, ProviderMetadata] = {
    "groq": ProviderMetadata(
        id="groq",
        name="Groq LPU Inference",
        description="Ultra-low latency inference engine powered by custom LPU hardware.",
        website="https://groq.com",
        docs_url="https://console.groq.com/docs",
        auth_header_type="Bearer",
        default_model="openai/gpt-oss-20b",
        models=[
            ModelMetadata(
                id="openai/gpt-oss-20b",
                name="GPT-OSS 20B (Groq LPU)",
                provider="groq",
                description="High-speed open-weights reasoning model optimized for sub-second editorial generation.",
                context_window=32768,
                max_output_tokens=4096,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                is_default=True,
                input_cost_per_million=0.0,
                output_cost_per_million=0.0
            ),
            ModelMetadata(
                id="openai/gpt-oss-120b",
                name="GPT-OSS 120B (Groq LPU)",
                provider="groq",
                description="Frontier scale open-weights architecture for deep multi-document research synthesis.",
                context_window=65536,
                max_output_tokens=8192,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                input_cost_per_million=0.15,
                output_cost_per_million=0.60
            ),
            ModelMetadata(
                id="qwen/qwen3.8-27b",
                name="Qwen 3.8 27B (Groq LPU)",
                provider="groq",
                description="Dense high-reasoning model optimized for editorial fact checking.",
                context_window=32768,
                max_output_tokens=4096,
                capabilities=["text", "structured_json", "summarization", "rewrite"],
                input_cost_per_million=0.05,
                output_cost_per_million=0.10
            )
        ]
    ),
    "openai": ProviderMetadata(
        id="openai",
        name="OpenAI",
        description="Industry standard generative models from OpenAI.",
        website="https://openai.com",
        docs_url="https://platform.openai.com/docs",
        auth_header_type="Bearer",
        default_model="gpt-4o-mini",
        models=[
            ModelMetadata(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description="Fast, cost-efficient model for real-time editorial checks and structured synthesis.",
                context_window=128000,
                max_output_tokens=16384,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                is_default=True,
                input_cost_per_million=0.15,
                output_cost_per_million=0.60
            ),
            ModelMetadata(
                id="gpt-4o",
                name="GPT-4o Omnimodal",
                provider="openai",
                description="Flagship multimodal model for complex technical synthesis.",
                context_window=128000,
                max_output_tokens=4096,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                input_cost_per_million=2.50,
                output_cost_per_million=10.00
            ),
            ModelMetadata(
                id="text-embedding-3-small",
                name="Text Embedding 3 Small",
                provider="openai",
                description="Vector representation model for semantic research claim matching.",
                context_window=8191,
                max_output_tokens=0,
                capabilities=["embeddings"],
                input_cost_per_million=0.02,
                output_cost_per_million=0.0
            )
        ]
    ),
    "anthropic": ProviderMetadata(
        id="anthropic",
        name="Anthropic Claude",
        description="Safety-aligned reasoning and long-context analysis models.",
        website="https://anthropic.com",
        docs_url="https://docs.anthropic.com",
        auth_header_type="x-api-key",
        default_model="claude-3-5-sonnet-latest",
        models=[
            ModelMetadata(
                id="claude-3-5-sonnet-latest",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                description="Industry-leading writing and nuanced editorial critique model.",
                context_window=200000,
                max_output_tokens=8192,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                is_default=True,
                input_cost_per_million=3.00,
                output_cost_per_million=15.00
            ),
            ModelMetadata(
                id="claude-3-5-haiku-latest",
                name="Claude 3.5 Haiku",
                provider="anthropic",
                description="Lightweight and rapid drafting assistant.",
                context_window=200000,
                max_output_tokens=4096,
                capabilities=["text", "structured_json", "summarization", "rewrite"],
                input_cost_per_million=0.80,
                output_cost_per_million=4.00
            )
        ]
    ),
    "google_gemini": ProviderMetadata(
        id="google_gemini",
        name="Google Gemini",
        description="Google's multimodal Gemini models with massive context windows.",
        website="https://ai.google.dev",
        docs_url="https://ai.google.dev/docs",
        auth_header_type="Bearer",
        default_model="gemini-1.5-flash",
        models=[
            ModelMetadata(
                id="gemini-1.5-flash",
                name="Gemini 1.5 Flash",
                provider="google_gemini",
                description="High-throughput, low-latency analysis model with 1M context.",
                context_window=1000000,
                max_output_tokens=8192,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                is_default=True,
                input_cost_per_million=0.075,
                output_cost_per_million=0.30
            ),
            ModelMetadata(
                id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                provider="google_gemini",
                description="Deep reasoning model with up to 2 million tokens of context.",
                context_window=2000000,
                max_output_tokens=8192,
                capabilities=["text", "structured_json", "summarization", "rewrite", "editorial_analysis"],
                input_cost_per_million=1.25,
                output_cost_per_million=5.00
            )
        ]
    )
}

def get_all_providers() -> List[Dict[str, Any]]:
    return [p.model_dump() for p in MODEL_REGISTRY.values()]

def get_all_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    if provider:
        p = MODEL_REGISTRY.get(provider.lower())
        return [m.model_dump() for m in p.models] if p else []
    all_m = []
    for p in MODEL_REGISTRY.values():
        all_m.extend([m.model_dump() for m in p.models])
    return all_m

def get_default_model(provider: str) -> Optional[str]:
    p = MODEL_REGISTRY.get(provider.lower())
    return p.default_model if p else None
