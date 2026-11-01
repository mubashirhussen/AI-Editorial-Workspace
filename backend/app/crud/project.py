from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.base import ResearchProject
from backend.app.schemas.research import ProjectCreate, ProjectUpdate

def create_project(db: Session, obj_in: ProjectCreate, organization_id: Optional[str] = None) -> ResearchProject:
    title = obj_in.title or getattr(obj_in, "name", None) or "Untitled Project"
    name = getattr(obj_in, "name", None) or title
    db_obj = ResearchProject(
        title=title,
        name=name,
        description=obj_in.description,
        status="draft",
        organization_id=organization_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_projects(db: Session, skip: int = 0, limit: int = 100, organization_id: Optional[str] = None) -> List[ResearchProject]:
    query = db.query(ResearchProject)
    if organization_id:
        query = query.filter(ResearchProject.organization_id == organization_id)
    return (
        query
        .order_by(ResearchProject.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def count_projects(db: Session, organization_id: Optional[str] = None) -> int:
    query = db.query(ResearchProject)
    if organization_id:
        query = query.filter(ResearchProject.organization_id == organization_id)
    return query.count()

def get_project_by_id(db: Session, project_id: str, organization_id: Optional[str] = None) -> Optional[ResearchProject]:
    query = db.query(ResearchProject).filter(ResearchProject.id == project_id)
    if organization_id:
        query = query.filter(ResearchProject.organization_id == organization_id)
    return query.first()

def update_project(db: Session, db_obj: ResearchProject, obj_in: ProjectUpdate) -> ResearchProject:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "name" in update_data and "title" not in update_data:
        update_data["title"] = update_data["name"]
    elif "title" in update_data and "name" not in update_data:
        update_data["name"] = update_data["title"]

    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_project(db: Session, project_id: str, organization_id: Optional[str] = None) -> bool:
    project = get_project_by_id(db, project_id, organization_id=organization_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True
