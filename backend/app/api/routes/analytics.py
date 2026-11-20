"""
Phase 37: Product Analytics & User Journey Intelligence Router.
Provides privacy-conscious endpoints for first-party event tracking,
funnel progression, feature adoption, workflow intelligence, and privacy controls.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import User, Organization
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.services.analytics_service import analytics_service
from backend.app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    AnalyticsOverviewResponse,
    AnalyticsWorkflowsResponse,
    AnalyticsFunnelsResponse,
    AnalyticsFeaturesResponse,
    AnalyticsTrendsResponse,
    AnalyticsHealthResponse,
    AnalyticsPrivacyPreferenceRequest,
    AnalyticsPrivacyPreferenceResponse,
)

router = APIRouter(prefix="/analytics", tags=["Product Analytics & Funnels"])


# ---------------------------------------------------------------------------
# 1. Event Ingestion Endpoints
# ---------------------------------------------------------------------------

@router.post("/events", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any])
def ingest_analytics_event(
    payload: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Ingests a privacy-conscious, validated first-party product analytics event.
    Applies property allowlisting, rejects sensitive payloads, deduplicates,
    and maps the user ID to a non-reversible cryptographic pseudonym.
    """
    event = analytics_service.record_event(
        db=db,
        event_name=payload.event_name,
        user_id=current_user.id,
        organization_id=org.id,
        project_id=payload.project_reference,
        workflow_type=payload.workflow_type,
        workflow_id=payload.workflow_reference,
        session_id=payload.session_reference,
        source=payload.source or "frontend",
        status=payload.status or "completed",
        duration_ms=payload.duration_ms,
        properties=payload.properties,
        client_event_id=payload.event_id,
        occurred_at=payload.occurred_at
    )

    if not event:
        # Dropped due to user opt-out or deduplication window
        return {
            "status": "acknowledged",
            "message": "Event processed (filtered by privacy preferences or duplicate suppression)."
        }

    return {
        "status": "recorded",
        "event_id": event.event_id or event.id,
        "event_name": event.event_name,
        "occurred_at": event.occurred_at.isoformat()
    }


# ---------------------------------------------------------------------------
# 2. Executive Product Metrics & Reporting Endpoints
# ---------------------------------------------------------------------------

@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    days: int = Query(default=30, ge=1, le=365, description="Lookback window in days"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns executive product metrics: active users, sessions, projects created,
    workflow completion rate, feature usage, AI success rate, and feedback volume.
    Strictly scoped to the user's organization.
    """
    data = analytics_service.get_overview(db=db, organization_id=org.id, days=days)
    return AnalyticsOverviewResponse(**data)


@router.get("/workflows", response_model=AnalyticsWorkflowsResponse)
def get_analytics_workflows(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns workflow lifecycle metrics for research, writing, and editorial journeys:
    completion rates, failure counts, median duration, and drop-off bottlenecks.
    """
    workflows_data = analytics_service.get_workflows(db=db, organization_id=org.id, days=days)
    return AnalyticsWorkflowsResponse(
        time_range=f"Last {days} days",
        workflows=workflows_data
    )


@router.get("/funnels", response_model=AnalyticsFunnelsResponse)
def get_analytics_funnels(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns multi-step conversion funnels for:
    - Research Knowledge Ingestion
    - Assisted Composition & Polish
    - Editorial Studio & Final Publication
    """
    funnels_data = analytics_service.get_funnels(db=db, organization_id=org.id, days=days)
    return AnalyticsFunnelsResponse(**funnels_data)


@router.get("/features", response_model=AnalyticsFeaturesResponse)
def get_analytics_features(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns feature adoption metrics, usage volumes, success rates,
    and average execution latency across all system modules.
    """
    features_data = analytics_service.get_features(db=db, organization_id=org.id, days=days)
    return AnalyticsFeaturesResponse(features=features_data)


@router.get("/trends", response_model=AnalyticsTrendsResponse)
def get_analytics_trends(
    days: int = Query(default=7, ge=3, le=90),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns daily time-series distribution for charts and trend visualizations."""
    trends_data = analytics_service.get_trends(db=db, organization_id=org.id, days=days)
    return AnalyticsTrendsResponse(period=f"Last {days} days", data_points=trends_data)


@router.get("/health", response_model=AnalyticsHealthResponse)
def get_analytics_subsystem_health(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns telemetry on the analytics subsystem: event volume, privacy filtering, and deduplication."""
    health_data = analytics_service.get_health(db=db, organization_id=org.id)
    return AnalyticsHealthResponse(**health_data)


# ---------------------------------------------------------------------------
# 3. Privacy Preference & Opt-Out Endpoints
# ---------------------------------------------------------------------------

@router.get("/privacy-preference", response_model=AnalyticsPrivacyPreferenceResponse)
def get_user_privacy_preference(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns the current user's analytics tracking privacy preference."""
    pref = analytics_service.get_user_privacy_preference(db=db, user_id=current_user.id, organization_id=org.id)
    return AnalyticsPrivacyPreferenceResponse(
        user_id=pref.user_id,
        organization_id=pref.organization_id,
        analytics_opt_out=pref.analytics_opt_out,
        do_not_track=pref.do_not_track,
        updated_at=pref.updated_at
    )


@router.put("/privacy-preference", response_model=AnalyticsPrivacyPreferenceResponse)
def update_user_privacy_preference(
    payload: AnalyticsPrivacyPreferenceRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Updates user privacy preference (e.g. opt-out of product analytics)."""
    pref = analytics_service.update_user_privacy_preference(
        db=db,
        user_id=current_user.id,
        organization_id=org.id,
        analytics_opt_out=payload.analytics_opt_out,
        do_not_track=payload.do_not_track
    )
    return AnalyticsPrivacyPreferenceResponse(
        user_id=pref.user_id,
        organization_id=pref.organization_id,
        analytics_opt_out=pref.analytics_opt_out,
        do_not_track=pref.do_not_track,
        updated_at=pref.updated_at
    )


# ---------------------------------------------------------------------------
# 4. Retention Management Endpoint
# ---------------------------------------------------------------------------

@router.post("/retention/cleanup", status_code=status.HTTP_200_OK)
def trigger_retention_cleanup(
    retention_days: int = Query(default=90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Administrative maintenance endpoint: purges analytics events older than retention_days.
    Does not delete any primary core application records.
    """
    deleted = analytics_service.cleanup_retention(db=db, retention_days=retention_days)
    return {
        "status": "success",
        "purged_events_count": deleted,
        "retention_days": retention_days
    }


# ---------------------------------------------------------------------------
# 5. Legacy Endpoints (Maintained for Backward Compatibility)
# ---------------------------------------------------------------------------

@router.get("/funnel")
def get_legacy_editorial_funnel(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Legacy endpoint returning funnel counters."""
    return analytics_service.get_funnel_summary(db=db, organization_id=org.id)


@router.get("/events")
def get_legacy_analytics_events(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Legacy endpoint returning recent privacy-safe events."""
    return analytics_service.get_recent_events(db=db, organization_id=org.id, limit=limit)


@router.post("/track", status_code=status.HTTP_201_CREATED)
def track_legacy_client_event(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Legacy client event tracker."""
    metric_name = payload.get("metric_name", "feature_used")
    metric_val = float(payload.get("metric_value", 1.0))
    metadata = payload.get("metadata")

    event = analytics_service.track_event(
        db=db,
        organization_id=org.id,
        metric_name=metric_name,
        metric_value=metric_val,
        metadata=metadata
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metric name or rejected un-sanitized metadata."
        )
    return {"status": "recorded", "event_id": event.id, "metric_name": event.metric_name}
