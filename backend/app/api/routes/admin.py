import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import User
from backend.app.schemas.auth import (
    UserResponse,
    AdminUserStatusUpdate,
    AdminUserRoleUpdate,
)
from backend.app.api.deps import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get("/users")
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: lists all registered users with search and pagination."""
    query = db.query(User)
    if search:
        s_clean = f"%{search.strip().lower()}%"
        query = query.filter((User.email.ilike(s_clean)) | (User.full_name.ilike(s_clean)))

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": (skip // limit) + 1,
        "page_size": limit
    }


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: retrieves detailed profile for any specific user."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return UserResponse.model_validate(target_user)


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: str,
    payload: AdminUserStatusUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: activates or deactivates a user account (prevents self-deactivation)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    if target_user.id == admin_user.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active account."
        )

    target_user.is_active = payload.is_active
    db.commit()
    db.refresh(target_user)
    return UserResponse.model_validate(target_user)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    payload: AdminUserRoleUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only: elevates or downgrades user system privileges (ADMIN vs USER)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    target_user.role = payload.role
    db.commit()
    db.refresh(target_user)
    return UserResponse.model_validate(target_user)

