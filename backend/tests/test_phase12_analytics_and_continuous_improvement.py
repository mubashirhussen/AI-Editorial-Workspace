import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.base import User, Organization, OrganizationMembership, UsageEvent
from backend.app.services.analytics_service import analytics_service

client = TestClient(app)

@pytest.fixture
def test_env():
    db = SessionLocal()
    org_id = f"test-org-{uuid.uuid4().hex[:8]}"
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    email = f"user_{uuid.uuid4().hex[:6]}@editorial.ai"

    org = Organization(id=org_id, name="Analytics Test Org", slug=f"slug-{uuid.uuid4().hex[:6]}")
    user = User(id=user_id, email=email, full_name="Analytics Tester", is_active=True, hashed_password="mock_hashed_pw")
    db.add_all([org, user])
    db.flush()

    mem = OrganizationMembership(
        id=f"mem-{uuid.uuid4().hex[:8]}",
        organization_id=org.id,
        user_id=user.id,
        role="OWNER"
    )
    db.add(mem)
    db.commit()

    from backend.app.core.security import create_access_token
    token = create_access_token({"sub": user.id, "email": user.email})

    yield {
        "db": db,
        "org_id": org_id,
        "user_id": user_id,
        "token": token,
        "headers": {
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": org_id
        }
    }
    db.close()


def test_track_privacy_safe_event(test_env):
    """Verifies approved analytics events are recorded with clean metadata."""
    db = test_env["db"]
    org_id = test_env["org_id"]

    event = analytics_service.track_event(
        db=db,
        organization_id=org_id,
        metric_name="project_created",
        metric_value=1.0,
        metadata={"category": "ai_research", "status": "active"}
    )
    assert event is not None
    assert event.metric_name == "project_created"
    assert event.tags_json.get("category") == "ai_research"
    assert event.tags_json.get("status") == "active"


def test_pii_sanitization_defense(test_env):
    """Verifies that unsanctioned metadata containing passwords, emails, or raw text is strictly discarded."""
    db = test_env["db"]
    org_id = test_env["org_id"]

    event = analytics_service.track_event(
        db=db,
        organization_id=org_id,
        metric_name="export_executed",
        metric_value=1.0,
        metadata={
            "format": "markdown",
            "password": "super_secret_password",
            "api_key": "sk-1234567890",
            "private_text": "Classified insider briefing"
        }
    )
    assert event is not None
    # Allowed key
    assert event.tags_json.get("format") == "markdown"
    # Prohibited keys must NOT be present
    assert "password" not in event.tags_json
    assert "api_key" not in event.tags_json
    assert "private_text" not in event.tags_json


def test_funnel_aggregation_metrics(test_env):
    """Verifies conversion rates and funnel summary across the complete editorial journey."""
    db = test_env["db"]
    org_id = test_env["org_id"]

    # Ingest 3 sources, generate 1 brief, create 1 draft
    analytics_service.track_event(db, org_id, "source_processed")
    analytics_service.track_event(db, org_id, "source_processed")
    analytics_service.track_event(db, org_id, "source_processed")
    analytics_service.track_event(db, org_id, "brief_generated")
    analytics_service.track_event(db, org_id, "draft_created")
    analytics_service.track_event(db, org_id, "writing_improved")
    analytics_service.track_event(db, org_id, "export_executed", metadata={"format": "html"})
    analytics_service.track_event(db, org_id, "workflow_failed", metadata={"category": "timeout"})

    funnel = analytics_service.get_funnel_summary(db=db, organization_id=org_id)
    assert funnel["sources_processed"] >= 3
    assert funnel["briefs_generated"] >= 1
    assert funnel["drafts_created"] >= 1
    assert funnel["writing_improved"] >= 1
    assert funnel["exports_executed"] >= 1
    assert funnel["workflow_failures"] >= 1
    assert funnel["total_events"] >= 8
    assert funnel["research_synthesis_rate"] > 0.0
    assert funnel["draft_generation_rate"] > 0.0


def test_analytics_api_endpoints(test_env):
    """Verifies REST endpoints for analytics: /funnel, /events, /track."""
    headers = test_env["headers"]

    # Track client-side UI event
    res = client.post(
        "/api/v1/analytics/track",
        json={
            "metric_name": "export_executed",
            "metric_value": 1.0,
            "metadata": {"format": "txt", "status": "completed"}
        },
        headers=headers
    )
    assert res.status_code == 201
    assert res.json()["status"] == "recorded"

    # Query funnel
    funnel_res = client.get("/api/v1/analytics/funnel", headers=headers)
    assert funnel_res.status_code == 200
    data = funnel_res.json()
    assert "total_events" in data
    assert "research_synthesis_rate" in data

    # Query recent events
    events_res = client.get("/api/v1/analytics/events?limit=10", headers=headers)
    assert events_res.status_code == 200
    events = events_res.json()
    assert isinstance(events, list)
    assert len(events) > 0
    assert "metric_name" in events[0]
