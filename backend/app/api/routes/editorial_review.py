"""
Editorial Review & Workflow Endpoints.
Provides API routes for human-in-the-loop editorial review, comments,
revisions, approvals, and workflow dashboard statistics.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import EditorialOutput, EditorialReview, EditorialComment, User
from backend.app.schemas.auth import OrgPermission
from backend.app.api.deps import get_current_user
from backend.app.api.v1.endpoints.projects import check_project_tenant_access
from backend.app.schemas.editorial_review import (
    EditorialReviewCreate,
    EditorialReviewResponse,
    EditorialCommentCreate,
    EditorialCommentUpdate,
    EditorialCommentResponse,
    EditorialChangeRequest,
    EditorialApproveRequest,
    EditorialFinalizeRequest,
    EditorialRevisionUpdate,
    EditorialDashboardStats,
    WorkflowStatus
)
from backend.app.services.editorial.review_workflow_service import review_workflow_service

router = APIRouter(prefix="/editorial", tags=["Editorial Workflow & Review"])

# =====================================================================
# 1. DASHBOARD STATS
# =====================================================================
@router.get("/dashboard/stats", response_model=EditorialDashboardStats)
def get_editorial_dashboard_stats(db: Session = Depends(get_db)):
    """Fetches real database-backed editorial workflow statistics."""
    return review_workflow_service.get_dashboard_stats(db)

# =====================================================================
# 2. AI PRE-REVIEW & WORKFLOW SUBMISSION
# =====================================================================
@router.post("/{editorial_id}/ai-review")
def run_ai_review(editorial_id: str, db: Session = Depends(get_db)):
    """
    Executes automated quality checks (word count, writing quality, missing sections,
    sources, uncertainties) before human review.
    Does NOT approve or finalize content.
    """
    return review_workflow_service.run_ai_pre_review(db, editorial_id)

@router.post("/{editorial_id}/submit-review")
def submit_editorial_for_review(editorial_id: str, db: Session = Depends(get_db)):
    """Submits an editorial for human review, moving status to HUMAN_REVIEW_PENDING."""
    editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial not found.")
    
    updated = review_workflow_service.transition_editorial_status(
        db=db,
        editorial=editorial,
        new_status=WorkflowStatus.HUMAN_REVIEW_PENDING,
        reviewer_name="Workflow Submitter",
        notes="Submitted for human editorial review."
    )
    return {"message": "Editorial submitted for human review.", "status": updated.status}

# =====================================================================
# 3. REVIEWS & COMMENTS
# =====================================================================
@router.get("/{editorial_id}/reviews", response_model=List[EditorialReviewResponse])
def get_editorial_reviews(editorial_id: str, db: Session = Depends(get_db)):
    """Fetches complete review audit history and comments for an editorial."""
    reviews = (
        db.query(EditorialReview)
        .filter(EditorialReview.editorial_id == editorial_id)
        .order_by(EditorialReview.created_at.desc())
        .all()
    )
    return reviews

@router.post("/{editorial_id}/reviews", response_model=EditorialReviewResponse)
def create_editorial_review(
    editorial_id: str,
    req: EditorialReviewCreate,
    db: Session = Depends(get_db)
):
    """Creates a new human review record and applies any attached comments."""
    editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial not found.")

    review = EditorialReview(
        editorial_id=editorial_id,
        reviewer_name=req.reviewer_name,
        review_status=req.review_status,
        overall_feedback=req.overall_feedback,
        reviewed_at=review_workflow_service.transition_editorial_status.__globals__['utc_now']()
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    for c in (req.comments or []):
        comm = EditorialComment(
            review_id=review.id,
            section_reference=c.section_reference,
            original_text=c.original_text,
            comment=c.comment,
            suggested_revision=c.suggested_revision,
            resolution_status="open"
        )
        db.add(comm)

    db.commit()
    db.refresh(review)
    return review

@router.post("/reviews/{review_id}/comments", response_model=EditorialCommentResponse)
def add_review_comment(
    review_id: str,
    req: EditorialCommentCreate,
    db: Session = Depends(get_db)
):
    """Adds a targeted comment or suggested revision to an existing review."""
    return review_workflow_service.add_comment(db, review_id, req)

@router.patch("/comments/{comment_id}", response_model=EditorialCommentResponse)
def update_comment_resolution(
    comment_id: str,
    req: EditorialCommentUpdate,
    db: Session = Depends(get_db)
):
    """Updates a comment's resolution status (open -> resolved / rejected) or text."""
    return review_workflow_service.update_comment(db, comment_id, req)

# =====================================================================
# 4. LIFECYCLE ACTIONS (REQUEST CHANGES, APPROVE, FINALIZE)
# =====================================================================
@router.post("/{editorial_id}/request-changes")
def request_editorial_changes(
    editorial_id: str,
    req: EditorialChangeRequest,
    db: Session = Depends(get_db)
):
    """Requests revisions on an editorial. Requires meaningful, constructive feedback."""
    updated = review_workflow_service.request_changes(db, editorial_id, req)
    return {
        "message": "Changes requested successfully.",
        "status": updated.status,
        "reviewer": req.reviewer_name
    }

@router.post("/{editorial_id}/approve")
def approve_editorial(
    editorial_id: str,
    req: EditorialApproveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Human editor approves the editorial. Required before finalization (enforces APPROVE_EDITORIALS)."""
    editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial not found.")
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.APPROVE_EDITORIALS)

    updated = review_workflow_service.approve_editorial(db, editorial_id, req)
    return {
        "message": "Editorial approved successfully.",
        "status": updated.status,
        "reviewer": req.reviewer_name
    }

@router.post("/{editorial_id}/finalize")
def finalize_editorial(
    editorial_id: str,
    req: EditorialFinalizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalizes an approved editorial and locks it from further modifications.
    Rejects unapproved editorials (enforces APPROVE_EDITORIALS).
    """
    editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial not found.")
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.APPROVE_EDITORIALS)

    updated = review_workflow_service.finalize_editorial(db, editorial_id, req)
    return {
        "message": "Editorial finalized and locked.",
        "status": updated.status,
        "finalized_by": req.finalized_by
    }

# =====================================================================
# 5. REVISION MANAGEMENT & DIFFS
# =====================================================================
@router.put("/{editorial_id}/revision")
def update_editorial_revision(
    editorial_id: str,
    req: EditorialRevisionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Applies text revisions, preserving original generated content and returning
    version diff details (enforces EDIT_DRAFTS).
    """
    editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
    if not editorial:
        raise HTTPException(status_code=404, detail="Editorial not found.")
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.EDIT_DRAFTS)

    updated, diff_summary = review_workflow_service.update_editorial_revision(db, editorial_id, req)
    return {
        "editorial_id": updated.id,
        "headline": updated.headline,
        "version": updated.version,
        "word_count": updated.word_count,
        "status": updated.status,
        "diff_summary": diff_summary
    }

