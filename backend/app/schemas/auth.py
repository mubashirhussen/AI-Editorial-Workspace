from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Set
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class OrgRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    REVIEWER = "REVIEWER"
    VIEWER = "VIEWER"

class OrgPermission(str, Enum):
    MANAGE_ORG = "manage_org"
    MANAGE_ORG_LIMITED = "manage_org_limited"
    INVITE_MEMBERS = "invite_members"
    CREATE_PROJECTS = "create_projects"
    ADD_SOURCES = "add_sources"
    EDIT_DRAFTS = "edit_drafts"
    REVIEW_EDITORIALS = "review_editorials"
    REVIEW_EDITORIALS_LIMITED = "review_editorials_limited"
    APPROVE_EDITORIALS = "approve_editorials"
    VIEW_CONTENT = "view_content"

# Explicit permission mapping corresponding strictly to assignment requirements
ROLE_PERMISSIONS: dict[OrgRole, Set[str]] = {
    OrgRole.OWNER: {
        OrgPermission.MANAGE_ORG,
        OrgPermission.MANAGE_ORG_LIMITED,
        OrgPermission.INVITE_MEMBERS,
        OrgPermission.CREATE_PROJECTS,
        OrgPermission.ADD_SOURCES,
        OrgPermission.EDIT_DRAFTS,
        OrgPermission.REVIEW_EDITORIALS,
        OrgPermission.REVIEW_EDITORIALS_LIMITED,
        OrgPermission.APPROVE_EDITORIALS,
        OrgPermission.VIEW_CONTENT,
    },
    OrgRole.ADMIN: {
        OrgPermission.MANAGE_ORG_LIMITED,
        OrgPermission.INVITE_MEMBERS,
        OrgPermission.CREATE_PROJECTS,
        OrgPermission.ADD_SOURCES,
        OrgPermission.EDIT_DRAFTS,
        OrgPermission.REVIEW_EDITORIALS,
        OrgPermission.REVIEW_EDITORIALS_LIMITED,
        OrgPermission.APPROVE_EDITORIALS,
        OrgPermission.VIEW_CONTENT,
    },
    OrgRole.EDITOR: {
        OrgPermission.CREATE_PROJECTS,
        OrgPermission.ADD_SOURCES,
        OrgPermission.EDIT_DRAFTS,
        OrgPermission.REVIEW_EDITORIALS_LIMITED,
        OrgPermission.VIEW_CONTENT,
    },
    OrgRole.REVIEWER: {
        OrgPermission.REVIEW_EDITORIALS,
        OrgPermission.APPROVE_EDITORIALS,
        OrgPermission.VIEW_CONTENT,
    },
    OrgRole.VIEWER: {
        OrgPermission.VIEW_CONTENT,
    },
}

def has_permission(role: str, permission: OrgPermission) -> bool:
    try:
        org_role = OrgRole(role.upper())
        return permission in ROLE_PERMISSIONS.get(org_role, set())
    except Exception:
        return False

# ================= AUTH SCHEMAS =================

class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)
    organization_name: Optional[str] = Field(None, max_length=255)

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    role: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: Optional[OrganizationResponse] = None

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=255)

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, min_length=2, max_length=255)

class MembershipResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None
    model_config = ConfigDict(from_attributes=True)

class RoleUpdateRequest(BaseModel):
    role: OrgRole

class InvitationCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    role: OrgRole = OrgRole.EDITOR

class InvitationResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    token: str
    expires_at: datetime
    created_at: datetime
    is_expired: bool = False
    model_config = ConfigDict(from_attributes=True)

class InvitationAcceptRequest(BaseModel):
    token: str



class PasswordResetRequest(BaseModel):
    email: str = Field(..., max_length=255)
    new_password: str = Field(..., min_length=8, max_length=128)

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
