import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password
from backend.app.models.base import User, UserSession, PasswordResetToken, EmailVerificationToken, Organization, OrganizationMembership


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ==============================================================================
# 1. REGISTRATION TESTS
# ==============================================================================

def test_register_successful(client: TestClient):
    """Test standard user registration with strong password policy."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "StrongPassword2026!#",
        "confirm_password": "StrongPassword2026!#",
        "full_name": "Test Candidate",
        "organization_name": "Test Candidate Desk",
        "terms_accepted": True
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["full_name"] == "Test Candidate"
    assert data["user"]["is_active"] is True
    assert "hashed_password" not in data["user"]
    assert data["organization"]["name"] == "Test Candidate Desk"


def test_register_duplicate_email_rejected(client: TestClient):
    """Test duplicate registration is rejected with appropriate 400 error."""
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "ValidPassword2026!#",
        "confirm_password": "ValidPassword2026!#",
        "full_name": "First User",
        "terms_accepted": True
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"].lower()


def test_register_weak_password_rejected(client: TestClient):
    """Test passwords failing length or complexity requirements are rejected."""
    # Too short (< 12 chars)
    resp = client.post("/api/v1/auth/register", json={
        "email": f"weak_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Short1!",
        "confirm_password": "Short1!",
        "full_name": "Weak Pwd User",
        "terms_accepted": True
    })
    assert resp.status_code == 400
    assert "at least 12 characters" in resp.json()["detail"].lower()

    # Missing special character
    resp = client.post("/api/v1/auth/register", json={
        "email": f"nospecial_{uuid.uuid4().hex[:8]}@example.com",
        "password": "NoSpecialCharacter123",
        "confirm_password": "NoSpecialCharacter123",
        "full_name": "No Special User",
        "terms_accepted": True
    })
    assert resp.status_code == 400
    assert "special character" in resp.json()["detail"].lower()


def test_register_password_mismatch_rejected(client: TestClient):
    """Test registration fails when password and confirm_password do not match."""
    resp = client.post("/api/v1/auth/register", json={
        "email": f"mismatch_{uuid.uuid4().hex[:8]}@example.com",
        "password": "CorrectPassword123!#",
        "confirm_password": "DifferentPassword123!#",
        "full_name": "Mismatch User",
        "terms_accepted": True
    })
    assert resp.status_code == 400
    assert "do not match" in resp.json()["detail"].lower()


def test_register_terms_not_accepted_rejected(client: TestClient):
    """Test registration fails if terms are not accepted."""
    resp = client.post("/api/v1/auth/register", json={
        "email": f"noterms_{uuid.uuid4().hex[:8]}@example.com",
        "password": "ValidPassword2026!#",
        "confirm_password": "ValidPassword2026!#",
        "full_name": "No Terms User",
        "terms_accepted": False
    })
    assert resp.status_code == 400
    assert "terms" in resp.json()["detail"].lower()


# ==============================================================================
# 2. LOGIN & SESSION TESTS
# ==============================================================================

def test_login_valid_credentials(client: TestClient):
    """Test successful authentication with valid credentials."""
    email = f"login_valid_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "ValidPassphrase2026!#"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "full_name": "Arthur Pendelton",
        "terms_accepted": True
    })
    assert reg.status_code == 201

    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": pwd,
        "remember_me": True
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


def test_login_invalid_credentials_generic_error(client: TestClient):
    """Test invalid credentials return generic error to prevent account enumeration."""
    # Non-existent user
    resp1 = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_random_user@example.com",
        "password": "WrongPassword123!#"
    })
    assert resp1.status_code == 401
    assert resp1.json()["detail"] == "Invalid email or password."

    # Existing user, wrong password
    email = f"exist_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "CorrectPassword123!#",
        "confirm_password": "CorrectPassword123!#",
        "full_name": "Exist User",
        "terms_accepted": True
    })
    resp2 = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "IncorrectPassword123!#"
    })
    assert resp2.status_code == 401
    assert resp2.json()["detail"] == "Invalid email or password."


def test_login_deactivated_user_rejected(client: TestClient, db_session: Session):
    """Test deactivated accounts cannot authenticate."""
    email = f"deact_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "AccountLockout123!#"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "full_name": "Marcus Kane",
        "terms_accepted": True
    })
    assert reg.status_code == 201
    uid = reg.json()["user"]["id"]

    # Deactivate directly in DB
    u = db_session.query(User).filter(User.id == uid).first()
    u.is_active = False
    db_session.commit()

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login_resp.status_code == 403
    assert "deactivated" in login_resp.json()["detail"].lower()


# ==============================================================================
# 3. PASSWORD STRENGTH VALIDATOR ENDPOINT
# ==============================================================================

def test_check_password_strength_endpoint(client: TestClient):
    """Test the live password strength checking endpoint."""
    # Strong password
    resp = client.post("/api/v1/auth/check-password-strength", json={
        "password": "SuperSecurePassphrase2026!#$",
        "email": "test@example.com",
        "full_name": "John Doe"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_valid"] is True
    assert data["strength_label"] == "Strong"
    assert data["requirements"]["length"] is True
    assert data["requirements"]["uppercase"] is True
    assert data["requirements"]["lowercase"] is True
    assert data["requirements"]["digit"] is True
    assert data["requirements"]["special"] is True


# ==============================================================================
# 4. FORGOT & RESET PASSWORD TESTS
# ==============================================================================

def test_forgot_and_reset_password_workflow(client: TestClient):
    """Test end-to-end password recovery with token validation."""
    email = f"forgot_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "OriginalPassword123!#"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "full_name": "Forgot User",
        "terms_accepted": True
    })
    assert reg.status_code == 201

    # Request reset
    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot_resp.status_code == 200
    dev_token = forgot_resp.json().get("dev_reset_token")
    assert dev_token is not None

    # Reset with new valid password
    new_pwd = "BrandNewPassword2026!#"
    reset_resp = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": new_pwd
    })
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # Confirm login with new password
    login_new = client.post("/api/v1/auth/login", json={"email": email, "password": new_pwd})
    assert login_new.status_code == 200

    # Confirm old password rejected
    login_old = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login_old.status_code == 401


# ==============================================================================
# 5. USER PROFILE & SESSIONS
# ==============================================================================

def test_user_profile_and_sessions_management(client: TestClient):
    """Test fetching profile, updating permitted fields, and viewing sessions."""
    email = f"profile_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "ProfilePassword123!#"
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "full_name": "Original Name",
        "terms_accepted": True
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # GET /users/me
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Original Name"

    # PUT /users/me (Update full_name)
    put_resp = client.put("/api/v1/users/me", json={
        "full_name": "Updated Name",
        "profile_image": "https://example.com/avatar.jpg"
    }, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["full_name"] == "Updated Name"
    assert put_resp.json()["profile_image"] == "https://example.com/avatar.jpg"

    # GET /users/me/sessions
    sess_resp = client.get("/api/v1/users/me/sessions", headers=headers)
    assert sess_resp.status_code == 200
    sessions = sess_resp.json()
    assert len(sessions) >= 1
    assert sessions[0]["is_current"] is True


# ==============================================================================
# 6. AUTHORIZATION & RBAC TESTS
# ==============================================================================

def test_rbac_admin_vs_user_permissions(client: TestClient, db_session: Session):
    """Test ordinary users are forbidden from admin endpoints while admins have access."""
    # Ordinary user
    user_email = f"regular_user_{uuid.uuid4().hex[:8]}@example.com"
    reg_user = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": "SampleClientPass123456!#",
        "confirm_password": "SampleClientPass123456!#",
        "full_name": "Thomas Edison",
        "terms_accepted": True
    })
    assert reg_user.status_code == 201, reg_user.text
    user_token = reg_user.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Ensure role is explicitly USER
    db_u = db_session.query(User).filter(User.email == user_email).first()
    db_u.role = "USER"
    db_session.commit()

    # User attempts to access admin endpoint -> 403 Forbidden
    admin_attempt = client.get("/api/v1/admin/users", headers=user_headers)
    assert admin_attempt.status_code == 403
    assert "administrative privileges required" in admin_attempt.json()["detail"].lower()

    # Admin user
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    reg_admin = client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": "ExecutiveRootKey123456!#",
        "confirm_password": "ExecutiveRootKey123456!#",
        "full_name": "Administrator Lead",
        "terms_accepted": True
    })
    assert reg_admin.status_code == 201, reg_admin.text
    admin_uid = reg_admin.json()["user"]["id"]
    admin_token = reg_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Elevate admin role
    db_admin = db_session.query(User).filter(User.id == admin_uid).first()
    db_admin.role = "ADMIN"
    db_session.commit()

    # Admin accesses admin endpoint -> 200 OK
    admin_ok = client.get("/api/v1/admin/users", headers=admin_headers)
    assert admin_ok.status_code == 200
    assert "items" in admin_ok.json()
    assert admin_ok.json()["total"] >= 2
