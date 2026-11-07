# AI Editorial Workspace — Architectural & Engineering Decision Records (ADRs)

**Author:** Senior Forward Deployed Engineer & Technical Architect  
**Project:** AI Editorial Workspace  
**Status:** Approved Architectural Record  
**Version:** 1.0.0 (Phase 10 Final Assessment)  
**Branch:** `docs/phase10-final-assessment-handover`

---

## 1. Core Framework & Language Decisions

### ADR-01: Python 3.10+ & FastAPI vs. Node.js / Go / Django
- **Context:** The system requires asynchronous HTTP routing, complex text processing, multi-source web extraction, semantic chunking, and unified multi-provider AI integrations.
- **Options Considered:**
  1. *Node.js / Express or NestJS:* Fast I/O, unified language across stack, but weaker native NLP and text extraction ecosystem.
  2. *Go (Golang):* High concurrency and low memory, but poor text processing, lack of mature HTML extraction libraries like Trafilatura, and high verbosity for AI SDKs.
  3. *Django / Django REST Framework:* Batteries-included ORM and admin, but monolithic overhead, synchronous core history, and excessive bloat for microservice APIs.
  4. *Python with FastAPI & Uvicorn (Chosen).*
- **Chosen Approach:** Python 3.10+ with FastAPI and Uvicorn ASGI server.
- **Reason:** FastAPI provides native asynchronous request handling, runtime data validation and serialization through Pydantic v2, and automatic OpenAPI schema generation. Python is the industry standard for AI engineering, token manipulation, and text parsing (Trafilatura, BeautifulSoup4).
- **Tradeoffs:** Python has higher memory consumption and slower raw CPU compute compared to Go or Rust. Mitigated by offloading compute-heavy tasks to C-accelerated libraries (`lxml`, `pydantic-core`) and utilizing asynchronous I/O for network-bound LLM calls.

---

### ADR-02: React 18 + TypeScript SPA vs. Next.js / Server-Side Rendering (SSR)
- **Context:** The frontend must provide rich, low-latency editorial tools: in-editor prose linters, floating selection toolbars, Afforai citation managers, and real-time diff visualizers.
- **Options Considered:**
  1. *Next.js (App Router / SSR):* Excellent initial page load and SEO, but introduces operational complexity (Node runtime servers, hydration mismatches, complex caching) for an authenticated internal workspace.
  2. *Vue 3 / Svelte:* Lightweight, but smaller ecosystem for rich text editing, citation management, and telemetry visualization.
  3. *React 18 SPA with Vite and TypeScript (Chosen).*
- **Chosen Approach:** Client-side React 18 SPA bundled with Vite 6 and Tailwind CSS.
- **Reason:** The AI Editorial Workspace is a desktop-grade operational tool used by authenticated staff, rendering public search indexing irrelevant. Client-side state transitions are instant, and Vite delivers sub-second Hot Module Replacement (HMR) and deterministic production chunking.
- **Tradeoffs:** Slightly larger initial JavaScript bundle payload. Mitigated by Vite chunk splitting, dynamic route imports (`React.lazy`), and Gzip compression at the Nginx reverse proxy.

---

## 2. Database Architecture & Persistence Decisions

### ADR-03: Relational Schema (SQLAlchemy 2.0) vs. Document / NoSQL Store
- **Context:** The system manages research projects, ingested sources, semantic chunks, extracted claims, briefs, drafts, suggestions, and version snapshots with strict multi-tenant ownership.
- **Options Considered:**
  1. *MongoDB / Document Store:* Flexible schema for research briefs, but lacks referential integrity, foreign-key cascade guarantees, and introduces risk of orphaned claims.
  2. *Relational PostgreSQL with SQLAlchemy 2.0 (Chosen).*
- **Chosen Approach:** Relational database with strict foreign-key constraints (`ON DELETE CASCADE`) and composite indexes on `(organization_id, id)`.
- **Reason:** Editorial research requires strict evidence provenance. If an investigation project is deleted, all associated sources, chunks, and briefs must cascade cleanly without data leakage. Relational schemas prevent orphaned citations and enforce multi-tenant isolation at the query level.
- **Tradeoffs:** Schema migrations require formal forward-planning. Mitigated by Alembic versioned migrations.

---

### ADR-04: Multi-Environment Database Strategy (SQLite in Dev, PostgreSQL in Prod)
- **Context:** Evaluators and engineers must be able to run and test the application with zero external dependencies, while production requires high-concurrency connection pooling.
- **Options Considered:**
  1. *PostgreSQL for all environments:* Requires Docker or a running PostgreSQL daemon for local development and unit tests, increasing friction for evaluators.
  2. *SQLite with PostgreSQL-Compatible Dialects (Chosen).*
- **Chosen Approach:** SQLite (WAL mode, `foreign_keys = ON`) for zero-friction local development and fast test execution; PostgreSQL 15 for production Docker Compose deployments.
- **Reason:** Allows any engineer to clone the repository, install requirements, and execute the 201-test regression suite immediately without launching containers.
- **Tradeoffs:** Dialect differences (e.g. `JSON` vs `JSONB`, datetime storage). Mitigated by using standard SQLAlchemy cross-platform types (`String(36)` UUIDs, ISO UTC timestamps) and running integration tests across both engines.

---

### ADR-05: Forward-Only Database Migrations via Alembic
- **Context:** Database models evolve across phases (adding prompt versions, token metrics, task queues).
- **Options Considered:**
  1. *`Base.metadata.create_all()`:* Works only on clean startups; destroys data or fails when adding columns to existing tables.
  2. *Versioned Alembic Migrations (Chosen).*
- **Chosen Approach:** Alembic migrations with linear revision history (head revision: `7a2c3d4e5f6a`).
- **Reason:** Guarantees reproducible, non-destructive schema evolution in staging and production pipelines.
- **Tradeoffs:** Developers must generate and test migration scripts for schema changes.

---

## 3. Security, Authentication & Multi-Tenancy

### ADR-06: JWT Access + Refresh Token Rotation with Argon2 Password Hashing
- **Context:** User authentication must support multi-device sessions, tenant organization switching, and defense against brute-force attacks.
- **Options Considered:**
  1. *Stateful Session Cookies:* Requires Redis session store lookup on every single API request, increasing latency and state coupling.
  2. *JWT Access (60m) + Refresh Token Rotation (7d) (Chosen).*
- **Chosen Approach:** Stateless JWT access tokens signed with HMAC-SHA256, paired with rotating refresh tokens stored in the database. Passwords hashed using Argon2id / bcrypt.
- **Reason:** Provides low-latency verification for high-throughput API calls while enabling instant session revocation upon password reset or organizational role revocation.
- **Tradeoffs:** Revoking access tokens prior to expiration requires token blacklisting. Mitigated by short 60-minute access token lifetimes.

---

### ADR-07: Row-Level Organization Scoping vs. Schema-per-Tenant
- **Context:** Enterprise clients require guaranteed multi-tenant data isolation.
- **Options Considered:**
  1. *Database-per-tenant:* Maximum isolation, but massive infrastructure overhead, expensive connection pooling, and complex cross-tenant analytics.
  2. *Schema-per-tenant (PostgreSQL schemas):* Medium complexity, but high migration overhead across hundreds of schemas.
  3. *Row-Level Organization Scoping with Middleware Enforcement (Chosen).*
- **Chosen Approach:** All persistent domain entities inherit from `TenantScopedBase`, enforcing indexed `organization_id` columns. The `get_active_organization` dependency injects tenant context into queries.
- **Reason:** Cost-effective, scalable, and simple to backup and migrate while maintaining complete tenant isolation.
- **Tradeoffs:** Risk of accidental developer query omissions. Mitigated by base model inheritance, strict unit tests (`test_phase24_multi_tenancy.py`), and returning HTTP 404 for foreign tenant IDs.

---

### ADR-08: Server-Side Request Forgery (SSRF) Defense Architecture
- **Context:** The Research Assistant ingests user-supplied URLs to fetch research material, exposing the server to SSRF and cloud metadata theft.
- **Options Considered:**
  1. *Simple regex URL validation:* Fails against DNS rebinding, HTTP redirects, IPv6 representations, and decimal IP formats.
  2. *Multi-Stage Defense-in-Depth SSRF Guard (Chosen).*
- **Chosen Approach:**
  - Whitelist `http` and `https` schemes only.
  - Resolve DNS before connection and validate IP addresses against blacklisted CIDRs (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`).
  - Re-validate IP destinations upon every HTTP 301/302 redirect.
  - Enforce strict 10-second connect/read timeouts and a 2MB response size limit.
- **Reason:** Prevents attackers from probing internal infrastructure, VPC services, or cloud instance metadata.
- **Tradeoffs:** May occasionally block valid intranet sites if intentionally run within an enterprise VPN. Configurable via `ALLOW_INTERNAL_IPS` setting.

---

## 4. AI Engineering & Evidence Grounding

### ADR-09: Unified AI Provider Router with 100% Deterministic Fallback
- **Context:** The workspace relies on LLMs for claim extraction, brief generation, and tone rewriting, but external AI APIs suffer from rate limits, outages, and cost spikes.
- **Options Considered:**
  1. *Direct Vendor SDK Coupling (OpenAI only):* Hard failure when OpenAI APIs experience downtime; vendor lock-in.
  2. *LangChain / LlamaIndex Heavy Abstractions:* Heavy dependency graph, frequent breaking changes, unneeded complexity for core editorial workflows.
  3. *Custom Unified `AIRouter` with Heuristic Fallback (Chosen).*
- **Chosen Approach:** Custom provider adapters (Groq, OpenAI, Anthropic, Gemini) adhering to a strict `BaseAIProvider` interface, coupled with an automatic `DeterministicFallbackAdapter`.
- **Reason:** Ensures the application never crashes with HTTP 500 when an API key is missing or an external provider fails. If offline, local deterministic NLP algorithms synthesize research briefs and audit drafts seamlessly.
- **Tradeoffs:** Heuristic fallback responses are less stylistically varied than frontier model outputs, though 100% factually grounded.

---

### ADR-10: Non-Destructive Sentence-Level Replacement Engine
- **Context:** Writers invest time formatting articles and inserting citations. Destructive AI overwrites erase formatting and corrupt adjacent copy.
- **Options Considered:**
  1. *Full Document Overwrite:* Rewrites the entire text; erases un-reviewed user edits and introduces hallucinated changes.
  2. *Non-Destructive Sentence Boundary Replacement (Chosen).*
- **Chosen Approach:** Identifies the precise start and end character offsets of the target sentence. Applying a rewrite replaces only the bounded text span while preserving the immutable `original_content` and adjacent citation anchors.
- **Reason:** Preserves author agency, trust, and citation traceability.
- **Tradeoffs:** Requires exact string matching and whitespace boundary tracking.

---

## 5. Deployment & Production Operations

### ADR-11: 3-Tier Container Architecture with Internal DNS and Non-Root Users
- **Context:** Production deployment must be reliable, secure, and reproducible.
- **Options Considered:**
  1. *Single Monolithic Container:* Bundles Nginx, Python, and PostgreSQL in one container; violates container single-responsibility principles and complicates horizontal scaling.
  2. *Decoupled 3-Tier Multi-Container Stack (Chosen).*
- **Chosen Approach:** Separate containers for Nginx (`frontend`), FastAPI (`backend`), PostgreSQL (`db`), and Redis (`redis`) communicating over an isolated Docker network using internal service names (`backend:8000`, `db:5432`, `redis:6379`). Containers run under non-root user `appuser` (UID 10001).
- **Reason:** Clean separation of concerns, principle of least privilege, and independent scaling.
- **Tradeoffs:** Requires Docker Compose orchestration.
