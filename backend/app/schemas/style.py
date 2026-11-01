from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class StyleProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    publication_name: str = Field(default="This Week in AI", max_length=255)
    tone: str = Field(default="Authoritative, analytical, objective", max_length=100)
    target_audience: str = Field(default="Founders, builders, and operators", max_length=255)
    max_sentence_length: int = Field(default=25, ge=10, le=60)
    preferred_sentence_length: int = Field(default=18, ge=8, le=35)
    max_paragraph_length: int = Field(default=75, ge=20, le=250)
    target_flesch_score: float = Field(default=65.0, ge=0.0, le=100.0)
    preferred_terminology: Dict[str, str] = Field(default_factory=dict)
    words_to_avoid: List[str] = Field(default_factory=list)
    headline_style: str = Field(default="Direct, analytical, hook-driven", max_length=100)
    formatting_preferences: Dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

class StyleProfileCreate(StyleProfileBase):
    pass

class StyleProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    publication_name: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    max_sentence_length: Optional[int] = None
    preferred_sentence_length: Optional[int] = None
    max_paragraph_length: Optional[int] = None
    target_flesch_score: Optional[float] = None
    preferred_terminology: Optional[Dict[str, str]] = None
    words_to_avoid: Optional[List[str]] = None
    headline_style: Optional[str] = None
    formatting_preferences: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

class StyleProfileResponse(StyleProfileBase):
    id: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StyleSuggestionItem(BaseModel):
    id: Optional[str] = None
    original_text: str
    suggested_rewrite: str
    explanation: str
    category: str  # style_sentence_length, style_avoided_phrase, style_terminology, style_promotional_hype, style_tone
    style_rule: str
    severity: str = "medium"  # high, medium, low
    confidence: float = 0.9
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    status: str = "PENDING"

class StyleCheckRequest(BaseModel):
    style_profile_id: Optional[str] = None
    content: Optional[str] = None

class StyleCheckResponse(BaseModel):
    draft_id: Optional[str] = None
    style_profile_id: str
    style_profile_name: str
    style_score: float
    metrics: Dict[str, Any]
    qualitative_feedback: str
    tone_detected: str
    terminology_deviations_count: int
    avoided_words_count: int
    suggestions: List[StyleSuggestionItem]

