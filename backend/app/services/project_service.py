from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import ResearchProject
from backend.app.schemas.research import ProjectCreate, ProjectUpdate

class ProjectService:
    @staticmethod
    def create_project(db: Session, data: ProjectCreate) -> ResearchProject:
        project = ResearchProject(
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            status="draft"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_projects(db: Session, skip: int = 0, limit: int = 50) -> List[ResearchProject]:
        return db.query(ResearchProject).order_by(ResearchProject.updated_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_project(db: Session, project_id: str) -> ResearchProject:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Research project not found")
        return project

    @staticmethod
    def update_project(db: Session, project_id: str, data: ProjectUpdate) -> ResearchProject:
        project = ProjectService.get_project(db, project_id)
        if data.title is not None:
            project.title = data.title.strip()
        if data.description is not None:
            project.description = data.description.strip()
        if data.status is not None:
            project.status = data.status
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        project = ProjectService.get_project(db, project_id)
        db.delete(project)
        db.commit()
        return True

project_service = ProjectService()

