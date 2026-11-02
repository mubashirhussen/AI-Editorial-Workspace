from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.crud import writing as crud_writing
from backend.app.models.base import WritingDraft, WritingSuggestion
from backend.app.schemas.writing import (
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    WritingAnalysisResponse,
    WritingMetrics,
    DraftCompareResponse
)
from backend.app.services.writing import writing_analyzer, metrics_service, suggestion_service

router = APIRouter(tags=["Writing"])

@router.post("/drafts", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def create_draft(payload: DraftCreate, db: Session = Depends(get_db)):
    """Create a new writing draft."""
    return crud_writing.create_draft(db, payload)

@router.get("/drafts", response_model=List[DraftResponse])
def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List writing drafts."""
    return crud_writing.get_drafts(db, skip=skip, limit=limit)

@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    """Get a draft by ID."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return draft

@router.put("/drafts/{draft_id}", response_model=DraftResponse)
def update_draft(draft_id: str, payload: DraftUpdate, db: Session = Depends(get_db)):
    """Update a draft."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return crud_writing.update_draft(db, draft, payload)

@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(draft_id: str, db: Session = Depends(get_db)):
    """Delete a writing draft."""
    success = crud_writing.delete_draft(db, draft_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return None

# --- Writing Analysis Endpoints ---

@router.post("/drafts/{draft_id}/analyze", response_model=WritingAnalysisResponse)
def analyze_draft(draft_id: str, db: Session = Depends(get_db)):
    """Run deterministic writing-quality checks on a draft and store suggestions."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")

    # Remove previous pending suggestions
    db.query(WritingSuggestion).filter(
        WritingSuggestion.draft_id == draft.id,
        WritingSuggestion.status.in_(["pending", "PENDING"])
    ).delete()
    db.commit()

    analysis = writing_analyzer.analyze_text(draft.revised_content, draft_id=draft.id)

    # Persist suggestions
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

@router.get("/drafts/{draft_id}/analysis", response_model=WritingAnalysisResponse)
def get_draft_analysis(draft_id: str, db: Session = Depends(get_db)):
    """Retrieve saved analysis and pending suggestions for a draft."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return writing_analyzer.analyze_text(draft.revised_content, draft_id=draft.id)

@router.get("/drafts/{draft_id}/metrics", response_model=WritingMetrics)
def get_draft_metrics(draft_id: str, db: Session = Depends(get_db)):
    """Calculate and return live writing metrics for a draft."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return metrics_service.calculate_metrics(draft.revised_content)

# --- Suggestion Management Endpoints ---

@router.get("/drafts/{draft_id}/suggestions")
def get_draft_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """List all suggestions generated for a draft."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return crud_writing.get_suggestions_by_draft(db, draft.id)

@router.post("/suggestions/{suggestion_id}/accept")
def accept_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Accept a suggestion by ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return suggestion_service.accept_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Reject a suggestion by ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return suggestion_service.reject_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/accept-all")
def accept_all_draft_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """Accept all non-overlapping pending suggestions for a draft."""
    return suggestion_service.accept_all_suggestions(db, draft_id)

@router.get("/drafts/{draft_id}/compare", response_model=DraftCompareResponse)
def compare_draft_versions(draft_id: str, db: Session = Depends(get_db)):
    """Compare original baseline content versus current revised content."""
    return suggestion_service.compare_draft(db, draft_id)


from backend.app.services.version_control.version_service import version_service
from backend.app.schemas.version import VersionResponse, VersionRestoreResponse

@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
def patch_draft(draft_id: str, payload: DraftUpdate, db: Session = Depends(get_db)):
    """Patch draft content or status and record version snapshot."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft with ID '{draft_id}' not found.")
    updated = crud_writing.update_draft(db, draft, payload)
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

@router.post("/drafts/{draft_id}/rewrite")
def request_draft_rewrite(draft_id: str, db: Session = Depends(get_db)):
    """Generates AI rewrite suggestions for full draft or highlighted passages."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    active_content = draft.revised_content or draft.original_content
    analysis = writing_analyzer.analyze_text(active_content, draft_id=draft.id)
    return {
        "draft_id": draft_id,
        "metrics": analysis.metrics.model_dump() if hasattr(analysis.metrics, "model_dump") else analysis.metrics.dict(),
        "issues_count": len(analysis.issues),
        "issues": [i.model_dump() if hasattr(i, "model_dump") else i.dict() for i in analysis.issues],
        "revised_content": active_content
    }

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/accept")
def accept_draft_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Accepts a rewrite suggestion specifically scoped to the draft."""
    return suggestion_service.accept_suggestion(db, draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/reject")
def reject_draft_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Rejects a rewrite suggestion specifically scoped to the draft."""
    return suggestion_service.reject_suggestion(db, draft_id, suggestion_id)

@router.get("/drafts/{draft_id}/versions", response_model=List[VersionResponse])
def get_draft_versions_timeline(draft_id: str, db: Session = Depends(get_db)):
    """Returns chronological snapshot versions for this draft."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    return version_service.list_versions(db, "WRITING_DRAFT", draft_id)

@router.post("/drafts/{draft_id}/restore/{version_id}", response_model=VersionRestoreResponse)
def restore_draft_version(draft_id: str, version_id: str, db: Session = Depends(get_db)):
    """Restores a previous draft snapshot non-destructively as a new version."""
    draft = crud_writing.get_draft_by_id(db, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Draft with ID '{draft_id}' not found.")
    version = version_service.get_version(db, version_id)
    return version_service.restore_version(db, "WRITING_DRAFT", draft_id, version.version_number)
