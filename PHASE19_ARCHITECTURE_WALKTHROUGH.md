# Phase 19: Technical Architecture Walkthrough & System Defense

**Project:** AI Editorial Workspace  
**Document Purpose:** Architectural Defense & Deep Technical Specification for FDE Assessment  
**Author:** Forward Deployed Engineer  
**Status:** **VERIFIED PRODUCTION ARCHITECTURE**

---

## 1. High-Level System Architecture

The AI Editorial Workspace is structured as a decoupled, multi-tenant, cloud-ready web application adhering to clean architecture principles.

```mermaid
graph TD
    subgraph ClientLayer["Client Layer (Frontend)"]
        SPA["React 18 SPA (TypeScript + Vite)"]
        Router["React Router v6"]
        State["Contexts (Auth, Health, Org, Theme)"]
        UI["Tailwind CSS + Lucide Icons + Recharts"]
    end

    subgraph GatewayLayer["Gateway & Ingress"]
        Nginx["Nginx Reverse Proxy / Port 80"]
        ViteDev["Vite Dev Server / Port 5173"]
    end

    subgraph ServiceLayer["Application Service Layer (FastAPI)"]
        API["FastAPI App (Python 3.10)"]
        Middleware["Security, CORS & X-Request-ID Middleware"]
        AuthModule["JWT Auth & PBKDF2 Password Hashing"]
        SSRFModule["SSRF URL Validator & Content Fetcher"]
        AuditEngine["Deterministic Linguistic & Style Auditor"]
        AIRouter["AI Provider Router & Fallback Engine"]
        TelemetryModule["Observability & Request Telemetry"]
    end

    subgraph DataLayer["Persistence & Storage Layer"]
        SQLA["SQLAlchemy 2.0 ORM Engine"]
        Alembic["Alembic Migration Manager (Head 7a2c3d4e5f6a)"]
        DB[("Relational Database (SQLite / PostgreSQL)")]
    end

    subgraph ExternalServices["External LLM Providers"]
        Groq["Groq Cloud LPU (LLaMA-3 / Mixtral)"]
        OpenAI["OpenAI API (GPT-4o / GPT-4o-mini)"]
    end

    SPA --> GatewayLayer
    GatewayLayer --> API
    API --> Middleware
    Middleware --> AuthModule
    Middleware --> SSRFModule
    Middleware --> AuditEngine
    Middleware --> AIRouter
    Middleware --> TelemetryModule
    AIRouter --> ExternalServices
    AIRouter -. Fallback .-> AuditEngine
    API --> SQLA
    SQLA --> Alembic
    SQLA --> DB
```

---

## 2. End-to-End Editorial Processing Lifecycle

The following sequence diagram illustrates the lifecycle from multi-source research ingestion to verified editorial publication.

```mermaid
sequenceDiagram
    autonumber
    actor Editor as Editorial Lead
    participant FE as React Frontend
    participant API as FastAPI Ingress
    participant Guard as SSRF Guardrail
    participant AI as AI Router / Fallback
    participant DB as Relational Database

    Editor->>FE: Ingest 3 Primary Sources (URLs / PDFs)
    FE->>API: POST /api/v1/research/sources
    API->>Guard: Validate Hostname & DNS Resolution
    Guard-->>API: Safe IP (Non-Private CIDR)
    API->>API: Parse Text & Extract Metadata
    API->>DB: INSERT INTO source_documents
    DB-->>FE: HTTP 201 Created (Sources Linked)

    Editor->>FE: Trigger "Generate Research Brief"
    FE->>API: POST /api/v1/research/projects/{id}/synthesize
    API->>AI: Synthesize Claims, Facts vs Speculation
    alt External LLM Available
        AI->>AI: Call Groq / OpenAI Provider
    else Rate Limited or No Key
        AI->>AI: Execute Local Deterministic Heuristics
    end
    AI->>DB: INSERT INTO research_briefs
    DB-->>FE: HTTP 200 OK (Structured Brief with Citations)

    Editor->>FE: Compose & Audit Draft
    FE->>API: POST /api/v1/writing/audit
    API->>API: Run 9 Deterministic Auditing Checks
    API-->>FE: Return Scores (Flesch, Grade, Passive, Jargon)

    Editor->>FE: Finalize & Publish Edition
    FE->>API: POST /api/v1/editorial/publish
    API->>DB: Record Edition & Create Immutable Audit Log
    DB-->>FE: HTTP 200 OK (Published Newsletter Edition)
```

---

## 3. Database Schema & Entity Relationships

The relational persistence schema is managed via SQLAlchemy ORM and versioned via Alembic migrations.

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : "employs"
    ORGANIZATIONS ||--o{ ORGANIZATION_MEMBERSHIPS : "contains"
    USERS ||--o{ ORGANIZATION_MEMBERSHIPS : "belongs to"
    ORGANIZATIONS ||--o{ RESEARCH_PROJECTS : "owns"
    RESEARCH_PROJECTS ||--o{ SOURCE_DOCUMENTS : "includes"
    RESEARCH_PROJECTS ||--o{ SOURCE_ANALYSES : "evaluates"
    RESEARCH_PROJECTS ||--o{ RESEARCH_BRIEFS : "synthesizes"
    RESEARCH_PROJECTS ||--o{ WRITING_DRAFTS : "develops"
    WRITING_DRAFTS ||--o{ EDITORIAL_VERSIONS : "versions"
    WRITING_DRAFTS ||--o{ EDITORIAL_OUTPUTS : "publishes"
    ORGANIZATIONS ||--o{ AUDIT_LOGS : "records"

    ORGANIZATIONS {
        uuid id PK
        string name
        string slug UK
        datetime created_at
    }

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string role
        boolean is_active
    }

    RESEARCH_PROJECTS {
        uuid id PK
        uuid organization_id FK
        string title
        string status
        string target_audience
    }

    SOURCE_DOCUMENTS {
        uuid id PK
        uuid project_id FK
        string title
        string url
        string source_type
        text raw_content
    }

    RESEARCH_BRIEFS {
        uuid id PK
        uuid project_id FK
        json synthesis_data
        json facts_vs_speculation
        json knowledge_graph
    }

    WRITING_DRAFTS {
        uuid id PK
        uuid project_id FK
        string title
        text content
        float quality_score
        float flesch_score
    }

    EDITORIAL_OUTPUTS {
        uuid id PK
        uuid draft_id FK
        string edition_number
        string status
        datetime published_at
    }
```

---

## 4. Architectural Deep Dives

### 4.1 Autonomous AI Router & Fallback Subsystem
- **Provider Interface:** `backend/app/services/ai_service.py` defines an abstract interface `AIProviderBase` implemented by `GroqProvider`, `OpenAIProvider`, and `DeterministicFallbackEngine`.
- **Dynamic Failover Policy:** 
  $$\text{Request} \longrightarrow \text{Primary LLM (Groq LPU)} \xrightarrow{\text{429 / 503 / Timeout}} \text{Secondary (OpenAI)} \xrightarrow{\text{Failure}} \text{Local Heuristic Engine}$$
- **Zero Runtime Downtime:** The fallback engine utilizes regular expressions, linguistic keyword frequency, statistical sentence tokenization, and deterministic citation mapping to produce structured briefs and drafts even during complete cloud connectivity loss.

### 4.2 Security Architecture & Hardening
- **SSRF Guardrail:** Validates URL hostnames using `socket.getaddrinfo()` before any HTTP fetch. Blocks loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), private RFC 1918 blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and carrier-grade NAT (`100.64.0.0/10`).
- **Authentication & Authorization:** Implements stateless JWT Bearer token authentication signed via HMAC-SHA256 with 60-minute token expiration. Password storage uses PBKDF2 with SHA-256 and salt.
- **Tenant Isolation:** Enforced via scoped queries in database repositories using `organization_id` derived from verified membership associations.

### 4.3 Deterministic Linguistic Auditing Engine
- **Formula Accuracy:** Computes Flesch Reading Ease using the standard formula:
  $$\text{FRE} = 206.835 - 1.015 \left(\frac{\text{total words}}{\text{total sentences}}\right) - 84.6 \left(\frac{\text{total syllables}}{\text{total words}}\right)$$
- **Flesch-Kincaid Grade Level:**
  $$\text{FKGL} = 0.39 \left(\frac{\text{total words}}{\text{total sentences}}\right) + 11.8 \left(\frac{\text{total syllables}}{\text{total words}}\right) - 15.59$$
- **Edge-Case Tolerance:** Gracefully handles empty inputs, single-word strings, markdown headers, and code snippets without division-by-zero exceptions.

### 4.4 Observability, Telemetry & Health Probes
- **Structured Logging:** Emits JSON log records with ISO-8601 timestamps, log level, module name, and correlated `request_id`.
- **Request Tracing:** The `RequestTracingMiddleware` inspects incoming `X-Request-ID` or generates a UUID4, binding it to FastAPI `request.state` and returning it in the HTTP response header.
- **Health Probes:**
  - `GET /health/live`: Unauthenticated liveness check for Kubernetes/container orchestration.
  - `GET /health/ready`: Dependency readiness probe evaluating live database connectivity.
  - `GET /health`: Comprehensive telemetry status returning uptime, database diagnostics, active AI engine mode, and token metrics.

---

## 5. Deployment & Production Topology

```mermaid
graph LR
    subgraph Host["Production Container Host"]
        subgraph IngressContainer["Frontend & Ingress (Nginx:Alpine)"]
            StaticFiles["Pre-compiled SPA (/usr/share/nginx/html)"]
            ProxyConfig["Reverse Proxy Engine"]
        end

        subgraph BackendContainer["Application Backend (Python:3.10-Slim)"]
            Uvicorn["Uvicorn ASGI Server"]
            FastAPIApp["FastAPI REST API"]
        end

        subgraph StorageVolume["Persistent Storage"]
            DBVolume[("Persistent SQLite / Postgres DB")]
        end
    end

    Client([Internet User]) -->|HTTP Port 80| ProxyConfig
    ProxyConfig -->|Static Assets| StaticFiles
    ProxyConfig -->|Proxy /api & /health| Uvicorn
    Uvicorn --> FastAPIApp
    FastAPIApp --> DBVolume
```

- **Multi-Stage Builds:** The frontend uses a two-stage Dockerfile (`node:18-alpine` builder followed by lightweight `nginx:alpine` runner).
- **Zero-Secret Containers:** Container images do not package hardcoded credentials; configuration is injected dynamically through environment variables or mounted secrets.
