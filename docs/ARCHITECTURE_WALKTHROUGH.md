# AI Editorial Workspace — Architecture Defense & Technical Walkthrough

**Architecture Paradigm:** Decoupled Asynchronous Microservices / Clean Layered Architecture  
**Primary Frameworks:** FastAPI (ASGI), React 18 (TypeScript), SQLAlchemy 2.0 (PostgreSQL/SQLite)  
**Security Model:** Defense-in-Depth (Socket DNS SSRF, Bcrypt, AES-128 Fernet, Sliding Rate Limiting)  

---

## 1. Complete System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Client Tier (Browser)"]
        SPA["React 18 / TypeScript SPA"]
        Axios["Axios Interceptor Client\n(JWT Bearer, X-Request-ID)"]
        Router["React Router v7\n(/dashboard, /research, /writing, /editorial)"]
    end

    subgraph Gateway["Reverse Proxy & Gateway"]
        Nginx["Nginx Alpine Container (Port 80)\n• Static File Serving & Gzip\n• Security Headers (CSP, X-Frame)\n• Reverse Proxy (/api/* -> Backend)"]
    end

    subgraph Backend["Application Server (FastAPI / Port 8000)"]
        RateLimit["InMemoryRateLimiterMiddleware\n(120 req/min/IP)"]
        ObsMiddleware["ObservabilityMiddleware\n(X-Request-ID Correlation, Latency Logging)"]
        AuthMiddleware["JWT Authentication & RBAC Filter"]
        
        subgraph Routers["API v1 Routers"]
            R_Auth["/auth"]
            R_Health["/health"]
            R_Research["/research & /sources"]
            R_Writing["/writing & /styles"]
            R_Editorial["/editorial & /editorial-review"]
            R_Versions["/documents/{type}/{id}/versions"]
        end

        subgraph ServiceLayer["Domain Service Layer"]
            S_Extraction["extraction_service.py\n• Socket DNS SSRF Guard\n• Trafilatura / BS4 / PDF / DOCX"]
            S_Epistemic["research_service.py\n• Facts vs Analysis vs Speculation"]
            S_Writing["writing_analysis_service.py\n• 6 Deterministic Quality Checks\n• Flesch Reading Ease Formula\n• replace_text_safely()"]
            S_Editorial["editorial_service.py\n• 300-500w Constrained Drafter\n• Numbered Citations [1], [2]"]
            S_AIRouter["ai/router.py & adapters\n• Intelligent Provider Router\n• Groq / OpenAI / Anthropic / Gemini\n• Deterministic Offline Rule Fallback"]
        end
    end

    subgraph Persistence["Persistence & Security Tier"]
        DB[(PostgreSQL 15 / SQLite\n• 34 Relational ORM Tables\n• Connection Pooling: pool_size=10\n• Alembic Head: 3b7c9f1e8a2d)]
        Backup["backup_db.py\n(SHA-256 Verified Snapshots)"]
        Crypto["Fernet AES-128 Encryption\n(Encrypted API Keys at Rest)"]
    end

    subgraph External["External Cloud & AI Ecosystem"]
        Groq["Groq LPU (GPT-OSS-20B)"]
        OpenAI["OpenAI (GPT-4o / o1)"]
        Anthropic["Anthropic (Claude 3.5 Sonnet)"]
        Gemini["Google Gemini (1.5 Flash/Pro)"]
        WebTargets["External Public Web Sources"]
    end

    %% Client Interactions
    SPA --> Axios
    Axios --> Nginx
    Nginx --> RateLimit
    RateLimit --> ObsMiddleware
    ObsMiddleware --> AuthMiddleware
    AuthMiddleware --> Routers

    %% Service Layer Connections
    R_Research --> S_Extraction
    R_Research --> S_Epistemic
    R_Writing --> S_Writing
    R_Editorial --> S_Editorial
    
    S_Extraction --> WebTargets
    S_Epistemic --> S_AIRouter
    S_Editorial --> S_AIRouter
    
    S_AIRouter --> Groq
    S_AIRouter --> OpenAI
    S_AIRouter --> Anthropic
    S_AIRouter --> Gemini
    
    %% Persistence Connections
    ServiceLayer --> DB
    Routers --> DB
    S_AIRouter --> Crypto
    DB --> Backup
```

---

## 2. Complete End-to-End Request Lifecycle

To illustrate the exact flow through the codebase, here is the trace of a user requesting source ingestion:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Editor
    participant FE as React Frontend (SPA)
    participant Nginx as Nginx Proxy
    participant MW as FastAPI Middleware
    participant Route as /api/v1/sources/extract
    participant Extr as extraction_service.py
    participant DB as Database (SQLAlchemy)
    participant Client as External Web Server

    User->>FE: Clicks "Add Source to Investigation" (URL)
    FE->>Nginx: POST /api/v1/sources/extract { url, project_id } (with Bearer JWT)
    Nginx->>MW: Forward HTTP request
    MW->>MW: ObservabilityMiddleware: Assigns X-Request-ID (UUIDv4)
    MW->>MW: RateLimiter: Checks IP sliding window (< 120 req/min)
    MW->>MW: Auth: Validates HS256 JWT signature & extracts user_id
    MW->>Route: Dispatches to route handler
    Route->>Extr: extract_content_from_url(url)
    
    Extr->>Extr: Socket DNS lookup: socket.getaddrinfo(hostname)
    alt IP is 127.0.0.1 or RFC 1918 Private Subnet
        Extr-->>Route: Raise SSRFSecurityException (400 Bad Request)
        Route-->>FE: Return 400 Bad Request ("Private IP rejected")
    else IP is Public & Legitimate
        Extr->>Client: HTTP GET request (12s timeout, 2MB max buffer)
        Client-->>Extr: Returns HTML document
        Extr->>Extr: Trafilatura parse (fallback: BeautifulSoup4 meta tags)
        Extr->>Extr: Epistemic categorization (Facts vs Analysis vs Speculation)
        Extr-->>Route: Return structured extraction result
        Route->>DB: INSERT into sources and claims (with foreign keys)
        DB-->>Route: Commit confirmed
        Route-->>MW: Return HTTP 201 Created with JSON payload
        MW-->>Nginx: Injects X-Request-ID header & records latency
        Nginx-->>FE: Return response to client
        FE-->>User: UI updates: source card transitions to "Content Verified"
    end
```

---

## 3. Architecture Component Defenses

### 3.1. Frontend Architecture
- **State Management:** Reactive local state paired with centralized Axios HTTP client. Component-level state manages form controls and modal triggers.
- **Routing:** React Router v7 enforcing route protection; unauthenticated tokens redirect to `/login`.
- **UI System:** Tailwind CSS design tokens matching the authoritative publication palette of *This Week in AI*.

### 3.2. Backend Layering & Dependency Injection
- **Separation of Concerns:** Zero business logic in FastAPI path operation functions. Routes validate schemas (`schemas/`), call services (`services/`), and query through ORM models (`models/`).
- **Database Sessions:** Injected via FastAPI's `Depends(get_db)` yielding scoped SQLAlchemy sessions that guarantee transaction rollback on unhandled exceptions.

### 3.3. Database Schema & Migration Strategy
- **Relational Tables:** 34 normalized tables managing Users, Organizations, Research Projects, Sources, Claims, Briefs, Drafts, Suggestions, Editorial Outputs, Style Guides, and Version Snapshots.
- **Alembic Versioning:** Linear, forward-only migrations (`fe217d474c9d -> 0d95531a1a07 -> 3b7c9f1e8a2d`). Every migration is tested against both fresh databases and populated databases to guarantee zero data loss.

### 3.4. Dual-Column Non-Destructive Editing Model
- **`WritingDraft` ORM Model:** Stores `original_content: Text` (immutable) alongside `revised_content: Text` (mutable).
- **Replacement Safety:** `replace_text_safely(revised_text, original_snippet, replacement_text)` calculates exact sentence-boundary indices, guaranteeing that surrounding copy, quotations, and citations are never corrupted.

### 3.5. Multi-Provider Intelligent AI Router
- **Provider Adapters:** Standard interface implemented across `GroqAdapter`, `OpenAIAdapter`, `AnthropicAdapter`, and `GeminiAdapter`.
- **Automatic Fallback:** If upstream credentials are missing, invalid, or rate-limited (HTTP 429), the router executes the **Deterministic Fallback Engine**, which parses text using rule-based heuristics so the editorial desk never experiences downtime.
