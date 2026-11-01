from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.base import EditorialOutput
from backend.app.schemas.editorial import EditorialUpdateRequest

def create_editorial_output(
    db: Session,
    project_id: str,
    headline: str,
    content: str,
    title: Optional[str] = None,
    word_count: Optional[int] = None,
    source_references: Optional[List[Dict[str, Any]]] = None,
    draft_id: Optional[str] = None
) -> EditorialOutput:
    wc = word_count if word_count is not None else len(content.split())
    db_obj = EditorialOutput(
        project_id=project_id,
        draft_id=draft_id,
        title=title or headline,
        headline=headline,
        content=content,
        word_count=wc,
        source_references=source_references or [],
        status="DRAFT"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_editorial_outputs(db: Session, skip: int = 0, limit: int = 100) -> List[EditorialOutput]:
    return (
        db.query(EditorialOutput)
        .order_by(EditorialOutput.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_editorial_by_id(db: Session, editorial_id: str) -> Optional[EditorialOutput]:
    return db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()

def get_editorial_by_project(db: Session, project_id: str) -> Optional[EditorialOutput]:
    return (
        db.query(EditorialOutput)
        .filter(EditorialOutput.project_id == project_id)
        .order_by(EditorialOutput.created_at.desc())
        .first()
    )

def update_editorial(db: Session, db_obj: EditorialOutput, obj_in: EditorialUpdateRequest) -> EditorialOutput:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "content" in update_data and update_data["content"] is not None:
        update_data["word_count"] = len(update_data["content"].split())

    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_editorial(db: Session, editorial_id: str) -> bool:
    output = get_editorial_by_id(db, editorial_id)
    if not output:
        return False
    db.delete(output)
    db.commit()
    return True

