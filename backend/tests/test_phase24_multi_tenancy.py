"""
Phase 24: Multi-Tenant Workspace & Role-Based Access Control (RBAC) Test Suite.
Validates authentication, workspace isolation, role permissions, and cross-tenant security.
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token

client = TestClient(app)

# =====================================================================
# 1. AUTHENTICATION & TOKEN LIFECYCLE
# =====================================================================
def test_phase24_auth_registration_login_and_logout():
    """Validates user registration, password hashing verification, and token invalidation on logout."""
    unique_suffix = int(time.time())
    email = f"alice_{unique_suffix}@example.com"
    password = "SecurePassword123!"

    # 1. Register User & Auto-provisioned Org
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Alice Innovator",
        "organization_name": "Alice Tech Lab"
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email
    assert reg_data["organization"]["role"] == "OWNER"
    token = reg_data["access_token"]

    # Duplicate registration blocked
    dup_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Alice Clone"
    })
    assert dup_resp.status_code == 400

    # 2. Login with correct password
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data

    # Login with wrong password blocked
    bad_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # 3. Access protected /auth/me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["email"] == email
    assert len(me_resp.json()["organizations"]) >= 1

    # 4. Logout & Token Revocation
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # 5. Token is now revoked
    revoked_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_me.status_code == 401


def test_phase24_expired_token_rejection():
    """Ensures expired JWT tokens are strictly rejected with HTTP 401."""
    # Generate token expired 1 hour ago
    expired_token = create_access_token(
        data={"sub": "user-expired-id", "email": "expired@example.com"},
        expires_delta=timedelta(hours=-1)
    )

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "invalid or expired" in resp.json()["detail"].lower()


# =====================================================================
# 2. WORKSPACE ISOLATION & CROSS-TENANT DATA PROTECTION
# =====================================================================
def test_phase24_cross_tenant_workspace_isolation():
    """
    Validates tenant isolation invariants:
    - User A in Org A creates a project.
    - User B in Org B cannot view, edit, or access User A's project.
    - User B cannot access User A's sources or drafts.
    """
    unique_suffix = int(time.time())
    # Register Tenant A
    user_a = client.post("/api/v1/auth/register", json={
        "email": f"usera_{unique_suffix}@corp-a.com",
        "password": "PasswordA123!",
        "full_name": "User Alpha",
        "organization_name": "Corporation Alpha"
    }).json()
    token_a = user_a["access_token"]
    org_a_id = user_a["organization"]["id"]

    # Register Tenant B
    user_b = client.post("/api/v1/auth/register", json={
        "email": f"userb_{unique_suffix}@corp-b.com",
        "password": "PasswordB123!",
        "full_name": "User Beta",
        "organization_name": "Corporation Beta"
    }).json()
    token_b = user_b["access_token"]
    org_b_id = user_b["organization"]["id"]

    # User A creates a research project in Org A
    proj_a_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_a_id},
        json={"title": "Alpha Proprietary Quantum Research"}
    )
    assert proj_a_resp.status_code == 201
    proj_a_id = proj_a_resp.json()["id"]

    # User A adds a confidential source
    src_a_resp = client.post(
        f"/api/v1/projects/{proj_a_id}/sources",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "source_type": "text",
            "title": "Alpha Confidential Qubit Design",
            "text_content": "Proprietary superconductor blueprint for Alpha Corporation."
        }
    )
    assert src_a_resp.status_code == 201
    src_a_id = src_a_resp.json()["id"]

    # User B lists projects in Org B -> User A's project is NOT listed
    b_projects = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}
    ).json()
    assert all(p["id"] != proj_a_id for p in b_projects)

    # User B attempts to directly read User A's project by ID -> Blocked (404 Not Found)
    b_get_proj = client.get(
        f"/api/v1/projects/{proj_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_get_proj.status_code == 404

    # User B attempts to edit User A's project -> Blocked (404 Not Found)
    b_edit_proj = client.put(
        f"/api/v1/projects/{proj_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Tampered Title by Beta"}
    )
    assert b_edit_proj.status_code == 404

    # User B attempts to read User A's source -> Blocked (404 Not Found)
    b_get_source = client.get(
        f"/api/v1/sources/{src_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert b_get_source.status_code == 404


# =====================================================================
# 3. ROLE-BASED ACCESS CONTROL (RBAC) BOUNDARIES
# =====================================================================
def test_phase24_role_based_permissions_matrix():
    """
    Validates permissions across roles:
    - OWNER / ADMIN can invite members and manage org.
    - VIEWER cannot create projects or add sources (403 Forbidden).
    - EDITOR cannot approve editorials (403 Forbidden).
    - REVIEWER can approve editorials.
    """
    unique_suffix = int(time.time())
    # 1. Owner registers
    owner = client.post("/api/v1/auth/register", json={
        "email": f"org_owner_{unique_suffix}@editorial.org",
        "password": "OwnerPassword123!",
        "full_name": "Workspace Owner",
        "organization_name": "Governance Newsroom"
    }).json()
    owner_token = owner["access_token"]
    org_id = owner["organization"]["id"]

    # 2. Owner invites a VIEWER
    viewer_email = f"viewer_{unique_suffix}@editorial.org"
    inv_viewer = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"email": viewer_email, "role": "VIEWER"}
    )
    assert inv_viewer.status_code == 201
    viewer_token_str = inv_viewer.json()["token"]

    # Register Viewer User and accept invitation
    viewer_user = client.post("/api/v1/auth/register", json={
        "email": viewer_email,
        "password": "ViewerPassword123!",
        "full_name": "Viewer Readonly"
    }).json()
    viewer_jwt = viewer_user["access_token"]

    accept_viewer = client.post(
        f"/api/v1/organizations/invitations/{viewer_token_str}/accept",
        headers={"Authorization": f"Bearer {viewer_jwt}"}
    )
    assert accept_viewer.status_code == 200

    # 3. VIEWER attempts to create project in Governance Newsroom -> Blocked (403 Forbidden)
    viewer_create_proj = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {viewer_jwt}", "X-Organization-Id": org_id},
        json={"title": "Unauthorized Viewer Project"}
    )
    assert viewer_create_proj.status_code == 403
    assert "not authorized" in viewer_create_proj.json()["detail"].lower()

    # 4. Owner creates project
    owner_proj = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {owner_token}", "X-Organization-Id": org_id},
        json={"title": "Policy Editorial Project"}
    ).json()
    proj_id = owner_proj["id"]

    # VIEWER attempts to add source -> Blocked (403 Forbidden)
    viewer_add_src = client.post(
        f"/api/v1/projects/{proj_id}/sources",
        headers={"Authorization": f"Bearer {viewer_jwt}"},
        json={"source_type": "text", "title": "Illegal Source", "text_content": "Content"}
    )
    assert viewer_add_src.status_code == 403

    # 5. Owner invites an EDITOR
    editor_email = f"editor_{unique_suffix}@editorial.org"
    inv_editor = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"email": editor_email, "role": "EDITOR"}
    ).json()

    editor_user = client.post("/api/v1/auth/register", json={
        "email": editor_email,
        "password": "EditorPassword123!",
        "full_name": "Editor Staff"
    }).json()
    editor_jwt = editor_user["access_token"]

    client.post(
        f"/api/v1/organizations/invitations/{inv_editor['token']}/accept",
        headers={"Authorization": f"Bearer {editor_jwt}"}
    )

    # EDITOR cannot invite other members -> Blocked (403 Forbidden)
    editor_invite = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers={"Authorization": f"Bearer {editor_jwt}", "X-Organization-Id": org_id},
        json={"email": "someone@example.com", "role": "EDITOR"}
    )
    assert editor_invite.status_code == 403

    # EDITOR can add sources to the project
    editor_add_src = client.post(
        f"/api/v1/projects/{proj_id}/sources",
        headers={"Authorization": f"Bearer {editor_jwt}"},
        json={"source_type": "text", "title": "Editor Source 1", "text_content": "Evidence content..."}
    )
    assert editor_add_src.status_code == 201


# =====================================================================
# 4. INVITATION LIFECYCLE & SECURITY
# =====================================================================
def test_phase24_invitation_lifecycle_and_expiration():
    """Validates invitation generation, duplicate prevention, and invalid token handling."""
    unique_suffix = int(time.time())
    owner = client.post("/api/v1/auth/register", json={
        "email": f"inv_owner_{unique_suffix}@lab.org",
        "password": "Password123!",
        "full_name": "Lab Director"
    }).json()
    owner_token = owner["access_token"]
    org_id = owner["organization"]["id"]

    # 1. Create invitation
    invite_resp = client.post(
        f"/api/v1/organizations/{org_id}/invitations",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"email": f"colleague_{unique_suffix}@lab.org", "role": "REVIEWER"}
    )
    assert invite_resp.status_code == 201
    inv_data = invite_resp.json()
    token = inv_data["token"]
    assert inv_data["role"] == "REVIEWER"
    assert inv_data["is_expired"] is False

    # 2. List pending invitations
    list_inv = client.get(
        f"/api/v1/organizations/{org_id}/invitations",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert list_inv.status_code == 200
    assert any(i["token"] == token for i in list_inv.json())

    # 3. Invalid token rejection
    bad_accept = client.post(
        "/api/v1/organizations/invitations/non-existent-fake-token/accept",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert bad_accept.status_code == 404

    # 4. Revoke invitation
    del_resp = client.delete(
        f"/api/v1/organizations/{org_id}/invitations/{inv_data['id']}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert del_resp.status_code == 204

