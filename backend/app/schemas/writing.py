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
    flesch_kincaid_grade: Optional[float] = None
    automated_readability_index: Optional[float] = None
    gunning_fog_index: Optional[float] = None
    grounding_score: Optional[float] = None
    unsupported_claims_count: Optional[int] = 0
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
    original_content: Optional[str] = Field(None, max_length=500_000)
    content: Optional[str] = Field(None, max_length=500_000)
    project_id: Optional[str] = None
    brief_id: Optional[str] = None
    content_type: Optional[str] = "editorial_analysis"
    target_audience: Optional[str] = "Founders, builders, and operators"
    tone: Optional[str] = "Authoritative, analytical, objective"
    desired_length: Optional[int] = 800
    style_profile_id: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.original_content and self.content:
            self.original_content = self.content
        elif not self.content and self.original_content:
            self.content = self.original_content
        if not self.original_content:
            raise ValueError("Draft must contain content.")

class DraftUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, max_length=500_000)
    revised_content: Optional[str] = Field(None, max_length=500_000)
    final_content: Optional[str] = Field(None, max_length=500_000)
    status: Optional[str] = Field(None, max_length=50)
    content_type: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    desired_length: Optional[int] = None
    style_profile_id: Optional[str] = None
    applied_issue_ids: Optional[List[str]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.revised_content and self.content:
            self.revised_content = self.content
        elif not self.content and self.revised_content:
            self.content = self.revised_content

class SuggestionAction(BaseModel):
    suggestion_id: str
    action: Literal["accept", "reject"]

class DraftVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    draft_id: str
    version_number: int
    content: str
    created_at: datetime
    description: Optional[str] = None

class DraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    brief_id: Optional[str] = None
    title: str
    content_type: Optional[str] = "editorial_analysis"
    target_audience: Optional[str] = "Founders, builders, and operators"
    tone: Optional[str] = "Authoritative, analytical, objective"
    desired_length: Optional[int] = 800
    original_content: str
    revised_content: Optional[str] = ""
    current_content: Optional[str] = ""
    final_content: Optional[str] = None
    word_count: Optional[int] = 0
    readability_score: Optional[float] = None
    research_grounding_score: Optional[float] = None
    unsupported_claims_count: Optional[int] = 0
    style_profile_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    suggestions: List[WritingIssue] = Field(default_factory=list)
    versions: Optional[List[DraftVersionResponse]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.current_content and self.revised_content:
            self.current_content = self.revised_content
        elif not self.revised_content and self.current_content:
            self.revised_content = self.current_content

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

# --- Phase 7 Editorial Intelligence Schemas ---

EditorialContentType = Literal[
    "news",
    "technology",
    "ai_industry_update",
    "editorial_analysis",
    "explainer",
    "research_report",
    "opinion",
    "summary"
]

class DraftGenerateRequest(BaseModel):
    topic: Optional[str] = None
    project_id: Optional[str] = None
    brief_id: Optional[str] = None
    content_type: str = "editorial_analysis"
    target_audience: str = "Founders, builders, and operators"
    tone: str = "Authoritative, analytical, objective"
    style_profile_id: Optional[str] = None
    desired_length: int = Field(800, ge=100, le=5000)
    keywords: Optional[List[str]] = Field(default_factory=list)
    editorial_instructions: Optional[str] = None

class DraftSection(BaseModel):
    heading: str
    content: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)

class DraftGenerateResponse(BaseModel):
    draft_id: str
    title: str
    headline: str
    subtitle: str
    content: str
    content_type: str
    word_count: int
    sections: List[DraftSection] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)
    evidence_citations: List[Dict[str, Any]] = Field(default_factory=list)
    unsupported_claims_warning: List[str] = Field(default_factory=list)
    grounding_score: float = 100.0

SelectionRewriteOperation = Literal[
    "improve_clarity",
    "improve_readability",
    "correct_grammar",
    "fix_spelling",
    "rewrite_selection",
    "simplify_complex_sentences",
    "improve_transitions",
    "remove_repetitive_content",
    "strengthen_headline",
    "generate_intros",
    "generate_conclusions",
    "adjust_tone",
    "expand_content",
    "shorten_content"
]

class SelectionRewriteRequest(BaseModel):
    draft_id: Optional[str] = None
    selected_text: str = Field(..., min_length=1, max_length=100_000)
    operation: SelectionRewriteOperation
    surrounding_context: Optional[str] = None
    target_tone: Optional[str] = None
    style_profile_id: Optional[str] = None
    custom_instructions: Optional[str] = None

class SelectionRewriteResponse(BaseModel):
    operation: str
    original_text: str
    rewritten_text: str
    explanation: str
    diff_summary: Optional[str] = None

class ClaimVerification(BaseModel):
    claim_text: str
    classification: Literal["grounded", "inferred", "unsupported", "contradictory"]
    supporting_excerpt: Optional[str] = None
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    confidence: float = 0.9
    warning: Optional[str] = None

class ResearchGroundingAuditResponse(BaseModel):
    draft_id: str
    grounding_score: float
    total_claims: int
    grounded_count: int
    inferred_count: int
    unsupported_count: int
    contradiction_count: int
    claims: List[ClaimVerification] = Field(default_factory=list)
    actionable_recommendations: List[str] = Field(default_factory=list)

class DraftExportResponse(BaseModel):
    format: str
    filename: str
    content: Optional[str] = None
    mime_type: str
    size_bytes: int
