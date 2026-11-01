from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class WritingIssue(BaseModel):
    id: str
    category: str
    severity: str = "medium"
    original_text: str
    explanation: str
    suggested_rewrite: str
    reason: Optional[str] = ""
    confidence: float = 0.9
    status: str = "pending"

class WritingMetrics(BaseModel):
    word_count: int = 0
    character_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    average_sentence_length: float = 0.0
    reading_time_minutes: float = 0.0
    readability_score: Optional[float] = None
    readability_grade: Optional[str] = "Standard"
    readability_note: Optional[str] = "Readability scores are diagnostic scanning indicators, not definitive measures of technical nuance or writing quality."

class WritingAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=500_000)
    title: Optional[str] = Field("Draft Article", max_length=255)
    draft_id: Optional[str] = None
    project_id: Optional[str] = None

class WritingAnalysisResponse(BaseModel):
    draft_id: Optional[str] = None
    overall_feedback: str
    issues: List[WritingIssue] = Field(default_factory=list)
    metrics: WritingMetrics

    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()

class DraftCreate(BaseModel):
    title: str = Field("Draft Article", max_length=255)
    original_content: str = Field(..., min_length=1, max_length=500_000)
    project_id: Optional[str] = None

class DraftUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    revised_content: Optional[str] = Field(None, max_length=500_000)
    final_content: Optional[str] = Field(None, max_length=500_000)
    status: Optional[str] = Field(None, max_length=50)

class SuggestionAction(BaseModel):
    suggestion_id: str
    action: Literal["accept", "reject"]

class DraftResponse(BaseModel):
    id: str
    project_id: Optional[str] = None
    title: str
    original_content: str
    revised_content: str
    final_content: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    suggestions: List[WritingIssue] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# Explicit Aliases for Phase 2 specification
WritingDraftCreate = DraftCreate
WritingDraftUpdate = DraftUpdate
WritingDraftResponse = DraftResponse
WritingSuggestionResponse = WritingIssue

class DraftCompareResponse(BaseModel):
    draft_id: str
    original_content: str
    revised_content: str
    word_count_diff: int
    readability_diff: float
    total_suggestions: int
    accepted_count: int
    rejected_count: int
    pending_count: int
