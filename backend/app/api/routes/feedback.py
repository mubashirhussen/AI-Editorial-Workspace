import logging
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.core.database import get_db
from backend.app.models.base import User, Organization, OrganizationMembership, UserFeedback
from backend.app.schemas.auth import OrgPermission, has_permission
from backend.app.schemas.feedback import (
    FeedbackCreateRequest,
    FeedbackUpdateRequest,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackSummaryResponse
)
from backend.app.api.deps import get_current_user, get_active_organization, get_current_user_optional
from backend.app.services.monitoring_service import monitoring_service

logger = logging.getLogger("editorial_workspace.feedback")

router = APIRouter(prefix="/feedback", tags=["User Feedback & Defect Triage"])

def check_feedback_access(
    db: Session,
    feedback: UserFeedback,
    user: User,
    required_permission: Optional[OrgPermission] = None
):
    """Ensures user belongs to the feedback's organization or authored the feedback."""
    if feedback.user_id == user.id:
        return  # Author always has view access

    if not feedback.organization_id:
        # Platform-level feedback, requires ADMIN role or authorized staff
        if user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff administrative privileges required to access platform feedback."
            )
        return

    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == feedback.organization_id,
        OrganizationMembership.user_id == user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feedback item '{feedback.id}' not found."
        )

    if required_permission and not has_permission(membership.role, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{membership.role}' lacks permission '{required_permission.value}' for feedback management."
        )

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED, summary="Submit user feedback or defect report")
def submit_feedback(
    req: FeedbackCreateRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Submits user feedback, defect report, AI quality issue, or UX suggestion.
    Automatically captures user identity and organization context when authenticated.
    """
    user_id = current_user.id if current_user else None
    user_email = current_user.email if current_user else None
    org_id = org.id if org else None

    # Strip dangerous HTML or format characters for security
    clean_title = req.title.strip()
    clean_description = req.description.strip()

    feedback = UserFeedback(
        organization_id=org_id,
        user_id=user_id,
        user_email=user_email,
        category=req.category,
        severity=req.severity,
        title=clean_title,
        description=clean_description,
        module_reference=req.module_reference,
        status="NEW"
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    logger.info(
        f"User feedback recorded: id={feedback.id}, category={feedback.category}, "
        f"severity={feedback.severity}, org={org_id}, user={user_email}"
    )

    try:
        from backend.app.services.analytics_service import analytics_service
        analytics_service.record_event(
            db=db,
            event_name="feedback_submitted",
            user_id=user_id,
            organization_id=org_id,
            status="completed",
            properties={
                "category": req.category,
                "severity": req.severity,
                "feature_id": req.module_reference or "general"
            }
        )
    except Exception:
        pass

    return feedback

@router.get("", response_model=FeedbackListResponse, summary="List feedback items with filters")
def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    severity: Optional[str] = None,
    module_reference: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Retrieves feedback submissions scoped to the active organization or current user.
    Supports filtering by status, category, severity, and module.
    """
    query = db.query(UserFeedback)

    if org:
        query = query.filter(UserFeedback.organization_id == org.id)
    else:
        # Non-org query: regular users see only their own feedback; Admins see all
        if current_user.role != "ADMIN":
            query = query.filter(UserFeedback.user_id == current_user.id)

    if status_filter:
        query = query.filter(UserFeedback.status == status_filter.upper())
    if category:
        query = query.filter(UserFeedback.category == category)
    if severity:
        query = query.filter(UserFeedback.severity == severity)
    if module_reference:
        query = query.filter(UserFeedback.module_reference == module_reference)

    total = query.count()
    items = query.order_by(desc(UserFeedback.created_at)).offset(skip).limit(limit).all()

    return FeedbackListResponse(total=total, items=items)

@router.get("/summary", response_model=FeedbackSummaryResponse, summary="Aggregate feedback metrics")
def get_feedback_summary(
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns high-level summary counts grouped by status, category, and severity.
    """
    query = db.query(UserFeedback)
    if org:
        query = query.filter(UserFeedback.organization_id == org.id)
    elif current_user.role != "ADMIN":
        query = query.filter(UserFeedback.user_id == current_user.id)

    feedbacks = query.all()
    total = len(feedbacks)

    by_status: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}

    for f in feedbacks:
        by_status[f.status] = by_status.get(f.status, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

    return FeedbackSummaryResponse(
        total=total,
        by_status=by_status,
        by_category=by_category,
        by_severity=by_severity
    )

@router.get("/{feedback_id}", response_model=FeedbackResponse, summary="Retrieve feedback item")
def get_feedback_item(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a single feedback submission by ID with tenant access check.
    """
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback '{feedback_id}' not found.")

    check_feedback_access(db, feedback, current_user)
    return feedback

@router.patch("/{feedback_id}", response_model=FeedbackResponse, summary="Update feedback status or triage notes")
def update_feedback_status(
    feedback_id: str,
    req: FeedbackUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triage and status update for feedback items (e.g. NEW -> TRIAGED -> IN_PROGRESS -> RESOLVED).
    Requires editor or administrative privileges.
    """
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback '{feedback_id}' not found.")

    check_feedback_access(db, feedback, current_user, OrgPermission.EDIT_DRAFTS)

    if req.status:
        feedback.status = req.status.upper()
    if req.admin_notes is not None:
        feedback.admin_notes = req.admin_notes
    if req.assigned_to is not None:
        feedback.assigned_to = req.assigned_to
    if req.resolution_summary is not None:
        feedback.resolution_summary = req.resolution_summary

    db.commit()
    db.refresh(feedback)

    logger.info(f"Feedback '{feedback_id}' updated to status '{feedback.status}' by user '{current_user.email}'")
    return feedback

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete feedback item")
def delete_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a feedback item. Requires organization administrator role.
    """
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feedback '{feedback_id}' not found.")

    check_feedback_access(db, feedback, current_user, OrgPermission.MANAGE_ORGANIZATION)

    db.delete(feedback)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
