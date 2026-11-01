# Operations & Observability Guide — AI Editorial Workspace

> **Service Reliability, Telemetry, and Incident Response Playbook**  
> Forward Deployed Engineer Intern Assignment — *This Week in AI*

---

## 1. Operational Overview & SRE Principles

The **AI Editorial Workspace** is designed following pragmatic Site Reliability Engineering (SRE) principles tailored for an agile, production-ready editorial platform:

1. **Zero Mandatory External Infrastructure Overhead:**  
   Monitoring, structured tracing, and metrics aggregation run in-process without requiring heavy external dependencies (such as Redis clusters, Celery workers, or Prometheus daemons) for baseline operation.
2. **Deterministic Graceful Degradation:**  
   External LLM provider outages or rate limits never trigger application downtime or catastrophic 500 errors. All six writing heuristic engines and research pipelines fail open to deterministic fallback generators.
3. **End-to-End Distributed Tracing (`X-Request-ID`):**  
   Every inbound HTTP request receives or inherits a unique UUID. This correlation identifier is propagated through log streams, response headers, structured error payloads, and frontend toast notifications.
4. **Zero-PII Logging Sanitization:**  
   Draft article content, scraped proprietary source material, and API keys are strictly excluded from server log outputs. Only path, method, status code, latency, and sanitized error categories are persisted.

---

## 2. Health & Readiness Architecture

The platform separates **Liveness** (process health) from **Readiness** (dependency availability) to integrate seamlessly with container orchestrators (Docker, Kubernetes, Render, AWS ECS):

| Endpoint | Method | Expected Status | Purpose | Dependency Checks |
|---|---|---|---|---|
| `/health/live` | `GET` | `200 OK` | Liveness Probe | Verifies the FastAPI Uvicorn ASGI process is alive and accepting event loop tasks. |
| `/health/ready` | `GET` | `200 OK` / `503 Service Unavailable` | Readiness Probe | Executes `SELECT 1` against the primary database (`editorial.db` SQLite or PostgreSQL). Returns 503 if the database is locked or unreachable. |
| `/health` | `GET` | `200 OK` (or `degraded`) | Operational Telemetry | Returns comprehensive system state, database connectivity, AI engine operational mode, cumulative token metrics, and recent activity buffer. |

*Note: All three health endpoints are available both at root (`/health`, `/health/live`, `/health/ready`) and under the API version prefix (`/api/v1/health`, `/api/v1/health/live`, `/api/v1/health/ready`).*

### Decoupled AI Dependency Principle
`/health/ready` **does not fail** if the external OpenAI API key is missing or invalid. The platform's built-in offline heuristic analysis ensures editorial writing suggestions and brief synthesis operate 100% deterministically offline. Only hard database unavailability marks the service unready.

---

## 3. Structured Logging & Correlation IDs

### Log Format Specification
The FastAPI ASGI layer uses Python standard logging formatted with timestamp, logger name, severity, and context:

```text
2026-11-01 20:25:01,120 - editorial_workspace - INFO - [4f7d2b12-9c88-4a18-9218-ec3795b5a8e1] START POST /api/v1/writing/analyze
2026-11-01 20:25:01,135 - editorial_workspace - INFO - [4f7d2b12-9c88-4a18-9218-ec3795b5a8e1] COMPLETED POST /api/v1/writing/analyze - Status: 200 - Duration: 15.22ms
```

### Log Levels
- **`INFO`**: Request lifecycle events (START / COMPLETED with HTTP method, path, status, and duration in milliseconds).
- **`WARNING`**: Client validation failures (HTTP 422 `RequestValidationError`), client parameter issues (HTTP 400), resource not found (HTTP 404).
- **`ERROR`**: Server-side unhandled exceptions (HTTP 500) with sanitized stack traces and database transaction aborts.

### Error Response Schema
Whenever an error occurs, the server responds with a standardized structured payload containing the correlation identifier:

```json
{
  "detail": "Field 'title' is required.",
  "request_id": "4f7d2b12-9c88-4a18-9218-ec3795b5a8e1",
  "error_category": "VALIDATION_ERROR"
}
```

---

## 4. AI Provider Monitoring & Token Accounting

The backend incorporates an in-memory `MonitoringService` (`backend/app/services/monitoring_service.py`) tracking runtime AI telemetry:

- **Telemetry Metrics Captured:**
  - `duration_ms`: Real execution latency of external LLM API calls or fallback synthesis.
  - `prompt_tokens`: Count of input prompt tokens consumed (from provider response usage).
  - `completion_tokens`: Count of output generation tokens produced.
  - `total_tokens`: Cumulative aggregate token count.
  - `status`: Execution outcome (`success`, `fallback`, `failed`).
  - `error_category`: Sanitized provider error categorization (`TIMEOUT`, `RATE_LIMIT_429`, `AUTH_ERROR_401`, `INVALID_REQUEST_400`, `SERVER_ERROR_5XX`).
- **Ring Buffer:**  
  A thread-safe circular buffer (`collections.deque(maxlen=50)`) stores the last 50 operational events for instant inspection in the UI without requiring database overhead.

---

## 5. Frontend Error Handling & UI Observability

### Correlation ID Surface
In `frontend/src/services/api.ts`, the Axios response interceptor intercepts all rejected promises:
1. Inspects `error.response.headers['x-request-id']` and `error.response.data.request_id`.
2. Appends `(Correlation ID: <uuid>)` to the generated error message string.
3. Exposes `requestId`, `statusCode`, and `errorCategory` on the typed `ApiError` object.
4. Alerts or notifications displayed to the user allow instant cross-referencing against backend server logs during support incidents.

### Operational Dashboard in Settings
Under the **Settings** view (`/settings`), an **Observability & SRE** tab displays real-time telemetry:
- Live Liveness and Readiness status badges.
- Process uptime in seconds.
- AI engine mode (`Live OpenAI API` vs. `Deterministic Fallback Engine`).
- Live token accounting metrics (Prompt, Completion, Total).
- Real-time tabular feed of the last 10 operations with status badges and latencies.

---

## 6. SRE Incident Response Runbooks

### Runbook A: Database Service Unavailable (`503 Service Unavailable`)
- **Symptom:** `/health/ready` returns `503`, frontend reports backend unready.
- **Root Causes:**
  - SQLite file permissions locked or database directory read-only.
  - PostgreSQL container stopped or network partition.
- **Remediation Steps:**
  1. Check file permissions on `editorial.db` (`chmod 664 editorial.db` or verify write permissions).
  2. For PostgreSQL, check connection pool exhaustion and test via `psql -h <host> -U <user> -d <db> -c "SELECT 1"`.
  3. Inspect backend logs for `[request_id] FAILED ... - Error: OperationalError`.

### Runbook B: OpenAI API Outage / Rate Limit (`429 Rate Limit`)
- **Symptom:** AI operations indicate fallback mode; recent events show `RATE_LIMIT_429`.
- **System Behavior:** Automatic graceful degradation. The application continues functioning without dropping user drafts or failing editorial requests.
- **Remediation Steps:**
  1. Verify OpenAI account quota and billing tier.
  2. If running under elevated load, configure `OPENAI_API_KEY` with a dedicated tier account or maintain default deterministic fallback mode.

### Runbook C: SSRF Exploit or Blocked IP Alert (`SSRF_VIOLATION`)
- **Symptom:** User scraping request rejected with `400 Bad Request: URL resolves to private or loopback IP range`.
- **System Behavior:** `SSRFProtectionService` pre-resolves DNS records and blocks all loopback (`127.0.0.1`), LAN (`10.0.0.0/8`, `192.168.0.0/16`), AWS metadata (`169.254.169.254`), and IPv6 private addresses before any HTTP socket is created.
- **Remediation Steps:**
  1. Verify whether the user attempted to scrape an internal service URL.
  2. Confirm that public domains resolve to globally routable IPv4/IPv6 addresses.

