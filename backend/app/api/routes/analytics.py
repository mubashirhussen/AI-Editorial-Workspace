"""
Product Analytics & Funnel Observability Router.
Privacy-conscious telemetry reporting on product lifecycle and conversion funnels.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import User, Organization
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Product Analytics & Funnels"])


class TrackEventRequest(BaseModel):
    metric_name: str = Field(..., description="Approved analytics metric name")
    metric_value: float = Field(default=1.0, ge=0.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Sanitized, non-PII operational metadata")


@router.get("/funnel")
def get_editorial_funnel(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated editorial funnel metrics:
    projects created, sources processed, briefs synthesized, drafts generated,
    writing improvements completed, exports, and failures.
    """
    return analytics_service.get_funnel_summary(db=db, organization_id=org.id)


@router.get("/events")
def get_analytics_events(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Returns recent privacy-safe operational events."""
    return analytics_service.get_recent_events(db=db, organization_id=org.id, limit=limit)


@router.post("/track", status_code=status.HTTP_201_CREATED)
def track_client_event(
    payload: TrackEventRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Records a client-side product event (e.g. export action, suggestion accept).
    Ensures zero PII, passwords, or raw document contents are captured.
    """
    event = analytics_service.track_event(
        db=db,
        organization_id=org.id,
        metric_name=payload.metric_name,
        metric_value=payload.metric_value,
        metadata=payload.metadata
    )
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metric name or rejected un-sanitized metadata."
        )
    return {"status": "recorded", "event_id": event.id, "metric_name": event.metric_name}

