from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.core.database import get_db
from backend.app.schemas.writing import (
    WritingAnalysisRequest,
    WritingAnalysisResponse,
    WritingMetrics,
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftCompareResponse
)
from backend.app.schemas.style import (
    StyleCheckRequest,
    StyleCheckResponse
)
from backend.app.schemas.version import VersionResponse, VersionRestoreResponse
from backend.app.services.writing_service import writing_service
from backend.app.services.style_intelligence.style_analyzer import style_analyzer
from backend.app.services.version_control.version_service import version_service
from backend.app.services.writing import writing_analyzer, metrics_service, suggestion_service
from backend.app.models.base import WritingDraft, WritingSuggestion, ResearchProject, EditorialStyleProfile, User, Organization
from backend.app.api.deps import get_current_user, get_active_organization

router = APIRouter(prefix="/writing", tags=["Writing Assistant"])

@router.post("/analyze", response_model=WritingAnalysisResponse, summary="Analyze writing text")
async def analyze_writing(req: WritingAnalysisRequest, db: Session = Depends(get_db)):
    """Executes writing quality, readability, and structural analysis on provided text."""
    return await writing_service.analyze_and_store(db, req)

@router.post("/drafts", response_model=DraftResponse, status_code=status.HTTP_201_CREATED, summary="Create a new draft")
def create_draft(data: DraftCreate, db: Session = Depends(get_db)):
    """Creates a new writing draft and records an initial version snapshot."""
    return writing_service.create_draft(db, data)

@router.get("/drafts", response_model=List[DraftResponse], summary="List writing drafts")
def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieves paginated writing drafts ordered by most recent."""
    return writing_service.get_drafts(db, skip=skip, limit=limit)

@router.get("/drafts/{draft_id}", response_model=DraftResponse, summary="Get draft by ID")
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    """Retrieves full writing draft details including revised and original content."""
    return writing_service.get_draft(db, draft_id)

@router.put("/drafts/{draft_id}", response_model=DraftResponse, summary="Update draft content")
def update_draft(draft_id: str, data: DraftUpdate, db: Session = Depends(get_db)):
    """Updates draft text, title, or status, creating a version snapshot if revised."""
    return writing_service.update_draft(db, draft_id, data)

@router.patch("/drafts/{draft_id}", response_model=DraftResponse, summary="Patch draft fields")
def patch_draft(draft_id: str, data: DraftUpdate, db: Session = Depends(get_db)):
    """Partially updates draft content, metadata, or status with automatic snapshot."""
    updated = writing_service.update_draft(db, draft_id, data)
    content = updated.revised_content or updated.original_content or ""
    try:
        version_service.create_snapshot(
            db,
            document_type="WRITING_DRAFT",
            document_id=draft_id,
            content=content,
            title=updated.title,
            change_type="MANUAL_EDIT",
            change_summary="Draft updated via API",
            force=True
        )
    except Exception:
        pass
    return updated

@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete draft")
def delete_draft(draft_id: str, db: Session = Depends(get_db)):
    """Deletes a writing draft and its associated suggestions."""
    writing_service.delete_draft(db, draft_id)
    return None

# --- Draft Analysis Endpoints ---

@router.post("/drafts/{draft_id}/analyze", response_model=WritingAnalysisResponse, summary="Run analysis on draft")
def analyze_draft(draft_id: str, db: Session = Depends(get_db)):
    """Analyzes an existing draft's text for readability and generates actionable rewrite suggestions."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    
    # Clean previous pending suggestions
    db.query(WritingSuggestion).filter(
        WritingSuggestion.draft_id == draft.id,
        WritingSuggestion.status.in_(["pending", "PENDING"])
    ).delete()
    db.commit()

    analysis = writing_analyzer.analyze_text(content, draft_id=draft.id)
    for issue in analysis.issues:
        sugg = WritingSuggestion(
            id=issue.id,
            draft_id=draft.id,
            category=issue.category,
            severity=issue.severity,
            original_text=issue.original_text,
            suggested_text=issue.suggested_rewrite,
            suggested_rewrite=issue.suggested_rewrite,
            explanation=issue.explanation,
            reason=issue.reason or "",
            confidence=issue.confidence,
            status="PENDING"
        )
        db.add(sugg)

    draft.status = "ANALYZED"
    draft.readability_score = analysis.metrics.readability_score
    db.commit()
    db.refresh(draft)
    return analysis

@router.get("/drafts/{draft_id}/analysis", response_model=WritingAnalysisResponse, summary="Get cached draft analysis")
def get_draft_analysis(draft_id: str, db: Session = Depends(get_db)):
    """Retrieves current analysis feedback and issues for a draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    return writing_analyzer.analyze_text(content, draft_id=draft.id)

@router.get("/drafts/{draft_id}/metrics", response_model=WritingMetrics, summary="Get draft writing metrics")
def get_draft_metrics(draft_id: str, db: Session = Depends(get_db)):
    """Calculates live writing metrics (word count, reading time, readability) for a draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    return metrics_service.calculate_metrics(content)

# --- Suggestions Management ---

@router.get("/drafts/{draft_id}/suggestions", summary="List draft suggestions")
def get_draft_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """Returns all suggestions generated for a writing draft."""
    writing_service.get_draft(db, draft_id)
    return db.query(WritingSuggestion).filter(WritingSuggestion.draft_id == draft_id).all()

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/accept", summary="Accept suggestion in draft")
def accept_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Applies a specific suggested rewrite to the draft content."""
    return writing_service.accept_suggestion(db, draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/reject", summary="Reject suggestion in draft")
def reject_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Marks a suggestion as rejected without altering draft content."""
    return writing_service.reject_suggestion(db, draft_id, suggestion_id)

@router.post("/suggestions/{suggestion_id}/accept", summary="Accept suggestion direct")
def accept_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Accepts a suggestion using its global ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return writing_service.accept_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/suggestions/{suggestion_id}/reject", summary="Reject suggestion direct")
def reject_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Rejects a suggestion using its global ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return writing_service.reject_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/accept-all", summary="Accept all suggestions")
@router.post("/drafts/{draft_id}/accept-all", summary="Accept all suggestions alias")
def accept_all_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """Accepts and applies all pending suggestions for the specified draft."""
    return writing_service.accept_all_suggestions(db, draft_id)

@router.get("/drafts/{draft_id}/compare", response_model=DraftCompareResponse, summary="Compare draft with baseline")
def compare_draft(draft_id: str, db: Session = Depends(get_db)):
    """Compares the current revised draft against its baseline original content."""
    return writing_service.compare_draft(db, draft_id)

@router.post("/drafts/{draft_id}/rewrite", summary="Request AI draft rewrite")
def request_draft_rewrite(draft_id: str, db: Session = Depends(get_db)):
    """Generates AI rewrite suggestions for the full draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    analysis = writing_analyzer.analyze_text(content, draft_id=draft.id)
    return {
        "draft_id": draft_id,
        "metrics": analysis.metrics.model_dump() if hasattr(analysis.metrics, "model_dump") else analysis.metrics.dict(),
        "issues_count": len(analysis.issues),
        "issues": [i.model_dump() if hasattr(i, "model_dump") else i.dict() for i in analysis.issues],
        "revised_content": content
    }

# --- Version History & Restoration ---

@router.get("/drafts/{draft_id}/versions", response_model=List[VersionResponse], summary="List draft version snapshots")
def get_draft_versions(draft_id: str, db: Session = Depends(get_db)):
    """Returns chronological snapshot versions for this draft."""
    writing_service.get_draft(db, draft_id)
    return version_service.list_versions(db, "WRITING_DRAFT", draft_id)

@router.post("/drafts/{draft_id}/restore/{version_id}", response_model=VersionRestoreResponse, summary="Restore draft snapshot")
def restore_draft_version(draft_id: str, version_id: str, db: Session = Depends(get_db)):
    """Restores a previous draft snapshot non-destructively as a new head version."""
    writing_service.get_draft(db, draft_id)
    version = version_service.get_version(db, version_id)
    return version_service.restore_version(db, "WRITING_DRAFT", draft_id, version.version_number)

# --- Style Intelligence ---

@router.post("/drafts/{draft_id}/style-check", response_model=StyleCheckResponse, summary="Audit style compliance")
def style_check_draft(
    draft_id: str,
    payload: Optional[StyleCheckRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """Executes an automated style-compliance audit on a writing draft against a selected Editorial Style Profile."""
    draft = writing_service.get_draft(db, draft_id)

    if draft.project_id:
        proj = db.query(ResearchProject).filter(ResearchProject.id == draft.project_id).first()
        if proj and proj.organization_id and proj.organization_id != active_org.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing draft not found")

    profile = None
    profile_id = payload.style_profile_id if payload else None
    if profile_id:
        profile = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == profile_id).first()
    elif draft.style_profile_id:
        profile = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == draft.style_profile_id).first()

    if not profile:
        profile = db.query(EditorialStyleProfile).filter(
            (EditorialStyleProfile.organization_id == active_org.id) & (EditorialStyleProfile.is_default == True)
        ).first()

    if not profile:
        profile = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.is_default == True).first()

    if not profile:
        profile = db.query(EditorialStyleProfile).first()

    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active style profile available")

    override_content = payload.content if payload else None
    return style_analyzer.analyze_and_update_draft(db, draft, profile, override_content=override_content)
