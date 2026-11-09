import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import hash_token
from backend.app.models.base import User, UserSession
from backend.app.schemas.auth import (
    UserResponse,
    UserProfileUpdateRequest,
    UserSessionResponse,
)
from backend.app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Fetches the authenticated user's complete profile information."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_user_profile(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates permitted profile fields (full_name, profile_image).
    Guarantees role, email, and privileges cannot be escalated.
    """
    if payload.full_name is not None:
        name_clean = payload.full_name.strip()
        if len(name_clean) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name must be at least 2 characters long."
            )
        current_user.full_name = name_clean

    if payload.profile_image is not None:
        current_user.profile_image = payload.profile_image

    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/me/sessions", response_model=List[UserSessionResponse])
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Lists all active and unrevoked login sessions for the authenticated user."""
    current_token_hash = None
    if authorization and authorization.lower().startswith("bearer "):
        current_token_hash = hash_token(authorization[7:].strip())

    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False
    ).order_by(UserSession.created_at.desc()).all()

    result = []
    for s in sessions:
        res = UserSessionResponse(
            id=s.id,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            created_at=s.created_at,
            last_activity_at=s.last_activity_at or s.created_at,
            expires_at=s.expires_at,
            is_current=(s.token_hash == current_token_hash)
        )
        result.append(res)
    return result


@router.delete("/me/sessions/{session_id}")
def revoke_user_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes a specific active session belonging to the authenticated user."""
    session_rec = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id
    ).first()

    if not session_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or does not belong to you."
        )

    session_rec.is_revoked = True
    db.commit()
    return {"success": True, "message": "Session revoked successfully."}
