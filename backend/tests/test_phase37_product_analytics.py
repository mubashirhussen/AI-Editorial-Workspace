"""
Phase 37: Advanced Product Analytics, User Journey Intelligence, Feature Adoption & Privacy-Conscious Metrics Tests.
Validates:
- Event ingestion with schema validation and unique event IDs
- Strict privacy data minimization (filtering raw text, prompts, emails, tokens, passwords)
- User pseudonymization via cryptographic HMAC-SHA256
- Event deduplication and idempotency
- User privacy preference and analytics opt-out enforcement
- Strict multi-tenant isolation across organizations
- Workflow journey completion metrics and funnel drop-off analysis
- Feature adoption matrix and daily usage trend reporting
- Subsystem health diagnostics and data retention cleanup
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    AnalyticsEvent,
    AnalyticsPrivacyPreference,
    ResearchProject,
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
def test_analytics_tenants(db_session):
    """Creates two isolated tenants for multi-tenant product analytics validation."""
    uid = uuid.uuid4().hex[:8]

    # Tenant Alpha
    org_a = Organization(id=f"org-an-a-{uid}", name="Alpha Analytics Org", slug=f"alpha-an-{uid}")
    user_a = User(
        id=f"user-an-a-{uid}",
        email=f"alpha.analyst.{uid}@example.com",
        hashed_password=hash_password("AnalyticsPass123!"),
        full_name="Alpha Analyst",
        is_active=True
    )
    mem_a = OrganizationMembership(
        id=f"mem-an-a-{uid}",
        organization_id=org_a.id,
        user_id=user_a.id,
        role="OWNER"
    )

    # Tenant Beta
    org_b = Organization(id=f"org-an-b-{uid}", name="Beta Analytics Org", slug=f"beta-an-{uid}")
    user_b = User(
        id=f"user-an-b-{uid}",
        email=f"beta.analyst.{uid}@example.com",
        hashed_password=hash_password("AnalyticsPass123!"),
        full_name="Beta Analyst",
        is_active=True
    )
    mem_b = OrganizationMembership(
        id=f"mem-an-b-{uid}",
        organization_id=org_b.id,
        user_id=user_b.id,
        role="MEMBER"
    )

    db_session.add_all([org_a, user_a, mem_a, org_b, user_b, mem_b])
    db_session.commit()

    token_a = create_access_token(data={"sub": user_a.id, "email": user_a.email})
    token_b = create_access_token(data={"sub": user_b.id, "email": user_b.email})

    return {
        "org_a": org_a,
        "user_a": user_a,
        "token_a": token_a,
        "org_b": org_b,
        "user_b": user_b,
        "token_b": token_b,
    }


def test_event_ingestion_and_schema_validation(client, test_analytics_tenants, db_session):
    """Test 1: Valid first-party events are accepted and invalid schemas are rejected."""
    token = test_analytics_tenants["token_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Valid event ingestion
    valid_payload = {
        "event_name": "research_brief_generation_completed",
        "event_version": 1,
        "workflow_type": "research",
        "workflow_reference": "wf-test-101",
        "session_reference": "sess-test-202",
        "source": "frontend",
        "status": "completed",
        "duration_ms": 1450,
        "properties": {
            "sources_count": 5,
            "format": "markdown",
            "status": "success"
        }
    }
    res = client.post("/api/v1/analytics/events", json=valid_payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["status"] == "recorded"
    assert data["event_name"] == "research_brief_generation_completed"

    # 2. Invalid schema (missing required event_name)
    invalid_payload = {
        "workflow_type": "research",
        "duration_ms": -50
    }
    res_err = client.post("/api/v1/analytics/events", json=invalid_payload, headers=headers)
    assert res_err.status_code in (400, 422)


def test_privacy_sanitization_and_pseudonymization(client, test_analytics_tenants, db_session):
    """Test 2: Sensitive keys are strictly stripped and user ID is converted to a pseudonym."""
    token = test_analytics_tenants["token_a"]
    user_a = test_analytics_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    sensitive_payload = {
        "event_name": "writing_draft_saved",
        "workflow_type": "writing",
        "workflow_reference": f"wf-priv-{uuid.uuid4().hex[:6]}",
        "properties": {
            # Forbidden sensitive keys
            "password": "super_secret_password",
            "prompt": "write a confidential article about internal acquisition",
            "text": "full article content with secret details",
            "email": "user@private.com",
            "bearer_token": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            # Safe allowlisted keys
            "word_count": 450,
            "flesch_score": 68.5,
            "format": "markdown"
        }
    }

    res = client.post("/api/v1/analytics/events", json=sensitive_payload, headers=headers)
    assert res.status_code == 201, res.text

    # Inspect persisted record in database
    event_row = db_session.query(AnalyticsEvent).filter(
        AnalyticsEvent.event_name == "writing_draft_saved",
        AnalyticsEvent.workflow_id == sensitive_payload["workflow_reference"]
    ).first()

    assert event_row is not None
    # User Pseudonym must NOT be the plain user ID or email
    assert event_row.user_pseudonym is not None
    assert event_row.user_pseudonym.startswith("usr_")
    assert user_a.id not in event_row.user_pseudonym
    assert user_a.email not in str(event_row.properties_json)

    # Sensitive keys must be purged
    props = event_row.properties_json
    assert "password" not in props
    assert "prompt" not in props
    assert "text" not in props
    assert "email" not in props
    assert "bearer_token" not in props

    # Safe keys must be retained
    assert props.get("word_count") == 450
    assert props.get("flesch_score") == 68.5
    assert props.get("format") == "markdown"


def test_event_deduplication(client, test_analytics_tenants, db_session):
    """Test 3: Identical event actions within the deduplication window are suppressed."""
    token = test_analytics_tenants["token_a"]
    headers = {"Authorization": f"Bearer {token}"}
    wf_id = f"wf-dedup-{uuid.uuid4().hex[:6]}"

    payload = {
        "event_name": "feature_used",
        "workflow_type": "editorial",
        "workflow_reference": wf_id,
        "session_reference": "sess-dedup-1",
        "properties": {"action": "headline_generation"}
    }

    # First call: recorded
    res1 = client.post("/api/v1/analytics/events", json=payload, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["status"] == "recorded"

    # Second call (immediate identical retry): deduplicated
    res2 = client.post("/api/v1/analytics/events", json=payload, headers=headers)
    assert res2.status_code == 201
    assert res2.json()["status"] == "acknowledged"
    assert "duplicate" in res2.json()["message"]


def test_user_privacy_preference_and_opt_out(client, test_analytics_tenants, db_session):
    """Test 4: Opt-out privacy preference blocks analytics tracking for the user."""
    token = test_analytics_tenants["token_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check default preference (opt-out = false)
    get_res = client.get("/api/v1/analytics/privacy-preference", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["analytics_opt_out"] is False

    # 2. Update preference to opt-out
    put_res = client.put(
        "/api/v1/analytics/privacy-preference",
        json={"analytics_opt_out": True, "do_not_track": True},
        headers=headers
    )
    assert put_res.status_code == 200
    assert put_res.json()["analytics_opt_out"] is True

    # 3. Submit event while opted out
    opt_out_wf = f"wf-optout-{uuid.uuid4().hex[:6]}"
    res_event = client.post(
        "/api/v1/analytics/events",
        json={"event_name": "research_workspace_opened", "workflow_reference": opt_out_wf},
        headers=headers
    )
    assert res_event.status_code == 201
    assert res_event.json()["status"] == "acknowledged"

    # 4. Confirm event was NOT persisted
    row = db_session.query(AnalyticsEvent).filter(AnalyticsEvent.workflow_id == opt_out_wf).first()
    assert row is None, "Opted-out user's event must not be saved in database."

    # Reset opt-out for remaining tests
    client.put(
        "/api/v1/analytics/privacy-preference",
        json={"analytics_opt_out": False, "do_not_track": False},
        headers=headers
    )


def test_tenant_isolation_on_analytics_overview(client, test_analytics_tenants, db_session):
    """Test 5: Organizations can only see their own metrics and active users."""
    token_a = test_analytics_tenants["token_a"]
    token_b = test_analytics_tenants["token_b"]
    org_a = test_analytics_tenants["org_a"]
    user_a = test_analytics_tenants["user_a"]

    # Seed 3 projects and 2 completed workflows for Org A
    proj_a = ResearchProject(
        id=f"proj-iso-{uuid.uuid4().hex[:6]}",
        organization_id=org_a.id,
        title="Alpha Internal Project",
        topic="Confidential Alpha AI Research"
    )
    db_session.add(proj_a)
    db_session.commit()

    from backend.app.services.analytics_service import analytics_service
    analytics_service.record_event(
        db=db_session,
        event_name="workflow_completed",
        user_id=user_a.id,
        organization_id=org_a.id,
        project_id=proj_a.id,
        workflow_type="editorial",
        status="completed"
    )

    # Org A overview
    res_a = client.get("/api/v1/analytics/overview?days=30", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["projects_created"] >= 1
    assert data_a["completed_workflows"] >= 1

    # Org B overview (must not see Org A's project or workflow)
    res_b = client.get("/api/v1/analytics/overview?days=30", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["projects_created"] == 0
    assert data_b["completed_workflows"] == 0


def test_workflow_intelligence_and_funnels(client, test_analytics_tenants, db_session):
    """Test 6: Deep workflow metrics and step-by-step conversion funnels."""
    token = test_analytics_tenants["token_a"]
    org = test_analytics_tenants["org_a"]
    user = test_analytics_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    from backend.app.services.analytics_service import analytics_service
    # Seed full research funnel events
    analytics_service.record_event(
        db=db_session,
        event_name="research_source_added",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="research",
        status="completed"
    )
    analytics_service.record_event(
        db=db_session,
        event_name="research_source_processing_completed",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="research",
        status="completed"
    )
    analytics_service.record_event(
        db=db_session,
        event_name="research_brief_generation_completed",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="research",
        status="completed"
    )

    # 1. Query Workflows endpoint
    wf_res = client.get("/api/v1/analytics/workflows?days=30", headers=headers)
    assert wf_res.status_code == 200
    wf_data = wf_res.json()
    assert "workflows" in wf_data
    types = [w["workflow_type"] for w in wf_data["workflows"]]
    assert "research" in types
    assert "writing" in types
    assert "editorial" in types

    # 2. Query Funnels endpoint
    fn_res = client.get("/api/v1/analytics/funnels?days=30", headers=headers)
    assert fn_res.status_code == 200
    fn_data = fn_res.json()
    assert "research_funnel" in fn_data
    assert "writing_funnel" in fn_data
    assert "editorial_funnel" in fn_data
    assert len(fn_data["research_funnel"]["steps"]) == 4


def test_features_and_trends_reporting(client, test_analytics_tenants, db_session):
    """Test 7: Feature adoption matrix and daily trend timeseries."""
    token = test_analytics_tenants["token_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # Features
    ft_res = client.get("/api/v1/analytics/features?days=30", headers=headers)
    assert ft_res.status_code == 200
    ft_data = ft_res.json()
    assert "features" in ft_data
    assert len(ft_data["features"]) >= 6
    for f in ft_data["features"]:
        assert "feature_name" in f
        assert "usage_count" in f
        assert "success_rate" in f

    # Trends
    tr_res = client.get("/api/v1/analytics/trends?days=7", headers=headers)
    assert tr_res.status_code == 200
    tr_data = tr_res.json()
    assert "data_points" in tr_data
    assert len(tr_data["data_points"]) == 7


def test_subsystem_health_and_retention_cleanup(client, test_analytics_tenants, db_session):
    """Test 8: Telemetry health probe and administrative retention purge."""
    token = test_analytics_tenants["token_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Health check
    hl_res = client.get("/api/v1/analytics/health", headers=headers)
    assert hl_res.status_code == 200
    hl_data = hl_res.json()
    assert hl_data["status"] == "HEALTHY"
    assert hl_data["storage_retention_days"] == 90
    assert "total_events" in hl_data

    # 2. Trigger retention purge
    purge_res = client.post("/api/v1/analytics/retention/cleanup?retention_days=90", headers=headers)
    assert purge_res.status_code == 200
    assert purge_res.json()["status"] == "success"
    assert "purged_events_count" in purge_res.json()
