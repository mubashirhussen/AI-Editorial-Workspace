# AI Editorial Workspace — Technical Architecture Document

**Author:** Senior Forward Deployed Engineer & Technical Architect  
**Project:** AI Editorial Workspace  
**Status:** Validated Production System  
**Version:** 1.0.0 (Phase 10 Final Assessment)  
**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Branch:** `docs/phase10-final-assessment-handover`

---

## 1. End-to-End System Architecture

The AI Editorial Workspace is engineered as a decoupled, 3-tier containerized system with strict boundaries between presentation, business logic, persistence, and external AI services.

```mermaid
flowchart TD
    subgraph PresentationTier["Presentation Tier (Client)"]
        Browser["User Browser<br/>(Desktop / Tablet)"]
        ReactApp["React 18 + TypeScript SPA<br/>Vite 6, Tailwind CSS, Recharts"]
        RUM["Real User Monitoring (RUM)<br/>Web Vitals, LCP, JS Error Tracking"]
    end

    subgraph IngressGateway["Ingress & Edge Routing"]
        NginxProxy["Nginx Reverse Proxy (Port 80/443)<br/>SSL Termination, Gzip, Rate-Limiting"]
    end

    subgraph LogicTier["Application & Business Logic Tier"]
        FastAPI["FastAPI ASGI Server (Port 8000)<br/>Python 3.10+, Uvicorn Workers"]
        
        subgraph Middlewares["Security & Context Middlewares"]
            CorrelationID["Request Correlation ID (`X-Request-Id`)"]
            RateLimiter["Rate Limiting Middleware (Redis/Memory)"]
            TenantContext["Tenant & Organization Context Injection"]
            SecurityHeaders["Security Headers (CSP, HSTS, X-Frame)"]
        end

        subgraph CoreEngines["Core Processing Engines"]
            SSRFGuard["SSRF & DNS Rebinding Validator"]
            Extractor["Extraction Pipeline (Trafilatura + BS4 + PDF)"]
            ResearchEngine["Research Synthesis & UNU Claim Verifier"]
            WritingEngine["Writing Linter & Quality Scorer (Hemingway)"]
            AIRouter["Unified AI Provider Router & Prompt Registry"]
            TaskQueue["Task Queue Engine (Redis + Async Fallback)"]
        end
    end

    subgraph DataTier["Data & State Persistence Tier"]
        Postgres[("PostgreSQL 15 Relational DB<br/>SQLAlchemy 2.0, Alembic 7a2c3d4e5f6a")]
        RedisStore[("Redis 7 In-Memory Cache<br/>Rate Limiting, Session, Task Queue")]
        EncryptedBackups["Automated Encrypted Backups<br/>SHA-256 Checksums, JSON Manifests"]
    end

    subgraph ExternalServices["External LLM Providers & Web Sources"]
        OpenAI["OpenAI (GPT-4o)"]
        Anthropic["Anthropic (Claude 3.5 Sonnet)"]
        Gemini["Google Gemini (1.5 Pro / 2.0 Flash)"]
        Groq["Groq LPU (Llama 3.3 70B)"]
        Fallback["100% Deterministic Offline Fallback"]
        ExternalWeb["External Web / ArXiv / Document Sources"]
    end

    Browser --> ReactApp
    ReactApp --> RUM
    ReactApp -->|REST API / HTTPS| NginxProxy
    NginxProxy -->|/api/*| FastAPI
    NginxProxy -->|Static Assets| ReactApp

    FastAPI --> Middlewares
    Middlewares --> CoreEngines

    SSRFGuard -->|Validated HTTP GET| ExternalWeb
    Extractor --> Postgres
    ResearchEngine --> Postgres
    WritingEngine --> Postgres
    AIRouter --> OpenAI
    AIRouter --> Anthropic
    AIRouter --> Gemini
    AIRouter --> Groq
    AIRouter --> Fallback
    
    FastAPI -->|Port 5432| Postgres
    FastAPI -->|Port 6379| RedisStore
    TaskQueue --> RedisStore
    Postgres --> EncryptedBackups
```

---

## 2. Frontend Architecture (React 18 + TypeScript)

### Component Hierarchy & Route Structure
The client application is built with React 18, TypeScript, and Tailwind CSS, bundled with Vite for fast HMR and optimized chunk splitting.

```
frontend/src/
├── App.tsx                     # Route definitions, protected route wrappers, layouts
├── main.tsx                    # React DOM root initialization with Providers
├── components/
│   ├── auth/                   # ProtectedRoute, TenantGuard
│   ├── common/                 # Button, Input, Modal, Badge, Toast, ConfirmDialog
│   ├── editorial/              # HeadlineEditor, WordCountIndicator, ArticlePreview
│   ├── layout/                 # DashboardLayout, Header, Sidebar, OrganizationSwitcher
│   ├── research/               # LocalLibraryView, ResearchIntelligenceDashboard
│   ├── version_control/        # VersionHistoryPanel, VersionComparison, VersionTimeline
│   └── writing/                # AfforaiCiteModal, ArticleImprovementsPanel, InlineReadabilityLinter
├── context/
│   ├── AuthContext.tsx         # JWT token management, user state, active organization
│   └── ToastContext.tsx        # Dismissible notification queue
├── pages/
│   ├── AuthPage.tsx            # Login, registration, password recovery
│   ├── DashboardPage.tsx       # Metrics overview, recent drafts, active projects
│   ├── ResearchPage.tsx        # Local library, multi-source ingestion, evidence briefs
│   ├── WritingPage.tsx         # Notalx templates, Afforai citation manager, Hemingway linter
│   ├── ObservabilityPage.tsx   # Splunk RUM & Instana APM metrics, token costs
│   └── SettingsPage.tsx        # AI engine selection, API key configuration, prompt registry
├── services/                   # Axios HTTP clients with request/response interceptors
└── types/                      # Strictly typed domain interfaces (Auth, Project, Source, Draft)
```

### Key UI Subsystems

1. **Local Library Hub ([`LocalLibraryView.tsx`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/frontend/src/components/research/LocalLibraryView.tsx)):**
   - Header stats bar tracking Sources, Retrieval Chunks, Supported Formats, and Indexed counts.
   - Pinned vs. Recently Added sources with filter pills (`All`, `Research Paper`, `Document`, `Web URL`).
   - Collapsible Outline (`▶ Outline`), bulleted Key Claims, Curation form (*Title*, *Why saved*, *Tags*), model provenance, and Retrieval Chunks viewer.

2. **Afforai Cite Extension ([`AfforaiCiteModal.tsx`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/frontend/src/components/writing/AfforaiCiteModal.tsx)):**
   - Reference search and multi-select checkboxes.
   - Removable citation pills (`Garcia, M. L. (2002) ×`, `Lee, K. W. (1999) ×`).
   - Integrated AI Research Assistant with prompt input supporting `@` citation mentions and one-click draft insertion.

3. **Article Improvements Panel ([`ArticleImprovementsPanel.tsx`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/frontend/src/components/writing/ArticleImprovementsPanel.tsx)):**
   - Visual quality progress bar reflecting calculated Flesch Reading Ease score.
   - Tabbed metrics (`SEO`, `Readability`, `Tone`).
   - Real-time statistics: Sentence count, reading time in seconds, word count.
   - One-click sentence rewrite cards.

4. **Inline Readability Linter ([`InlineReadabilityLinter.tsx`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/frontend/src/components/writing/InlineReadabilityLinter.tsx)):**
   - Real-time prose highlight overlay: Purple (hard-to-read sentences), Blue (passive voice), Amber (complex vocabulary).
   - Interactive popover tooltip on hover/click with direct `[Simplify]` action.

---

## 3. Backend Architecture & Request Lifecycle

FastAPI serves as the core asynchronous ASGI application, structured around clean dependency injection and modular routers.

```mermaid
sequenceDiagram
    autonumber
    actor Client as React Client (Axios)
    participant Nginx as Nginx Proxy
    participant MW as Middleware Pipeline
    participant Router as API Route Handler
    participant Service as Domain Service Layer
    participant DB as PostgreSQL 15 (SQLAlchemy)
    participant AI as AI Router / Fallback

    Client->>Nginx: HTTP POST /api/v1/writing/analyze (Bearer Token)
    Nginx->>MW: Forward Request with X-Request-Id
    MW->>MW: Enforce Security Headers & Rate Limit
    MW->>MW: Authenticate JWT & Resolve Active Organization
    MW->>Router: Dispatch Request with Injected Session & Org
    Router->>Service: Execute Writing Quality Audit
    Service->>Service: Compute 6 Deterministic Quality Checks
    Service->>AI: Synthesize Rewrite Proposals (or Fallback)
    AI-->>Service: Validated Structured Proposal
    Service->>DB: Record Analytics Event & Update Draft
    DB-->>Service: Transaction Committed
    Service-->>Router: Pydantic Response Model
    Router-->>MW: Format JSON Response
    MW-->>Nginx: Inject X-Process-Time-Ms
    Nginx-->>Client: HTTP 200 OK + JSON Payload
```

---

## 4. Multi-Tenant Organization Isolation

Tenancy isolation is enforced at the database, session, and dependency injection layers:

```mermaid
classDiagram
    class Organization {
        +UUID id
        +string name
        +string slug
        +datetime created_at
    }

    class OrganizationMembership {
        +UUID id
        +UUID organization_id
        +UUID user_id
        +OrgRole role
    }

    class TenantScopedBase {
        +UUID organization_id
        +UUID created_by_user_id
        +datetime created_at
        +datetime updated_at
    }

    class ResearchProject {
        +UUID id
        +string title
        +string description
        +string status
    }

    class WritingDraft {
        +UUID id
        +string title
        +text original_content
        +text revised_content
    }

    Organization "1" -- "*" OrganizationMembership : has
    Organization "1" -- "*" TenantScopedBase : owns
    TenantScopedBase <|-- ResearchProject
    TenantScopedBase <|-- WritingDraft
```

- **Row-Level Organization Scoping:** All tenant entities inherit from `TenantScopedBase`, enforcing non-nullable `organization_id` columns with database indexes.
- **Dependency Guard (`get_active_organization`):** Resolves the caller's organization from `X-Organization-Id` header or defaults to the user's primary membership.
- **Tenant Enumeration Defense:** If an authenticated user attempts to access an entity belonging to another organization, the API returns `HTTP 404 Not Found` rather than `403 Forbidden`, preventing resource enumeration attacks.

---

## 5. Research Ingestion, Extraction & Claim Verification Pipeline

```mermaid
flowchart TD
    A[Raw URL or File Submission] --> B{URL or File?}
    
    B -->|URL Ingestion| C[SSRF Validation Engine]
    C --> C1[Check Scheme: HTTP/HTTPS Only]
    C1 --> C2[Resolve DNS &amp; Check IP against CIDR Blacklist]
    C2 --> C3[Block 127.0.0.1, 10.0.0.0/8, 169.254.169.254]
    C3 --> C4[Fetch with 10s Timeout &amp; 2MB Size Limit]
    C4 --> D[Trafilatura Main Text Extraction]
    D -->|Failure?| D1[BeautifulSoup4 DOM Fallback]
    
    B -->|File Ingestion| E[File Upload Guard]
    E --> E1[Verify MIME Magic Bytes &amp; File Extension]
    E1 --> E2[Enforce 10MB Maximum File Limit]
    E2 --> E3[Extract Text: PyPDF / python-docx / UTF-8]

    D1 --> F[Text Normalization &amp; SHA-256 Hashing]
    E3 --> F
    F --> G{Duplicate Content Hash in Org?}
    G -->|Yes| G1[Reject Ingestion: Duplicate Source Detected]
    G -->|No| H[Semantic Chunking: 150-Word Windows]
    H --> I[UNU Claim Extraction Engine]
    I --> J[Epistemic Classification]
    J --> J1[Verified Facts]
    J --> J2[Editorial Analysis]
    J --> J3[Speculative Claims]
    J1 & J2 & J3 --> K[10-Section Structured Research Brief]
```

### 5-Tier Claim Verification Taxonomy
Each factual statement in research briefs and editorial drafts is evaluated across five distinct epistemic states:
1. **`SUPPORTED`:** Claim is directly corroborated by verbatim quotes in primary sources.
2. **`PARTIALLY_SUPPORTED`:** Core claim is accurate, but scope or numerical parameters are broader than source evidence.
3. **`UNSUPPORTED`:** No matching factual passage found in any ingested source document.
4. **`CONTRADICTED`:** Opposing source documents explicitly refute the assertion.
5. **`NOT_VERIFIABLE`:** Claim is an inherently subjective opinion or unmeasurable prediction.

---

## 6. Writing Assistant, Quality Linters & Non-Destructive Rewriting

The Writing Assistant implements a deterministic quality auditing engine alongside an AI selection-rewrite service:

```mermaid
flowchart LR
    subgraph InputProse["Input Draft Prose"]
        RawDraft["Raw Article Draft"]
    end

    subgraph DeterministicAuditor["6-Check Deterministic Hemingway Auditor"]
        Check1["Sentence Length: Flags &gt;25 words"]
        Check2["Passive Voice: Flags auxiliary + participle"]
        Check3["Filler Phrases: Flags 'in order to', etc."]
        Check4["Jargon Detector: Flags uncontextualized terms"]
        Check5["Repetition: Flags adjacent repeated openers"]
        Check6["Flesch Score: Computes exact reading ease"]
    end

    subgraph NonDestructiveEngine["Non-Destructive Replacement Engine"]
        TargetSpan["Isolate Target Sentence Bounds"]
        PreserveContext["Preserve Surrounding Prose &amp; Citations"]
        ApplyRewrite["Apply Accepted Rewrite to Bounded Span"]
        VersionSnapshot["Record Immutable Version Snapshot"]
    end

    RawDraft --> DeterministicAuditor
    DeterministicAuditor --> TargetSpan
    TargetSpan --> PreserveContext
    PreserveContext --> ApplyRewrite
    ApplyRewrite --> VersionSnapshot
```

---

## 7. AI Provider Abstraction & Offline Fallback Strategy

The application integrates external AI providers through a unified interface (`AIRouter`) with built-in retry backoff, prompt versioning, and zero-downtime offline fallback:

```mermaid
flowchart TD
    Request[AI Operation Request] --> Router{Select Provider}
    Router -->|Groq Configured| Groq[Groq LPU API]
    Router -->|OpenAI Configured| OpenAI[OpenAI GPT-4o]
    Router -->|Anthropic Configured| Anthropic[Anthropic Claude 3.5]
    Router -->|Gemini Configured| Gemini[Google Gemini 2.0]
    Router -->|Offline / No Keys / API Outage| Fallback[100% Deterministic Offline Fallback]

    Groq -->|Timeout / Rate Limit| Fallback
    OpenAI -->|Timeout / Rate Limit| Fallback
    Anthropic -->|Timeout / Rate Limit| Fallback
    Gemini -->|Timeout / Rate Limit| Fallback

    Fallback --> Output[Structured, Validated Pydantic Response]
    Groq & OpenAI & Anthropic & Gemini --> Validate[JSON Schema Validation]
    Validate --> Output
```

---

## 8. SRE Health Probes & Observability Architecture

To ensure operational excellence in production environments, the system exposes dedicated SRE health endpoints and comprehensive APM observability:

- **Liveness Probe (`GET /health/live`):** Returns HTTP 200 `{"status": "alive"}` to indicate process execution.
- **Readiness Probe (`GET /health/ready`):** Executes `SELECT 1` on PostgreSQL and probes Redis connectivity. Returns `db_latency_ms` and returns HTTP 503 if dependencies are degraded.
- **Startup Probe (`GET /health/startup`):** Validates database schema migrations and configuration invariants.
- **APM Telemetry Dashboard ([`ObservabilityPage.tsx`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/frontend/src/pages/ObservabilityPage.tsx)):** Mirrors Splunk RUM and Instana APM metrics:
  - Real User Monitoring: Page views, JavaScript errors, Core Web Vitals (LCP < 2.5s).
  - Backend Telemetry: Calls vs. errors, average latency, P50/P90/P95/P99 latency distribution, tier processing breakdown (Database, HTTP, Task Queue), and exact $USD token cost accounting.

---

## 9. 3-Tier Production Container Architecture & Internal DNS

In production, all services communicate across an isolated Docker bridge network (`editorial-network`) using internal container DNS service names:

```
External Traffic (HTTPS / Port 80/443)
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Nginx Reverse Proxy Container (`frontend`)             │
│ Routes `/api/*` to `backend:8000`                      │
│ Serves compiled React assets on `/`                    │
└──────────────────────┬─────────────────────────────────┘
                       │ Internal Docker DNS Resolution
                       ▼
┌────────────────────────────────────────────────────────┐
│ FastAPI Application Container (`backend`)              │
│ Runs Uvicorn with 4 workers under non-root UID 10001   │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
   Port 5432   ▼              Port 6379   ▼
┌────────────────────────┐  ┌────────────────────────────┐
│ PostgreSQL Container   │  │ Redis Container (`redis`)  │
│ Named volume: `db-data`│  │ Persistent cache & queue   │
└────────────────────────┘  └────────────────────────────┘
```
