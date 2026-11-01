import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.base import User, Organization, OrganizationMembership, OrganizationInvitation
from backend.app.schemas.auth import (
    OrgRole,
    OrgPermission,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    MembershipResponse,
    RoleUpdateRequest,
    InvitationCreate,
    InvitationResponse,
    InvitationAcceptRequest,
    UserResponse
)
from backend.app.api.deps import get_current_user, get_active_organization, require_permission

router = APIRouter(prefix="/organizations", tags=["Organizations & Workspaces"])

@router.get("", response_model=List[OrganizationResponse])
def list_user_organizations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all organizations where the current user holds membership."""
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id
    ).all()

    results = []
    for mem in memberships:
        if mem.organization:
            results.append(
                OrganizationResponse(
                    id=mem.organization.id,
                    name=mem.organization.name,
                    slug=mem.organization.slug,
                    role=mem.role,
                    created_at=mem.organization.created_at
                )
            )
    return results


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new organization and grants current user the OWNER role."""
    base_slug = payload.slug or payload.name.strip().lower().replace(" ", "-")
    unique_slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"

    org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        slug=unique_slug
    )
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER.value
    )
    db.add(membership)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role=OrgRole.OWNER.value,
        created_at=org.created_at
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization_details(
    org_id: str,
    org: Organization = Depends(get_active_organization)
):
    """Gets organization details (membership strictly verified)."""
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role=getattr(org, "current_user_role", None),
        created_at=org.created_at
    )


@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    org: Organization = Depends(require_permission(OrgPermission.MANAGE_ORG_LIMITED)),
    db: Session = Depends(get_db)
):
    """Updates organization name or slug (requires OWNER or ADMIN)."""
    if payload.name:
        org.name = payload.name.strip()
    if payload.slug:
        existing = db.query(Organization).filter(Organization.slug == payload.slug, Organization.id != org.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Organization slug is already in use.")
        org.slug = payload.slug.strip()

    org.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role=getattr(org, "current_user_role", None),
        created_at=org.created_at
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    org_id: str,
    org: Organization = Depends(require_permission(OrgPermission.MANAGE_ORG)),
    db: Session = Depends(get_db)
):
    """Deletes an entire organization and cascades to projects and drafts (requires OWNER)."""
    db.delete(org)
    db.commit()
    return None


# ================= MEMBERSHIP & ROLES =================

@router.get("/{org_id}/members", response_model=List[MembershipResponse])
def list_organization_members(
    org_id: str,
    org: Organization = Depends(require_permission(OrgPermission.VIEW_CONTENT)),
    db: Session = Depends(get_db)
):
    """Lists all members of the organization."""
    memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org.id
    ).all()

    return [
        MembershipResponse(
            id=mem.id,
            organization_id=mem.organization_id,
            user_id=mem.user_id,
            role=mem.role,
            joined_at=mem.joined_at,
            user=UserResponse.model_validate(mem.user) if mem.user else None
        )
        for mem in memberships
    ]


@router.put("/{org_id}/members/{user_id}/role", response_model=MembershipResponse)
def update_member_role(
    org_id: str,
    user_id: str,
    payload: RoleUpdateRequest,
    org: Organization = Depends(get_active_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates a member's role (enforcing strict permission boundaries)."""
    current_role = getattr(org, "current_user_role", None)
    if current_role not in [OrgRole.OWNER.value, OrgRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Only Owners and Admins can update roles.")

    # Target member
    target_mem = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=404, detail="Member not found in organization.")

    # Admins cannot alter an OWNER's role or promote to OWNER/ADMIN
    if current_role == OrgRole.ADMIN.value:
        if target_mem.role in [OrgRole.OWNER.value, OrgRole.ADMIN.value]:
            raise HTTPException(status_code=403, detail="Admins cannot modify Owners or fellow Admins.")
        if payload.role in [OrgRole.OWNER, OrgRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Admins cannot promote members to Owner or Admin.")

    target_mem.role = payload.role.value
    db.commit()
    db.refresh(target_mem)

    return MembershipResponse(
        id=target_mem.id,
        organization_id=target_mem.organization_id,
        user_id=target_mem.user_id,
        role=target_mem.role,
        joined_at=target_mem.joined_at,
        user=UserResponse.model_validate(target_mem.user) if target_mem.user else None
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_organization_member(
    org_id: str,
    user_id: str,
    org: Organization = Depends(get_active_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a member from the organization."""
    current_role = getattr(org, "current_user_role", None)
    if current_role not in [OrgRole.OWNER.value, OrgRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Only Owners and Admins can remove members.")

    target_mem = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == user_id
    ).first()
    if not target_mem:
        raise HTTPException(status_code=404, detail="Member not found in organization.")

    # Owners cannot be removed
    if target_mem.role == OrgRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot remove the organization Owner.")

    # Admins cannot remove fellow admins
    if current_role == OrgRole.ADMIN.value and target_mem.role == OrgRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admins cannot remove fellow Admins.")

    db.delete(target_mem)
    db.commit()
    return None


# ================= INVITATIONS =================

@router.post("/{org_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def create_invitation(
    org_id: str,
    payload: InvitationCreate,
    org: Organization = Depends(require_permission(OrgPermission.INVITE_MEMBERS)),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invites a user to join the organization (expires in 7 days)."""
    email_clean = payload.email.strip().lower()

    # Check if target user already belongs to org
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        existing_mem = db.query(OrganizationMembership).filter(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == existing_user.id
        ).first()
        if existing_mem:
            raise HTTPException(status_code=400, detail="User is already a member of this organization.")

    # Check for active pending invitation
    active_inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == org.id,
        OrganizationInvitation.email == email_clean,
        OrganizationInvitation.accepted_at == None,
        OrganizationInvitation.expires_at > datetime.now(timezone.utc)
    ).first()
    if active_inv:
        return InvitationResponse(
            id=active_inv.id,
            organization_id=active_inv.organization_id,
            email=active_inv.email,
            role=active_inv.role,
            token=active_inv.token,
            expires_at=active_inv.expires_at,
            created_at=active_inv.created_at,
            is_expired=False
        )

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = OrganizationInvitation(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=email_clean,
        role=payload.role.value,
        token=token,
        invited_by_id=current_user.id,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        organization_id=invitation.organization_id,
        email=invitation.email,
        role=invitation.role,
        token=invitation.token,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        is_expired=False
    )


def is_invitation_expired(exp: datetime) -> bool:
    if exp is None:
        return False
    now = datetime.now(timezone.utc)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp < now

@router.get("/{org_id}/invitations", response_model=List[InvitationResponse])
def list_pending_invitations(
    org_id: str,
    org: Organization = Depends(require_permission(OrgPermission.INVITE_MEMBERS)),
    db: Session = Depends(get_db)
):
    """Lists all active and pending invitations for the organization."""
    invitations = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.organization_id == org.id,
        OrganizationInvitation.accepted_at == None
    ).order_by(OrganizationInvitation.created_at.desc()).all()

    return [
        InvitationResponse(
            id=inv.id,
            organization_id=inv.organization_id,
            email=inv.email,
            role=inv.role,
            token=inv.token,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            is_expired=is_invitation_expired(inv.expires_at)
        )
        for inv in invitations
    ]


@router.delete("/{org_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    org_id: str,
    invitation_id: str,
    org: Organization = Depends(require_permission(OrgPermission.INVITE_MEMBERS)),
    db: Session = Depends(get_db)
):
    """Revokes a pending invitation."""
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.id == invitation_id,
        OrganizationInvitation.organization_id == org.id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    db.delete(inv)
    db.commit()
    return None


@router.post("/invitations/{token}/accept", response_model=MembershipResponse)
def accept_invitation(
    token: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accepts an organization invitation using its secure token."""
    now = datetime.now(timezone.utc)
    inv = db.query(OrganizationInvitation).filter(
        OrganizationInvitation.token == token
    ).first()

    if not inv:
        raise HTTPException(status_code=404, detail="Invalid invitation token.")

    if inv.accepted_at is not None:
        raise HTTPException(status_code=400, detail="This invitation has already been accepted.")

    # Check expiration (handling offset-naive or offset-aware)
    exp = inv.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        raise HTTPException(status_code=400, detail="This invitation has expired.")

    # Check if membership already exists
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == inv.organization_id,
        OrganizationMembership.user_id == user.id
    ).first()
    if existing:
        inv.accepted_at = now
        db.commit()
        return MembershipResponse(
            id=existing.id,
            organization_id=existing.organization_id,
            user_id=existing.user_id,
            role=existing.role,
            joined_at=existing.joined_at,
            user=UserResponse.model_validate(user)
        )

    # Create new membership
    membership = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=inv.organization_id,
        user_id=user.id,
        role=inv.role,
        joined_at=now
    )
    inv.accepted_at = now
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return MembershipResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        role=membership.role,
        joined_at=membership.joined_at,
        user=UserResponse.model_validate(user)
    )
