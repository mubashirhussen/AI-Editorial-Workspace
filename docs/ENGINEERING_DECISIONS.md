# AI Editorial Workspace — Architectural & Engineering Decisions

**Author:** Senior Forward Deployed Engineer & Technical Architect  
**Project:** AI Editorial Workspace  
**Status:** Approved Architectural Record  

---

## 1. Core Framework & Language Decisions

### 1.1 Python & FastAPI vs. Node.js / Go / Django
- **Decision:** Python 3.10+ with FastAPI and Uvicorn.
- **Rationale:** 
  - Natural ecosystem for AI engineering, token manipulation, and NLP libraries (Trafilatura, BeautifulSoup4, regex parsing).
  - FastAPI provides native ASGI asynchronous request handling, automatic OpenAPI schema generation, and strict runtime data validation via Pydantic v2.
  - Compared to Django, FastAPI avoids monolithic bloat and provides superior performance for I/O-bound AI provider calls.
  - Compared to Node.js, Python offers substantially richer text processing and semantic extraction capabilities.

### 1.2 React 18 + Vite vs. Next.js / Server-Side Rendering (SSR)
- **Decision:** React 18 SPA bundled with Vite and Tailwind CSS.
- **Rationale:**
  - The AI Editorial Workspace is a high-interactivity editorial desktop application with rich client-side text editing, live Hemingway checking, inline diffing, and dynamic verification badges.
  - Next.js SSR introduces operational complexity (Node runtime servers, hydration mismatches, complex edge caching) without offering tangible SEO benefits for an authenticated internal workspace.
  - Vite delivers sub-second HMR and deterministic production builds.

---

## 2. Database Architecture & Persistence Decisions

### 2.1 Relational Schema (SQLAlchemy 2.0) vs. NoSQL / Document Store
- **Decision:** Strict relational model with foreign-key cascades and composite indexing.
- **Rationale:**
  - Editorial projects, sources, claims, drafts, and versions have strict hierarchical relationships. An orphaned claim or draft without a parent project destroys evidence provenance.
  - Relational foreign keys (`ON DELETE CASCADE`) guarantee referential integrity: deleting a project cleanly cleans up associated sources, briefs, and draft versions without orphaned records.
  - Document databases (MongoDB, DynamoDB) complicate multi-tenant data isolation and require manual application-level cascade logic.

### 2.2 SQLite (Dev) with PostgreSQL Compatibility vs. Cloud-Only DB
- **Decision:** SQLite with WAL mode and strict `PRAGMA foreign_keys = ON` for local development; PostgreSQL-compatible relational types (`VARCHAR(36)` UUIDs, ISO UTC timestamps) for production.
- **Rationale:**
  - Zero-friction onboarding: any engineer or evaluator can clone the repository and run the entire application locally without configuring Docker containers or remote databases.
  - Preserves standard SQL semantics so that deploying to PostgreSQL requires only changing `DATABASE_URL`.

### 2.3 Managed Schema Evolution with Alembic Migrations
- **Decision:** Strict forward-only Alembic migrations (`base` $\rightarrow$ `5e9a2f1b4c3d` $\rightarrow$ `6f1b2a3c4d5e` $\rightarrow$ `7a2c3d4e5f6a`).
- **Rationale:**
  - Direct `Base.metadata.create_all()` works only on initial startup and cannot perform non-destructive column additions (such as adding `prompt_version` and `estimated_cost_usd` in Phase 8).
  - Versioned migration files guarantee reproducible deployments across CI/CD, staging, and production environments.

---

## 3. AI Architecture, Routing & Fallback Strategies

### 3.1 Unified Provider Adapter Pattern vs. Vendor-Locked SDKs
- **Decision:** Custom `AIRouter` with standardized adapters (`GroqAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, `GeminiAdapter`, `FallbackAdapter`).
- **Rationale:**
  - Prevents vendor lock-in. If OpenAI experiences an outage or increases pricing, an editor can switch to Groq or Anthropic without code changes.
  - Standardizes error categorization, retry backoff, latency measurement, and token cost calculations across all providers.

### 3.2 100% Deterministic Offline Fallback Guarantee
- **Decision:** Implement a complete, zero-dependency `FallbackAdapter` that uses heuristic NLP algorithms to generate structured briefs, editorial drafts, and claim audits.
- **Rationale:**
  - Evaluators and continuous integration runners should not fail simply because an external API key is missing or an upstream AI service encounters an outage.
  - Ensures predictable, deterministic test execution with 100% pass rates.

### 3.3 Process-Level Claim Verification (5-Tier) vs. Binary Boolean Check
- **Decision:** 5-tier classification hierarchy (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`).
- **Rationale:**
  - Real-world technical claims are rarely black-and-white. An assertion may be conceptually accurate but lack precise context (`PARTIALLY_SUPPORTED`), or it may be editorial commentary that cannot be verified against physical documents (`NOT_VERIFIABLE`).
  - Binary True/False checks force models to arbitrarily reject valid journalistic analysis.

---

## 4. Security & Multi-Tenancy Decisions

### 4.1 SSRF Defense: Network-Layer DNS Resolution vs. Simple String Parsing
- **Decision:** Strict DNS resolution and IP blacklist verification before issuing HTTP requests.
- **Rationale:**
  - Simple regex checks against `localhost` can be trivially bypassed using decimal IP encodings (`http://2130706433`), hexadecimal IPs (`http://0x7f000001`), or DNS rebinding domains.
  - Resolving the hostname via `socket.getaddrinfo()` and checking the resulting socket against `ipaddress.ip_network` guarantees that private IPs (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`) and cloud metadata endpoints (`169.254.169.254`) are strictly blocked regardless of URL obfuscation.

### 4.2 Multi-Tenant Data Isolation: Scoped Queries vs. Schema-Per-Tenant
- **Decision:** Row-level multi-tenancy with mandatory `organization_id` scoping in queries and middleware.
- **Rationale:**
  - Schema-per-tenant (creating a separate PostgreSQL schema per org) creates immense migration overhead and does not scale well on SQLite.
  - Row-level scoping enforced via dependency injection (`get_active_organization`) provides robust data isolation with low administrative complexity.

### 4.3 Prompt Injection Defense: Delimited Sandboxing vs. Naive String Interpolation
- **Decision:** Strict `<source_content>` and `<user_instruction>` XML sandboxing with explicit anti-injection system prompt guardrails.
- **Rationale:**
  - Ingested web documents often contain hidden text or prompt injection attacks designed to hijack LLM behavior.
  - Enclosing source text in explicit delimiters and instructing the model to treat content within delimiters strictly as inert data to be analyzed neutralizes prompt injection vectors.

---

## 5. Architectural Trade-Offs & Technical Debt

| Architectural Area | Decision Made | Trade-off Accepted | Future Remediation |
| :--- | :--- | :--- | :--- |
| **URL Extraction** | Trafilatura + BS4 sync scraping in async handler | Extreme load could block ASGI worker threads | Migrate heavy scraping to a Celery/Redis background worker queue |
| **Draft Versioning** | Full text snapshot in `draft_versions` | Higher database storage over time | Introduce git-style delta compression for very large articles |
| **Real-time Editing** | REST polling & optimistic UI updates | Lacks real-time multiplayer cursor visibility | Implement WebSocket-based CRDTs (Yjs / Automerge) |
| **Cloudflare Gated Sites** | Graceful failure toast with Paste Text fallback | Cannot scrape heavily protected sites directly | Integrate headless browser proxy (Playwright) with stealth plugins |
