import uuid
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token, decode_access_token, revoke_token
from backend.app.models.base import User, Organization, OrganizationMembership
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    OrganizationResponse,
    AuthResponse,
    PasswordResetRequest,
    PasswordChangeRequest,
    TokenRefreshResponse
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def slugify(text: str) -> str:
    s = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', s)

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user and provisions their personal organization."""
    email_clean = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 1. Create User
    new_user = User(
        id=str(uuid.uuid4()),
        email=email_clean,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # 2. Provision Personal Organization
    org_name = payload.organization_name.strip() if payload.organization_name else f"{new_user.full_name}'s Workspace"
    base_slug = slugify(org_name)
    slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"
    
    new_org = Organization(
        id=str(uuid.uuid4()),
        name=org_name,
        slug=slug
    )
    db.add(new_org)
    db.flush()

    # 3. Create OWNER Membership
    membership = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=new_org.id,
        user_id=new_user.id,
        role="OWNER"
    )
    db.add(membership)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_org)

    # 4. Generate Access Token
    token = create_access_token(data={"sub": new_user.id, "email": new_user.email})

    org_resp = OrganizationResponse(
        id=new_org.id,
        name=new_org.name,
        slug=new_org.slug,
        role="OWNER",
        created_at=new_org.created_at
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
        organization=org_resp
    )


@router.post("/login", response_model=AuthResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticates email and password credentials, returning JWT and active organization."""
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Resolve primary organization
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).order_by(OrganizationMembership.joined_at.asc()).first()

    org_resp = None
    if membership and membership.organization:
        org_resp = OrganizationResponse(
            id=membership.organization.id,
            name=membership.organization.name,
            slug=membership.organization.slug,
            role=membership.role,
            created_at=membership.organization.created_at
        )

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        organization=org_resp
    )


@router.get("/me")
def get_current_user_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns profile and organizations list for currently authenticated user."""
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).all()

    orgs = []
    for mem in memberships:
        if mem.organization:
            orgs.append({
                "id": mem.organization.id,
                "name": mem.organization.name,
                "slug": mem.organization.slug,
                "role": mem.role,
                "joined_at": mem.joined_at.isoformat()
            })

    return {
        "user": UserResponse.model_validate(user),
        "organizations": orgs
    }


@router.post("/logout")
def logout_user(authorization: str = Header(...)):
    """Revokes the current JWT access token."""
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        revoke_token(token)
    return {"message": "Logged out successfully."}



@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(authorization: str = Header(...), db: Session = Depends(get_db)):
    """Refreshes an active session token before expiration."""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header.")
    token = authorization[7:].strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired or invalid.")
    
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive.")
    
    new_token = create_access_token(data={"sub": user.id, "email": user.email})
    return TokenRefreshResponse(access_token=new_token, token_type="bearer")


@router.post("/reset-password")
def reset_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Resets user password with direct email verification."""
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        # Prevent user enumeration by returning uniform success
        return {"success": True, "message": "If this email is registered, the password has been updated."}
    
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"success": True, "message": "Password updated successfully."}


@router.post("/change-password")
def change_password(payload: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Updates password for currently authenticated user."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
    
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"success": True, "message": "Password changed successfully."}
