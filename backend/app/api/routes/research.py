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
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    return research_service.create_project(db, data)

@router.get("/projects", response_model=ProjectListResponse)
def list_projects(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    projects = research_service.get_projects(db, skip=skip, limit=limit)
    total = db.query(ResearchProject).count()
    return {"items": projects, "total": total}

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return research_service.get_project(db, project_id)

@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    return research_service.update_project(db, project_id, data)

@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    research_service.delete_project(db, project_id)
    return {"success": True, "message": "Project deleted successfully."}

@router.post("/projects/{project_id}/analyze")
async def analyze_project_sources(project_id: str, db: Session = Depends(get_db)):
    sources = await research_service.analyze_project_sources(db, project_id)
    return {"success": True, "sources_analyzed": len(sources)}

@router.post("/projects/{project_id}/generate-brief", response_model=ResearchBriefResponse)
async def generate_brief(project_id: str, db: Session = Depends(get_db)):
    return await research_service.generate_research_brief(db, project_id)

@router.get("/projects/{project_id}/brief", response_model=ResearchBriefResponse)
def get_brief(project_id: str, db: Session = Depends(get_db)):
    return research_service.get_brief(db, project_id)

