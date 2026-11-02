# AI Editorial Workspace — Comprehensive Technical Interview Q&A (100 Questions)

**Role:** Forward Deployed Engineer (FDE) / Full-Stack AI Engineer  
**Focus:** AI Editorial Workspace Architecture, Implementation & Defense  

---

## Category A: Project and Product Understanding (Questions 1–10)

### 1. Why did you build the AI Editorial Workspace?
**Answer:** I built it for the senior editorial desk at *This Week in AI* to solve two critical editorial failure modes: first, unverified AI company PR and benchmark claims being blindly accepted by standard LLMs without citation links; second, technical drafts becoming bloated with passive voice and filler words while generic rewriters flatten authorial voice.

### 2. Who are the primary target users?
**Answer:** Senior technical editors, newsletter curators, and research analysts at technology publications who must turn dense technical announcements, papers, and roadmaps into concise, evidence-backed 300–500-word newsletter briefings.

### 3. What are the three core functional modules?
**Answer:** 
1. *Module A (Research Assistant):* Multi-source ingestion ($\ge 3$ sources), SSRF-guarded scraping, claim-to-excerpt extraction, and 10-section brief synthesis.
2. *Module B (Writing Assistant):* 6 deterministic Hemingway-style writing checks, Flesch Reading Ease calculations, and non-destructive sentence replacements.
3. *Module C (Editorial Studio):* 3-column newsletter production studio generating 300–500-word drafts with inline citations `[1]`, `[2]` and multi-format exports.

### 4. What was your biggest technical challenge during development?
**Answer:** Ensuring that user-accepted editorial suggestions never corrupt surrounding copy or citations. In early iterations, naive string replacement risked replacing identical words in different sentences. I solved this by implementing `replace_text_safely()`, which calculates sentence boundaries and performs targeted substring replacement on `revised_content` while preserving `original_content` as an immutable baseline.

### 5. Why did you choose deterministic heuristics over LLMs for the Writing Assistant?
**Answer:** Speed, cost, and repeatability. Using an LLM to identify passive voice or filler phrases like `"in order to"` incurs unnecessary API latency (800ms+), costs money, and risks hallucinating or mutating unaffected text. Our deterministic Python heuristics run in under 15ms, cost zero dollars, and produce 100% predictable results.

### 6. What is the difference between Verified Facts, Editorial Analysis, and Speculation?
**Answer:**
- *Verified Facts:* Empirical, measurable data (e.g. "Scored 79.8% on AIME 2024", "Released under MIT license").
- *Editorial Analysis:* Logical interpretations of economic or architectural trends (e.g. "Shifts competitive advantage from pre-training compute to inference compute").
- *Speculation:* Forward-looking vendor claims or subjective predictions (e.g. "Will replace all software engineers by 2026").

### 7. What happens if a user submits an inaccessible or bot-blocked URL?
**Answer:** Our extraction service attempts 4 tiers: Trafilatura, BeautifulSoup4 DOM parsing, OpenGraph/meta tag description extraction, and raw text extraction. If an anti-bot wall (like Cloudflare) blocks all programmatic fetching, the UI provides an immediate inline **"Paste Text"** and **"Retry"** action so the editor can continue without interruption.

### 8. What is the dual-column draft architecture?
**Answer:** In our `WritingDraft` database model, we store two distinct text columns: `original_content` and `revised_content`. When a user accepts a rewrite, changes are applied only to `revised_content`. This enables instant side-by-side visual diffing and guarantees that the author's original submission can be restored at any time.

### 9. What makes this application production-ready rather than a prototype?
**Answer:** 104 passing automated tests with 0 failures, 0 TypeScript compiler errors, multi-stage Docker containerization with non-root security (`appuser:10001`), database migrations managed by Alembic across 34 tables, automated backup scripts with SHA-256 integrity verification, and socket-level SSRF defense.

### 10. If you had another sprint, what would you improve?
**Answer:** I would add a headless browser container (Playwright) to automatically bypass client-rendered JavaScript SPAs, and implement real-time collaborative editing using Yjs CRDTs over WebSockets for multi-editor teams.

---

## Category B: React and TypeScript (Questions 11–26)

### 11. What is the difference between React state and props?
**Answer:** Props are read-only inputs passed from a parent component to configure a child. State is internal, reactive data managed within a component that triggers a re-render when updated via its setter (e.g. `useState`).

### 12. How do you handle centralized API communication in this frontend?
**Answer:** We created a centralized Axios client in `frontend/src/services/api.ts` with request interceptors that attach the JWT Bearer token and `X-Request-ID` correlation headers, and response interceptors that handle 401 unauthenticated redirects globally.

### 13. What is TypeScript's `interface` vs `type`?
**Answer:** Both define object shapes, but `interface` supports declaration merging and is idiomatic for public API contracts and domain models (like `Source` and `WritingDraft` in `types/`), whereas `type` is better for union types, primitives, and complex utility transformations.

### 14. What are React hooks, and what rules must they follow?
**Answer:** Hooks are functions (`useState`, `useEffect`, `useCallback`) that let function components use state and lifecycle features. They must only be called at the top level (never inside loops, conditions, or nested functions) and only inside React function components.

### 15. How do you prevent unnecessary re-renders in complex React pages?
**Answer:** By lifting state only as far as necessary, memoizing expensive computational transforms with `useMemo`, wrapping stable callback handlers with `useCallback`, and breaking large views into isolated leaf components.

### 16. How does React Router v7 handle protected routes in this application?
**Answer:** We wrap private workspace routes inside a `ProtectedRoute` component that checks for an active JWT token in localStorage/state; if missing or expired, it redirects the user to `/login` while preserving the intended destination path.

### 17. What is an Error Boundary in React?
**Answer:** A React class component that implements `componentDidCatch` or `getDerivedStateFromError` to catch JavaScript errors anywhere in its child component tree, logging the error and displaying a fallback UI instead of crashing the entire page.

### 18. How do you manage form state and validation?
**Answer:** We use controlled React components where inputs bind their `value` to state and trigger `onChange` handlers, validating data formats (such as URLs and min-length constraints) before dispatching API requests.

### 19. What is Vite, and why is it preferred over Create React App (Webpack)?
**Answer:** Vite is a next-generation frontend build tool that leverages native ES modules in development for instant server start and lightning-fast HMR (Hot Module Replacement), and bundles with Rollup for optimized production chunking.

### 20. How is dark and light theme toggling implemented?
**Answer:** By toggling a `dark` class on the root `<html>` element and managing user preference in `localStorage`. Tailwind CSS's `dark:` modifier automatically styles dark and light themes accordingly.

### 21. How do you verify zero TypeScript compiler errors before production?
**Answer:** We run `npx tsc -b` (TypeScript Project References build mode), which enforces strict type checking across all files without emitting JavaScript if any type errors exist.

### 22. What is the purpose of `package-lock.json`?
**Answer:** It locks the exact versions of every transitive dependency and sub-dependency in the dependency tree, ensuring that every developer and CI runner installs byte-for-byte identical packages via `npm ci`.

### 23. What are React synthetic events?
**Answer:** Synthetic events are React's cross-browser wrapper around the browser's native DOM events, ensuring consistent event property behavior across all browsers and operating systems.

### 24. What are Tailwind CSS utility classes and why use them?
**Answer:** Small, composable CSS classes applied directly in JSX (e.g. `flex items-center px-4 py-2`). They eliminate context switching between CSS files and JSX, prevent unused CSS bloat via PurgeCSS/tree-shaking, and enforce consistent design tokens.

### 25. How do you handle user notifications and feedback in the UI?
**Answer:** We use the `sonner` toast notification library, rendering non-blocking status toasts on user actions like "Draft Saved", "Source Extracted", and "Writing Quality Audit Completed".

### 26. How does the user profile widget in the top-right navbar operate?
**Answer:** It reads the authenticated user's profile from auth state, rendering their avatar/initials, workspace role badge (`OWNER`), and providing a dropdown menu for quick access to workspace settings and sign-out.

---

## Category C: Python and FastAPI (Questions 27–42)

### 27. What is ASGI, and how does FastAPI utilize it?
**Answer:** ASGI (Asynchronous Server Gateway Interface) is the asynchronous successor to WSGI. It allows FastAPI to handle concurrent I/O-bound requests (such as database queries and external HTTP calls) asynchronously using Python's `async/await` event loop without blocking worker threads.

### 28. What is Pydantic v2 and how does FastAPI use it?
**Answer:** Pydantic is a data validation and parsing library written in Rust (Pydantic Core). FastAPI uses Pydantic schemas to automatically validate request bodies, deserialize JSON, enforce field types and constraints, and generate OpenAPI documentation.

### 29. What is Dependency Injection in FastAPI?
**Answer:** A design pattern implemented via `Depends()`. It allows route handlers to declare dependencies (such as database sessions, authenticated users, or configuration objects) that FastAPI resolves and injects automatically, promoting clean separation of concerns and easy test mocking.

### 30. How does FastAPI middleware work?
**Answer:** Middleware wraps the entire HTTP request/response cycle. It intercepts incoming requests before reaching route handlers (e.g. for rate limiting or tracing), calls `await call_next(request)`, and inspects or modifies outgoing responses (e.g. injecting `X-Request-ID` headers).

### 31. Explain Python's `async` and `await` keywords.
**Answer:** `async def` declares an asynchronous coroutine that can pause execution when awaiting an I/O operation via `await`, allowing the event loop to execute other concurrent tasks while waiting for network or disk operations to complete.

### 32. How do you structure global exception handling in FastAPI?
**Answer:** By decorating handlers with `@app.exception_handler(Exception)` and `@app.exception_handler(RequestValidationError)`. This intercepts unhandled exceptions, logs tracebacks with correlation IDs, and returns consistent JSON error payloads to clients.

### 33. How is API versioning implemented in this project?
**Answer:** We mount our sub-routers under the `/api/v1` prefix defined in `settings.API_V1_PREFIX`. This ensures backwards compatibility if future `/api/v2` endpoints are developed.

### 34. What is the difference between synchronous and asynchronous database drivers?
**Answer:** Synchronous drivers (like standard `sqlite3` or `psycopg2`) block the executing thread until the query returns. Asynchronous drivers (like `asyncpg`) yield control back to the event loop, allowing high concurrent throughput on I/O-heavy endpoints.

### 35. How does Python's `compileall` module ensure release quality?
**Answer:** `python -m compileall` parses and compiles all Python source files into `.pyc` bytecode without running them, detecting syntax errors, invalid indentation, and malformed expressions before test execution or deployment.

### 36. What is the purpose of FastAPI's `lifespan` context manager?
**Answer:** It replaces deprecated `@app.on_event("startup")` and `"shutdown"` hooks, allowing developers to execute initialization code (like verifying database tables or pre-loading style profiles) and clean up resources when the app shuts down.

### 37. What is CORS and how is it configured in FastAPI?
**Answer:** Cross-Origin Resource Sharing is a browser security mechanism that restricts web pages from making requests to a different domain. In FastAPI, `CORSMiddleware` configures allowed origins, credentials, methods, and headers.

### 38. How does rate limiting work in this application?
**Answer:** `InMemoryRateLimiterMiddleware` tracks client IP addresses using a sliding window timestamps list, rejecting requests exceeding 120 per minute with HTTP 429 Too Many Requests and a `Retry-After: 60` header.

### 39. What is the difference between `HTTP_422_UNPROCESSABLE_ENTITY` and `HTTP_400_BAD_REQUEST`?
**Answer:** HTTP 400 is returned when the request syntax is malformed (e.g. invalid JSON syntax or SSRF violation). HTTP 422 is returned when the JSON syntax is valid, but fails semantic schema validation (e.g. missing required field, negative number where positive required).

### 40. How do you measure request latency and telemetry in FastAPI?
**Answer:** Our `ObservabilityMiddleware` captures `time.perf_counter()` before `call_next(request)` and calculates elapsed duration in milliseconds upon completion, logging duration and updating our monitoring ring buffer.

### 41. How are environment variables managed in FastAPI?
**Answer:** Using `pydantic-settings`. A `Settings` class inheriting from `BaseSettings` reads from `.env` files and environment variables, validating types and setting defaults automatically.

### 42. What is Uvicorn?
**Answer:** A lightning-fast, production-grade ASGI web server implementation for Python, built on `uvloop` and `httptools`.

---

## Category D: Database and SQL (Questions 43–57)

### 43. What is an ORM and why use SQLAlchemy 2.0?
**Answer:** An Object-Relational Mapper translates database tables into Python classes and rows into Python objects. SQLAlchemy 2.0 provides type safety, relationship mapping, cascading deletes, and SQL injection protection while supporting both SQLite and PostgreSQL.

### 44. What is Alembic and how does it manage database migrations?
**Answer:** Alembic is a lightweight database migration tool for SQLAlchemy. It tracks schema revisions linearly (e.g. `fe217d474c9d -> 0d95531a1a07 -> 3b7c9f1e8a2d`), applying forward upgrades and downgrades via migration scripts.

### 45. What are foreign keys and how do they enforce data integrity?
**Answer:** Foreign keys are columns in one table that reference primary keys in another table (e.g. `claims.source_id -> sources.id`). They enforce referential integrity by ensuring child records cannot reference nonexistent parents, and can automatically cascade deletes.

### 46. What is the difference between SQLite and PostgreSQL?
**Answer:** SQLite is a serverless, file-based database ideal for zero-friction local development, testing, and embedded apps. PostgreSQL is a full-featured, client-server relational database with concurrent connection pooling, MVCC, and advanced indexing for production.

### 47. What is connection pooling?
**Answer:** A cache of active database connections maintained by the application server (e.g. `pool_size=10, max_overflow=20`), eliminating the expensive overhead of establishing a new TCP connection and TLS handshake for every database query.

### 48. What is database indexing and when should you use it?
**Answer:** An index is a data structure (typically a B-tree) that speeds up data retrieval on specified columns at the cost of slower writes and additional storage. We index foreign keys and columns frequently used in `WHERE` and `JOIN` clauses (such as `organization_id` and `project_id`).

### 49. What are ACID properties in relational databases?
**Answer:**
- *Atomicity:* All operations in a transaction succeed, or all fail.
- *Consistency:* Database transitions from one valid state to another.
- *Isolation:* Concurrent transactions do not interfere with one another.
- *Durability:* Committed transactions survive power loss or crashes.

### 50. How do you prevent SQL injection?
**Answer:** By using parameterized queries. SQLAlchemy ORM automatically binds variables separately from the SQL statement structure, ensuring that user input is never interpreted as executable SQL syntax.

### 51. What is the purpose of database transactions and rollbacks?
**Answer:** A transaction groups multiple database operations into a single atomic unit. If any step fails or raises an exception, calling `session.rollback()` reverts all uncommitted modifications, preventing partial or corrupted data.

### 52. What is `PRAGMA integrity_check` in SQLite?
**Answer:** An internal SQLite verification command that scans the database file for out-of-order index entries, missing pages, malformed records, and corrupt cells, returning `"ok"` if the database is healthy.

### 53. How does the automated backup script `backup_db.py` work?
**Answer:** It runs a pre-backup integrity check, uses SQLite's online backup API to copy pages cleanly without locking concurrent readers, validates the target backup file, and calculates its SHA-256 checksum for audit verification.

### 54. What is multi-tenant data isolation?
**Answer:** Ensuring that data belonging to Organization A is never visible to or modifiable by Organization B. We enforce this by tagging models with `organization_id` and scoping all queries by the authenticated user's organization.

### 55. What is the N+1 query problem and how do you resolve it?
**Answer:** The N+1 problem occurs when querying 1 parent entity results in N additional separate queries to fetch related child entities. In SQLAlchemy, it is resolved using eager loading via `.options(joinedload(...))` or `.options(selectinload(...))`.

### 56. What is database seeding?
**Answer:** Automatically populating the database with initial baseline records upon startup, such as creating the default publication style profile ("This Week in AI Standard") if none exists.

### 57. What are database cascades?
**Answer:** Rules that define what happens to child records when a parent record is deleted. For example, `ondelete="CASCADE"` on `claims.source_id` ensures that deleting a source automatically deletes all claims extracted from it.

---

## Category E: AI and LLM Engineering (Questions 58–72)

### 58. What is a Large Language Model (LLM)?
**Answer:** An autoregressive neural network trained on vast amounts of text data to predict the next token in a sequence given a context window, capable of semantic text generation, summarization, and reasoning.

### 59. How does prompt engineering work in this application?
**Answer:** We structure prompts with explicit role framing, task definitions, few-shot examples, JSON schema constraints, and `<source_data>` XML fences to ensure reliable extraction without conversational filler.

### 60. What is structured JSON output generation?
**Answer:** Enforcing that an LLM returns strictly valid JSON adhering to a specified schema (e.g. using OpenAI's `response_format={"type": "json_object"}`), validated immediately upon receipt by Pydantic models.

### 61. How do you prevent AI hallucinations in editorial drafting?
**Answer:**
1. Grounding: All factual assertions must originate from extracted source claims.
2. Citations: Requiring numbered bracketed markers `[1]`, `[2]` pointing to verified references.
3. Separation: Explicitly separating verified facts from analytical speculation.

### 62. What is prompt injection and how is it mitigated?
**Answer:** An attack where untrusted user input contains adversarial instructions attempting to override system prompts. We mitigate this by wrapping untrusted source text in `<source_data>` XML fences and instructing the LLM to treat all enclosed content strictly as inert data.

### 63. How do you handle AI provider outages and rate limits?
**Answer:** Our Intelligent AI Router implements jittered exponential backoff retries. If the provider continues to fail or return HTTP 429/500, it falls back to our **Deterministic Rule Engine**, ensuring the editorial desk never experiences downtime.

### 64. What is Groq LPU and why is it supported?
**Answer:** Groq is an ultra-high-speed Language Processing Unit designed for deterministic tensor compute, providing near-instantaneous token generation speeds (300+ tokens/sec) ideal for real-time editorial synthesis.

### 65. What is the purpose of the 10-section research brief?
**Answer:** It synthesizes disparate sources into an organized document covering Executive Summary, Core Technical Developments, Benchmarks, Commercial Impact, Divergent Points, and Newsletter Angles.

### 66. How does the headline formula generator operate?
**Answer:** It generates 5 distinct headline angles for each story: How-To, Curiosity Gap, Direct Benefit, Contrarian, and Data-Driven, allowing editors to select the angle best suited for their newsletter audience.

### 67. How do you evaluate AI output quality systematically?
**Answer:** Using automated evaluation suites that measure benchmark accuracy, citation precision, length compliance (300–500 words), and readability improvement.

### 68. What are embeddings and semantic similarity?
**Answer:** Embeddings are high-dimensional vector representations of text where semantic similarity corresponds to cosine proximity in vector space.

### 69. Why did you use relational foreign keys instead of a vector database for citations?
**Answer:** For 3–10 source editorial briefings, exact textual excerpt matching via relational foreign keys provides 100% deterministic attribution with zero cold-start latency and zero extra infrastructure overhead.

### 70. How are third-party AI credentials stored securely?
**Answer:** API keys are encrypted at rest using AES-128 via Python's `cryptography.fernet` symmetric encryption, and masked as `••••••••1234` in all UI views and logs.

### 71. What is temperature in LLM generation?
**Answer:** A sampling hyperparameter that scales logits before softmax. Lower temperatures (0.1–0.3) produce deterministic, factual outputs (ideal for extraction), while moderate temperatures (0.7) produce creative prose (ideal for headline drafting).

### 72. What happens if an LLM returns malformed JSON?
**Answer:** Our backend implements a regex recovery fallback (`re.search(r"\{.*\}", text, re.DOTALL)`) to extract the valid JSON substring; if that fails, it transparently activates the deterministic rule engine.

---

## Category F: API and Integration Engineering (Questions 73–86)

### 73. What is a RESTful API?
**Answer:** An architectural style for networked applications that uses HTTP methods (`GET`, `POST`, `PUT`, `DELETE`) on versioned, noun-based resource URIs to perform stateless CRUD operations.

### 74. What is the difference between `PUT` and `PATCH`?
**Answer:** `PUT` replaces the entire resource representation with the provided payload. `PATCH` applies partial updates only to the fields specified in the request.

### 75. What are the standard HTTP status codes used in this application?
**Answer:**
- `200 OK`: Successful retrieval or update.
- `201 Created`: Resource successfully created (e.g. project, draft).
- `400 Bad Request`: Invalid request syntax or SSRF rejection.
- `401 Unauthorized`: Missing or invalid JWT bearer token.
- `403 Forbidden`: Insufficient permissions for organization resource.
- `404 Not Found`: Target resource does not exist.
- `422 Unprocessable Content`: Schema validation error.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Unhandled exception trapped by global handler.

### 76. What is an API correlation ID (`X-Request-ID`)?
**Answer:** A unique UUID assigned to an incoming request that flows across logs, services, and response headers, allowing engineers to trace the complete lifecycle of a request during debugging.

### 77. What is the difference between `/health/live` and `/health/ready`?
**Answer:**
- `/health/live`: Unconditional liveness probe verifying that the application process is running.
- `/health/ready`: Deep readiness probe verifying that external dependencies (PostgreSQL database) are accessible and executing queries.

### 78. What are exponential backoff and jitter in network retries?
**Answer:** Exponential backoff doubles the wait time between retry attempts ($2^n$). Jitter adds random variance to the backoff interval, preventing thousands of clients from retrying simultaneously and causing a thundering herd problem.

### 79. How do you handle HTTP timeouts during article extraction?
**Answer:** Using `httpx.AsyncClient(timeout=12.0)`. If a remote web server fails to respond within 12 seconds, the client raises a timeout exception and gracefully falls back to alternative extraction methods.

### 80. How is multi-format article export implemented?
**Answer:** The Editorial Studio transforms the generated draft into three formats: clean GitHub-Flavored Markdown, formatted Plain Text, and semantic HTML5 with styled superscript citations and entity-escaped content.

### 81. What is an API gateway or reverse proxy?
**Answer:** An intermediary server (like Nginx) that sits in front of application backends to handle TLS termination, static asset serving, compression, security headers, and routing.

### 82. What is idempotency in API design?
**Answer:** The property where performing an operation multiple times produces the exact same result as performing it once. `GET`, `PUT`, and `DELETE` are inherently idempotent; `POST` typically is not unless paired with idempotency keys.

### 83. How do you prevent oversized payload attacks?
**Answer:** By enforcing maximum content-length bounds on file uploads (10MB limit) and streaming web page extraction (2MB limit).

### 84. What is OpenAPI / Swagger?
**Answer:** A standardized specification for documenting REST APIs. FastAPI automatically generates interactive OpenAPI documentation at `/docs` directly from route definitions and Pydantic schemas.

### 85. What is HTTP keep-alive?
**Answer:** An HTTP feature that keeps underlying TCP connections open for multiple requests and responses, reducing latency by avoiding repeated three-way TCP handshakes.

### 86. How are third-party API keys masked in responses?
**Answer:** Via `mask_api_key()`, which replaces all characters except the last four with dots (`••••••••1234`), preventing accidental exposure in UI screen shares or logs.

---

## Category G: Security and DevOps (Questions 87–100)

### 87. What is Server-Side Request Forgery (SSRF)?
**Answer:** A vulnerability where an attacker forces a server to issue HTTP requests to internal, private, or unexpected destinations (e.g. AWS metadata `169.254.169.254` or internal services on `127.0.0.1`).

### 88. How does this project prevent SSRF?
**Answer:** Before issuing any HTTP request, `extraction_service.py` resolves the destination domain via `socket.getaddrinfo()` and checks the resulting IP against RFC 1918 subnets, loopback, and link-local ranges, aborting immediately if a match is found.

### 89. What is JWT and how does it authenticate users?
**Answer:** JSON Web Token is a compact, URL-safe token consisting of Header, Payload, and Signature. The server signs the payload using HMAC-SHA256 (`HS256`) and verifies the signature on subsequent requests without requiring server-side session lookups.

### 90. Why is `bcrypt` preferred over MD5 or SHA-256 for password hashing?
**Answer:** MD5 and SHA-256 are fast hash functions vulnerable to brute-force and ASIC cracking. Bcrypt is deliberately slow and computationally intensive, incorporating a work factor and automatic unique salts to defeat rainbow tables.

### 91. What is Cross-Site Scripting (XSS) and how is it prevented?
**Answer:** An attack where malicious JavaScript is injected into web pages viewed by other users. In our app, React automatically escapes values in JSX, and exported HTML newsletters run through Python's `html.escape()`.

### 92. Why should Docker containers run as non-root users?
**Answer:** Running containers as root creates severe security risks: if an attacker achieves remote code execution inside the container, they could escape to the host with root privileges. We run our backend as unprivileged `appuser:10001`.

### 93. What is a multi-stage Docker build?
**Answer:** A Dockerfile technique that uses multiple `FROM` instructions. The first stage installs build tools and compiles packages; the final runtime stage copies only the compiled assets, leaving behind compilers, dev tools, and reducing image attack surface.

### 94. How does GitHub Actions automate CI/CD in this repository?
**Answer:** Workflows in `.github/workflows/` trigger on push and PR to `main`, running Python test matrices (3.10 and 3.11), clean Alembic migrations, Node Vite builds, secret pattern scanning, and dependency vulnerability audits.

### 95. What is the purpose of `.dockerignore`?
**Answer:** It prevents sensitive or bulky files (`.env`, `.git`, `venv`, `node_modules`, `dist`, local `.db` files) from being copied into Docker build contexts, speeding up builds and preventing secret leaks.

### 96. What is Content Security Policy (CSP)?
**Answer:** An HTTP response header that restricts the resources (scripts, images, stylesheets) the browser is allowed to load for a given page, serving as a powerful defense against XSS and clickjacking.

### 97. What is Recovery Point Objective (RPO) and Recovery Time Objective (RTO)?
**Answer:**
- *RPO:* The maximum acceptable data loss measured in time (our target: $< 1\text{ hour}$).
- *RTO:* The maximum acceptable downtime to restore service after a disaster (our target: $< 15\text{ minutes}$).

### 98. How do you prevent secret leaks in Git?
**Answer:** By adding `.env` files to `.gitignore`, providing `.env.example` templates with empty placeholders, and running automated regex scans in CI that fail the build if secret signatures (e.g. `sk-...`) are detected.

### 99. What are Docker volumes and why are they used?
**Answer:** Persistent storage mechanisms managed by Docker outside the container lifecycle. We use named volumes (`postgres_data`, `backend_data`, `backend_backups`) so database records survive container restarts and updates.

### 100. How do you verify database disaster recovery?
**Answer:** By running `backup_db.py --action backup`, verifying the SHA-256 checksum and `PRAGMA integrity_check`, simulating data corruption on a test database, and executing `--action restore` to confirm full recovery.
