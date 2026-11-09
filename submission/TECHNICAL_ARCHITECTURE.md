# Technical Architecture & Systems Engineering

**Project:** AI Editorial Workspace  
**Document Type:** Technical Architecture Specification  
**Author:** Forward Deployed Engineer  
**Status:** **VERIFIED PRODUCTION ARCHITECTURE**

---

## 1. Technology Stack & Component Rationale

| Tier | Technology | Justification |
| :--- | :--- | :--- |
| **Frontend SPA** | React 18, TypeScript, Vite | Strict type safety, instantaneous HMR during development, optimized tree-shaken production bundles (< 400KB vendor chunks). |
| **Styling & Icons** | Tailwind CSS, Lucide React, Recharts | Utility-first responsive design, accessible iconography, dynamic metric data visualization. |
| **Backend API** | FastAPI, Python 3.10, Uvicorn | High-throughput asynchronous I/O, Pydantic v2 runtime payload validation, automated OpenAPI/Swagger documentation. |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic | Type-annotated query construction, transactional safety, deterministic schema evolution via SQLite batch mode and Postgres support. |
| **Security Layer** | JWT (HMAC-SHA256), PBKDF2-SHA256, Socket DNS | Stateless session tokens, secure password hashing, proactive SSRF network defense. |
| **AI Layer** | Groq (LPU), OpenAI API, Local Heuristics | Sub-second inference for primary generation, backed by zero-dependency deterministic rule engines for offline resilience. |

---

## 2. Directory Structure & Code Organization

```
AI-Editorial-Workspace/
├── backend/
│   ├── alembic/                 # Alembic migration environment & revision scripts
│   │   └── versions/            # 10 migration revisions to head 7a2c3d4e5f6a
│   ├── app/
│   │   ├── api/routes/          # REST route handlers (auth, research, writing, editorial, health)
│   │   ├── core/                # Global config, database session, security utilities
│   │   ├── evaluation/          # AI benchmarking harness & 34 evaluation datasets
│   │   ├── middleware/          # Request tracing (X-Request-ID), CORS, exception handling
│   │   ├── models/              # SQLAlchemy 2.0 ORM entity definitions
│   │   ├── schemas/             # Pydantic request/response validation schemas
│   │   └── services/            # Business logic (ai_service, writing_auditor, url_validator)
│   ├── scripts/                 # Standalone utilities (seed_demo_environment.py)
│   └── tests/                   # 212 automated pytest unit, integration, & E2E tests
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI elements (Navbar, Sidebar, Modals, DiffViewer)
│   │   ├── context/             # AuthContext, HealthContext, OrganizationContext
│   │   ├── pages/               # Top-level route pages (Dashboard, Research, Writing, Editorial)
│   │   ├── services/            # Axios API clients, health monitoring, error parsing
│   │   └── types/               # Shared TypeScript interfaces & types
│   ├── index.html
│   ├── vite.config.ts           # Dev server proxy configuration (/api and /health)
│   └── nginx.conf               # Production container reverse proxy configuration
├── submission/                  # Official FDE intern assessment package
├── docker-compose.yml           # Local multi-container development environment
└── docker-compose.prod.yml      # Hardened production container deployment
```

---

## 3. Database Architecture & Alembic Schema Strategy

### Normalized Entities & Relationships
1. **Organizations (`organizations`)**: Root tenant entity with unique slugs.
2. **Users (`users`)**: Authenticated identities storing PBKDF2 password hashes and system roles.
3. **Memberships (`organization_memberships`)**: Junction table binding users to organizations with role attributes (`owner`, `editor`, `viewer`).
4. **Research Projects (`research_projects`)**: Top-level containers for research investigations.
5. **Source Documents (`source_documents`)**: Primary ingested research sources with URL provenance and raw content.
6. **Research Briefs (`research_briefs`)**: Synthesized evidence summaries, facts vs speculation matrices, and knowledge graph JSON payloads.
7. **Writing Drafts (`writing_drafts`)**: Composed editorial drafts tracking quality scores, Flesch scores, and status flags.
8. **Editorial Versions (`editorial_versions`)**: Immutable historical revisions recording character-level diffs, revision authors, and timestamps.
9. **Editorial Outputs (`editorial_outputs`)**: Published newsletter editions ready for syndication.
10. **Audit Logs (`audit_logs`)**: Structured operational ledger capturing security and administrative events.

### SQLite Batch Mode Migration Strategy
To ensure Alembic migrations succeed identically on local SQLite and production PostgreSQL, `backend/alembic/env.py` enforces batch alter mode:
```python
with context.begin_transaction():
    context.run_migrations(render_as_batch=True)
```
This circumvents SQLite's native lack of `ALTER COLUMN` support by automating shadow table recreation and index restoration.

---

## 4. API Architecture & Standardized Responses

All REST endpoints under `/api/v1` adhere to predictable JSON structures.

### Standardized Error Envelope
```json
{
  "error": {
    "code": "SSRF_VIOLATION",
    "message": "The requested URL resolves to a prohibited internal network address.",
    "details": {
      "host": "169.254.169.254",
      "resolved_ip": "169.254.169.254"
    }
  },
  "request_id": "8fa21b7e-90c4-4b51-b845-d86b72a912e3"
}
```

### Standardized Success Envelope (List Responses)
```json
{
  "items": [ ... ],
  "total": 31,
  "page": 1,
  "page_size": 20
}
```

---

## 5. Security & SSRF Protection Architecture

The source ingestion subsystem defends against Server-Side Request Forgery via a multi-phase verification pipeline in `backend/app/services/url_validator.py`:

```
Input URL
   │
   ▼
[ Parse Scheme ] ──── Reject if not http/https
   │
   ▼
[ socket.getaddrinfo ] ──── Resolves all IPv4 & IPv6 records
   │
   ▼
[ CIDR Evaluation ] ──── Matches against 127/8, 10/8, 172.16/12, 192.168/16, 169.254/16, ::1
   │
   ├── Matches Private CIDR ────► Raise SSRFProtectionException (HTTP 400)
   └── Valid Public IP ─────────► Proceed with Async HTTP Fetch (timeout=30s, max_bytes=10MB)
```

---

## 6. Observability & Telemetry Infrastructure

- **Correlated Request Tracing:** The `RequestTracingMiddleware` inspects incoming `X-Request-ID` headers or mints a UUID4, binding it to the request lifecycle and propagating it through response headers and structured application logs.
- **Health Probes:**
  - `GET /health/live`: Fast process liveness verification.
  - `GET /health/ready`: Deep dependency readiness verifying database connectivity and query latency.
  - `GET /health`: Comprehensive operational telemetry exposing uptime, active AI engine mode, token consumption, and recent system events.

