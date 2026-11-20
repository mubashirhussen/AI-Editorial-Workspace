"""
Phase 38: Product Intelligence, Data-Driven Recommendations & Automated Workflow Optimization Router.
Provides endpoints for intelligence analysis, evidence-backed insights,
recommendation lifecycles, safe workflow actions, and impact evaluation.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import User, Organization
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.services.product_intelligence_service import product_intelligence_service
from backend.app.schemas.intelligence import (
    IntelligenceOverviewResponse,
    IntelligenceInsightResponse,
    RecommendationResponse,
    RecommendationStatusUpdateRequest,
    RecommendationFeedbackCreate,
    RecommendationFeedbackResponse,
    OptimizationActionRequest,
    OptimizationActionResponse,
    ImpactEvaluationResponse,
    DataQualityReport,
)

router = APIRouter(prefix="/intelligence", tags=["Product Intelligence & Recommendations"])


# ---------------------------------------------------------------------------
# 1. Intelligence Analysis & Overview
# ---------------------------------------------------------------------------

@router.post("/analyze", status_code=status.HTTP_200_OK, response_model=Dict[str, Any])
def trigger_intelligence_analysis(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Triggers end-to-end product intelligence analysis.
    Validates analytics data quality, executes deterministic pattern rules,
    and produces evidence-backed insights and prioritized recommendations.
    """
    return product_intelligence_service.run_intelligence_analysis(db=db, organization_id=org.id, days=days)


@router.get("/overview", response_model=IntelligenceOverviewResponse)
def get_intelligence_overview(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns aggregated intelligence overview, data quality diagnostics, active insights, and recommendations."""
    return product_intelligence_service.get_overview(db=db, organization_id=org.id)


@router.get("/status", response_model=DataQualityReport)
def get_intelligence_status(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns analytics data quality score and statistical completeness diagnostics."""
    return product_intelligence_service.validate_data_quality(db=db, organization_id=org.id, days=days)


# ---------------------------------------------------------------------------
# 2. Insights Feed & Detail
# ---------------------------------------------------------------------------

@router.get("/insights", response_model=List[IntelligenceInsightResponse])
def list_insights(
    category: Optional[str] = Query(None, description="Optional category filter"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Lists evidence-grounded insights detected for the active organization."""
    return product_intelligence_service.get_insights(db=db, organization_id=org.id, category=category)


@router.get("/insights/{insight_id}", response_model=IntelligenceInsightResponse)
def get_insight_detail(
    insight_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns detailed view of an insight with full evidence references."""
    insights = product_intelligence_service.get_insights(db=db, organization_id=org.id)
    target = next((i for i in insights if i.id == insight_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Insight '{insight_id}' not found.")
    return target


# ---------------------------------------------------------------------------
# 3. Recommendations & Lifecycle Transitions
# ---------------------------------------------------------------------------

@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Lists prioritized product optimization recommendations."""
    return product_intelligence_service.get_recommendations(
        db=db,
        organization_id=org.id,
        status=status_filter,
        priority=priority
    )


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation_detail(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns detailed view of a single recommendation."""
    recs = product_intelligence_service.get_recommendations(db=db, organization_id=org.id)
    target = next((r for r in recs if r.id == recommendation_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Recommendation '{recommendation_id}' not found.")
    return target


@router.post("/recommendations/{recommendation_id}/accept", response_model=RecommendationResponse)
def accept_recommendation(
    recommendation_id: str,
    req: Optional[RecommendationStatusUpdateRequest] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Accepts a recommendation for implementation."""
    try:
        notes = req.notes if req else None
        assignee = req.assigned_to if req else current_user.full_name or current_user.email
        return product_intelligence_service.update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            new_status="ACCEPTED",
            notes=notes,
            assigned_to=assignee
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/reject", response_model=RecommendationResponse)
def reject_recommendation(
    recommendation_id: str,
    req: Optional[RecommendationStatusUpdateRequest] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Rejects a recommendation with justification."""
    try:
        notes = req.notes if req else "Marked not applicable by editor."
        return product_intelligence_service.update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            new_status="REJECTED",
            notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/defer", response_model=RecommendationResponse)
def defer_recommendation(
    recommendation_id: str,
    req: Optional[RecommendationStatusUpdateRequest] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Defers a recommendation for future review."""
    try:
        notes = req.notes if req else "Deferred for upcoming release cycle."
        return product_intelligence_service.update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            new_status="DEFERRED",
            notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/implement", response_model=RecommendationResponse)
def implement_recommendation(
    recommendation_id: str,
    req: Optional[RecommendationStatusUpdateRequest] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Marks a recommendation as implemented, initiating impact baseline tracking."""
    try:
        notes = req.notes if req else "Implementation verified by operator."
        return product_intelligence_service.update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            new_status="IMPLEMENTED",
            notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/verify", response_model=RecommendationResponse)
def verify_recommendation(
    recommendation_id: str,
    req: Optional[RecommendationStatusUpdateRequest] = None,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Verifies and completes the recommendation lifecycle after demonstrated impact."""
    try:
        notes = req.notes if req else "Improvements formally certified."
        return product_intelligence_service.update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            new_status="VERIFIED",
            notes=notes
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/recommendations/{recommendation_id}/feedback", response_model=RecommendationFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_recommendation_feedback(
    recommendation_id: str,
    payload: RecommendationFeedbackCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Submits user feedback regarding recommendation accuracy, relevance, or feasibility."""
    fb = product_intelligence_service.record_feedback(
        db=db,
        recommendation_id=recommendation_id,
        user_id=current_user.id,
        organization_id=org.id,
        feedback_type=payload.feedback_type,
        rating=payload.rating,
        comment=payload.comment
    )
    return fb


# ---------------------------------------------------------------------------
# 4. Safe Automated Workflow Optimization & Impact Evaluation
# ---------------------------------------------------------------------------

@router.post("/optimize", response_model=OptimizationActionResponse, status_code=status.HTTP_201_CREATED)
def execute_workflow_optimization(
    payload: OptimizationActionRequest,
    recommendation_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Executes a pre-approved, deterministic low-risk workflow optimization.
    Strictly forbids modifying application infrastructure, databases, authentication, or user drafts.
    """
    try:
        action = product_intelligence_service.execute_safe_action(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id,
            action_type=payload.action_type,
            payload=payload.action_payload,
            executed_by=current_user.email
        )
        return action
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/impact/{recommendation_id}", response_model=ImpactEvaluationResponse)
def get_recommendation_impact(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Calculates and returns pre/post implementation metric deltas for an implemented recommendation."""
    try:
        return product_intelligence_service.evaluate_impact(
            db=db,
            recommendation_id=recommendation_id,
            organization_id=org.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/workflow-optimization")
def get_workflow_optimizations(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns curated workflow optimization recommendations across Research, Writing, and Editorial."""
    recs = product_intelligence_service.get_recommendations(db=db, organization_id=org.id)
    return {
        "research_optimizations": [r for r in recs if "research" in r.category],
        "writing_optimizations": [r for r in recs if "writing" in r.category],
        "editorial_optimizations": [r for r in recs if "editorial" in r.category],
        "system_optimizations": [r for r in recs if r.category in ("reliability", "performance", "workflow_optimization")]
    }
