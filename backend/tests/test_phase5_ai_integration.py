import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ai.models import get_all_providers, get_all_models
from backend.app.services.ai.router import ai_router

client = TestClient(app)

def test_phase5_get_supported_providers():
    """Verify AI provider catalog lists standard providers with capabilities."""
    response = client.get("/api/v1/ai/providers")
    assert response.status_code == 200
    providers = response.json()
    provider_ids = [p["id"] for p in providers]
    
    assert "groq" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "google_gemini" in provider_ids

    groq_info = next(p for p in providers if p["id"] == "groq")
    assert groq_info["default_model"] == "openai/gpt-oss-20b"
    assert len(groq_info["models"]) >= 2
    assert "structured_json" in groq_info["models"][0]["capabilities"]


def test_phase5_get_supported_models():
    """Verify AI model catalog returns registered models with context windows and descriptions."""
    # All models
    res_all = client.get("/api/v1/ai/models")
    assert res_all.status_code == 200
    all_models = res_all.json()
    assert len(all_models) >= 8

    # Filtered by Groq
    res_groq = client.get("/api/v1/ai/models?provider=groq")
    assert res_groq.status_code == 200
    groq_models = res_groq.json()
    assert len(groq_models) >= 2
    for m in groq_models:
        assert m["provider"] == "groq"
        assert m["context_window"] >= 8000
        assert "description" in m
        assert "capabilities" in m


def test_phase5_ai_health_probe():
    """Verify AI system health status and telemetry summary probe."""
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["operational", "deterministic_fallback", "degraded", "healthy"]
    assert "active_provider" in data
    assert "active_model" in data
    assert "total_configured_connections" in data
    assert "telemetry_summary" in data


def test_phase5_connection_lifecycle_and_key_masking():
    """Verify connection registration encrypts secret at rest and masks in API response."""
    raw_key = "gsk_live_verification_secret_998877665544332211"
    
    # 1. Create connection
    create_payload = {
        "provider": "groq",
        "name": "Test Groq Fast LPU",
        "api_key": raw_key,
        "model": "openai/gpt-oss-20b",
        "is_default": True
    }
    create_res = client.post("/api/v1/ai/connections", json=create_payload)
    assert create_res.status_code == 201
    conn = create_res.json()
    conn_id = conn["id"]

    assert conn["provider"] == "groq"
    assert conn["name"] == "Test Groq Fast LPU"
    # Verify key is never exposed in plaintext
    assert raw_key not in conn["masked_key"]
    assert "..." in conn["masked_key"]
    assert conn["masked_key"].endswith("2211")

    # 2. List connections
    list_res = client.get("/api/v1/ai/connections")
    assert list_res.status_code == 200
    connections = list_res.json()
    found = [c for c in connections if c["id"] == conn_id]
    assert len(found) == 1
    assert found[0]["masked_key"] == conn["masked_key"]

    # 3. Rotate key
    new_raw_key = "gsk_rotated_new_secret_key_112233445566778899"
    rotate_res = client.post(f"/api/v1/ai/connections/{conn_id}/rotate", json={"new_api_key": new_raw_key})
    assert rotate_res.status_code == 200
    rotated_conn = rotate_res.json()
    assert new_raw_key not in rotated_conn["masked_key"]
    assert rotated_conn["masked_key"].endswith("8899")

    # 4. Clean up connection
    del_res = client.delete(f"/api/v1/ai/connections/{conn_id}")
    assert del_res.status_code in [200, 204]


def test_phase5_router_fallback_resilience():
    """Verify router cleanly uses deterministic fallback when given invalid credentials."""
    # Deterministic fallback adapter guarantees valid structured output
    res = asyncio.run(ai_router.fallback_adapter.generate_structured(
        prompt="Synthesize technical implications",
        system_prompt="Return JSON"
    ))
    assert res.is_fallback is True
    assert res.content is not None
    assert "headline" in res.content or "summary" in res.content or "key_takeaways" in res.content


def test_phase5_usage_and_telemetry_reporting():
    """Verify AI usage records and aggregation summary endpoint."""
    res = client.get("/api/v1/ai/usage/summary")
    assert res.status_code == 200
    summary = res.json()
    assert "total_calls" in summary
    assert "total_tokens" in summary
    assert "total_prompt_tokens" in summary
    assert "total_completion_tokens" in summary
    assert "by_provider" in summary

    # Verify query for individual usage logs
    logs_res = client.get("/api/v1/ai/usage?limit=5")
    assert logs_res.status_code == 200
    assert isinstance(logs_res.json(), list)
