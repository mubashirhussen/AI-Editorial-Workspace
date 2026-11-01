from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.crud import source as crud_source
from backend.app.crud import project as crud_project
from backend.app.schemas.source import SourceCreate, SourceResponse
from backend.app.schemas.auth import OrgPermission
from backend.app.models.base import User
from backend.app.api.deps import get_current_user
from backend.app.api.v1.endpoints.projects import check_project_tenant_access

router = APIRouter(tags=["Sources"])

# Sub-router for /projects/{project_id}/sources
project_sources_router = APIRouter(tags=["Sources"])

@project_sources_router.post("/{project_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def add_source_to_project(
    project_id: str,
    payload: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a source to a project (enforcing ADD_SOURCES tenant permission)."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.ADD_SOURCES)

    # Check duplicate URL within project
    if payload.url:
        existing = db.query(crud_source.Source).filter(
            crud_source.Source.project_id == project_id,
            crud_source.Source.url == str(payload.url)
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source with this URL is already added to this project.")

    return crud_source.create_source(db, project_id, payload)

@project_sources_router.get("/{project_id}/sources", response_model=List[SourceResponse])
def list_project_sources(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all sources associated with a project (enforcing VIEW_CONTENT)."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.VIEW_CONTENT)
    return crud_source.get_sources_by_project(db, project_id, skip=skip, limit=limit)

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a source by ID."""
    source = crud_source.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.VIEW_CONTENT)
    return source

@router.put("/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: str,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update source details."""
    source = crud_source.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)
    return crud_source.update_source(db, source, payload)

@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a source."""
    source = crud_source.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)
    crud_source.delete_source(db, source_id)
    return None

@router.post("/{source_id}/extract", response_model=SourceResponse)
async def extract_source_content(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract readable content from URL."""
    source = crud_source.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)

    from backend.app.services.research import extraction_service
    return await extraction_service.extract_content(db, source)

@router.post("/{source_id}/analyze")
async def analyze_source_content(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze source content into structured components."""
    source = crud_source.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)

    from backend.app.services.research import analysis_service
    analysis = await analysis_service.analyze_source(db, source)
    return {
        "id": analysis.id,
        "source_id": analysis.source_id,
        "key_facts": analysis.key_facts,
        "analytical_insights": analysis.analytical_insights,
        "speculative_points": analysis.speculative_points,
        "created_at": analysis.created_at
    }
