# AI Editorial Workspace — Technical Architecture Document

**Author:** Senior Forward Deployed Engineer & System Architect  
**Project:** AI Editorial Workspace  
**Status:** Validated Production System  
**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  

---

## 1. System Overview & Architecture Diagram

The AI Editorial Workspace is architected as a high-reliability, decoupled full-stack application built for evidence-grounded research, editorial synthesis, and automated quality auditing.

```
                              [ React 18 + TypeScript Client ]
                                             |
                         (Axios + Interceptors + Request-ID)
                                             |
                        [ Nginx / Reverse Proxy / Vite Dev ]
                                             |
                                 +-----------+-----------+
                                 |                       |
                     [ FastAPI ASGI Application ]   [ Static Assets ]
                                 |
         +-----------------------+-----------------------+
         |                       |                       |
   [ Auth & RBAC ]        [ API v1 Routers ]     [ Security Middleware ]
   (JWT / Argon2)         (/research, /writing,   (SSRF Guard, XSS Filter,
                          /observability, etc.)    Request Tracing)
                                 |
         +-----------------------+-----------------------+
         |                       |                       |
   [ AI Router Engine ]   [ Relational ORM ]    [ Extraction Engine ]
   - Groq LPU Adapter     (SQLAlchemy 2.0 /     (Trafilatura + BS4 +
   - OpenAI GPT-4o         SQLite / Postgres)    SSRF Validation)
   - Anthropic Claude 3.5        |
   - Gemini 1.5 Pro       [ Alembic Migrations ]
   - Deterministic Fallback      |
         |                (Revision 7a2c3d4e5f6a)
   [ 5-Tier Verification ]
   [ Token Cost Accounting ]
```

---

## 2. Frontend Architecture (React 18 + TypeScript)

### Component Hierarchy & Layouts
The client application is built with React 18, TypeScript, and Tailwind CSS, bundled with Vite for optimized chunk splitting.
- **`App.tsx`:** Root routing definition using React Router v7. Configures public routes (`/login`, `/register`), protected authenticated routes, and the `DashboardLayout`.
- **`DashboardLayout.tsx`:** Core wrapper integrating `Header`, `Sidebar`, and contextual breadcrumbs.
- **State Management & Contexts:**
  - `AuthContext.tsx`: Tracks active JWT, user profile, active organization, and granular role permissions (`canManageOrg`, `canInvite`, `canEditDrafts`, etc.).
  - `ToastContext.tsx`: Manages dismissible toast alerts for asynchronous operational feedback.
- **Service Layer (`frontend/src/services/`):**
  - `api.ts`: Central Axios instance injecting `Authorization: Bearer <token>` and `X-Organization-Id: <id>`, with automated request deduplication for idempotent GETs.
  - `researchService.ts` / `researchApi.ts`: Ingestion, extraction, and research brief lifecycle.
  - `writingService.ts`: Draft CRUD, Hemingway analysis, selection-targeted rewriting, and version history.
  - `observabilityService.ts`: Real-time operational metrics, token consumption, and benchmark execution.

---

## 3. Backend Architecture (FastAPI + ASGI)

### Route Architecture & Versioning
All business APIs are versioned under `/api/v1` to ensure backward compatibility:
- `/api/v1/health`: Liveness (`/live`), readiness (`/ready`), and operational telemetry.
- `/api/v1/auth`: Registration, login, profile inspection, and password recovery.
- `/api/v1/organizations`: Multi-tenant organization CRUD, membership management, and invitation flows.
- `/api/v1/research`: Research project management, source ingestion, claim extraction, and 10-section brief synthesis.
- `/api/v1/sources`: Source content extraction, SSRF validation, and manual override editing.
- `/api/v1/writing`: Editorial draft generation, Hemingway 6-check auditor, selection rewriting, version snapshots, and exports.
- `/api/v1/observability`: AI metrics, token usage, cost summaries ($USD), and benchmark evaluation runners.

---

## 4. Database Architecture & Alembic Migrations

### Relational Schema (SQLAlchemy 2.0)
The schema enforces relational data integrity across 10 tables:
1. `users`: Stores user identity, hashed passwords (Argon2), and account status.
2. `organizations`: Tenant root entity supporting multi-tenant isolation.
3. `organization_memberships`: Join table linking users and organizations with strict enum roles (`OWNER`, `ADMIN`, `EDITOR`, `REVIEWER`, `VIEWER`).
4. `organization_invitations`: Secure tokenized invitations with expiration timestamps.
5. `projects`: Root entity for research investigations, scoped by `organization_id`.
6. `sources`: Ingested research documents, storing raw text, cleaned markdown, extraction status, and domain metadata.
7. `claims`: Epistemically sorted assertions (Facts, Analysis, Speculation) linked to sources.
8. `research_briefs`: 10-section structured synthesis documents tied to projects.
9. `editorial_drafts`: Full editorial drafts supporting title, content, target tone, word count, and approval status.
10. `draft_versions`: Immutable historical snapshots enabling safe rollbacks and diff computations.
11. `provider_usage_records`: High-granularity telemetry recording timestamp, operation, provider, prompt tokens, completion tokens, prompt version, and estimated cost in `$USD`.

### Migration Progression
Managed via Alembic in `backend/alembic/versions/`:
- `initial_migration`: Base schemas for users, projects, sources, claims.
- `5e9a2f1b4c3d`: Multi-tenancy, organization memberships, and draft versioning.
- `6f1b2a3c4d5e`: Writing Assistant intelligence, selection rewrites, and quality metrics.
- `7a2c3d4e5f6a`: Phase 8 AI reliability, prompt versions, and token cost tracking.

---

## 5. Multi-Provider AI Engine & Fallback Architecture

### Provider Adapters (`backend/app/services/ai/`)
The system abstracts LLM operations through `AIRouter`, which standardizes prompt injection, model parameters, and response formats:
- **`GroqAdapter`:** Ultra-fast inference via Groq LPU (Llama 3.3 70B Versatile).
- **`OpenAIAdapter`:** High-capability reasoning via GPT-4o.
- **`AnthropicAdapter`:** Long-context analytical synthesis via Claude 3.5 Sonnet.
- **`GeminiAdapter`:** Deep multimodal context window via Gemini 1.5 Pro.
- **`FallbackAdapter`:** 100% deterministic local heuristic engine providing instant, offline text generation with zero external API dependencies.

### Exponential Backoff & Circuit Breaking
Transient network failures and HTTP 429 rate limits trigger bounded exponential backoff with jitter (up to 3 retries, `0.5s`, `1.0s`, `1.5s`). Persistent provider failures fail over automatically to `FallbackAdapter` without emitting 500 errors to clients.

---

## 6. Research & Extraction Pipeline

### SSRF Defense Layer (`backend/app/services/extraction_service.py`)
To prevent Server-Side Request Forgery attacks, all user-supplied URLs undergo strict security screening before connection:
- Rejects non-HTTP/HTTPS protocols (`file://`, `gopher://`, `ftp://`).
- Resolves DNS to IP and blocks private IPv4/IPv6 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `::1`).
- Blocks cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- Enforces payload size limits ($\le 2$ MB) and max redirect depth ($\le 3$).

### Content Extraction
Leverages `trafilatura` for primary content extraction (removing navigation bars, cookie banners, and footers), automatically falling back to `BeautifulSoup4` with `lxml_html_clean` if Trafilatura fails.

---

## 7. Evidence Grounding & Claim Verification Engine

### 5-Tier Verification Hierarchy
Implemented in `ClaimVerificationService`:
- `SUPPORTED`: $\ge 75\%$ semantic/verbatim alignment with ingested source text.
- `PARTIALLY_SUPPORTED`: $50\% - 74\%$ overlap; core concept present, minor nuance discrepancy.
- `UNSUPPORTED`: Claim contains factual assertions or numerical figures absent from sources.
- `CONTRADICTED`: Claim asserts the direct opposite of source facts (detected via semantic polarity matching).
- `NOT_VERIFIABLE`: Subjective opinion, future predictions, or speculative commentary.

### Semantic Polarity Contradiction Detection
Audits antonym pairs (`increased` vs `decreased`/`dropped`, `succeeded` vs `failed`) associated with shared subject nouns to catch inverted factual statements without requiring external LLM evaluations.

### Numerical Hallucination Auditing
All numerical figures, percentages, and dollar amounts are extracted via regex and verified against reference documents. Unmatched figures automatically escalate status to `UNSUPPORTED`.

---

## 8. Security, Multi-Tenancy & Governance

- **Authentication:** Stateless JWT bearer tokens with Argon2 password hashing.
- **Multi-Tenant Data Isolation:** Tenant boundaries are strictly enforced. All database queries must include `organization_id` filters, preventing cross-organization visibility.
- **Role-Based Access Control (RBAC):**
  - `OWNER`: Full administrative control, organization deletion, billing, role assignments.
  - `ADMIN`: Member invitation, project creation, role management (cannot alter Owners).
  - `EDITOR`: Full research, drafting, and writing access.
  - `REVIEWER`: Read-only access with commenting and review approval permissions.
  - `VIEWER`: Read-only access to published briefs and drafts.
- **XSS & Prompt Injection Defenses:**
  - Client and export endpoints sanitize HTML with entity escaping.
  - Prompts encapsulate untrusted data in `<source_content>` delimiters with adversarial override instructions.

---

## 9. Observability & Telemetry

- **Health Probes:**
  - `GET /api/v1/health/live`: Fast process health check (200 OK).
  - `GET /api/v1/health/ready`: Deep dependency check (database connectivity, migration status).
- **Request Tracing:** Unique `X-Request-ID` UUID generated per request and returned in response headers for distributed trace correlation.
- **Cost Accounting:** Real-time token tracking ($USD) based on live provider pricing models, queryable by tenant.

