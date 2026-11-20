"""
Phase 38: AI Product Intelligence, Data-Driven Recommendations & Automated Workflow Optimization Tests.
Validates:
- Analytics data quality validation & statistical sufficiency checks
- Deterministic rules engine & pattern detection
- Evidence-grounded insights & prioritized recommendations
- Recommendation lifecycle state transitions (READY -> ACCEPTED -> IMPLEMENTED -> VERIFIED)
- Invalid lifecycle state transition rejection
- User recommendation feedback submission & persistence
- Safe automated workflow optimization execution & audit trails
- Impact measurement evaluation & metric deltas
- Strict multi-tenant organization isolation
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
    ProductIntelligenceInsight,
    ProductIntelligenceRecommendation,
    ProductIntelligenceAction,
    RecommendationImpactEvaluation,
    RecommendationFeedback,
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
def test_intel_tenants(db_session):
    """Creates two isolated organizations for intelligence testing."""
    uid = uuid.uuid4().hex[:8]

    # Tenant Alpha
    org_a = Organization(id=f"org-pi-a-{uid}", name="Alpha Intelligence Org", slug=f"alpha-pi-{uid}")
    user_a = User(
        id=f"user-pi-a-{uid}",
        email=f"alpha.lead.{uid}@example.com",
        hashed_password=hash_password("ProductIntel123!"),
        full_name="Alpha Tech Lead",
        is_active=True
    )
    mem_a = OrganizationMembership(
        id=f"mem-pi-a-{uid}",
        organization_id=org_a.id,
        user_id=user_a.id,
        role="OWNER"
    )

    # Tenant Beta
    org_b = Organization(id=f"org-pi-b-{uid}", name="Beta Intelligence Org", slug=f"beta-pi-{uid}")
    user_b = User(
        id=f"user-pi-b-{uid}",
        email=f"beta.lead.{uid}@example.com",
        hashed_password=hash_password("ProductIntel123!"),
        full_name="Beta Tech Lead",
        is_active=True
    )
    mem_b = OrganizationMembership(
        id=f"mem-pi-b-{uid}",
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


def seed_telemetry_for_tenant(db_session, user, org):
    """Helper to seed reliable telemetry and trigger intelligence analysis for tests."""
    from backend.app.services.analytics_service import analytics_service
    analytics_service.record_event(db=db_session, event_name="project_created", user_id=user.id, organization_id=org.id, workflow_type="project")
    for i in range(3):
        analytics_service.record_event(
            db=db_session,
            event_name="research_source_added",
            user_id=user.id,
            organization_id=org.id,
            workflow_type="research",
            workflow_id=f"wf-r-{i}"
        )
    analytics_service.record_event(
        db=db_session,
        event_name="research_source_processing_failed",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="research",
        status="failed"
    )
    analytics_service.record_event(
        db=db_session,
        event_name="editorial_workspace_opened",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="editorial"
    )
    analytics_service.record_event(
        db=db_session,
        event_name="editorial_generation_completed",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="editorial"
    )
    analytics_service.record_event(
        db=db_session,
        event_name="writing_draft_created",
        user_id=user.id,
        organization_id=org.id,
        workflow_type="writing"
    )


def test_data_quality_validation(client, test_intel_tenants, db_session):
    """Test 1: Evaluates analytics data quality before intelligence execution."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial empty state -> INSUFFICIENT_DATA
    res_empty = client.get("/api/v1/intelligence/status", headers=headers)
    assert res_empty.status_code == 200
    data_empty = res_empty.json()
    assert data_empty["status"] == "INSUFFICIENT_DATA"
    assert data_empty["is_sufficient"] is False

    # 2. Seed diverse events
    seed_telemetry_for_tenant(db_session, user, org)

    # 3. Re-evaluate quality -> Sufficient
    res_seeded = client.get("/api/v1/intelligence/status", headers=headers)
    assert res_seeded.status_code == 200
    data_seeded = res_seeded.json()
    assert data_seeded["is_sufficient"] is True
    assert data_seeded["sample_size"] >= 4
    assert data_seeded["score"] >= 40.0


def test_intelligence_analysis_and_pattern_detection(client, test_intel_tenants, db_session):
    """Test 2: Pattern detection rules identify bottlenecks and produce evidence-backed insights."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)

    # Run analysis
    res_run = client.post("/api/v1/intelligence/analyze?days=30", headers=headers)
    assert res_run.status_code == 200
    data_run = res_run.json()
    assert data_run["status"] == "completed"
    assert data_run["insights_generated"] >= 1
    assert data_run["recommendations_generated"] >= 1

    # Verify insights feed contains evidence references
    res_ins = client.get("/api/v1/intelligence/insights", headers=headers)
    assert res_ins.status_code == 200
    insights = res_ins.json()
    assert len(insights) >= 1
    for ins in insights:
        assert "evidence" in ins
        assert "confidence_score" in ins
        assert ins["confidence_score"] > 0.5


def test_recommendation_prioritization_and_overview(client, test_intel_tenants, db_session):
    """Test 3: Recommendations are ranked by priority with estimated effort and expected benefit."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)
    client.post("/api/v1/intelligence/analyze?days=30", headers=headers)

    res_ov = client.get("/api/v1/intelligence/overview", headers=headers)
    assert res_ov.status_code == 200
    ov = res_ov.json()
    assert "data_quality" in ov
    assert "recommendations" in ov
    assert len(ov["recommendations"]) >= 1

    recs = ov["recommendations"]
    priorities = [r["priority"] for r in recs]
    assert any(p in ("CRITICAL", "HIGH", "MEDIUM") for p in priorities)
    for r in recs:
        assert r["estimated_effort"] in ("LOW", "MEDIUM", "HIGH")
        assert len(r["proposed_action"]) > 10
        assert len(r["expected_benefit"]) > 10


def test_recommendation_lifecycle_state_machine(client, test_intel_tenants, db_session):
    """Test 4: Recommendation lifecycle transitions through states and rejects invalid hops."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)
    client.post("/api/v1/intelligence/analyze?days=30", headers=headers)

    # Fetch initial recommendation
    res_list = client.get("/api/v1/intelligence/recommendations", headers=headers)
    assert res_list.status_code == 200
    recs = res_list.json()
    assert len(recs) >= 1
    rec = recs[0]
    rec_id = rec["id"]

    # 1. READY -> ACCEPTED
    res_accept = client.post(f"/api/v1/intelligence/recommendations/{rec_id}/accept", json={"notes": "Approved for action"}, headers=headers)
    assert res_accept.status_code == 200
    assert res_accept.json()["status"] == "ACCEPTED"

    # 2. ACCEPTED -> IMPLEMENTED
    res_impl = client.post(f"/api/v1/intelligence/recommendations/{rec_id}/implement", json={"notes": "Completed fix"}, headers=headers)
    assert res_impl.status_code == 200
    assert res_impl.json()["status"] == "IMPLEMENTED"

    # 3. IMPLEMENTED -> VERIFIED
    res_verify = client.post(f"/api/v1/intelligence/recommendations/{rec_id}/verify", json={"notes": "Impact demonstrated"}, headers=headers)
    assert res_verify.status_code == 200
    assert res_verify.json()["status"] == "VERIFIED"

    # 4. Invalid transition: VERIFIED cannot transition to ACCEPTED
    res_invalid = client.post(f"/api/v1/intelligence/recommendations/{rec_id}/accept", json={}, headers=headers)
    assert res_invalid.status_code == 400


def test_recommendation_feedback_submission(client, test_intel_tenants, db_session):
    """Test 5: Captures user feedback on recommendation accuracy and utility."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)
    client.post("/api/v1/intelligence/analyze?days=30", headers=headers)

    recs = client.get("/api/v1/intelligence/recommendations", headers=headers).json()
    rec_id = recs[0]["id"]

    feedback_payload = {
        "feedback_type": "helpful",
        "rating": 5,
        "comment": "Accelerated source ingestion by 40% after enabling cache."
    }
    res_fb = client.post(f"/api/v1/intelligence/recommendations/{rec_id}/feedback", json=feedback_payload, headers=headers)
    assert res_fb.status_code == 201
    fb_data = res_fb.json()
    assert fb_data["feedback_type"] == "helpful"
    assert fb_data["rating"] == 5

    # Confirm persistence in DB
    row = db_session.query(RecommendationFeedback).filter(RecommendationFeedback.recommendation_id == rec_id).first()
    assert row is not None
    assert row.comment == feedback_payload["comment"]


def test_safe_automated_workflow_optimization(client, test_intel_tenants, db_session):
    """Test 6: Safe automated actions execute with audit trail; dangerous actions are blocked."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)
    client.post("/api/v1/intelligence/analyze?days=30", headers=headers)

    recs = client.get("/api/v1/intelligence/recommendations", headers=headers).json()
    rec_id = recs[0]["id"]

    # 1. Allowed safe action
    safe_action = {
        "action_type": "cache_reuse_optimization",
        "action_payload": {"cache_ttl_seconds": 3600}
    }
    res_safe = client.post(f"/api/v1/intelligence/optimize?recommendation_id={rec_id}", json=safe_action, headers=headers)
    assert res_safe.status_code == 201
    action_data = res_safe.json()
    assert action_data["status"] == "EXECUTED"
    assert len(action_data["audit_trail"]) >= 1

    # 2. Disallowed arbitrary/dangerous action
    dangerous_action = {
        "action_type": "drop_production_table",
        "action_payload": {}
    }
    res_danger = client.post(f"/api/v1/intelligence/optimize", json=dangerous_action, headers=headers)
    assert res_danger.status_code == 400


def test_impact_measurement_evaluation(client, test_intel_tenants, db_session):
    """Test 7: Pre/post implementation metric comparison computes deltas and status."""
    token = test_intel_tenants["token_a"]
    org = test_intel_tenants["org_a"]
    user = test_intel_tenants["user_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_telemetry_for_tenant(db_session, user, org)
    client.post("/api/v1/intelligence/analyze?days=30", headers=headers)

    recs = client.get("/api/v1/intelligence/recommendations", headers=headers).json()
    rec_id = recs[0]["id"]

    res_impact = client.get(f"/api/v1/intelligence/impact/{rec_id}", headers=headers)
    assert res_impact.status_code == 200
    imp = res_impact.json()
    assert "baseline_metrics" in imp
    assert "current_metrics" in imp
    assert "metric_delta" in imp
    assert imp["evaluation_status"] in ("IMPROVED", "NO_SIGNIFICANT_CHANGE", "REGRESSED", "INSUFFICIENT_DATA")


def test_tenant_isolation_on_intelligence(client, test_intel_tenants, db_session):
    """Test 8: Strict multi-tenant isolation prevents cross-tenant insight leakage."""
    token_b = test_intel_tenants["token_b"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Org B queries overview
    res_b = client.get("/api/v1/intelligence/overview", headers=headers_b)
    assert res_b.status_code == 200
    ov_b = res_b.json()
    # Org B must see 0 insights and 0 recommendations because Org B has no telemetry
    assert ov_b["active_insights_count"] == 0
    assert len(ov_b["recommendations"]) == 0
    assert ov_b["data_quality"]["status"] == "INSUFFICIENT_DATA"
