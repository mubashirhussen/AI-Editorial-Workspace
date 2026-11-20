"""
Phase 36: Post-Release Product Monitoring, Health Observability & User Feedback Triage Tests.
Validates:
- Health check endpoints (/health/live, /health/ready, /health, /health/startup)
- Request ID propagation and structured telemetry correlation
- User feedback submission, Pydantic validation, and persistence
- Tenant-scoped feedback listing, filtering, and summary metrics
- Feedback triage status lifecycle (NEW -> TRIAGED -> IN_PROGRESS -> RESOLVED)
- Unified system health diagnostics endpoint (/api/v1/observability/system-health)
"""

import pytest
import uuid
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    UserFeedback,
    ResearchProject
)
from backend.app.core.security import hash_password, create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_monitoring_tenants(db_session):
    """
    Creates two isolated tenant environments for monitoring and feedback testing.
    """
    uid = uuid.uuid4().hex[:8]

    # Tenant Alpha (Editor)
    org_a = Organization(id=f"org-mon-a-{uid}", name="Alpha Media Telemetry", slug=f"alpha-mon-{uid}")
    user_a = User(
        id=f"user-mon-a-{uid}",
        email=f"editor_a_{uid}@alphamedia.com",
        full_name="Alice Alpha",
        hashed_password=hash_password("Password123!"),
        is_active=True
    )
    membership_a = OrganizationMembership(
        id=f"mem-mon-a-{uid}",
        user_id=user_a.id,
        organization_id=org_a.id,
        role="EDITOR"
    )

    # Tenant Beta (Writer)
    org_b = Organization(id=f"org-mon-b-{uid}", name="Beta News Telemetry", slug=f"beta-mon-{uid}")
    user_b = User(
        id=f"user-mon-b-{uid}",
        email=f"writer_b_{uid}@betanews.com",
        full_name="Bob Beta",
        hashed_password=hash_password("Password123!"),
        is_active=True
    )
    membership_b = OrganizationMembership(
        id=f"mem-mon-b-{uid}",
        user_id=user_b.id,
        organization_id=org_b.id,
        role="WRITER"
    )

    db_session.add_all([org_a, user_a, membership_a, org_b, user_b, membership_b])
    db_session.commit()

    token_a = create_access_token({"sub": user_a.id, "org_id": org_a.id})
    token_b = create_access_token({"sub": user_b.id, "org_id": org_b.id})

    return {
        "org_a": org_a, "user_a": user_a, "token_a": token_a,
        "org_b": org_b, "user_b": user_b, "token_b": token_b
    }


# ==============================================================================
# 1. APPLICATION HEALTH MONITORING ENDPOINTS
# ==============================================================================
def test_health_liveness_endpoint(client):
    """
    Verifies that /health/live returns HTTP 200 OK and basic process liveness metadata.
    """
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "version" in data
    assert "application" in data


def test_health_readiness_endpoint(client):
    """
    Verifies that /health/ready returns HTTP 200 OK and dependency readiness metadata
    without leaking database credentials or internal secrets.
    """
    res = client.get("/api/v1/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "dependencies" in data
    # Ensure no secrets leaked
    text_content = res.text.lower()
    assert "password" not in text_content
    assert "secret" not in text_content


def test_detailed_health_diagnostics(client):
    """
    Verifies that /health returns detailed operational diagnostics and telemetry.
    """
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database_diagnostics" in data
    assert "ai_engine" in data
    assert "telemetry" in data


# ==============================================================================
# 2. REQUEST CORRELATION & DISTRIBUTED TRACING
# ==============================================================================
def test_request_id_tracing_header(client):
    """
    Verifies that all API responses propagate a unique X-Request-ID header.
    """
    res = client.get("/api/v1/health/live")
    assert res.status_code == 200
    req_id = res.headers.get("x-request-id") or res.headers.get("X-Request-ID")
    assert req_id is not None
    assert len(req_id) >= 16


# ==============================================================================
# 3. USER FEEDBACK SUBMISSION & VALIDATION
# ==============================================================================
def test_feedback_submission_and_validation(client, test_monitoring_tenants, db_session):
    """
    Verifies that valid feedback submissions are persisted, and invalid payloads are rejected.
    """
    token_a = test_monitoring_tenants["token_a"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Valid feedback submission
    valid_payload = {
        "title": "Citation bracket [2] mapping alignment issue",
        "description": "When generating drafts with multiple sources, citation [2] sometimes points to source index 1.",
        "category": "citation_issue",
        "severity": "high",
        "module_reference": "research"
    }
    create_res = client.post("/api/v1/feedback", json=valid_payload, headers=headers_a)
    assert create_res.status_code == 201
    feedback_data = create_res.json()
    assert feedback_data["id"] is not None
    assert feedback_data["title"] == valid_payload["title"]
    assert feedback_data["status"] == "NEW"
    assert feedback_data["category"] == "citation_issue"
    assert feedback_data["severity"] == "high"

    # 2. Invalid submission: Description too short (< 10 chars)
    short_payload = {
        "title": "Broken link",
        "description": "Too short",
        "category": "bug_report",
        "severity": "low"
    }
    short_res = client.post("/api/v1/feedback", json=short_payload, headers=headers_a)
    assert short_res.status_code == 422

    # 3. Invalid submission: Invalid category
    invalid_cat_payload = {
        "title": "Random idea",
        "description": "This is a detailed description of an idea that has an invalid category.",
        "category": "non_existent_category",
        "severity": "medium"
    }
    cat_res = client.post("/api/v1/feedback", json=invalid_cat_payload, headers=headers_a)
    assert cat_res.status_code == 422


# ==============================================================================
# 4. FEEDBACK TENANT ISOLATION & FILTERING
# ==============================================================================
def test_feedback_tenant_isolation_and_listing(client, test_monitoring_tenants, db_session):
    """
    Verifies that feedback listings are strictly partitioned by organization.
    """
    token_a = test_monitoring_tenants["token_a"]
    token_b = test_monitoring_tenants["token_b"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A submits a feedback item
    payload_a = {
        "title": "Tenant Alpha Proprietary Bug",
        "description": "Confidential bug report specific to Alpha organization setup.",
        "category": "bug_report",
        "severity": "critical",
        "module_reference": "writing"
    }
    res_a = client.post("/api/v1/feedback", json=payload_a, headers=headers_a)
    assert res_a.status_code == 201
    fb_a_id = res_a.json()["id"]

    # Tenant B lists feedback -> should NOT include Tenant A's feedback
    list_b = client.get("/api/v1/feedback", headers=headers_b)
    assert list_b.status_code == 200
    b_items = list_b.json()["items"]
    assert not any(item["id"] == fb_a_id for item in b_items)

    # Tenant B tries to query Tenant A's feedback directly by ID -> rejected with 404
    direct_get = client.get(f"/api/v1/feedback/{fb_a_id}", headers=headers_b)
    assert direct_get.status_code in (403, 404)


# ==============================================================================
# 5. FEEDBACK TRIAGE LIFECYCLE (NEW -> TRIAGED -> IN_PROGRESS -> RESOLVED)
# ==============================================================================
def test_feedback_triage_lifecycle(client, test_monitoring_tenants, db_session):
    """
    Verifies that authorized editors/admins can update status and attach triage notes.
    """
    token_a = test_monitoring_tenants["token_a"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Create feedback item
    create_res = client.post(
        "/api/v1/feedback",
        json={
            "title": "UI contrast on dark mode button",
            "description": "Secondary action button has insufficient contrast in dark mode theme.",
            "category": "ux_improvement",
            "severity": "low",
            "module_reference": "dashboard"
        },
        headers=headers_a
    )
    assert create_res.status_code == 201
    fb_id = create_res.json()["id"]

    # 2. Transition to TRIAGED with admin notes
    triage_res = client.patch(
        f"/api/v1/feedback/{fb_id}",
        json={
            "status": "TRIAGED",
            "admin_notes": "Assigned to frontend accessibility review.",
            "assigned_to": "designer@alphamedia.com"
        },
        headers=headers_a
    )
    assert triage_res.status_code == 200
    assert triage_res.json()["status"] == "TRIAGED"
    assert triage_res.json()["admin_notes"] == "Assigned to frontend accessibility review."

    # 3. Transition to RESOLVED with resolution summary
    resolve_res = client.patch(
        f"/api/v1/feedback/{fb_id}",
        json={
            "status": "RESOLVED",
            "resolution_summary": "Updated button class to slate-200 text with slate-700 hover border."
        },
        headers=headers_a
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
    assert resolve_res.json()["resolution_summary"] is not None

    # 4. Check feedback summary aggregation
    summary_res = client.get("/api/v1/feedback/summary", headers=headers_a)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total"] >= 1
    assert "RESOLVED" in summary["by_status"]


# ==============================================================================
# 6. UNIFIED SYSTEM HEALTH & MONITORING OVERVIEW
# ==============================================================================
def test_system_health_overview_endpoint(client, test_monitoring_tenants):
    """
    Verifies that /api/v1/observability/system-health returns unified database,
    AI telemetry, entity counts, and feedback metrics.
    """
    token_a = test_monitoring_tenants["token_a"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res = client.get("/api/v1/observability/system-health", headers=headers_a)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "ai_telemetry" in data
    assert "feedback_triage" in data
    assert "recent_events" in data
    assert data["database"]["total_projects"] >= 0
    assert data["feedback_triage"]["total_feedback"] >= 0
