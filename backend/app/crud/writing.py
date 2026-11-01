from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.models.base import WritingDraft, WritingSuggestion
from backend.app.schemas.writing import DraftCreate, DraftUpdate

def create_draft(db: Session, obj_in: DraftCreate) -> WritingDraft:
    word_count = len(obj_in.original_content.split())
    db_obj = WritingDraft(
        project_id=obj_in.project_id,
        title=obj_in.title or "Draft Article",
        original_content=obj_in.original_content,
        revised_content=obj_in.original_content,
        word_count=word_count,
        status="DRAFT"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_drafts(db: Session, skip: int = 0, limit: int = 100) -> List[WritingDraft]:
    return (
        db.query(WritingDraft)
        .order_by(WritingDraft.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_draft_by_id(db: Session, draft_id: str) -> Optional[WritingDraft]:
    return db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()

def update_draft(db: Session, db_obj: WritingDraft, obj_in: DraftUpdate) -> WritingDraft:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "revised_content" in update_data and update_data["revised_content"] is not None:
        update_data["word_count"] = len(update_data["revised_content"].split())

    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_draft(db: Session, draft_id: str) -> bool:
    draft = get_draft_by_id(db, draft_id)
    if not draft:
        return False
    db.delete(draft)
    db.commit()
    return True

def create_suggestion(db: Session, draft_id: str, suggestion_data: dict) -> WritingSuggestion:
    sugg = WritingSuggestion(
        draft_id=draft_id,
        category=suggestion_data.get("category", "complexity"),
        severity=suggestion_data.get("severity", "medium"),
        original_text=suggestion_data.get("original_text", ""),
        suggested_text=suggestion_data.get("suggested_text") or suggestion_data.get("suggested_rewrite", ""),
        suggested_rewrite=suggestion_data.get("suggested_rewrite") or suggestion_data.get("suggested_text", ""),
        explanation=suggestion_data.get("explanation", ""),
        start_offset=suggestion_data.get("start_offset"),
        end_offset=suggestion_data.get("end_offset"),
        reason=suggestion_data.get("reason", ""),
        confidence=suggestion_data.get("confidence", 0.9),
        status="PENDING"
    )
    db.add(sugg)
    db.commit()
    db.refresh(sugg)
    return sugg

def get_suggestions_by_draft(db: Session, draft_id: str) -> List[WritingSuggestion]:
    return db.query(WritingSuggestion).filter(WritingSuggestion.draft_id == draft_id).all()

