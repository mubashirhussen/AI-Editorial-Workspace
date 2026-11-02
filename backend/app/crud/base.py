from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Centralized, type-safe CRUD repository providing multi-tenant isolation,
    query pagination, soft-deletion handling, and optimistic updates.
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any, organization_id: Optional[str] = None) -> Optional[ModelType]:
        query = db.query(self.model).filter(self.model.id == id)
        if organization_id and hasattr(self.model, "organization_id"):
            query = query.filter(self.model.organization_id == organization_id)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[ModelType]:
        query = db.query(self.model)
        if organization_id and hasattr(self.model, "organization_id"):
            query = query.filter(self.model.organization_id == organization_id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        if hasattr(self.model, "created_at"):
            query = query.order_by(self.model.created_at.desc())
        return query.offset(skip).limit(limit).all()

    def count(
        self,
        db: Session,
        *,
        organization_id: Optional[str] = None,
        include_deleted: bool = False
    ) -> int:
        query = db.query(func.count(self.model.id))
        if organization_id and hasattr(self.model, "organization_id"):
            query = query.filter(self.model.organization_id == organization_id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        return query.scalar() or 0

    def paginate(
        self,
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size
        items = self.get_multi(db, skip=skip, limit=page_size, organization_id=organization_id)
        total = self.count(db, organization_id=organization_id)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    def soft_delete(self, db: Session, *, id: str, organization_id: Optional[str] = None) -> bool:
        obj = self.get(db, id=id, organization_id=organization_id)
        if not obj:
            return False
        if hasattr(obj, "deleted_at"):
            setattr(obj, "deleted_at", datetime.now(timezone.utc))
            db.add(obj)
            db.commit()
            return True
        # If model doesn't support soft delete, hard delete
        db.delete(obj)
        db.commit()
        return True

    def remove(self, db: Session, *, id: str, organization_id: Optional[str] = None) -> bool:
        obj = self.get(db, id=id, organization_id=organization_id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

