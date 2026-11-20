from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Literal
from datetime import datetime

FeedbackCategory = Literal[
    "bug_report",
    "feature_request",
    "ux_improvement",
    "ai_output_quality",
    "research_accuracy",
    "citation_issue",
    "writing_quality",
    "editorial_workflow",
    "general"
]

FeedbackSeverity = Literal["low", "medium", "high", "critical"]

FeedbackStatus = Literal["NEW", "TRIAGED", "IN_PROGRESS", "RESOLVED", "CLOSED", "REJECTED"]

class FeedbackCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Brief summary of feedback or issue")
    description: str = Field(..., min_length=10, max_length=10000, description="Detailed explanation, steps to reproduce, or suggestion")
    category: FeedbackCategory = Field("general", description="Feedback classification")
    severity: FeedbackSeverity = Field("medium", description="Perceived urgency / severity")
    module_reference: Optional[str] = Field(None, max_length=100, description="Subsystem (e.g. research, writing, editorial, dashboard)")

class FeedbackUpdateRequest(BaseModel):
    status: Optional[FeedbackStatus] = Field(None, description="Triage status update")
    admin_notes: Optional[str] = Field(None, max_length=5000, description="Internal notes from triage team")
    assigned_to: Optional[str] = Field(None, max_length=255, description="Assignee email or name")
    resolution_summary: Optional[str] = Field(None, max_length=5000, description="Summary of resolution or fix implemented")

class FeedbackResponse(BaseModel):
    id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    title: str
    description: str
    category: str
    severity: str
    module_reference: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FeedbackListResponse(BaseModel):
    total: int
    items: List[FeedbackResponse]

class FeedbackSummaryResponse(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
