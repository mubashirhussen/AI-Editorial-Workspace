from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.base import Source, SourceAnalysis
from backend.app.schemas.source import SourceCreate

def create_source(db: Session, project_id: str, obj_in: SourceCreate) -> Source:
    url = obj_in.url or getattr(obj_in, "original_url", None)
    source_type = (obj_in.source_type or "URL").upper()
    title = obj_in.title or (url if url else "Pasted Source Text")
    raw_content = getattr(obj_in, "text_content", None) or getattr(obj_in, "raw_content", None)
    
    db_obj = Source(
        project_id=project_id,
        title=title,
        url=str(url) if url else None,
        original_url=str(url) if url else None,
        source_type=source_type,
        raw_content=raw_content,
        extracted_content=raw_content,
        extraction_status="COMPLETED" if raw_content else "PENDING"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_sources_by_project(db: Session, project_id: str, skip: int = 0, limit: int = 100) -> List[Source]:
    return (
        db.query(Source)
        .filter(Source.project_id == project_id)
        .order_by(Source.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_source_by_id(db: Session, source_id: str) -> Optional[Source]:
    return db.query(Source).filter(Source.id == source_id).first()

def update_source(db: Session, db_obj: Source, update_data: dict) -> Source:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_source(db: Session, source_id: str) -> bool:
    source = get_source_by_id(db, source_id)
    if not source:
        return False
    db.delete(source)
    db.commit()
    return True

def create_or_update_analysis(db: Session, source_id: str, analysis_data: dict) -> SourceAnalysis:
    db_obj = db.query(SourceAnalysis).filter(SourceAnalysis.source_id == source_id).first()
    if not db_obj:
        db_obj = SourceAnalysis(source_id=source_id)
        db.add(db_obj)

    for field, value in analysis_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)

    db.commit()
    db.refresh(db_obj)
    return db_obj

