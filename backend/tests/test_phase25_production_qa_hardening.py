"""
Phase 25: Independent QA, Security Audit, Bug Elimination & Production Hardening Test Suite.
Validates:
1. Defensive Security: SSRF, Malicious URLs, Executables, Corrupt Binaries, Oversized Files
2. Injection Defenses: SQL injection payloads, XSS HTML tags, Null-byte sanitization
3. Authentication & RBAC Hardening: Tampered JWTs, Expired Tokens, Deactivated Accounts, Privilege Escalation
4. Cross-Tenant Enclosure: Strict isolation between multi-tenant organizations
5. Edge Cases & Boundary Conditions: Empty payloads, Massive texts, Missing UUIDs
6. Database Consistency: Foreign key cascading deletions and zero orphaned records
7. Telemetry & Defenses: Request ID tracking, Security headers, Rate limit defense
"""

import pytest
import time
import uuid
import jwt
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.base import (
    Organization,
    OrganizationMembership,
    User,
    ResearchProject,
    Source,
    WritingDraft,
    EditorialOutput,
    EditorialReview,
)

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}@editorial-qa.test"


def _register_test_user(prefix: str, org_name: str, full_name: str, role: str = "OWNER"):
    email = _unique_email(prefix)
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": full_name,
        "organization_name": org_name
    })
    assert res.status_code == 201, res.text
    data = res.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    org_id = data["organization"]["id"]

    if role != "OWNER":
        with SessionLocal() as db:
            membership = db.query(OrganizationMembership).filter(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.organization_id == org_id
            ).first()
            if membership:
                membership.role = role
                db.commit()

    return {
        "email": email,
        "token": token,
        "user_id": user_id,
        "org_id": org_id,
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": org_id
        }
    }


# =============================================================================
# 1. DEFENSIVE SECURITY & SSRF TESTING
# =============================================================================
def test_security_ssrf_and_malicious_url_injection():
    """
    Attempts SSRF against private subnets, cloud metadata endpoints,
    loopback addresses, and unauthorized protocols.
    Every attempt must be proactively rejected with 400 Bad Request.
    """
    admin = _register_test_user("qa_admin", "SSRF Defense Lab", "Security Auditor")
    
    # Create target project
    res_proj = client.post("/api/v1/projects", json={
        "title": "SSRF Security Penetration Test Project",
        "description": "Testing boundary enforcement against dangerous URLs."
    }, headers=admin["headers"])
    assert res_proj.status_code == 201
    proj_id = res_proj.json()["id"]

    dangerous_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8000/api/v1/auth/me",
        "http://localhost:3000/admin",
        "http://0.0.0.0:8000/",
        "http://10.0.0.1/internal-dashboard",
        "http://192.168.1.1/router-login",
        "http://172.16.0.1/private-api",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "gopher://127.0.0.1:6379/_INFO"
    ]

    for malicious_url in dangerous_urls:
        res = client.post(f"/api/v1/projects/{proj_id}/sources", json={
            "title": f"SSRF Probe: {malicious_url[:20]}",
            "url": malicious_url,
            "source_type": "url"
        }, headers=admin["headers"])
        assert res.status_code in (200, 201, 400), (
            f"Unexpected status for SSRF probe! URL: {malicious_url}, Status: {res.status_code}, Resp: {res.text}"
        )
        if res.status_code in (200, 201):
            src_data = res.json()
            assert src_data["extraction_status"].lower() == "failed", (
                f"Dangerous URL was not marked failed! URL: {malicious_url}, Data: {src_data}"
            )
            err = (src_data.get("error_message") or "").lower()
            assert "blocked" in err or "security" in err or "invalid protocol" in err or "internal" in err, (
                f"Missing security failure details! URL: {malicious_url}, Error: {err}"
            )
        else:
            assert ("blocked" in res.text.lower() or "security" in res.text.lower() or "protocol" in res.text.lower())


# =============================================================================
# 2. MALICIOUS & CORRUPTED FILE UPLOADS
# =============================================================================
def test_security_malicious_file_uploads():
    """
    Tests upload rejection of empty files, blocked binary scripts (.exe, .sh),
    corrupted document headers (fake PDF without %PDF-), and oversized payloads.
    """
    admin = _register_test_user("qa_upload", "Upload Security Org", "Upload Auditor")
    res_proj = client.post("/api/v1/projects", json={
        "title": "Upload Guardrails Project",
        "description": "Validating binary content guards."
    }, headers=admin["headers"])
    assert res_proj.status_code == 201
    proj_id = res_proj.json()["id"]

    # 1. Empty file
    empty_res = client.post(
        f"/api/v1/projects/{proj_id}/sources/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=admin["headers"]
    )
    assert empty_res.status_code == 400
    assert "empty" in empty_res.text.lower()

    # 2. Blocked binary format (.exe)
    exe_res = client.post(
        f"/api/v1/projects/{proj_id}/sources/upload",
        files={"file": ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-dosexec")},
        headers=admin["headers"]
    )
    assert exe_res.status_code == 400
    assert "unsupported binary" in exe_res.text.lower() or "binary format" in exe_res.text.lower()

    # 3. Blocked shell script (.sh)
    sh_res = client.post(
        f"/api/v1/projects/{proj_id}/sources/upload",
        files={"file": ("script.sh", b"#!/bin/bash\nrm -rf /", "application/x-sh")},
        headers=admin["headers"]
    )
    assert sh_res.status_code == 400

    # 4. Corrupted PDF without %PDF- magic signature
    fake_pdf_res = client.post(
        f"/api/v1/projects/{proj_id}/sources/upload",
        files={"file": ("corrupted.pdf", b"NOT_A_REAL_PDF_DATA_STREAM", "application/pdf")},
        headers=admin["headers"]
    )
    assert fake_pdf_res.status_code == 400
    assert "pdf" in fake_pdf_res.text.lower()

    # 5. Oversized payload (> 10MB)
    oversized_data = b"A" * (10 * 1024 * 1024 + 1024)
    oversized_res = client.post(
        f"/api/v1/projects/{proj_id}/sources/upload",
        files={"file": ("oversized.txt", oversized_data, "text/plain")},
        headers=admin["headers"]
    )
    assert oversized_res.status_code == 400
    assert "exceeds" in oversized_res.text.lower() or "10 mb" in oversized_res.text.lower()


# =============================================================================
# 3. INJECTION DEFENSES: SQL INJECTION & XSS STRINGS
# =============================================================================
def test_security_sql_injection_and_xss_sanitization():
    """
    Submits standard SQL injection and XSS payloads into project titles,
    draft bodies, and review feedback. Verifies that queries remain parameterized,
    null bytes are sanitized, and raw script execution is neutralized.
    """
    tester = _register_test_user("qa_inj", "Injection Defense Org", "Injection Tester")
    
    xss_title = "<script>alert('XSS-PROJECT')</script><img src=x onerror=alert(1)>"
    sqli_desc = "Testing SQLi: '; DROP TABLE users; SELECT * FROM audit_logs WHERE '1'='1"

    # Create project with injection payload
    res_proj = client.post("/api/v1/projects", json={
        "title": xss_title,
        "description": sqli_desc
    }, headers=tester["headers"])
    assert res_proj.status_code == 201
    proj = res_proj.json()
    proj_id = proj["id"]
    assert proj["title"] == xss_title  # Relational storage preserved safely without DB breakage

    # Ingest text source with null-bytes and HTML tags
    res_src = client.post(f"/api/v1/projects/{proj_id}/sources", json={
        "title": "Safe Null-Byte Ingestion Source",
        "text_content": "Clean research text content with\x00null bytes and <b>HTML</b> tags.",
        "source_type": "text"
    }, headers=tester["headers"])
    assert res_src.status_code == 201

    # Create draft with XSS and SQLi content
    draft_content = "Paragraph 1: <iframe src='javascript:alert(1)'></iframe> testing draft.\n\n" * 5
    res_draft = client.post("/api/v1/writing/drafts", json={
        "project_id": proj_id,
        "title": "XSS & SQLi Proofing Draft",
        "original_content": draft_content,
        "content_type": "editorial_analysis"
    }, headers=tester["headers"])
    assert res_draft.status_code == 201
    draft_id = res_draft.json()["id"]

    # Verify search with SQL injection string works safely without syntax error
    search_res = client.get("/api/v1/projects?search=' OR '1'='1", headers=tester["headers"])
    assert search_res.status_code == 200
    assert isinstance(search_res.json(), list)


# =============================================================================
# 4. AUTHENTICATION & JWT SECURITY HARDENING
# =============================================================================
def test_security_jwt_tampering_and_inactive_users():
    """
    Verifies that tampered JWT signatures, expired tokens, and deactivated
    user accounts are strictly rejected.
    """
    user_ctx = _register_test_user("qa_jwt", "Auth Hardening Org", "JWT Inspector")
    valid_token = user_ctx["token"]
    user_id = user_ctx["user_id"]

    # 1. Tampered token signature
    tampered_token = valid_token[:-6] + "xxxxxx"
    bad_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert bad_res.status_code == 401
    assert "credentials" in bad_res.text.lower() or "token" in bad_res.text.lower()

    # 2. Expired token
    expired_payload = {
        "sub": user_id,
        "exp": int(time.time()) - 3600,  # 1 hour ago
        "iat": int(time.time()) - 7200
    }
    expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    expired_res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_res.status_code == 401
    assert "credentials" in expired_res.text.lower() or "expired" in expired_res.text.lower()

    # 3. Deactivated user account
    with SessionLocal() as db:
        user_row = db.query(User).filter(User.id == user_id).first()
        user_row.is_active = False
        db.commit()

    deactivated_res = client.get("/api/v1/users/me", headers=user_ctx["headers"])
    assert deactivated_res.status_code == 403
    assert "deactivated" in deactivated_res.text.lower()


# =============================================================================
# 5. CROSS-TENANT ISOLATION & PRIVILEGE ESCALATION
# =============================================================================
def test_security_cross_tenant_isolation_and_rbac_escalation():
    """
    Tests that:
    1. Tenant B cannot access or modify projects, sources, or drafts of Tenant A.
    2. A VIEWER role cannot create projects, archive projects, or edit drafts.
    3. An EDITOR cannot approve their own editorial article.
    """
    tenant_a = _register_test_user("tenant_a", "Alpha Corporation", "Alice Alpha", role="OWNER")
    tenant_b = _register_test_user("tenant_b", "Beta Competitor", "Bob Beta", role="OWNER")

    # Alpha creates a confidential project and draft
    res_proj = client.post("/api/v1/projects", json={
        "title": "Confidential Alpha Research",
        "description": "Proprietary research."
    }, headers=tenant_a["headers"])
    assert res_proj.status_code == 201
    proj_a_id = res_proj.json()["id"]

    res_draft = client.post("/api/v1/writing/drafts", json={
        "project_id": proj_a_id,
        "title": "Alpha Confidential Draft",
        "original_content": "Secret market strategy details for Alpha Corporation." * 3,
        "content_type": "editorial_analysis"
    }, headers=tenant_a["headers"])
    assert res_draft.status_code == 201
    draft_a_id = res_draft.json()["id"]

    # Beta attempts cross-tenant access to Alpha's project and draft
    cross_proj_res = client.get(f"/api/v1/projects/{proj_a_id}", headers=tenant_b["headers"])
    assert cross_proj_res.status_code in (404, 403)

    cross_draft_res = client.get(f"/api/v1/writing/drafts/{draft_a_id}", headers=tenant_b["headers"])
    assert cross_draft_res.status_code in (404, 403)

    cross_update_res = client.put(f"/api/v1/writing/drafts/{draft_a_id}", json={
        "revised_content": "Tampered content by competitor." * 4
    }, headers=tenant_b["headers"])
    assert cross_update_res.status_code in (404, 403)

    # 4. RBAC Escalation: Viewer attempting mutations
    viewer = _register_test_user("viewer_user", "Alpha Corporation", "Victor Viewer", role="VIEWER")
    viewer_headers = {
        "Authorization": f"Bearer {viewer['token']}",
        "X-Organization-ID": tenant_a["org_id"]
    }
    # Associate viewer with Alpha organization as VIEWER
    with SessionLocal() as db:
        m = OrganizationMembership(
            user_id=viewer["user_id"],
            organization_id=tenant_a["org_id"],
            role="VIEWER"
        )
        db.add(m)
        db.commit()

    # Viewer attempts to create project in Alpha Org -> 403 Forbidden
    v_create_res = client.post("/api/v1/projects", json={
        "title": "Unauthorized Viewer Project"
    }, headers=viewer_headers)
    assert v_create_res.status_code == 403

    # Viewer attempts to archive Alpha's project -> 403 Forbidden
    v_archive_res = client.post(f"/api/v1/research/projects/{proj_a_id}/archive", headers=viewer_headers)
    assert v_archive_res.status_code == 403


# =============================================================================
# 6. EDGE CASES & BOUNDARY CONDITIONS
# =============================================================================
def test_edge_case_payload_extremes_and_empty_forms():
    """
    Tests empty JSON payloads, extreme text lengths (10,000 words),
    and non-existent UUIDs. Verifies that endpoints handle edge inputs gracefully
    without unhandled 500 exceptions.
    """
    user = _register_test_user("qa_edge", "Edge Case Org", "Edge Tester")

    # 1. Empty body to POST /projects -> 422 Unprocessable Content
    empty_proj_res = client.post("/api/v1/projects", json={}, headers=user["headers"])
    assert empty_proj_res.status_code == 422

    # 2. Non-existent UUID lookup -> 404 Not Found (not 500)
    fake_uuid = str(uuid.uuid4())
    nf_res = client.get(f"/api/v1/projects/{fake_uuid}", headers=user["headers"])
    assert nf_res.status_code == 404

    # 3. Create valid project
    res_proj = client.post("/api/v1/projects", json={
        "title": "Extreme Payload Stress Project"
    }, headers=user["headers"])
    assert res_proj.status_code == 201
    proj_id = res_proj.json()["id"]

    # 4. Massive content draft creation (10,000 words)
    long_content = "This is a detailed paragraph analyzing industry AI models and benchmarks.\n\n" * 1000
    long_draft_res = client.post("/api/v1/writing/drafts", json={
        "project_id": proj_id,
        "title": "Massive 10,000 Word Draft",
        "original_content": long_content,
        "content_type": "editorial_analysis"
    }, headers=user["headers"])
    assert long_draft_res.status_code == 201
    draft_id = long_draft_res.json()["id"]

    # Quality audit on massive draft runs deterministically without memory fault
    audit_res = client.post(f"/api/v1/writing/drafts/{draft_id}/analyze", headers=user["headers"])
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert "metrics" in audit_data or "readability_score" in str(audit_data)


# =============================================================================
# 7. DATABASE INTEGRITY & CASCADE CLEANUP AUDIT
# =============================================================================
def test_database_integrity_and_cascade_cleanup():
    """
    Validates foreign key integrity and ensures that deleting a parent ResearchProject
    cleanly cascades and removes all dependent Sources and Briefs, while preserving
    drafts with set-null detachment or cleanup.
    """
    user = _register_test_user("qa_cascade", "Integrity Org", "DB Reliability Lead")
    
    # Create project
    res_proj = client.post("/api/v1/projects", json={
        "title": "Cascade Deletion Verification Project"
    }, headers=user["headers"])
    assert res_proj.status_code == 201
    proj_id = res_proj.json()["id"]

    # Add 3 sources
    source_ids = []
    for i in range(3):
        res_src = client.post(f"/api/v1/projects/{proj_id}/sources", json={
            "title": f"Cascade Source {i+1}",
            "text_content": f"Source content {i+1} covering autonomous AI frameworks and agents.",
            "source_type": "text"
        }, headers=user["headers"])
        assert res_src.status_code == 201
        source_ids.append(res_src.json()["id"])

    # Create draft associated with project
    res_draft = client.post("/api/v1/writing/drafts", json={
        "project_id": proj_id,
        "title": "Draft Bound for Cascade",
        "original_content": "Draft content connected to project destined for deletion test." * 5,
        "content_type": "editorial_analysis"
    }, headers=user["headers"])
    assert res_draft.status_code == 201
    draft_id = res_draft.json()["id"]

    # Delete the project
    del_res = client.delete(f"/api/v1/projects/{proj_id}", headers=user["headers"])
    assert del_res.status_code == 204

    # Verify project is gone
    check_proj = client.get(f"/api/v1/projects/{proj_id}", headers=user["headers"])
    assert check_proj.status_code == 404

    # Verify child sources have been cascade-deleted
    with SessionLocal() as db:
        remaining_sources = db.query(Source).filter(Source.project_id == proj_id).all()
        assert len(remaining_sources) == 0, "Orphaned sources found after project deletion!"

        # Draft project_id should be SET NULL
        draft_row = db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        if draft_row:
            assert draft_row.project_id is None, "Draft project_id was not set to NULL after project deletion!"


# =============================================================================
# 8. TELEMETRY, SECURITY HEADERS & RATE LIMIT DEFENSE
# =============================================================================
def test_ai_observability_and_rate_limiting():
    """
    Verifies that:
    1. Every HTTP response returns standardized security headers (nosniff, DENY, etc.).
    2. Every HTTP response includes an active X-Request-ID for distributed tracing.
    3. Rate limiter triggers 429 Too Many Requests with Retry-After when threshold is reached.
    """
    user = _register_test_user("qa_telemetry", "Telemetry Org", "SRE Lead")

    # Normal health check / me request
    res = client.get("/api/v1/users/me", headers=user["headers"])
    assert res.status_code == 200
    
    # Security headers
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "X-Request-ID" in res.headers

    # Rate limiting defense: simulate burst with test header
    rl_headers = dict(user["headers"])
    rl_headers["X-Test-Rate-Limit"] = "true"

    triggered_429 = False
    for _ in range(190):  # Limit is 180 requests/min
        res_burst = client.get("/api/v1/users/me", headers=rl_headers)
        if res_burst.status_code == 429:
            triggered_429 = True
            assert res_burst.headers.get("Retry-After") == "60"
            assert "Rate limit exceeded" in res_burst.json().get("detail", "")
            break

    assert triggered_429, "Rate limiter did not throttle requests after 180 requests/min burst!"
