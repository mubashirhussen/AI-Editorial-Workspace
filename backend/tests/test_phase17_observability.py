import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.services.monitoring_service import monitoring_service

client = TestClient(app)

def test_health_liveness():
    """
    Verify GET /health/live returns 200 OK and status 'alive'.
    """
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "application" in data
    assert "version" in data

def test_health_readiness_connected():
    """
    Verify GET /health/ready returns 200 OK when database is reachable.
    """
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
    assert "dependencies" in data

def test_health_readiness_db_failure():
    """
    Verify GET /health/ready returns 503 Service Unavailable when DB is disconnected.
    """
    # Mock a failing DB session
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("Simulated connection timeout to SQLite/Postgres")
    
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"
        assert "Simulated connection timeout" in data["detail"]
    finally:
        app.dependency_overrides.clear()

def test_health_comprehensive_telemetry():
    """
    Verify GET /health returns database status, AI engine state, and telemetry metrics.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "ai_engine" in data
    assert "telemetry" in data
    telemetry = data["telemetry"]
    assert "uptime_seconds" in telemetry
    assert "ai_telemetry" in telemetry
    assert "recent_events" in telemetry

def test_request_id_generation_and_propagation():
    """
    Verify ObservabilityMiddleware generates X-Request-ID when not supplied,
    and returns it in the response header.
    """
    response = client.get("/health/live")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    assert len(request_id) > 10

def test_request_id_custom_forwarding():
    """
    Verify ObservabilityMiddleware preserves incoming client X-Request-ID header.
    """
    custom_id = "fde-trace-custom-uuid-98765"
    response = client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

def test_structured_validation_error_with_request_id():
    """
    Verify 422 validation errors include request_id in the JSON body matching header.
    """
    custom_id = "test-validation-error-id-123"
    # POST to /api/v1/projects with invalid payload (missing required title)
    response = client.post(
        "/api/v1/projects",
        json={"invalid_field": 123},
        headers={"X-Request-ID": custom_id}
    )
    assert response.status_code == 422
    assert response.headers.get("X-Request-ID") == custom_id
    data = response.json()
    assert data["request_id"] == custom_id
    assert data["error_category"] == "VALIDATION_ERROR"
    assert "detail" in data

def test_monitoring_service_records_ai_operation():
    """
    Verify monitoring_service accurately records AI events and token aggregates.
    """
    initial_summary = monitoring_service.get_telemetry_summary()
    initial_total = initial_summary["ai_telemetry"]["total_operations"]
    initial_tokens = initial_summary["ai_telemetry"]["cumulative_tokens"]["total_tokens"]

    event = monitoring_service.record_ai_operation(
        operation_type="unit_test_analysis",
        duration_ms=45.2,
        status="success",
        provider_error=None,
        prompt_tokens=150,
        completion_tokens=50
    )

    assert event["operation"] == "unit_test_analysis"
    assert event["duration_ms"] == 45.2
    assert event["status"] == "success"
    assert event["tokens"]["total"] == 200

    updated_summary = monitoring_service.get_telemetry_summary()
    assert updated_summary["ai_telemetry"]["total_operations"] == initial_total + 1
    assert updated_summary["ai_telemetry"]["cumulative_tokens"]["total_tokens"] == initial_tokens + 200
    assert len(updated_summary["recent_events"]) > 0
    assert updated_summary["recent_events"][0]["operation"] == "unit_test_analysis"

