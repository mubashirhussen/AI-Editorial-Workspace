# AI Editorial Workspace — Monitoring & Observability Guide

The AI Editorial Workspace provides built-in observability, structured logging, request correlation, health probes, and performance metrics.

---

## 1. Observability Architecture

```
HTTP Request
     │
     ▼
[ ObservabilityMiddleware ]
     │ ── Assigns unique X-Request-ID (UUIDv4) if not present
     │ ── Starts high-precision timer (time.perf_counter())
     ▼
[ Route Handler / Service Layer ]
     │ ── Structured log with [request_id] prefix
     │ ── AI Router logs provider calls, token usage & latency
     ▼
[ Response / Completion ]
     │ ── Injects X-Request-ID into HTTP response headers
     │ ── Records status code & latency in Monitoring Ring Buffer
     │ ── Records error category on 4xx/5xx responses
     ▼
Client receives response with X-Request-ID
```

---

## 2. Health & Readiness Probes

The backend exposes three standardized health endpoints:

### 2.1. Liveness Probe (`GET /health/live`)
- **Purpose:** Kubernetes / Docker container liveness. Verifies that the FastAPI process is alive and accepting connections.
- **Response:**
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-11-02T11:00:00Z"
  }
  ```

### 2.2. Readiness Probe (`GET /health/ready`)
- **Purpose:** Verifies that external dependencies (PostgreSQL / SQLite database) are connected and accepting queries (`SELECT 1`).
- **Response (Success - HTTP 200):**
  ```json
  {
    "status": "ready",
    "database": "connected",
    "timestamp": "2026-11-02T11:00:00Z"
  }
  ```
- **Response (Failure - HTTP 503):** If database connection drops, immediately returns 503 Service Unavailable to remove container from load balancer pool.

### 2.3. Deep System Health (`GET /health` or `GET /api/v1/health`)
- **Purpose:** Real-time diagnostics for SREs and frontend status badges.
- **Payload Contents:**
  - `application`: `"AI Editorial Workspace"`
  - `status`: `"healthy"` or `"degraded"`
  - `database_connected`: `true`
  - `database_latency_ms`: Float query latency
  - `uptime_seconds`: Process uptime
  - `active_ai_providers`: List of configured and active AI providers
  - `recent_errors_count`: Number of recorded errors in the sliding window

---

## 3. Structured Logging Standard

All log entries adhere to structured formatting:
```text
YYYY-MM-DD HH:MM:SS,mmm - logger_name - LEVEL - [request_id] MESSAGE
```

### Examples:
```text
2026-11-02 11:05:01,120 - editorial_workspace - INFO - [c1f7a840-7e61] START POST /api/v1/research/projects
2026-11-02 11:05:01,154 - editorial_workspace - INFO - [c1f7a840-7e61] COMPLETED POST /api/v1/research/projects - Status: 201 - Duration: 34.2ms
2026-11-02 11:05:02,810 - editorial_workspace - WARNING - [d9a102bf-90ab] Validation error on /api/v1/writing/drafts: [{'loc': ('body', 'original_content'), 'msg': 'Field required'}]
```

---

## 4. Error Categories & Incident Tracking

Errors returned to clients include an `error_category` to enable automated aggregation:
- `VALIDATION_ERROR`: Schema or input format mismatch (HTTP 422).
- `AUTHENTICATION_ERROR`: Missing, invalid, or expired credentials (HTTP 401).
- `AUTHORIZATION_ERROR`: Insufficient privileges for workspace resource (HTTP 403).
- `NOT_FOUND`: Referenced project, source, or draft does not exist (HTTP 404).
- `RATE_LIMIT_EXCEEDED`: Client exceeded rate quota (HTTP 429).
- `INTERNAL_SERVER_ERROR`: Unhandled exception trapped by global exception handler (HTTP 500).

---

## 5. Recommended Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
| :--- | :--- | :--- | :--- |
| **P95 Latency** | > 1,500 ms | > 3,000 ms | Inspect AI provider timeout & DB connection pool |
| **5xx Error Rate** | > 1.0% | > 5.0% | Check application logs for unhandled exceptions |
| **DB Latency** | > 50 ms | > 200 ms | Check connection pool saturation / vacuum database |
| **AI Provider Fallbacks** | > 5 fallbacks/hr | > 20 fallbacks/hr | Verify primary provider quota & API key validity |
