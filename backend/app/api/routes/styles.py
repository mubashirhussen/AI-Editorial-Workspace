import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import EditorialStyleProfile, User, Organization
from backend.app.schemas.style import (
    StyleProfileCreate,
    StyleProfileUpdate,
    StyleProfileResponse
)
from backend.app.api.deps import get_current_user, get_active_organization

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/styles", tags=["editorial-styles"])

@router.post("", response_model=StyleProfileResponse, status_code=status.HTTP_201_CREATED)
def create_style_profile(
    payload: StyleProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Creates a new customized Editorial Style Profile for the tenant organization.
    """
    # If set as default, unset other defaults in this organization
    if payload.is_default:
        db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id == active_org.id
        ).update({"is_default": False})

    profile = EditorialStyleProfile(
        organization_id=active_org.id,
        name=payload.name,
        publication_name=payload.publication_name,
        tone=payload.tone,
        target_audience=payload.target_audience,
        max_sentence_length=payload.max_sentence_length,
        preferred_sentence_length=payload.preferred_sentence_length,
        max_paragraph_length=payload.max_paragraph_length,
        target_flesch_score=payload.target_flesch_score,
        preferred_terminology=payload.preferred_terminology,
        words_to_avoid=payload.words_to_avoid,
        headline_style=payload.headline_style,
        formatting_preferences=payload.formatting_preferences,
        is_default=payload.is_default
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("", response_model=List[StyleProfileResponse])
def list_style_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Lists all style profiles accessible to the user (organization profiles + system global templates).
    """
    profiles = db.query(EditorialStyleProfile).filter(
        (EditorialStyleProfile.organization_id == active_org.id) |
        (EditorialStyleProfile.organization_id.is_(None))
    ).order_by(EditorialStyleProfile.is_default.desc(), EditorialStyleProfile.name).all()
    return profiles

@router.get("/{style_id}", response_model=StyleProfileResponse)
def get_style_profile(
    style_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves a specific style profile.
    """
    profile = db.query(EditorialStyleProfile).filter(
        EditorialStyleProfile.id == style_id
    ).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    # Isolation check: Must be system default or belong to active organization
    if profile.organization_id and profile.organization_id != active_org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    return profile

@router.put("/{style_id}", response_model=StyleProfileResponse)
def update_style_profile(
    style_id: str,
    payload: StyleProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Updates an existing style profile.
    """
    profile = db.query(EditorialStyleProfile).filter(
        EditorialStyleProfile.id == style_id
    ).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    if profile.organization_id and profile.organization_id != active_org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    # If setting as default, clear others
    if payload.is_default is True and active_org:
        db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id == active_org.id,
            EditorialStyleProfile.id != profile.id
        ).update({"is_default": False})

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile

@router.delete("/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_style_profile(
    style_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Deletes a custom style profile.
    """
    profile = db.query(EditorialStyleProfile).filter(
        EditorialStyleProfile.id == style_id
    ).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    if profile.organization_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System default style profile cannot be deleted")

    if profile.organization_id != active_org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found")

    db.delete(profile)
    db.commit()
    return None

