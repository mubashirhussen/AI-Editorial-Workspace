# System Architecture: AI Editorial Workspace

**System:** AI Editorial Workspace  
**Assignment:** Forward Deployed Engineer (FDE) Intern Assignment  
**Publication:** *This Week in AI*  
**Author:** Mubashir Hussain  

---

## 1. System Architecture Overview

The **AI Editorial Workspace** is a decoupled full-stack platform consisting of a React single-page application, an asynchronous FastAPI REST backend, a relational persistence layer managed via SQLAlchemy 2.0 and Alembic, and an evidence-grounded AI integration pipeline with deterministic offline fallbacks.

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Client (React 18 + Vite)"]
        UI["Tailwind CSS UI / Dashboard"]
        State["Client State & React Router"]
        Axios["Axios API Client (Interceptor & Timeout 30s)"]
        UI --> State --> Axios
    end

    subgraph SecurityBoundary["Security & Transport Boundary"]
        CORS["CORS Middleware (Allowed Origins)"]
        SSRF["SSRF Defense (Socket DNS Resolution)"]
    end

    subgraph APILayer["Backend REST API (FastAPI)"]
        Router["API Router (/api/v1)"]
        ProjCtrl["Projects Controller"]
        SourceCtrl["Sources Controller"]
        ResearchCtrl["Research Controller"]
        WritingCtrl["Writing Controller"]
        EditorialCtrl["Editorial Controller"]
        HealthCtrl["Health & Metrics Controller"]

        Router --> ProjCtrl
        Router --> SourceCtrl
        Router --> ResearchCtrl
        Router --> WritingCtrl
        Router --> EditorialCtrl
        Router --> HealthCtrl
    end

    subgraph ServiceLayer["Business Logic & Service Layer"]
        ExtService["Extraction Service (Trafilatura / BS4)"]
        EpistemicEngine["Epistemic Classifier (Facts vs. Analysis)"]
        WritingAnalyzer["Writing Analyzer (6 Deterministic Checks)"]
        MetricsService["Metrics Service (Flesch Formula)"]
        SuggestionEngine["Suggestion Engine (Safe String Replacement)"]
        EditorialService["Editorial Service (300-500w & Citations)"]
        ExportService["Export Service (MD, PlainText, HTML5 Escaped)"]
        AIService["AI Service Wrapper (OpenAI-compatible)"]
        DeterministicFallback["Deterministic Heuristic Fallback Engine"]
    end

    subgraph PersistenceLayer["Relational Database (SQLAlchemy 2.0)"]
        Engine["Engine (SQLite / PostgreSQL)"]
        Alembic["Alembic Version Tracking"]
        Tables[("7 Normalized Tables")]
        Engine --- Alembic
        Engine --> Tables
    end

    Axios -->|HTTPS JSON| CORS --> Router
    SourceCtrl --> SSRF --> ExtService
    ResearchCtrl --> EpistemicEngine
    ResearchCtrl --> AIService
    ResearchCtrl --> DeterministicFallback
    WritingCtrl --> WritingAnalyzer
    WritingCtrl --> MetricsService
    WritingCtrl --> SuggestionEngine
    EditorialCtrl --> EditorialService
    EditorialService --> AIService
    EditorialService --> DeterministicFallback
    EditorialService --> ExportService

    ProjCtrl & SourceCtrl & ResearchCtrl & WritingCtrl & EditorialCtrl & HealthCtrl --> Engine
```

---

## 2. Frontend-to-Backend Communication & API Organization

The frontend communicates with the backend exclusively via typed JSON requests executed by a centralized Axios client (`frontend/src/services/api.ts`).

### Communication Characteristics
* **Base URL Resolution:** Resolved dynamically from `import.meta.env.VITE_API_BASE_URL` with a default local fallback to `http://localhost:8000/api/v1`.
* **Bounded Timeout:** All outbound requests have a strict 30-second timeout to prevent UI freezes during heavy operations.
* **Global Error Interception:** Axios response interceptors parse HTTP 400, 404, 422, and 500 error payloads (including Pydantic validation error lists) and display user-friendly toast notifications via Sonner.

### API Endpoint Hierarchy

| Route Prefix | Domain | Primary Responsibilities |
| :--- | :--- | :--- |
| `/api/v1/health` | System | Health check, live database ping (`SELECT 1`), and active AI engine mode. |
| `/api/v1/projects` | Projects | CRUD lifecycle for investigations, pagination, and status tracking. |
| `/api/v1/sources` | Sources | Ingestion (URL/Text), SSRF validation, Trafilatura extraction, and epistemic claim analysis. |
| `/api/v1/research` | Research | Multi-source triangulation, consensus/divergence synthesis, and newsletter angle generation. |
| `/api/v1/writing` | Writing | 6 deterministic writing checks, readability scoring, and non-destructive suggestion replacement. |
| `/api/v1/editorial` | Editorial | 5 headline formulas, 300–500 word draft generation, inline citation mapping, and exports. |

---

## 3. Database Entity-Relationship Model

The relational persistence layer uses 7 normalized tables mapped via SQLAlchemy 2.0 with foreign key cascades:

```mermaid
erDiagram
    RESEARCH_PROJECTS ||--o{ SOURCES : "contains (1:N)"
    RESEARCH_PROJECTS ||--o{ RESEARCH_BRIEFS : "synthesizes (1:N)"
    RESEARCH_PROJECTS ||--o{ WRITING_DRAFTS : "generates (1:N, nullable)"
    RESEARCH_PROJECTS ||--o{ EDITORIAL_OUTPUTS : "publishes (1:N)"

    SOURCES ||--o| SOURCE_ANALYSES : "evaluates (1:1)"
    WRITING_DRAFTS ||--o{ WRITING_SUGGESTIONS : "audits (1:N)"
    WRITING_DRAFTS ||--o| EDITORIAL_OUTPUTS : "linked_to (1:1, nullable)"

    RESEARCH_PROJECTS {
        string id PK
        string title
        string name
        text description
        string status
        datetime created_at
        datetime updated_at
    }

    SOURCES {
        string id PK
        string project_id FK
        string title
        string url
        string source_type
        text raw_content
        text extracted_content
        string extraction_status
        datetime created_at
    }

    SOURCE_ANALYSES {
        string id PK
        string source_id FK
        text summary
        json key_points
        json reported_facts
        json analysis
        json founder_implications
        json uncertainties
        json newsletter_angles
    }

    RESEARCH_BRIEFS {
        string id PK
        string project_id FK
        string title
        text executive_summary
        json key_developments
        json strategic_implications
        json newsletter_angles
        json source_references
        json brief_content
        json evidence
        json recommended_angle
        datetime created_at
    }

    WRITING_DRAFTS {
        string id PK
        string project_id FK
        string title
        text original_content
        text revised_content
        int word_count
        float readability_score
        string status
        datetime created_at
        datetime updated_at
    }

    WRITING_SUGGESTIONS {
        string id PK
        string draft_id FK
        string category
        string severity
        text original_text
        text suggested_text
        text suggested_rewrite
        text explanation
        string reason
        float confidence
        string status
        datetime created_at
    }

    EDITORIAL_OUTPUTS {
        string id PK
        string project_id FK
        string draft_id FK
        string headline
        text content
        int word_count
        json source_references
        string status
        datetime created_at
        datetime updated_at
    }
```

### Cascade & Integrity Guarantees
* **`CASCADE` Deletion:** Deleting a `ResearchProject` automatically purges child `sources`, `source_analyses`, `research_briefs`, and `editorial_outputs`. Deleting a `WritingDraft` cascades to its `writing_suggestions`.
* **`SET NULL` Preservation:** Deleting a `ResearchProject` retains standalone `writing_drafts` by nullifying `project_id`, protecting editorial work from accidental project deletion.

---

## 4. AI Request & Response Lifecycle

The AI integration layer enforces prompt fencing, schema validation, and defensive fallback:

```mermaid
sequenceDiagram
    autonumber
    actor Editor as User / Frontend
    participant Service as Editorial / Research Service
    participant Guard as Prompt Guard & Fencer
    participant AI as AIService (OpenAI Provider)
    participant Validator as Pydantic Schema Validator
    participant Fallback as Deterministic NLP Engine
    participant DB as Relational Database

    Editor->>Service: Trigger Generation / Synthesis Request
    Service->>Guard: Enclose source texts in <source_data> XML tags
    Guard-->>Service: Sanitized, prompt-fenced payload

    alt AI_API_KEY Configured & Service Available
        Service->>AI: POST /chat/completions (response_format: json_object)
        alt Successful Response Received
            AI-->>Validator: Raw JSON String
            Validator->>Validator: Validate against Pydantic schema
            Validator-->>Service: Structured Domain Model
        else Provider Timeout / 429 Rate Limit / Invalid JSON
            AI-->>Service: Exception / Error
            Service->>Fallback: Divert to Deterministic Fallback Engine
            Fallback-->>Service: Structured Domain Model (Heuristic Extraction)
        end
    else No API Key Configured (Offline Mode)
        Service->>Fallback: Engage Deterministic Heuristic Engine
        Fallback-->>Service: Structured Domain Model
    end

    Service->>DB: Persist validated model record
    DB-->>Service: Confirmed Record
    Service-->>Editor: HTTP 200 OK + JSON Response
```

---

## 5. Source Evidence Validation & Classification

The Research Assistant separates marketing claims from empirical reality through a three-stage epistemic validation pipeline:

1. **Extraction & Excerpt Isolation:** Trafilatura extracts clean body text. Sentence tokenization isolates atomic factual assertions.
2. **Epistemic Classification:**
   * **Verified Facts:** Empirical benchmarks (e.g. *"79.8% on AIME 2024"*), hardware clusters, pricing, and dates.
   * **Editorial Analysis:** Logical deductions regarding inference costs, architectural choices, and market implications.
   * **Speculation & Projections:** Forward-looking roadmap claims (e.g. *"will achieve human parity in 12 months"*). Flagged with warning markers.
3. **Traceability Binding:** Every item in the research brief contains an explicit `source_id`, canonical URL, and verbatim extracted quote. If a claim cannot be verified against the ingested text, it is excluded.

---

## 6. Writing Suggestion Acceptance Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Writing Analysis (6 Checks)
    
    state PENDING {
        [*] --> Evaluated
        Evaluated: Highlighted in Editor
        Evaluated: Metrics Displayed
    }

    PENDING --> ACCEPTED: User clicks "Accept"
    PENDING --> REJECTED: User clicks "Reject"

    state ACCEPTED {
        [*] --> CheckMatch: String Match in revised_content
        CheckMatch --> ExactReplace: Match found
        CheckMatch --> StaleError: Match not found (Stale)
        ExactReplace --> UpdateDraft: Apply surgical replacement
        UpdateDraft --> RecalcMetrics: Recompute Flesch & word count
        RecalcMetrics --> CommitDB: Update revised_content in DB
    }

    state REJECTED {
        [*] --> LogDismissal: Mark suggestion status REJECTED
        LogDismissal --> DraftUntouched: revised_content remains unchanged
    }

    ACCEPTED --> [*]
    REJECTED --> [*]
```

### Non-Destructive Replacement Safety
The function `replace_text_safely` guarantees:
1. **Targeted Boundary Isolation:** It replaces only the target substring within `revised_content`. Neighboring sentences, paragraphs, and inline citations (`[1]`) are preserved.
2. **Stale Suggestion Detection:** If previous edits altered the target text, the function returns an error without performing ambiguous substitutions.
3. **Immutable Baseline:** `original_content` is never modified during suggestion acceptance.

---

## 7. Error Handling & Failure Paths

| Failure Scenario | Component | Detection & Mitigation |
| :--- | :--- | :--- |
| **SSRF Ingestion Attack** | `security.py` | DNS socket resolution catches private IPs (`10.x`, `127.x`, `169.254.x`) before request. Returns HTTP 400. |
| **Blocked / Paywalled URL** | `extraction_service.py` | Caught via HTTP status or timeout (12s). Returns HTTP 400 prompting manual raw text paste. |
| **AI Provider Outage / 429** | `ai_service.py` | Catches `APIConnectionError` or `RateLimitError`. Automatically engages deterministic fallback engine. |
| **Malformed AI JSON Output** | `ai_service.py` | Regex fallback isolates JSON substring `{...}`; Pydantic parses or triggers deterministic synthesis. |
| **XSS in HTML Export** | `export_service.py` | All dynamic fields run through `html.escape()`. Malicious tags are entity-escaped. |
| **Database Transaction Failure**| `database.py` | Scoped sessions execute `db.rollback()` on exception, preventing locked tables or corrupted states. |

---

## 8. Technology Stack Justifications

### 1. Frontend: React 18 + TypeScript + Vite
* **Component-Driven State:** An editorial workspace requires complex UI states (live suggestion cards, side-by-side diff viewers, active citations, and real-time metric indicators). React's component hierarchy manages these transitions cleanly.
* **Type Safety:** TypeScript enforces domain contracts between backend schemas and frontend components, preventing runtime property mismatch errors.
* **Sub-Second Build Velocity:** Vite provides instantaneous Hot Module Replacement (HMR) and optimized production compilation (2,281 modules in under 10 seconds).

### 2. Backend: Python + FastAPI + Uvicorn
* **Asynchronous Non-Blocking I/O:** Content extraction involves concurrent external HTTP calls. FastAPI's `async/await` pipeline prevents worker thread starvation.
* **Pydantic v2 Schema Enforcement:** Automatic request validation, response serialization, and OpenAPI Swagger documentation generation.
* **Python NLP Ecosystem:** Native access to robust text extraction libraries (`trafilatura`, `beautifulsoup4`) and string processing algorithms.

### 3. Persistence: SQLAlchemy 2.0 ORM + Alembic
* **Relational Integrity:** Editorial workflows require strict entity associations (projects $\rightarrow$ sources $\rightarrow$ analyses $\rightarrow$ briefs $\rightarrow$ drafts $\rightarrow$ suggestions $\rightarrow$ outputs). Relational foreign keys and cascade rules prevent data corruption.
* **Migration Versioning:** Alembic ensures reproducible schema versioning across development, test, and production environments.

### 4. Database Engine: Dual SQLite & PostgreSQL Support
* **Zero-Friction Local Evaluation:** SQLite requires no daemon setup or external credentials, allowing evaluators to run all 25 automated tests instantly.
* **Production Scalability:** The application automatically connects to PostgreSQL via `DATABASE_URL` in production, supporting connection pooling (`pool_size=10, max_overflow=20`) and persistent multi-tenant scalability on cloud providers like Render or Supabase.

