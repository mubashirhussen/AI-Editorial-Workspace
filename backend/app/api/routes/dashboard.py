from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from backend.app.core.database import get_db
from backend.app.models.base import (
    ResearchProject,
    Source,
    WritingDraft,
    WritingSuggestion,
    EditorialOutput,
    EditorialReview,
    EditorialVersion,
    User,
    Organization,
    OrganizationMembership
)
from backend.app.api.deps import get_current_user, get_active_organization

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

@router.get("")
@router.get("/")
@router.get("/overview")
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Aggregates primary dashboard KPIs directly from live database records scoped by organization."""
    if org:
        org_id = org.id
        project_query = db.query(ResearchProject).filter(
            ResearchProject.organization_id == org_id,
            ResearchProject.deleted_at.is_(None)
        )
        project_ids = [p[0] for p in project_query.with_entities(ResearchProject.id).all()]

        total_projects = project_query.count()
        total_sources = db.query(Source).filter(
            Source.project_id.in_(project_ids),
            Source.deleted_at.is_(None)
        ).count() if project_ids else 0

        verified_sources = db.query(Source).filter(
            Source.project_id.in_(project_ids),
            func.lower(Source.extraction_status) == "completed",
            Source.deleted_at.is_(None)
        ).count() if project_ids else 0

        draft_query = db.query(WritingDraft).filter(
            WritingDraft.organization_id == org_id,
            WritingDraft.deleted_at.is_(None)
        )
        total_drafts = draft_query.count()
        draft_ids = [d[0] for d in draft_query.with_entities(WritingDraft.id).all()]

        editorial_query = db.query(EditorialOutput).filter(
            EditorialOutput.project_id.in_(project_ids)
        ) if project_ids else None
        total_editorials = editorial_query.count() if editorial_query else 0
        editorial_ids = [e[0] for e in editorial_query.with_entities(EditorialOutput.id).all()] if editorial_query else []

        total_reviews = db.query(EditorialReview).filter(
            EditorialReview.editorial_id.in_(editorial_ids)
        ).count() if editorial_ids else 0

        pending_suggestions = db.query(WritingSuggestion).filter(
            WritingSuggestion.draft_id.in_(draft_ids),
            func.lower(WritingSuggestion.status) == "pending"
        ).count() if draft_ids else 0

        doc_ids = list(set(draft_ids + editorial_ids))
        total_versions = db.query(EditorialVersion).filter(
            EditorialVersion.document_id.in_(doc_ids)
        ).count() if doc_ids else 0

        recent_projects = project_query.order_by(ResearchProject.updated_at.desc()).limit(5).all()
        recent_drafts = draft_query.order_by(WritingDraft.updated_at.desc()).limit(5).all()
    else:
        total_projects = db.query(ResearchProject).filter(ResearchProject.deleted_at.is_(None)).count()
        total_sources = db.query(Source).filter(Source.deleted_at.is_(None)).count()
        verified_sources = db.query(Source).filter(func.lower(Source.extraction_status) == "completed", Source.deleted_at.is_(None)).count()
        total_drafts = db.query(WritingDraft).filter(WritingDraft.deleted_at.is_(None)).count()
        total_editorials = db.query(EditorialOutput).count()
        total_reviews = db.query(EditorialReview).count()
        pending_suggestions = db.query(WritingSuggestion).filter(func.lower(WritingSuggestion.status) == "pending").count()
        total_versions = db.query(EditorialVersion).count()

        recent_projects = db.query(ResearchProject).filter(ResearchProject.deleted_at.is_(None)).order_by(ResearchProject.updated_at.desc()).limit(5).all()
        recent_drafts = db.query(WritingDraft).filter(WritingDraft.deleted_at.is_(None)).order_by(WritingDraft.updated_at.desc()).limit(5).all()

    return {
        "metrics": {
            "total_projects": total_projects,
            "total_sources": total_sources,
            "verified_sources": verified_sources,
            "total_drafts": total_drafts,
            "total_editorials": total_editorials,
            "total_reviews": total_reviews,
            "pending_suggestions": pending_suggestions,
            "total_versions": total_versions
        },
        "recent_projects": [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "sources_count": len(p.sources),
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in recent_projects
        ],
        "recent_drafts": [
            {
                "id": d.id,
                "title": d.title,
                "status": d.status,
                "word_count": d.word_count,
                "readability_score": d.readability_score,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None
            }
            for d in recent_drafts
        ]
    }

@router.get("/activity")
def get_dashboard_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Retrieves unified timeline activity from version snapshots, source updates, and reviews scoped by organization."""
    activities = []

    if org:
        org_id = org.id
        project_ids = [p[0] for p in db.query(ResearchProject.id).filter(
            ResearchProject.organization_id == org_id,
            ResearchProject.deleted_at.is_(None)
        ).all()]
        draft_ids = [d[0] for d in db.query(WritingDraft.id).filter(
            WritingDraft.organization_id == org_id,
            WritingDraft.deleted_at.is_(None)
        ).all()]
        editorial_ids = [e[0] for e in db.query(EditorialOutput.id).filter(
            EditorialOutput.project_id.in_(project_ids)
        ).all()] if project_ids else []

        doc_ids = list(set(draft_ids + editorial_ids))
        if doc_ids:
            versions = db.query(EditorialVersion).filter(
                EditorialVersion.document_id.in_(doc_ids)
            ).order_by(EditorialVersion.created_at.desc()).limit(limit).all()
        else:
            versions = []

        if editorial_ids:
            reviews = db.query(EditorialReview).filter(
                EditorialReview.editorial_id.in_(editorial_ids)
            ).order_by(EditorialReview.created_at.desc()).limit(limit).all()
        else:
            reviews = []
    else:
        versions = db.query(EditorialVersion).order_by(EditorialVersion.created_at.desc()).limit(limit).all()
        reviews = db.query(EditorialReview).order_by(EditorialReview.created_at.desc()).limit(limit).all()

    # 1. Version history snapshots
    for v in versions:
        activities.append({
            "id": v.id,
            "type": "VERSION_SNAPSHOT",
            "title": f"Snapshot created for {v.document_type.replace('_', ' ').title()}",
            "summary": v.change_summary or f"Version {v.version_number} saved ({v.change_type})",
            "timestamp": v.created_at.isoformat() if v.created_at else None,
            "document_id": v.document_id,
            "badge": v.change_type
        })

    # 2. Recent Editorial Reviews
    for r in reviews:
        activities.append({
            "id": r.id,
            "type": "EDITORIAL_REVIEW",
            "title": f"Editorial Review by {r.reviewer_name}",
            "summary": f"Review status updated to {r.review_status}",
            "timestamp": r.created_at.isoformat() if r.created_at else None,
            "document_id": r.editorial_id,
            "badge": r.review_status
        })

    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return {"activities": activities[:limit]}

@router.get("/research-analytics")
def get_research_analytics(
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Provides breakdown of research sources by type, extraction status, and volume scoped by organization."""
    if org:
        project_ids = [p[0] for p in db.query(ResearchProject.id).filter(
            ResearchProject.organization_id == org.id,
            ResearchProject.deleted_at.is_(None)
        ).all()]
        if not project_ids:
            return {
                "total_sources": 0,
                "verified_count": 0,
                "failed_count": 0,
                "pending_count": 0,
                "verification_rate_pct": 100.0,
                "verification_rate": 100.0,
                "sources_by_type": {}
            }
        base_query = db.query(Source).filter(Source.project_id.in_(project_ids), Source.deleted_at.is_(None))
    else:
        base_query = db.query(Source).filter(Source.deleted_at.is_(None))

    total_sources = base_query.count()
    completed = base_query.filter(func.lower(Source.extraction_status) == "completed").count()
    failed = base_query.filter(func.lower(Source.extraction_status) == "failed").count()
    pending = total_sources - completed - failed

    by_type_rows = base_query.with_entities(Source.source_type, func.count(Source.id)).group_by(Source.source_type).all()
    sources_by_type = {t or "UNKNOWN": count for t, count in by_type_rows}

    return {
        "total_sources": total_sources,
        "verified_count": completed,
        "failed_count": failed,
        "pending_count": max(0, pending),
        "verification_rate_pct": round((completed / total_sources * 100), 1) if total_sources > 0 else 100.0,
        "verification_rate": round((completed / total_sources * 100), 1) if total_sources > 0 else 100.0,
        "sources_by_type": sources_by_type
    }

@router.get("/writing-analytics")
def get_writing_analytics(
    current_user: User = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Provides breakdown of draft word counts, readability scores, and suggestions scoped by organization."""
    if org:
        drafts = db.query(WritingDraft).filter(
            WritingDraft.organization_id == org.id,
            WritingDraft.deleted_at.is_(None)
        ).all()
        draft_ids = [d.id for d in drafts]
    else:
        drafts = db.query(WritingDraft).filter(WritingDraft.deleted_at.is_(None)).all()
        draft_ids = [d.id for d in drafts]

    total_drafts = len(drafts)
    total_words = sum(d.word_count or 0 for d in drafts)
    valid_scores = [d.readability_score for d in drafts if d.readability_score is not None]
    avg_flesch = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 65.0

    if draft_ids:
        suggestions_by_cat = db.query(WritingSuggestion.category, func.count(WritingSuggestion.id)).filter(
            WritingSuggestion.draft_id.in_(draft_ids)
        ).group_by(WritingSuggestion.category).all()
    else:
        suggestions_by_cat = []

    return {
        "total_drafts": total_drafts,
        "total_words_written": total_words,
        "average_readability_score": avg_flesch,
        "suggestions_by_category": {cat: count for cat, count in suggestions_by_cat}
    }

@router.get("/usage")
def get_dashboard_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns AI token accounting and resource consumption metrics."""
    from backend.app.services.monitoring_service import monitoring_service
    telemetry = monitoring_service.get_telemetry_summary()
    return {
        "ai_telemetry": telemetry["ai_telemetry"],
        "uptime_seconds": telemetry["uptime_seconds"],
        "recent_ai_events_count": len(telemetry.get("recent_events", [])),
        "api_calls": telemetry["ai_telemetry"]["total_operations"],
        "rate_limit_quota": {"limit": 1000, "remaining": 995, "reset_in_seconds": 3600}
    }
