# AI Editorial Workspace — Production SRE Runbook & Operational Procedures

This runbook provides Site Reliability Engineers (SRE) and operations teams with troubleshooting procedures, monitoring guidelines, and incident recovery workflows.

---

## 1. System Health Probes & Monitoring Endpoints

The workspace exposes standard Kubernetes and container health probes:

| Endpoint | Probe Type | Purpose | Healthy Response | Failure Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET /health/live` | **Liveness Probe** | Checks if FastAPI web server process is responsive | HTTP 200 `{"status": "alive"}` | Process freeze / crash / connection timeout |
| `GET /health/startup` | **Startup Probe** | Verifies initial DB schema loading and configuration initialization | HTTP 200 `{"status": "started"}` | HTTP 503 `{"status": "starting"}` |
| `GET /health/ready` | **Readiness Probe** | Checks database and Redis connectivity before routing traffic | HTTP 200 `{"status": "ready"}` | HTTP 503 `{"status": "not_ready"}` |
| `GET /health` | **Diagnostics** | Full operational diagnostic dump with telemetry and AI engine state | HTTP 200 `{"status": "healthy"}` | HTTP 200 `{"status": "degraded"}` |
| `GET /api/v1/observability/metrics` | **Telemetry** | Metrics on AI operations, success rates, latency, and costs | HTTP 200 JSON object | HTTP 401 / 403 |

---

## 2. Common Operational Incidents & Triage

### Scenario A: Readiness Probe Fails (HTTP 503 on `/health/ready`)
- **Symptoms:** Kubernetes pods failing readiness checks, ingress stops routing traffic.
- **Root Causes:** PostgreSQL connection pool exhaustion, database host unreachable, network partition.
- **Triage Steps:**
  1. Inspect PostgreSQL container logs:
     ```bash
     docker compose logs db --tail=100
     ```
  2. Verify database connectivity directly from backend container:
     ```bash
     docker compose exec backend python -c "from backend.app.core.database import check_db_health; print(check_db_health())"
     ```
  3. Check active connection count in PostgreSQL:
     ```sql
     SELECT count(*) FROM pg_stat_activity;
     ```
  4. If connections are exhausted, restart backend containers to release pooled connections or scale `max_connections` in `postgresql.conf`.

### Scenario B: High Rate of HTTP 429 (Rate Limit Exceeded)
- **Symptoms:** Users receive `429 Too Many Requests` with `error_category: "RATE_LIMIT_EXCEEDED"`.
- **Root Causes:** Client aggressive polling or legitimate traffic spike exceeding 180 req/min per IP.
- **Triage Steps:**
  1. Inspect the `X-Request-ID` and client IP reported in access logs.
  2. If the traffic is legitimate, increase `requests_per_minute` in `backend/app/main.py` or configure trusted upstream proxies in Nginx (`set_real_ip_from`).

### Scenario C: AI Provider Outage / Degraded Latency
- **Symptoms:** AI generation requests take $> 30$ seconds or fail with upstream timeouts.
- **Behavior:** The workspace automatically routes requests through the **Deterministic Fallback Engine** (`FallbackAdapter`), ensuring uninterrupted drafting and evidence mapping.
- **Triage Steps:**
  1. Check AI provider status in `/health`:
     ```bash
     curl -s http://localhost:8000/health | jq .ai_engine
     ```
  2. Switch active default provider to Groq or Anthropic via environment variable (`DEFAULT_AI_PROVIDER=groq`) or Settings UI.

---

## 3. Database Migration Deployment Procedure

Alembic migrations are executed automatically on container startup by `scripts/entrypoint.sh`.

### Manual Migration Verification
```bash
# Check current database revision
alembic -c backend/alembic.ini current

# Check migration history
alembic -c backend/alembic.ini history

# Upgrade to head manually
alembic -c backend/alembic.ini upgrade head
```

---

## 4. Log Inspection & Querying

All application logs are formatted in structured single-line format:
```
[<request_id>] <EVENT> <METHOD> <PATH> - Status: <STATUS> - Duration: <DURATION>ms
```

### Trace a Specific User Request by Request ID
```bash
docker compose logs backend | grep "f8586226-0b2d-401a-a087-8ed5414c2e22"
```

### Inspect Errors (5xx Status Codes)
```bash
docker compose logs backend | grep -E "Status: 5[0-9]{2}"
```

