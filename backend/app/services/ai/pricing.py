"""
AI Provider Model Pricing & Cost Estimation Module.
Provides configurable, updatable per-token pricing tables for cost management.
"""

from typing import Dict, Any, Tuple

# Default pricing rates in USD per 1,000,000 tokens (input_cost, output_cost)
DEFAULT_PRICING_RATES: Dict[str, Tuple[float, float]] = {
    # Groq LPU Models
    "groq:llama-3.3-70b-versatile": (0.59, 0.79),
    "groq:llama-3.1-8b-instant": (0.05, 0.08),
    "groq:openai/gpt-oss-20b": (0.59, 0.79),
    "groq:default": (0.59, 0.79),

    # OpenAI Models
    "openai:gpt-4o-mini": (0.15, 0.60),
    "openai:gpt-4o": (2.50, 10.00),
    "openai:gpt-4-turbo": (10.00, 30.00),
    "openai:default": (0.15, 0.60),

    # Anthropic Claude Models
    "anthropic:claude-3-5-sonnet-latest": (3.00, 15.00),
    "anthropic:claude-3-5-haiku-latest": (0.80, 4.00),
    "anthropic:default": (3.00, 15.00),

    # Google Gemini Models
    "google_gemini:gemini-1.5-flash": (0.075, 0.30),
    "google_gemini:gemini-1.5-pro": (1.25, 5.00),
    "google_gemini:default": (0.075, 0.30),

    # Fallback / Mock
    "fallback:deterministic": (0.0, 0.0),
    "fallback:default": (0.0, 0.0),
}

def calculate_estimated_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int
) -> float:
    """
    Computes estimated cost in USD based on model token counts.
    Never returns negative values.
    """
    if prompt_tokens <= 0 and completion_tokens <= 0:
        return 0.0

    prov = (provider or "fallback").lower().strip()
    mod = (model or "default").lower().strip()

    # Exact match: "provider:model"
    key = f"{prov}:{mod}"
    if key in DEFAULT_PRICING_RATES:
        in_rate, out_rate = DEFAULT_PRICING_RATES[key]
    else:
        # Fallback to provider default
        fallback_key = f"{prov}:default"
        in_rate, out_rate = DEFAULT_PRICING_RATES.get(fallback_key, (0.20, 0.80))

    cost = ((prompt_tokens / 1_000_000.0) * in_rate) + ((completion_tokens / 1_000_000.0) * out_rate)
    return round(max(0.0, cost), 6)
