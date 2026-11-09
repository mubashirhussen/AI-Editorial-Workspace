# Phase 19: Forward Deployed Engineer Interview Preparation & Question Defense Bank

**Project:** AI Editorial Workspace  
**Candidate Role:** Forward Deployed Engineer (FDE) Intern / Technical Interviewee  
**Evaluation Scope:** Full-Stack Architecture, AI Systems, Production Engineering & Customer Defense  

---

## Category 1: Product Strategy & Architectural Decisions

### Q1.1: Why build a dedicated AI Editorial Workspace instead of using standard LLM chat interfaces (ChatGPT, Claude, etc.)?
**Answer:**  
Standard chat interfaces are unstructured, lack primary source grounding, and produce unverifiable outputs. In an enterprise editorial pipeline:
1. **Hallucination Risk:** Generative models make factual assertions without citations. Our workspace enforces a *research-first paradigm* where drafts are strictly anchored in ingested primary sources.
2. **Editorial Governance:** Publications require deterministic standards (e.g., maximum sentence lengths, reading grade level ceilings, passive voice constraints). Generic chat models cannot guarantee deterministic adherence to formatting or readability rules.
3. **Auditability & Multi-Tenancy:** We require complete version lineage (`EditorialVersion`), author attribution, and strict organizational tenant boundaries (`OrganizationMembership`).

### Q1.2: How does the system prevent hallucinated claims in generated editorial content?
**Answer:**  
Hallucination prevention is enforced through a three-layer pipeline:
1. **Source Constraint:** The AI synthesis engine is provided with parsed raw text and instructed with strict negative constraints ("Do not extrapolate beyond the provided text; if an entity is not mentioned, state 'Unverified'").
2. **Fact vs. Speculation Classifier:** Extracted statements are categorized as *Empirical Fact*, *Theoretical Model*, or *Industry Speculation* based on lexical verification and source citation mappings.
3. **Citation Anchoring:** Every key takeaway in the Research Brief is tied to a specific `source_id`. In the Editorial Studio, quotes and data points retain provenance tags linking back to the original document hash.

---

## Category 2: Frontend Engineering (React, Vite, TypeScript)

### Q2.1: How is client-side state managed, and how do you prevent unnecessary re-renders across complex editorial screens?
**Answer:**  
We utilize scoped React Contexts (`AuthContext`, `HealthContext`, `OrganizationContext`) paired with custom hooks:
- **Separation of Concerns:** High-frequency state (such as in-editor keystrokes and word counts) is kept local to component state (`useState` and `useRef` in `WritingPage.tsx`), preventing global re-renders.
- **Request Deduplication:** In `frontend/src/services/api.ts`, an in-flight GET request deduplication cache (`pendingGetRequests`) maps serialized endpoints to existing promises, preventing identical duplicate calls caused by simultaneous component mounting.
- **Dynamic Connection Backoff:** `HealthContext.tsx` uses a dynamic cadence (30s polling when connected, exponential backoff from 3s to 24s during disconnects) to minimize background thread consumption.

### Q2.2: How did you resolve the "Backend unavailable" status indicator in the UI?
**Answer:**  
In `frontend/src/services/api.ts`, `apiClient` had a default `baseURL` of `/api/v1`. When `healthService.ts` requested `apiClient.get('/health')`, the leading slash caused Axios to resolve the path relative to the root (`/health`) rather than the API prefix. Furthermore, `vite.config.ts` had only proxied `/api` to the backend. We aligned both ends:
1. Added `/health` to the Vite proxy table in `vite.config.ts` (matching `nginx.conf`).
2. Standardized health route availability on both `/health` and `/api/v1/health` in FastAPI (`backend/app/main.py`), ensuring that health checks resolve whether called via relative or absolute proxy paths.

---

## Category 3: Backend Engineering (FastAPI, Python, Async)

### Q3.1: Why choose FastAPI over Django or Flask for this application?
**Answer:**  
FastAPI was selected for three core technical reasons:
1. **Asynchronous Throughput:** Asynchronous endpoint definitions allow high-concurrency non-blocking I/O during source URL fetching, AI provider calls, and database operations.
2. **Pydantic Type Validation:** Strict serialization/deserialization via Pydantic v2 schemas (`backend/app/schemas/`) guarantees compile-time and runtime type safety, automatically rejecting malformed JSON payloads with descriptive 422 errors.
3. **Standardized OpenAPI Documentation:** FastAPI generates compliant OpenAPI 3.0 specs out of the box (`/docs` and `/redoc`), simplifying client SDK generation and partner API integrations.

### Q3.2: How do you handle request tracing and error correlation in production?
**Answer:**  
We implemented custom middleware (`backend/app/middleware/request_tracing.py`). For every incoming HTTP request:
1. It inspects the `X-Request-ID` header; if absent, it generates a unique UUID4.
2. The ID is injected into FastAPI's `request.state.request_id` and bound to the logging context.
3. The response header returns `X-Request-ID`. If an unhandled exception or 422 validation failure occurs, the standardized error payload includes this exact `request_id`, allowing SREs to correlate client-side errors directly with server log traces.

---

## Category 4: Database Architecture & Data Persistence

### Q4.1: How do you manage schema evolution, and what challenges did you face with SQLite DDL?
**Answer:**  
Schema migrations are managed through Alembic (`backend/alembic/versions/`). SQLite does not support standard `ALTER COLUMN` or `DROP COLUMN` operations natively. To achieve production parity without requiring Postgres for local tests:
1. We configured Alembic migrations to run in **batch mode** (`render_as_batch=True`).
2. Batch mode automatically creates temporary tables, copies existing data, drops old tables, and recreates indexes.
3. The current schema stands at revision `7a2c3d4e5f6a`, encompassing 34 synced tables with complete multi-tenant constraints.

### Q4.2: How do you guarantee multi-tenant data isolation?
**Answer:**  
Multi-tenancy is enforced at three distinct layers:
1. **Schema Constraint:** Every core table (`ResearchProject`, `WritingDraft`, `SourceDocument`, `AuditLog`) contains an indexed `organization_id` foreign key referencing `organizations.id`.
2. **Middleware / Dependency Validation:** Incoming requests pass through an organization membership verification dependency (`get_current_organization`) that extracts `X-Organization-Id` and verifies the authenticated user has an active membership record in `organization_memberships`.
3. **Repository Scoping:** All database queries explicitly filter by `organization_id == current_org.id`, making cross-tenant data leaks impossible even in the event of parameter tampering.

---

## Category 5: AI / LLM Systems & Factual Grounding

### Q5.1: What happens when the external LLM provider experiences an outage or rate limit (HTTP 429 / 503)?
**Answer:**  
We architected a zero-downtime **Autonomous Fallback Engine** (`backend/app/services/ai_service.py`):
- If the primary provider (e.g., Groq) fails due to rate limits or invalid keys, the service catches the exception and falls back to our secondary provider (OpenAI).
- If all cloud providers fail or if the system is running offline, the request routes to the **Deterministic Fallback Engine**.
- The fallback engine applies rule-based heuristic text extraction, regex summarization, and statistical scoring to generate the requested research brief or draft.
- The response metadata explicitly flags `"mode": "Deterministic Fallback Engine"`, maintaining system availability and transparently alerting the user.

### Q5.2: How do your deterministic linguistic checks work in the Writing Assistant?
**Answer:**  
In `backend/app/services/writing_auditor.py`, 9 deterministic checks evaluate the text:
1. **Sentence Length:** Tokenizes sentences using punctuation boundaries (`.!?`) and flags sentences containing > 30 words.
2. **Passive Voice:** Uses regex matching for auxiliary verbs (`is`, `was`, `were`, `been`) followed by past participles (e.g., `by the`).
3. **Filler Words:** Scans against a compiled lexicon of conversational filler phrases (`in order to`, `at the end of the day`, `basically`).
4. **Flesch Reading Ease & Grade Level:** Calculates mathematical scores based on total words, sentences, and syllable counts computed via phonetic vowel-group clustering.

---

## Category 6: Security, Reliability & Observability

### Q6.1: What is Server-Side Request Forgery (SSRF), and how does the application defend against it during URL ingestion?
**Answer:**  
SSRF occurs when an attacker inputs an internal URL (e.g., `http://169.254.169.254/latest/meta-data/` or `http://127.0.0.1:8000/admin`) to trick the server into accessing intranet resources or cloud instance metadata.  
In `backend/app/services/url_validator.py`:
1. We parse the URL and extract the hostname.
2. We resolve the hostname using `socket.getaddrinfo()` to obtain all corresponding IP addresses.
3. Every resolved IP is evaluated against a blacklist of private CIDR blocks (`127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`).
4. Any attempt to access a private or link-local address raises an immediate `SSRFProtectionException` (HTTP 400), terminating the request before any HTTP connection is established.

### Q6.2: How do you verify system readiness in a containerized or Kubernetes deployment?
**Answer:**  
We expose three tiered health probes in `backend/app/api/routes/health.py`:
1. `/health/live` (Liveness): Validates that the ASGI process is alive and responding (HTTP 200).
2. `/health/startup` (Startup): Confirms that application initialization and database connections are ready.
3. `/health/ready` (Readiness): Executes an active `SELECT 1` database query and measures latency. If the database is unreachable, it returns HTTP 503 so the load balancer stops routing traffic to the unready pod.

---

## Category 7: Forward Deployed Engineering (FDE) Specific Scenarios

### Q7.1: A client enterprise wants to deploy the AI Editorial Workspace on-premises in an air-gapped environment with no internet access. Can the system operate?
**Answer:**  
Yes. The entire architecture was deliberately designed for air-gapped support:
1. **Zero External CDN Dependencies:** Frontend dependencies (fonts, icons, styles) are bundled into local static assets via Vite.
2. **Local Fallback Engine:** The research synthesis and writing audit engines run entirely on local CPU heuristics when no external LLM API keys are provided.
3. **Local Vector / Relational Storage:** The database operates natively on local SQLite or customer-managed PostgreSQL without telemetry call-homes.
4. **Local Model Integration:** The `AIProviderBase` interface makes it straightforward to point the AI service to an on-premises Ollama or vLLM instance by setting `AI_PROVIDER_BASE_URL` in the environment configuration.

### Q7.2: An enterprise customer reports that some long research papers fail during ingestion. How would you diagnose and resolve this in the field?
**Answer:**  
As an FDE, my diagnostic playbook would be:
1. **Correlate Request ID:** Obtain the `X-Request-ID` from the client's failure response and inspect the structured backend logs.
2. **Identify Bottleneck:**
   - If payload size exceeded limits: Inspect `MAX_UPLOAD_SIZE` in `settings.py` (default 10MB) and adjust if legitimate files require it.
   - If parser timeout occurred: Check `httpx` timeout limits (default 30s) or PDF text extractor memory overhead.
   - If token window overflowed: Ensure the text chunker splits oversized documents into 4,000-token chunks before ingestion.
3. **Provide Hotfix / Configuration Update:** Ship a scoped configuration fix or update the chunking pipeline without destabilizing existing customer workflows.
