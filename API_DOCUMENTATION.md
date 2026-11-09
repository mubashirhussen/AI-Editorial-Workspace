# API Reference Specification

This reference document catalogs the key REST API routes, HTTP methods, authorization requirements, request contracts, and response schemas for the **AI Editorial Workspace** under prefix `/api/v1`.

---

## 1. Authentication & Users (`/api/v1/auth`)

### Register New User
* **Endpoint**: `POST /api/v1/auth/register`
* **Status**: `201 Created`
* **Request Body**:
  ```json
  {
    "email": "editor@editorial.ai",
    "password": "SecurePassword123!",
    "full_name": "Lead Editor",
    "organization_name": "Editorial Guild"
  }
  ```
* **Response**: `AuthResponse` containing `access_token`, `token_type`, `user` profile, and `organization`.

### Authenticate (Login)
* **Endpoint**: `POST /api/v1/auth/login`
* **Status**: `200 OK`
* **Request Body**:
  ```json
  {
    "email": "editor@editorial.ai",
    "password": "SecurePassword123!"
  }
  ```
* **Response**: `AuthResponse` with fresh JWT access token.

### Current User Profile
* **Endpoint**: `GET /api/v1/auth/me`
* **Headers**: `Authorization: Bearer <token>`
* **Status**: `200 OK`
* **Response**: Returns `user` details and list of active `organizations` with associated membership roles.

### Session Revocation (Logout)
* **Endpoint**: `POST /api/v1/auth/logout`
* **Headers**: `Authorization: Bearer <token>`
* **Status**: `200 OK`

---

## 2. Research Projects & Sources (`/api/v1/research`)

### List Projects
* **Endpoint**: `GET /api/v1/research/projects` (Alias: `/api/v1/projects`)
* **Headers**: `Authorization: Bearer <token>`, `X-Organization-Id: <org_id>`
* **Query Params**: `skip` (default 0), `limit` (default 50, max 100)
* **Status**: `200 OK`
* **Response**: `{"items": [ProjectResponse], "total": int}`

### Create Project
* **Endpoint**: `POST /api/v1/research/projects` (Alias: `/api/v1/projects`)
* **Status**: `201 Created`
* **Request Body**:
  ```json
  {
    "title": "Quantum Computing Frontiers 2026",
    "description": "Parametric evaluation of superconducting quantum architectures."
  }
  ```

### Add Source to Project
* **Endpoint**: `POST /api/v1/research/projects/{project_id}/sources`
* **Status**: `201 Created`
* **Request Body**:
  ```json
  {
    "title": "Nature Physics Publication",
    "source_type": "text",
    "text_content": "Extracted benchmark data from empirical peer-reviewed report."
  }
  ```

### Synthesize Research Brief
* **Endpoint**: `POST /api/v1/research/projects/{project_id}/generate-brief` (Alias: `.../brief`)
* **Pre-condition**: Minimum 3 sources ingested for project.
* **Status**: `200 OK`
* **Response**: `ResearchBriefResponse` containing `executive_summary`, `what_happened`, `why_it_matters`, `evidence_verification`, and `newsletter_angles`.

---

## 3. Writing Assistant (`/api/v1/writing`)

### Create Writing Draft
* **Endpoint**: `POST /api/v1/writing/drafts`
* **Status**: `201 Created`
* **Request Body**:
  ```json
  {
    "title": "The Quantum Advantage Paradigm",
    "content": "Draft article body exploring enterprise quantum deployment."
  }
  ```

### Analyze Draft & Generate Suggestions
* **Endpoint**: `POST /api/v1/writing/drafts/{draft_id}/analyze`
* **Status**: `200 OK`
* **Response**: `WritingAnalysisResponse` containing readability metrics, flesch grade, and actionable suggestions.

### Calculate Draft Metrics
* **Endpoint**: `GET /api/v1/writing/drafts/{draft_id}/metrics`
* **Status**: `200 OK`
* **Response**: Word count, character count, sentence count, reading time, and readability grade.

### Selection Rewrite
* **Endpoint**: `POST /api/v1/writing/rewrite-selection`
* **Status**: `200 OK`
* **Request Body**:
  ```json
  {
    "selected_text": "In order to comprehend model evaluation...",
    "operation": "simplify_complex_sentences"
  }
  ```
* **Response**: `SelectionRewriteResponse` with `rewritten_text`, `diff_summary`, and rationale.

### Document Export
* **Endpoint**: `GET /api/v1/writing/drafts/{draft_id}/export?format={markdown|docx|html|txt}`
* **Status**: `200 OK`
* **Response**: Binary / text file payload with appropriate `Content-Type` and `Content-Disposition`.

---

## 4. System Health & Observability

### Workspace Health Check
* **Endpoint**: `GET /api/v1/health`
* **Status**: `200 OK`
* **Response**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "application": "AI Editorial Workspace",
    "version": "1.0.0",
    "ai_engine": { "status": "available", "mode": "Deterministic Fallback Engine" }
  }
  ```
