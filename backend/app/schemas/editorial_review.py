"""
Editorial Review & Workflow Schemas.
Enforces lifecycle status transitions and validation rules for human-in-the-loop review.
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# =====================================================================
# 1. WORKFLOW LIFECYCLE STATUSES & TRANSITIONS
# =====================================================================
class WorkflowStatus:
    RESEARCH_IN_PROGRESS = "RESEARCH_IN_PROGRESS"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    DRAFT_CREATED = "DRAFT_CREATED"
    DRAFT = "DRAFT"  # Alias for backward compatibility
    AI_REVIEW_COMPLETED = "AI_REVIEW_COMPLETED"
    HUMAN_REVIEW_PENDING = "HUMAN_REVIEW_PENDING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    FINALIZED = "FINALIZED"
    ARCHIVED = "ARCHIVED"

VALID_STATUS_TRANSITIONS: Dict[str, Set[str]] = {
    WorkflowStatus.RESEARCH_IN_PROGRESS: {WorkflowStatus.RESEARCH_COMPLETED, WorkflowStatus.ARCHIVED},
    WorkflowStatus.RESEARCH_COMPLETED: {WorkflowStatus.DRAFT_CREATED, WorkflowStatus.DRAFT, "draft", WorkflowStatus.ARCHIVED},
    WorkflowStatus.DRAFT_CREATED: {WorkflowStatus.AI_REVIEW_COMPLETED, WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.ARCHIVED},
    WorkflowStatus.DRAFT: {WorkflowStatus.AI_REVIEW_COMPLETED, WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.ARCHIVED},
    "draft": {WorkflowStatus.AI_REVIEW_COMPLETED, WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.ARCHIVED},
    WorkflowStatus.AI_REVIEW_COMPLETED: {WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.CHANGES_REQUESTED, WorkflowStatus.ARCHIVED},
    WorkflowStatus.HUMAN_REVIEW_PENDING: {WorkflowStatus.APPROVED, WorkflowStatus.CHANGES_REQUESTED, WorkflowStatus.ARCHIVED},
    WorkflowStatus.CHANGES_REQUESTED: {WorkflowStatus.DRAFT_CREATED, WorkflowStatus.DRAFT, "draft", WorkflowStatus.AI_REVIEW_COMPLETED, WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.ARCHIVED},
    WorkflowStatus.APPROVED: {WorkflowStatus.FINALIZED, WorkflowStatus.CHANGES_REQUESTED, WorkflowStatus.ARCHIVED},
    WorkflowStatus.FINALIZED: {WorkflowStatus.ARCHIVED},  # Immutable locked state
    WorkflowStatus.ARCHIVED: {WorkflowStatus.DRAFT_CREATED, WorkflowStatus.DRAFT, "draft"}
}

def is_valid_transition(current_status: str, next_status: str) -> bool:
    """Checks whether the requested status transition is strictly allowed."""
    curr = current_status.upper() if current_status else ""
    nxt = next_status.upper() if next_status else ""
    
    # Handle alias
    if curr == "DRAFT":
        curr = WorkflowStatus.DRAFT
    
    allowed = {s.upper() for s in VALID_STATUS_TRANSITIONS.get(curr, set())}
    # Also check lowercase lookup
    if not allowed and current_status in VALID_STATUS_TRANSITIONS:
        allowed = {s.upper() for s in VALID_STATUS_TRANSITIONS[current_status]}

    return nxt in allowed

# =====================================================================
# 2. COMMENT SCHEMAS
# =====================================================================
class EditorialCommentBase(BaseModel):
    section_reference: Optional[str] = Field(None, max_length=100)
    original_text: Optional[str] = None
    comment: str = Field(..., min_length=3, max_length=5000)
    suggested_revision: Optional[str] = None

class EditorialCommentCreate(EditorialCommentBase):
    pass

class EditorialCommentUpdate(BaseModel):
    resolution_status: Optional[str] = Field(None, pattern="^(open|resolved|rejected)$")
    comment: Optional[str] = Field(None, min_length=3, max_length=5000)
    suggested_revision: Optional[str] = None

class EditorialCommentResponse(EditorialCommentBase):
    id: str
    review_id: str
    resolution_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# 3. REVIEW SCHEMAS
# =====================================================================
class EditorialReviewBase(BaseModel):
    reviewer_name: str = Field("Human Editor", min_length=2, max_length=255)
    review_status: str = Field(..., pattern="^(APPROVED|CHANGES_REQUESTED|HUMAN_REVIEW_PENDING|AI_REVIEW_COMPLETED)$")
    overall_feedback: Optional[str] = Field(None, max_length=10000)

class EditorialReviewCreate(EditorialReviewBase):
    comments: Optional[List[EditorialCommentCreate]] = []

class EditorialReviewResponse(EditorialReviewBase):
    id: str
    editorial_id: str
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comments: List[EditorialCommentResponse] = []

    model_config = ConfigDict(from_attributes=True)

# =====================================================================
# 4. ACTION REQUEST SCHEMAS
# =====================================================================
class EditorialChangeRequest(BaseModel):
    reviewer_name: str = Field("Human Editor", min_length=2, max_length=255)
    feedback: str = Field(..., min_length=10, max_length=10000, description="Constructive, meaningful feedback is required when requesting revisions.")

class EditorialApproveRequest(BaseModel):
    reviewer_name: str = Field("Human Editor", min_length=2, max_length=255)
    approval_notes: Optional[str] = Field(None, max_length=5000)

class EditorialFinalizeRequest(BaseModel):
    finalized_by: str = Field("Lead Editor", min_length=2, max_length=255)
    publication_notes: Optional[str] = Field(None, max_length=5000)

class EditorialRevisionUpdate(BaseModel):
    revised_content: str = Field(..., min_length=50, max_length=500000)
    headline: Optional[str] = Field(None, min_length=5, max_length=255)

class EditorialDashboardStats(BaseModel):
    pending_human_reviews: int
    approved_editorials: int
    changes_requested: int
    finalized_editorials: int
    total_editorials: int
    recent_activity: List[Dict[str, Any]] = []
