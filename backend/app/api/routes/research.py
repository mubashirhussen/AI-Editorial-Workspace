from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.api.v1.endpoints.projects import check_project_tenant_access
from backend.app.models.base import User, Organization
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_db
from backend.app.models.base import ResearchProject, Source, WritingDraft, EditorialOutput
from backend.app.schemas.research import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ResearchBriefResponse
)
from backend.app.schemas.source import SourceResponse
from backend.app.services.research_service import research_service
from backend.app.services.analytics_service import analytics_service

router = APIRouter(prefix="/research", tags=["Research"])

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Provides high-level dashboard metrics for the editorial workspace."""
    total_projects = db.query(ResearchProject).count()
    total_sources = db.query(Source).count()
    total_drafts = db.query(WritingDraft).count()
    total_editorial = db.query(EditorialOutput).count()
    
    recent_projects = db.query(ResearchProject).order_by(ResearchProject.updated_at.desc()).limit(5).all()
    recent_sources = db.query(Source).order_by(Source.created_at.desc()).limit(5).all()

    return {
        "total_projects": total_projects,
        "total_sources": total_sources,
        "total_drafts": total_drafts,
        "total_editorial": total_editorial,
        "recent_projects": [
            {
                "id": p.id,
                "title": p.title,
                "status": p.status,
                "sources_count": len(p.sources),
                "has_brief": len(p.briefs) > 0,
                "updated_at": p.updated_at
            }
            for p in recent_projects
        ],
        "recent_sources": [
            {
                "id": s.id,
                "project_id": s.project_id,
                "title": s.title,
                "url": s.url,
                "status": s.extraction_status,
                "created_at": s.created_at
            }
            for s in recent_sources
        ]
    }

@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    target_org_id = getattr(data, "organization_id", None) or (org.id if org else None)
    proj = research_service.create_project(db, data, organization_id=target_org_id)
    analytics_service.track_event(db, target_org_id, "project_created")
    return proj

@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    # Scope query strictly to user's active organization (preserving unassigned legacy dev items)
    query = db.query(ResearchProject).filter(
        (ResearchProject.organization_id == org.id) | (ResearchProject.organization_id == None)
    )
    total = query.count()
    projects = query.order_by(ResearchProject.updated_at.desc()).offset(skip).limit(limit).all()
    return {"items": projects, "total": total}

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    return project

@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    return research_service.update_project(db, project_id, data)

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    research_service.delete_project(db, project_id)
    return {"success": True, "message": "Project deleted successfully."}

@router.post("/projects/{project_id}/analyze")
async def analyze_project_sources(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    sources = await research_service.analyze_project_sources(db, project_id)
    return {"success": True, "sources_analyzed": len(sources)}

@router.post("/projects/{project_id}/generate-brief", response_model=ResearchBriefResponse)
@router.post("/projects/{project_id}/brief", response_model=ResearchBriefResponse)
async def generate_brief(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    brief = await research_service.generate_research_brief(db, project_id)
    analytics_service.track_event(db, getattr(project, "organization_id", None), "brief_generated")
    return brief

@router.get("/projects/{project_id}/brief", response_model=ResearchBriefResponse)
def get_brief(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = research_service.get_project(db, project_id)
    check_project_tenant_access(db, project, current_user)
    return research_service.get_brief(db, project_id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def patch_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    """Patch project details."""
    return research_service.update_project(db, project_id, data)

@router.post("/projects/{project_id}/process")
async def process_project_pipeline(project_id: str, db: Session = Depends(get_db)):
    """Triggers analysis of all sources and synthesizes a research brief."""
    await research_service.analyze_project_sources(db, project_id)
    brief = await research_service.generate_research_brief(db, project_id)
    return {
        "status": "completed",
        "project_id": project_id,
        "brief_id": brief.id,
        "executive_summary": brief.executive_summary
    }

@router.get("/projects/{project_id}/results")
def get_project_results(project_id: str, db: Session = Depends(get_db)):
    """Retrieves full research investigation results including sources, analyses, and brief."""
    project = research_service.get_project(db, project_id)
    brief = None
    try:
        brief = research_service.get_brief(db, project_id)
    except Exception:
        pass
    
    ready = len(project.sources) >= 3 and brief is not None
    return {
        "project": project,
        "sources": project.sources,
        "brief": brief,
        "sources_count": len(project.sources),
        "is_ready_for_drafting": ready,
        "is_ready_for_editorial": ready,
        "ready_for_editorial": ready
    }

@router.get("/projects/{project_id}/sources", response_model=List[SourceResponse])
def get_project_sources_list(project_id: str, db: Session = Depends(get_db)):
    """List sources belonging to a research project."""
    return research_service.get_project_sources(db, project_id)
