from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ConnectionCreate(BaseModel):
    provider: str = Field(..., description="Provider name: groq, openai, anthropic, google_gemini")
    name: str = Field(..., max_length=255)
    api_key: str = Field(..., min_length=1, description="API credential secret")
    model: Optional[str] = None
    is_default: bool = False

class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class ConnectionRotate(BaseModel):
    new_api_key: str = Field(..., min_length=1, description="New secret to replace existing credential")

class ConnectionResponse(BaseModel):
    id: str
    provider: str
    name: str
    status: str
    model: str
    masked_key: str
    is_active: bool
    is_default: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime

class AIHealthResponse(BaseModel):
    status: str  # operational, deterministic_fallback, error
    active_provider: str
    active_model: str
    total_configured_connections: int
    providers: List[Dict[str, Any]]
    telemetry_summary: Dict[str, Any]

class UsageSummaryResponse(BaseModel):
    total_calls: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    active_connections_count: int
    by_provider: Dict[str, Dict[str, Any]]
    by_operation: Dict[str, int]

