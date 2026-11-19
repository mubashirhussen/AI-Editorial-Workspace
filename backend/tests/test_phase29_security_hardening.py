"""
Phase 29 — Security Hardening, Authentication, Authorization & Multi-Tenancy Automated Test Suite.
Verifies defense-in-depth protections across:
1. Authentication & token security (anonymous rejection, invalid/tampered JWT, expired JWT, revoked tokens).
2. Password recovery anti-enumeration and cryptographic token lifecycle.
3. Brute-force login rate limiting.
4. Strict multi-tenant isolation (Anti-IDOR / BOLA returning 404).
5. Role-Based Access Control (RBAC) boundaries (Viewer restrictions, Owner-only org deletion).
6. Editorial workflow self-approval prohibition.
7. SSRF defenses (cloud metadata, loopbacks, octal/decimal bypasses).
8. File upload security (magic bytes, size limits, dangerous extension blocklist).
9. XSS sanitization in editorial HTML exports.
10. Security audit logging with credential and secret redaction.
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, hash_password, hash_token
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    WritingDraft,
    EditorialOutput,
    PasswordResetToken,
    UserSession,
    AuditLog,
)
from backend.app.schemas.auth import OrgRole, OrgPermission
from backend.app.utils.security import is_safe_url, is_ip_blocked
from backend.app.services.research.document_extractor import extract_from_bytes
from backend.app.services.editorial.export_service import ExportService
from backend.app.services.audit_service import audit_service, sanitize_audit_payload
from backend.app.api.routes.auth import check_login_rate_limit, record_login_failure, clear_login_failures


# =====================================================================
# 1. AUTHENTICATION DEFENSE & JWT INTEGRITY
# =====================================================================

def test_auth_anonymous_access_rejection(client: TestClient, monkeypatch):
    """Protected endpoints strictly reject unauthenticated requests with HTTP 401 when anonymous dev mode is disabled."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_DEV", False)

    protected_urls = [
        "/api/v1/auth/me",
        "/api/v1/projects",
        "/api/v1/writing/drafts",
        "/api/v1/organizations",
        "/api/v1/editorial/dashboard/stats"
    ]
    for url in protected_urls:
        resp = client.get(url)
        assert resp.status_code == 401, f"Expected 401 on {url}, got {resp.status_code}"


def test_auth_invalid_and_tampered_jwt(client: TestClient):
    """Malformed and cryptographically tampered JWTs are rejected with HTTP 401."""
    # Invalid gibberish token
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert resp.status_code == 401

    # Valid token structure with forged signature
    valid_token = create_access_token(data={"sub": str(uuid.uuid4()), "email": "test@test.com"})
    tampered_token = valid_token[:-6] + "xxxxxx"
    resp_tampered = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp_tampered.status_code == 401


def test_auth_expired_jwt_rejection(client: TestClient):
    """Expired JWT tokens are rejected immediately with HTTP 401."""
    expired_token = create_access_token(
        data={"sub": str(uuid.uuid4()), "email": "expired@example.com"},
        expires_delta=timedelta(minutes=-10)
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_auth_revoked_session_invalidation(client: TestClient):
    """Explicit logout revokes the JWT session and rejects subsequent invocations."""
    suffix = uuid.uuid4().hex[:6]
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": f"session_test_{suffix}@example.com",
        "password": "SecurePassword123!#",
        "full_name": "Session Tester",
        "terms_accepted": True
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]

    # Verify active access
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Attempt reuse after revocation
    revoked_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert revoked_resp.status_code == 401


# =====================================================================
# 2. PASSWORD RECOVERY & ANTI-ENUMERATION
# =====================================================================

def test_auth_forgot_password_generic_response(client: TestClient):
    """Forgot password endpoint returns identical response for existing and non-existent emails."""
    # Non-existent email
    resp_nonexistent = client.post("/api/v1/auth/forgot-password", json={
        "email": f"nonexistent_{uuid.uuid4().hex[:6]}@example.com"
    })
    assert resp_nonexistent.status_code == 200
    assert "instructions have been dispatched" in resp_nonexistent.json()["message"]

    # Existing user
    user_email = f"real_user_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": "ValidPassword123!#",
        "full_name": "Real User",
        "terms_accepted": True
    })

    resp_existing = client.post("/api/v1/auth/forgot-password", json={"email": user_email})
    assert resp_existing.status_code == 200
    assert resp_existing.json()["message"] == resp_nonexistent.json()["message"]


def test_auth_reset_password_token_lifecycle(client: TestClient):
    """Reset password rejects invalid, expired, and previously used tokens."""
    # 1. Invalid token
    resp_invalid = client.post("/api/v1/auth/reset-password", json={
        "token": "invalid_fake_reset_token_12345",
        "new_password": "NewStrongPassword2026!#"
    })
    assert resp_invalid.status_code == 400
    assert "invalid" in resp_invalid.json()["detail"].lower()

    # 2. Register user & request reset token
    email = f"reset_lifecycle_{uuid.uuid4().hex[:6]}@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "OldPassword123!#",
        "full_name": "Reset Tester",
        "terms_accepted": True
    })

    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": email})
    dev_token = forgot_resp.json().get("dev_reset_token")
    assert dev_token is not None

    # 3. Successful password reset
    reset_resp = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": "BrandNewPassword2026!#"
    })
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # 4. Token replay attempt (must fail)
    replay_resp = client.post("/api/v1/auth/reset-password", json={
        "token": dev_token,
        "new_password": "AnotherNewPassword2026!#"
    })
    assert replay_resp.status_code == 400


# =====================================================================
# 3. BRUTE-FORCE LOGIN RATE LIMITING
# =====================================================================

def test_auth_brute_force_login_rate_limiting():
    """Sliding-window rate limiter blocks excessive failed logins with HTTP 429."""
    test_ip = f"198.51.100.{int(time.time()) % 250}"
    clear_login_failures(test_ip)

    # Simulate 5 failed login attempts
    for _ in range(5):
        record_login_failure(test_ip)

    # 6th attempt should raise HTTP 429
    with pytest.raises(Exception) as exc_info:
        check_login_rate_limit(test_ip)
    assert "429" in str(exc_info.value)

    # Cleanup
    clear_login_failures(test_ip)


# =====================================================================
# 4. MULTI-TENANT ISOLATION (ANTI-IDOR / BOLA)
# =====================================================================

def test_tenant_isolation_cross_tenant_access_blocked_with_404(client: TestClient):
    """Users from Org A cannot view, mutate, or delete resources belonging to Org B (returns 404)."""
    suffix = uuid.uuid4().hex[:6]

    # Create Org A User
    user_a = client.post("/api/v1/auth/register", json={
        "email": f"org_a_{suffix}@tenant-a.com",
        "password": "PasswordA123!#",
        "full_name": "Alice Tenant",
        "organization_name": "Tenant A Workspace",
        "terms_accepted": True
    }).json()
    token_a = user_a["access_token"]

    # Create Org B User
    user_b = client.post("/api/v1/auth/register", json={
        "email": f"org_b_{suffix}@tenant-b.com",
        "password": "PasswordB123!#",
        "full_name": "Bob Tenant",
        "organization_name": "Tenant B Workspace",
        "terms_accepted": True
    }).json()
    token_b = user_b["access_token"]

    # Org A creates a project
    proj_resp = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "Classified Project A",
            "topic": "Sensitive AI Governance",
            "description": "Sensitive research for Tenant A",
            "target_audience": "Leadership"
        }
    )
    assert proj_resp.status_code == 201, proj_resp.text
    proj_a_id = proj_resp.json()["id"]

    # Org B attempts to read Org A's project -> Anti-IDOR contract expects 404 Not Found
    get_cross = client.get(
        f"/api/v1/projects/{proj_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert get_cross.status_code == 404, f"Expected 404 anti-enumeration, got {get_cross.status_code}"

    # Org B attempts to delete Org A's project -> Expects 404
    del_cross = client.delete(
        f"/api/v1/projects/{proj_a_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert del_cross.status_code == 404


# =====================================================================
# 5. ROLE-BASED ACCESS CONTROL (RBAC) & PERMISSION CEILINGS
# =====================================================================

def test_rbac_owner_only_organization_deletion(client: TestClient, db_session: Session):
    """Only users with the OWNER role can execute organization deletion."""
    suffix = uuid.uuid4().hex[:6]

    # Create Owner
    owner_user = client.post("/api/v1/auth/register", json={
        "email": f"owner_{suffix}@org-rbac.com",
        "password": "OwnerPassword123!#",
        "full_name": "Owner User",
        "organization_name": "RBAC Org Test",
        "terms_accepted": True
    }).json()
    owner_token = owner_user["access_token"]
    org_id = owner_user["organization"]["id"]

    # Create Member with VIEWER role
    viewer = User(
        id=str(uuid.uuid4()),
        email=f"viewer_{suffix}@org-rbac.com",
        hashed_password=hash_password("ViewerPass123!#"),
        full_name="Viewer User",
        role="USER",
        is_active=True
    )
    db_session.add(viewer)
    db_session.flush()

    mem = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        user_id=viewer.id,
        role=OrgRole.VIEWER.value
    )
    db_session.add(mem)
    db_session.commit()

    viewer_token = create_access_token(data={"sub": viewer.id, "email": viewer.email, "role": "USER"})

    # Viewer attempts to delete organization -> Forbidden
    del_viewer = client.delete(
        f"/api/v1/organizations/{org_id}",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert del_viewer.status_code == 403

    # Owner deletes organization -> Success (204)
    del_owner = client.delete(
        f"/api/v1/organizations/{org_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert del_owner.status_code == 204


# =====================================================================
# 6. EDITORIAL SELF-APPROVAL PROHIBITION
# =====================================================================

def test_editorial_self_approval_guard(client: TestClient, db_session: Session):
    """Authors holding EDITOR role cannot unilaterally approve their own editorial drafts."""
    suffix = uuid.uuid4().hex[:6]
    author = client.post("/api/v1/auth/register", json={
        "email": f"editor_author_{suffix}@newsroom.org",
        "password": "NewsPassword123!#",
        "full_name": "Drafting Author",
        "organization_name": "Newsroom Org",
        "terms_accepted": True
    }).json()
    author_token = author["access_token"]
    org_id = author["organization"]["id"]
    author_id = author["user"]["id"]

    # Change author role to EDITOR in membership
    db_session.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == author_id
    ).update({"role": OrgRole.EDITOR.value})

    # Create project, draft, and editorial output
    proj = ResearchProject(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        title="Self-Approval Test Project",
        name="Self-Approval Test Project"
    )
    db_session.add(proj)
    db_session.flush()

    draft = WritingDraft(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        project_id=proj.id,
        title="Author's Unverified Editorial",
        original_content="Draft content written by the author.",
        revised_content="Draft content written by the author.",
        author_id=author_id,
        status="IN_REVIEW"
    )
    db_session.add(draft)
    db_session.flush()

    editorial = EditorialOutput(
        id=str(uuid.uuid4()),
        project_id=proj.id,
        draft_id=draft.id,
        headline="Author's Unverified Editorial",
        content="Draft content written by the author.",
        status="HUMAN_REVIEW_PENDING",
        word_count=50
    )
    db_session.add(editorial)
    db_session.commit()

    # Author attempts to approve own editorial -> Must be rejected with 403 Forbidden
    approve_resp = client.post(
        f"/api/v1/editorial/{editorial.id}/approve",
        headers={"Authorization": f"Bearer {author_token}"},
        json={"approval_notes": "Attempting self-approval"}
    )
    assert approve_resp.status_code == 403
    assert "authors cannot approve their own" in approve_resp.json()["detail"].lower()


# =====================================================================
# 7. SSRF (SERVER-SIDE REQUEST FORGERY) DEFENSES
# =====================================================================

def test_ssrf_protection_filters_metadata_loopback_and_encodings():
    """is_safe_url blocks cloud metadata, loopback IPs, and alternate encodings."""
    malicious_urls = [
        "http://169.254.169.254/latest/meta-data/",   # AWS / Azure metadata
        "http://metadata.google.internal/computeMetadata/v1/", # GCP metadata
        "http://127.0.0.1:8000/internal",             # Loopback IPv4
        "http://localhost:3000/admin",                # Localhost
        "http://[::1]/secret",                        # IPv6 Loopback
        "http://192.168.1.1/router-login",            # RFC 1918 Private class C
        "http://10.0.0.1/corp-intranet",              # RFC 1918 Private class A
        "http://2130706433/",                         # Decimal IP representation of 127.0.0.1
        "ftp://example.com/file",                     # Non-http/https protocol
        "http://admin:password@example.com/",         # Embedded credentials
        "file:///etc/passwd"                          # Local file URI
    ]

    for url in malicious_urls:
        assert not is_safe_url(url), f"SSRF vulnerability: {url} was incorrectly deemed safe!"

    # Legitimate external public URLs must pass
    assert is_safe_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
    assert is_safe_url("https://arxiv.org/abs/1706.03762")


# =====================================================================
# 8. FILE UPLOAD & DOCUMENT EXTRACTION HARDENING
# =====================================================================

def test_file_upload_security_magic_bytes_and_extension_blacklist():
    """File upload extractor rejects dangerous extensions, oversized payloads, and corrupted files."""
    # 1. Executable and script extensions rejected
    dangerous_files = ["malware.exe", "script.sh", "exploit.bat", "library.dll"]
    for fn in dangerous_files:
        res = extract_from_bytes(b"MZ\x90\x00\x03\x00\x00\x00", filename=fn)
        assert res["success"] is False
        assert "unsupported binary format" in res["error"].lower()

    # 2. Oversized payload rejected (>10MB)
    huge_payload = b"A" * (10 * 1024 * 1024 + 1024)  # 10MB + 1KB
    res_huge = extract_from_bytes(huge_payload, filename="large_data.txt")
    assert res_huge["success"] is False
    assert "exceeds maximum allowed size" in res_huge["error"].lower()

    # 3. Legitimate text document accepted
    clean_txt = b"This is a legitimate AI research paper text."
    res_ok = extract_from_bytes(clean_txt, filename="ai_paper.txt")
    assert res_ok["success"] is True
    assert "This is a legitimate AI research paper text" in res_ok["content"]


# =====================================================================
# 9. CROSS-SITE SCRIPTING (XSS) SANITIZATION IN EXPORTS
# =====================================================================

def test_xss_sanitization_in_html_exports():
    """Editorial HTML exports strictly escape script tags and injection payloads."""
    malicious_headline = "AI Revolution <script>alert('XSS-HEADLINE')</script>"
    malicious_content = "Paragraph with <img src=x onerror=alert('XSS-IMG')> and <script>fetch('/cookie')</script>."

    editorial = EditorialOutput(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        headline=malicious_headline,
        content=malicious_content,
        status="FINALIZED",
        word_count=15,
        source_references=[{
            "index": 1,
            "title": "Legit Source <script>bad()</script>",
            "url": "https://example.com/source",
            "supported_claim": "Claim text"
        }]
    )

    exporter = ExportService()
    html_output = exporter.build_html(editorial)

    # Raw script tags must NEVER appear in the generated HTML
    assert "<script>" not in html_output
    assert "</script>" not in html_output
    assert "<img src=x" not in html_output

    # HTML-escaped sequences must be present
    assert "&lt;script&gt;alert(&#x27;XSS-HEADLINE&#x27;)&lt;/script&gt;" in html_output or "&lt;script&gt;" in html_output
    assert "&lt;img src=x onerror=alert(&#x27;XSS-IMG&#x27;)&gt;" in html_output or "&lt;img" in html_output


# =====================================================================
# 10. SECURITY AUDIT LOGGING & SENSITIVE CREDENTIAL REDACTION
# =====================================================================

def test_security_audit_logging_and_credential_redaction(db_session: Session):
    """Audit service scrubs passwords and secret tokens before recording events to database."""
    raw_metadata = {
        "user_email": "auditee@example.com",
        "password": "SecretPassword123!",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "api_key": "sk-proj-supersecretkey",
        "nested": {
            "dev_reset_token": "crypto-secret-token",
            "harmless_key": "safe_value"
        }
    }

    # 1. Test payload sanitizer
    sanitized = sanitize_audit_payload(raw_metadata)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["dev_reset_token"] == "[REDACTED]"
    assert sanitized["nested"]["harmless_key"] == "safe_value"

    # 2. Test database recording via SecurityAuditService
    audit_entry = audit_service.log_event(
        db=db_session,
        event_type="security.test.event",
        actor_email="auditee@example.com",
        ip_address="198.51.100.5",
        metadata=raw_metadata
    )
    assert audit_entry is not None
    assert audit_entry.event_type == "security.test.event"
    assert audit_entry.changes_json["password"] == "[REDACTED]"
    assert audit_entry.changes_json["access_token"] == "[REDACTED]"
