from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.core.database import get_db
from backend.app.schemas.writing import (
    WritingAnalysisRequest,
    WritingAnalysisResponse,
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftCompareResponse
)
from backend.app.schemas.style import (
    StyleCheckRequest,
    StyleCheckResponse
)
from backend.app.services.writing_service import writing_service
from backend.app.services.style_intelligence.style_analyzer import style_analyzer
from backend.app.models.base import WritingDraft, ResearchProject, EditorialStyleProfile, User, Organization
from backend.app.api.deps import get_current_user, get_active_organization

router = APIRouter(prefix="/writing", tags=["Writing Assistant"])

@router.post("/analyze", response_model=WritingAnalysisResponse)
async def analyze_writing(req: WritingAnalysisRequest, db: Session = Depends(get_db)):
    return await writing_service.analyze_and_store(db, req)

@router.post("/drafts", response_model=DraftResponse, status_code=201)
def create_draft(data: DraftCreate, db: Session = Depends(get_db)):
    return writing_service.create_draft(db, data)

@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str, db: Session = Depends(get_db)):
    return writing_service.get_draft(db, draft_id)

@router.put("/drafts/{draft_id}", response_model=DraftResponse)
def update_draft(draft_id: str, data: DraftUpdate, db: Session = Depends(get_db)):
    return writing_service.update_draft(db, draft_id, data)

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/accept")
def accept_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    return writing_service.accept_suggestion(db, draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/reject")
def reject_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    return writing_service.reject_suggestion(db, draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/accept-all")
def accept_all_suggestions(draft_id: str, db: Session = Depends(get_db)):
    return writing_service.accept_all_suggestions(db, draft_id)

@router.get("/drafts/{draft_id}/compare", response_model=DraftCompareResponse)
def compare_draft(draft_id: str, db: Session = Depends(get_db)):
    return writing_service.compare_draft(db, draft_id)

@router.post("/drafts/{draft_id}/style-check", response_model=StyleCheckResponse)
def style_check_draft(
    draft_id: str,
    payload: Optional[StyleCheckRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Executes an automated style-compliance audit on a writing draft against a selected Editorial Style Profile.
    """
    draft = db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing draft not found")

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
        profile = db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.is_default == True
        ).first()

    if not profile:
        profile = db.query(EditorialStyleProfile).first()

    if not profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active style profile available")

    override_content = payload.content if payload else None
    return style_analyzer.analyze_and_update_draft(db, draft, profile, override_content=override_content)


