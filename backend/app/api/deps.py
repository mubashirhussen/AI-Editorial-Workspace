from typing import Optional
from fastapi import Depends, HTTPException, Header, Query, Request, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.base import User, Organization, OrganizationMembership
from backend.app.schemas.auth import OrgPermission, has_permission

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None)
) -> User:
    """
    Extracts and authenticates the user from Bearer JWT.
    Supports backward-compatible fallback to the default owner in development.
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    
    if token:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload["sub"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )
        return user

    # Fallback for single-tenant backward compatibility during local development & legacy tests
    if settings.ALLOW_ANONYMOUS_DEV:
        default_user = db.query(User).filter(User.email == "owner@editorial.ai").first()
        if not default_user:
            # Dynamically provision default user and org for clean test database runs
            default_user = User(
                id="default-user-uuid-000000000000",
                email="owner@editorial.ai",
                hashed_password="$2b$12$e6/K8Vf0XQeU5b8mZcM5v.o38sY8O4i6B7V2yGf3sW3U/sK6V5m6K",
                full_name="Lead Editor",
                is_active=True
            )
            db.add(default_user)
            db.flush()

            default_org = db.query(Organization).filter(Organization.id == "default-org-uuid-000000000000").first()
            if not default_org:
                default_org = Organization(
                    id="default-org-uuid-000000000000",
                    name="Personal Workspace",
                    slug="default-workspace"
                )
                db.add(default_org)
                db.flush()

            membership = OrganizationMembership(
                id="default-mem-uuid-000000000000",
                organization_id=default_org.id,
                user_id=default_user.id,
                role="OWNER"
            )
            db.add(membership)
            db.commit()
            db.refresh(default_user)

        return default_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials were not provided.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_active_organization(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id")
) -> Organization:
    """
    Resolves and verifies active organization membership for current user.
    Never trusts client-supplied organization_id without checking database membership.
    """
    target_org_id = (
        x_organization_id or 
        request.path_params.get("org_id") or 
        request.query_params.get("org_id")
    )
    
    if not target_org_id:
        # Default to first active membership of the user
        membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user.id
        ).order_by(OrganizationMembership.joined_at.asc()).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not belong to any active organization."
            )
        target_org_id = membership.organization_id
    else:
        # Verify explicitly requested organization against database membership
        membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == target_org_id,
            OrganizationMembership.user_id == user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User '{user.email}' is not a member of organization '{target_org_id}'."
            )

    org = db.query(Organization).filter(Organization.id == target_org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    # Attach verified user role to the organization object for downstream permission checks
    setattr(org, "current_user_role", membership.role)
    return org


def require_permission(permission: OrgPermission):
    """Factory creating dependency to enforce granular role-based permissions."""
    def permission_checker(
        org: Organization = Depends(get_active_organization),
    ) -> Organization:
        role = getattr(org, "current_user_role", None)
        if not role or not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is not authorized to perform '{permission.value}' in this organization."
            )
        return org
    return permission_checker
