from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.models.base import Source, User
from backend.app.schemas.source import SourceCreate, SourceUpdate, SourceResponse, SourceListResponse, SourceAnalysisSchema
from backend.app.schemas.auth import OrgPermission
from backend.app.services.research_service import research_service
from backend.app.api.deps import get_current_user
from backend.app.api.v1.endpoints.projects import check_project_tenant_access

router = APIRouter(tags=["Sources"])

@router.post("/research/projects/{project_id}/sources", response_model=SourceResponse, status_code=201)
async def add_source(
    project_id: str,
    data: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = await research_service.add_source(db, project_id, data)
    return source

@router.get("/research/projects/{project_id}/sources", response_model=List[SourceResponse])
def list_project_sources(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sources = db.query(Source).filter(Source.project_id == project_id).order_by(Source.created_at.asc()).all()
    return sources

@router.get("/sources/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.VIEW_CONTENT)
    return source

@router.put("/sources/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: str,
    data: SourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)

    if data.title and data.title.strip():
        source.title = data.title.strip()

    content = data.text_content or data.raw_content
    if content and content.strip():
        cleaned = content.strip()
        source.raw_content = cleaned
        source.extracted_content = cleaned
        source.extraction_status = "completed"
        source.error_message = None
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            source.summary = lines[0][:280]

    db.commit()
    db.refresh(source)
    return source

@router.delete("/sources/{source_id}")
def delete_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)
    db.delete(source)
    db.commit()
    return {"success": True, "message": "Source removed successfully."}

@router.post("/sources/{source_id}/extract", response_model=SourceResponse)
async def extract_source_content(source_id: str, db: Session = Depends(get_db)):
    source = await research_service.extract_source(db, source_id)
    return source

@router.post("/sources/{source_id}/analyze")
async def analyze_source(source_id: str, db: Session = Depends(get_db)):
    analysis = await research_service.analyze_single_source(db, source_id)
    return {"success": True, "analysis_id": analysis.id}

@router.get("/sources/{source_id}/analysis")
def get_source_analysis(source_id: str, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    if not source.analyses:
        raise HTTPException(status_code=404, detail="Source analysis not found.")
    return source.analyses

