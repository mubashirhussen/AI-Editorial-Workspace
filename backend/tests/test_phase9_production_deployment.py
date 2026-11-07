import os
import sys
import time
import json
import base64
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from sqlalchemy import create_engine

from backend.app.core.config import Settings, _WEAK_SECRETS
from backend.app.core.database import Base, get_db, create_db_engine
from backend.app.main import app
from backend.app.services.task_queue import AsyncTaskQueue, TaskStatus
from backend.app.utils.security import is_safe_url
from backend.app.services.ai.pricing import calculate_estimated_cost
import scripts.backup_db as backup_module
import scripts.restore_db as restore_module


# ==============================================================================
# TEST 1: Production Settings Validation
# ==============================================================================
def test_production_settings_rejects_weak_and_short_secrets():
    """Verify that in production mode, default or short JWT secrets raise ValueError."""
    # 1. Weak default secret
    with pytest.raises(ValueError, match="cannot use default or weak secrets"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="super-secret-editorial-ai-jwt-key-change-in-production",
            ALLOW_ANONYMOUS_DEV=False
        )

    # 2. Short secret (< 32 chars)
    with pytest.raises(ValueError, match="at least 32 characters long"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-secret-12345",
            ALLOW_ANONYMOUS_DEV=False
        )

    # 3. Disallow anonymous dev mode in production
    with pytest.raises(ValueError, match="ALLOW_ANONYMOUS_DEV must be set to False"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 32,
            ALLOW_ANONYMOUS_DEV=True
        )

    # 4. Valid production settings pass cleanly
    valid_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a" * 32,
        ALLOW_ANONYMOUS_DEV=False
    )
    assert valid_settings.ENVIRONMENT == "production"
    assert valid_settings.ALLOW_ANONYMOUS_DEV is False


# ==============================================================================
# TEST 2: Encryption Key Validation
# ==============================================================================
def test_production_encryption_key_validation():
    """Verify Fernet 32-byte urlsafe base64 encryption key format validation."""
    valid_fernet = Fernet.generate_key().decode()
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="b" * 32,
        ALLOW_ANONYMOUS_DEV=False,
        ENCRYPTION_KEY=valid_fernet
    )
    assert settings.ENCRYPTION_KEY == valid_fernet

    # Invalid encryption key (not 32 bytes or invalid base64)
    with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="b" * 32,
            ALLOW_ANONYMOUS_DEV=False,
            ENCRYPTION_KEY="invalid-base64-string!!"
        )


# ==============================================================================
# TEST 3: Database Engine and Connection Pooling
# ==============================================================================
def test_database_engine_connection_pooling_and_prepings():
    """Verify that Postgres engines are instantiated with connection pool configurations."""
    # SQLite has check_same_thread=False
    sqlite_eng = create_db_engine("sqlite:///./test_pool.db")
    assert sqlite_eng is not None

    # Test postgres pooling configuration instantiation logic
    with patch("backend.app.core.database.create_engine") as mock_engine_create:
        mock_engine_create.return_value = MagicMock()
        _ = create_db_engine("postgresql://user:pass@localhost:5432/editorial")
        mock_engine_create.assert_called_once()
        _, kwargs = mock_engine_create.call_args
        assert kwargs.get("pool_pre_ping") is True
        assert kwargs.get("pool_size") == 10
        assert kwargs.get("max_overflow") == 20
        assert kwargs.get("pool_recycle") == 1800


# ==============================================================================
# TEST 4: SRE Health Probes (/health/live, /health/ready, /health/startup, /health)
# ==============================================================================
def test_sre_health_probes():
    """Verify Kubernetes liveness, readiness, startup, and aggregate health probes."""
    client = TestClient(app)

    # 1. Liveness Probe
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json().get("status") == "alive"

    # 2. Readiness Probe
    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    ready_data = res_ready.json()
    assert ready_data.get("status") == "ready"
    assert ready_data.get("database") in ("healthy", "connected")
    assert "db_latency_ms" in ready_data

    # 3. Startup Probe
    res_startup = client.get("/health/startup")
    assert res_startup.status_code == 200
    assert res_startup.json().get("status") == "started"

    # 4. Standard Health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json().get("status") == "healthy"


# ==============================================================================
# TEST 5: Security Headers Enforcement
# ==============================================================================
def test_security_headers_enforcement():
    """Verify that all responses include strict security hardening headers."""
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# ==============================================================================
# TEST 6: Rate Limiting Under Load
# ==============================================================================
def test_rate_limiting_middleware_exhaustion():
    """Verify rate limiter blocks excessive requests with HTTP 429."""
    from backend.app.main import InMemoryRateLimiterMiddleware
    limiter = InMemoryRateLimiterMiddleware(app=MagicMock(), requests_per_minute=5)
    
    now = time.time()
    limiter.request_records["198.51.100.1"] = [now - 10] * 5  # 5 requests within window

    # Test request with X-Test-Rate-Limit header
    mock_request = MagicMock()
    mock_request.client.host = "198.51.100.1"
    mock_request.headers.get.side_effect = lambda h: "true" if h == "X-Test-Rate-Limit" else None
    mock_request.url.path = "/api/v1/research/projects"
    mock_request.state.request_id = "test-request-id-12345"

    import asyncio
    async def dummy_call_next(req):
        return None

    resp = asyncio.run(limiter.dispatch(mock_request, dummy_call_next))
    assert resp.status_code == 429
    data = json.loads(resp.body.decode())
    assert data["error_category"] == "RATE_LIMIT_EXCEEDED"


# ==============================================================================
# TEST 7: Strict CORS Origin Parsing
# ==============================================================================
def test_cors_origin_parsing():
    """Verify comma-delimited ALLOWED_ORIGINS string is properly converted to a clean list."""
    settings = Settings(
        ALLOWED_ORIGINS="https://app.editorial.com, https://admin.editorial.com,https://preview.editorial.com"
    )
    assert isinstance(settings.ALLOWED_ORIGINS, list)
    assert len(settings.ALLOWED_ORIGINS) == 3
    assert "https://app.editorial.com" in settings.ALLOWED_ORIGINS
    assert "https://admin.editorial.com" in settings.ALLOWED_ORIGINS


# ==============================================================================
# TEST 8: SSRF Protection Against Cloud Metadata and Private IPs
# ==============================================================================
def test_ssrf_protection_blocked_destinations():
    """Verify SSRF validator blocks localhost, 127.0.0.1, 10.0.0.0/8, and AWS metadata (169.254.169.254)."""
    assert is_safe_url("http://127.0.0.1:8000/secret") is False
    assert is_safe_url("http://localhost:3000") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://10.0.0.1/internal-api") is False
    assert is_safe_url("http://192.168.1.1/router") is False
    assert is_safe_url("https://arxiv.org/abs/1706.03762") is True
    assert is_safe_url("https://en.wikipedia.org/wiki/Artificial_intelligence") is True


# ==============================================================================
# TEST 9: Structured Logging and Zero Secret Leakage
# ==============================================================================
def test_logging_zero_secret_leakage():
    """Verify that sensitive headers and API keys are scrubbed and not logged in plaintext."""
    client = TestClient(app)
    sensitive_token = "Bearer test_super_sensitive_jwt_token_12345"
    
    with patch("backend.app.main.logger.info") as mock_log:
        response = client.get("/health/live", headers={"Authorization": sensitive_token})
        assert response.status_code == 200
        
        # Verify that the sensitive token does not appear in any logged arguments
        for call_args in mock_log.call_args_list:
            log_str = str(call_args)
            assert sensitive_token not in log_str


# ==============================================================================
# TEST 10: Database Backup Execution and Checksum Manifest
# ==============================================================================
def test_database_backup_generation(tmp_path):
    """Verify database backup creates a file, manifest, and correct SHA256 checksum."""
    db_file = tmp_path / "test.db"
    db_file.write_text("PRAGMA user_version = 1;")
    backup_dir = tmp_path / "backups"

    res = backup_module.backup_database(
        database_url=f"sqlite:///{db_file}",
        backup_dir=str(backup_dir),
        retention_days=7
    )

    assert res["status"] == "success"
    assert os.path.exists(res["backup_path"])
    assert os.path.exists(res["manifest_path"])
    assert len(res["sha256"]) == 64

    # Verify manifest JSON integrity
    with open(res["manifest_path"], "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["sha256"] == res["sha256"]


# ==============================================================================
# TEST 11: Database Restore Execution and Integrity Check
# ==============================================================================
def test_database_restore_dry_run_and_execution(tmp_path):
    """Verify database restore script checks SHA256 and executes restore with dry-run support."""
    # 1. Create a simulated backup and manifest
    backup_file = tmp_path / "db_backup.db"
    backup_file.write_text("PRAGMA user_version = 42;")
    sha256_hash = backup_module.calculate_sha256(str(backup_file))

    manifest_file = tmp_path / "db_backup.json"
    manifest_data = {
        "backup_file": str(backup_file),
        "sha256": sha256_hash,
        "database_type": "sqlite",
        "timestamp": time.time(),
        "status": "complete"
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)

    target_db = tmp_path / "restored.db"
    target_url = f"sqlite:///{target_db}"

    # 2. Test Dry Run
    dry_run_res = restore_module.restore_database(
        manifest_path=str(manifest_file),
        target_database_url=target_url,
        dry_run=True
    )
    assert dry_run_res["status"] == "dry_run_passed"
    assert not target_db.exists()

    # 3. Test Full Restore
    restore_res = restore_module.restore_database(
        manifest_path=str(manifest_file),
        target_database_url=target_url,
        dry_run=False
    )
    assert restore_res["status"] == "success"
    assert target_db.exists()
    assert target_db.read_text() == "PRAGMA user_version = 42;"


# ==============================================================================
# TEST 12: Background Task Queue Dispatch, Idempotency, and Retries
# ==============================================================================
@pytest.mark.asyncio
async def test_background_task_queue_execution_and_retries():
    """Verify task queue executes handlers, tracks status, enforces idempotency, and retries on failure."""
    queue = AsyncTaskQueue()

    call_count = {"count": 0}

    async def flaky_handler(attempt_target: int):
        call_count["count"] += 1
        if call_count["count"] < attempt_target:
            raise RuntimeError(f"Attempt {call_count['count']} failed!")
        return {"processed": True, "attempts": call_count["count"]}

    queue.register_handler("test_flaky", flaky_handler)

    # Dispatch task with max_retries=3
    task_id = "test-task-uuid-12345"
    task = await queue.dispatch("test_flaky", task_id=task_id, max_retries=3, kwargs={"attempt_target": 2})

    # Wait for completion
    completed_task = await queue.wait_for_task(task_id, timeout=5.0)
    assert completed_task is not None
    assert completed_task.status == TaskStatus.SUCCESS
    assert completed_task.result == {"processed": True, "attempts": 2}

    # Verify idempotency: dispatching same task_id returns existing task
    duplicate_task = await queue.dispatch("test_flaky", task_id=task_id)
    assert duplicate_task.task_id == task_id
    assert duplicate_task.status == TaskStatus.SUCCESS


# ==============================================================================
# TEST 13: Alembic Migrations and Schema Consistency
# ==============================================================================
def test_alembic_migrations_head_exists():
    """Verify Alembic configuration and migration heads are valid and aligned."""
    import alembic.config
    import alembic.script
    
    cfg = alembic.config.Config("backend/alembic.ini")
    script = alembic.script.ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) > 0
    assert "7a2c3d4e5f6a" in heads or len(heads) == 1


# ==============================================================================
# TEST 14: End-to-End Full Deployment Flow
# ==============================================================================
def test_e2e_full_deployment_workflow():
    """Verify complete end-to-end operational pipeline: auth -> project -> source -> brief -> draft -> observability."""
    client = TestClient(app)

    # 1. Health check
    res_health = client.get("/health/ready")
    assert res_health.status_code == 200

    # 2. Anonymous / Dev Project Creation
    res_proj = client.post(
        "/api/v1/research/projects",
        json={"title": "Phase 9 Production Verification Project", "description": "Cloud Native Deployments"}
    )
    assert res_proj.status_code in (200, 201)
    project_id = res_proj.json()["id"]

    # 3. Source Ingestion
    res_source = client.post(
        f"/api/v1/research/projects/{project_id}/sources",
        json={
            "title": "Production DevOps Best Practices",
            "url": "https://example.com/devops-guide",
            "source_type": "url",
            "text_content": "Kubernetes readiness probes prevent traffic routing to unready pods."
        }
    )
    assert res_source.status_code in (200, 201)

    # 4. Draft Creation
    res_draft = client.post(
        "/api/v1/writing/drafts",
        json={
            "project_id": project_id,
            "title": "Modern Cloud Reliability",
            "content": "Automated deployments must include health verification probes."
        }
    )
    assert res_draft.status_code in (200, 201)
    draft_id = res_draft.json()["id"]

    # 5. Observability telemetry
    res_metrics = client.get("/api/v1/observability/metrics")
    assert res_metrics.status_code == 200
    metrics_data = res_metrics.json()
    assert "total_operations" in metrics_data or "total_requests" in metrics_data or "system_status" in metrics_data


# ==============================================================================
# TEST 15: Performance Benchmarks & Latency SLA
# ==============================================================================
def test_performance_sla_and_token_cost_calculation():
    """Verify core health and read endpoints satisfy production SLA (< 100ms response time)."""
    client = TestClient(app)

    # Measure latency for 10 sequential health checks
    latencies = []
    for _ in range(10):
        t0 = time.perf_counter()
        resp = client.get("/health/live")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 100.0, f"Average health probe latency was {avg_latency}ms, exceeding 100ms SLA"

    # Token cost calculation benchmark
    cost = calculate_estimated_cost(provider="openai", model="gpt-4o-mini", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0
    assert cost == 0.000450


# ==============================================================================
# TEST 16: Standardized Error Structures
# ==============================================================================
def test_standardized_error_response_structures():
    """Verify standardized JSON error responses with status, detail, and request tracing."""
    client = TestClient(app)

    # 1. 404 Not Found
    res_404 = client.get("/api/v1/writing/drafts/non-existent-uuid-9999999999")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert "detail" in data_404

    # 2. 422 Unprocessable Entity
    res_422 = client.post("/api/v1/research/projects", json={"invalid_field": 123})
    assert res_422.status_code == 422
    data_422 = res_422.json()
    assert "detail" in data_422
