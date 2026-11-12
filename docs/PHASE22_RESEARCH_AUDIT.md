# Phase 22 — Research Assistant Comprehensive Audit & Implementation Blueprint

**Target Application:** AI Editorial Workspace — Research Assistant  
**Evaluated Routes:** `/research`, `/research/:projectId`, `/api/v1/research/*`, `/api/v1/sources/*`  
**Reference Environment:** Production Vercel (`ai-editorial-workspace-blue.vercel.app`) & Local Staging  
**Assessment Date:** November 2026  
**Auditor:** Senior Full-Stack Engineer, AI Engineer & Research Systems Architect  

---

## 1. Executive Summary

The Research Assistant is the foundational intelligence engine of the AI Editorial Workspace. It collects multi-modal primary sources (URLs, PDFs, DOCX, text snippets, and research papers), validates and extracts content securely against SSRF vectors, analyzes individual claims, synthesizes cross-source evidence briefs with explicit epistemic status (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`), and provides clean context handoffs directly into the Editorial Studio.

This audit evaluates the current source code, API routes, database schemas, and frontend interfaces against Phase 22 enterprise requirements.

---

## 2. Existing Functionality Audit

### 2.1 Working Core Modules
1. **URL Ingestion Pipeline:**
   - Supported via `POST /api/v1/research/projects/{id}/sources` and `/api/v1/sources`.
   - Utilizes `trafilatura` and `BeautifulSoup4` with basic HTTP extraction and HTML metadata parsing.
   - Initial SSRF checks in `is_safe_url` checking IP ranges and blocked loopback addresses.
2. **Multi-Modal Document Extraction:**
   - Implemented in `backend/app/services/research/document_extractor.py`.
   - Supports PDF parsing via `pypdf`, Word document parsing via `python-docx`, plain text decoding (UTF-8, Latin-1), and OCR fallback via `pytesseract`.
   - Enforces a 10MB payload limit and blocks executable binaries (`.exe`, `.dll`, `.bin`, `.sh`, etc.).
3. **Deterministic & AI Cross-Source Synthesis:**
   - Implemented in `backend/app/services/research/synthesis_service.py` and `ai_service.py`.
   - Requires at least 3 ingested sources to compile a research brief.
   - Extracts key developments, strategic implications, newsletter angles, and epistemic fact segregation (facts vs. analysis vs. speculation).
4. **Evidence Grounding Algorithm:**
   - Maps claims to source passages with verbatim matching and classifies status as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, or `NOT_VERIFIABLE`.

---

## 3. Defect & Gap Analysis (Prioritized)

| Defect ID | Severity | Category | Description | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-2201** | **CRITICAL** | API / Persistence | No `PUT /research/projects/{project_id}/brief` route exists to save user edits to a research brief. | Users cannot modify synthesized brief sections or save custom editorial notes to database. |
| **DEF-2202** | **CRITICAL** | API / Versioning | No `GET /research/projects/{project_id}/brief/history` endpoint exists to inspect brief version lineages. | Brief revisions cannot be inspected, restored, or compared across iterations. |
| **DEF-2203** | **HIGH** | Schema / Domain | `ResearchProject` model and `ProjectCreate` / `ProjectUpdate` schemas lack required enterprise project fields: `topic`, `research_objective`, `target_audience`, `research_scope`, `keywords`, `preferred_source_types`. | Frontend project modal cannot capture structured research briefs or scoping metadata. |
| **DEF-2204** | **HIGH** | Export | No dedicated multi-format export route (`GET /research/projects/{project_id}/brief/export`) exists for research briefs. | Users cannot export research briefs to Markdown (`.md`), Plain Text (`.txt`), or JSON (`.json`). |
| **DEF-2205** | **MEDIUM** | Project Operations | Projects lack explicit archiving (`POST /projects/{id}/archive`) and reopening (`POST /projects/{id}/reopen`) endpoints. | Users cannot manage lifecycle transitions for retired or completed investigations. |
| **DEF-2206** | **MEDIUM** | UX / Integration | In `ResearchPage.tsx`, "Write This" navigates to `/writing` instead of providing a direct handoff to Editorial Studio (`/editorial?projectId=...`). | Bypasses Editorial Studio, causing workflow discontinuity for newsletter drafting. |
| **DEF-2207** | **MEDIUM** | Security / SSRF | URL extraction lacks strict re-validation across multiple DNS resolution hops and redirect chains (rebinding defense). | Cloud metadata (`169.254.169.254`) or DNS rebinding could expose internal network services. |
| **DEF-2208** | **LOW** | UX / Ergonomics | Source list lacks real-time search, status filtering, and in-place document text preview modal. | Hard to manage large investigations with 10+ sources. |

---

## 4. API & Database Dependencies

### 4.1 Database Models
- `ResearchProject` (`research_projects`): Needs columns for `topic`, `research_objective`, `target_audience`, `research_scope`, `keywords`, and `preferred_source_types`.
- `ResearchBrief` (`research_briefs`): Needs `is_user_edited: Boolean` and `user_notes: Text` to track editorial modifications.
- `Source` (`sources`): Tracks `extraction_status`, `content_hash`, `summary`, `author`, and `published_at`.
- `ResearchClaim` & `ResearchEvidence`: Relational mapping of claims and direct supporting excerpts with confidence metrics.

### 4.2 Endpoint Scope
- `POST /api/v1/research/projects`: Project creation with rich metadata.
- `GET /api/v1/research/projects`: Search, status filter, pagination, tenant-scoping.
- `GET /api/v1/research/projects/{id}`: Detailed project with sources and brief.
- `PUT /api/v1/research/projects/{id}`: Update project metadata.
- `DELETE /api/v1/research/projects/{id}`: Delete with cascading cleanup.
- `POST /api/v1/research/projects/{id}/archive`: Lifecycle archiving.
- `POST /api/v1/research/projects/{id}/reopen`: Lifecycle reopening.
- `POST /api/v1/research/projects/{id}/sources`: URL or text ingestion.
- `POST /api/v1/research/projects/{id}/sources/upload`: Multi-format file upload.
- `POST /api/v1/sources/{source_id}/retry`: Extraction retry.
- `DELETE /api/v1/sources/{source_id}`: Source removal.
- `POST /api/v1/research/projects/{id}/generate-brief`: Synthesis with evidence grounding.
- `GET /api/v1/research/projects/{id}/brief`: Fetch latest brief.
- `PUT /api/v1/research/projects/{id}/brief`: Update & persist user-edited brief.
- `GET /api/v1/research/projects/{id}/brief/history`: Version history.
- `GET /api/v1/research/projects/{id}/brief/export`: Multi-format export (`md`, `txt`, `json`).
- `GET /api/v1/research/projects/{id}/evidence`: Claim-to-evidence mappings.

---

## 5. Security Architecture (SSRF & Ingestion)

1. **Strict Protocol Enforcement:** Only `http` and `https` allowed. Schemes like `file://`, `gopher://`, `ftp://` are rejected.
2. **Private IP & Loopback Blocking:**
   - Blocks `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` (Cloud Metadata).
   - Re-checks every redirect hop `Location` header to prevent open redirect SSRF bypasses.
   - Resolves DNS prior to request and validates destination IP against forbidden ranges.
3. **Payload Bounds:**
   - 10MB maximum file size on uploads.
   - 2MB maximum HTTP extraction response size.
   - 12-second connection and read timeout.

---

## 6. Implementation Action Plan

1. **Step 1 — Models & Database Migration:** Add project fields (`topic`, `research_objective`, `target_audience`, `research_scope`, `keywords`, `preferred_source_types`) and brief fields (`is_user_edited`, `user_notes`). Create Alembic migration.
2. **Step 2 — Backend Schemas & Service Layer:** Update schemas, add brief update, versioning, export service, and project lifecycle handlers in `research_service.py`.
3. **Step 3 — API Endpoints Hardening:** Expose `PUT /brief`, `GET /brief/history`, `GET /brief/export`, `archive`, `reopen`, and `retry` in `research.py` and `sources.py`.
4. **Step 4 — SSRF & Document Extractor Hardening:** Harden URL verification, DNS resolution checking, and file signature validation.
5. **Step 5 — Frontend Upgrades:** Update `ResearchPage.tsx` with:
   - Full project creation modal (Topic, Objective, Target Audience, Scope, Keywords).
   - Brief in-place editor with section editing and saving.
   - Version history modal and comparison.
   - Multi-format brief export modal (Markdown, TXT, JSON).
   - Direct button to "Open in Editorial Studio".
   - Project archiving, filtering, and search.
6. **Step 6 — Test Suites:**
   - Pytest: `backend/tests/test_phase22_research_assistant.py` (SSRF, extraction, brief CRUD, version history, export, tenant isolation).
   - Playwright: `frontend/e2e/research-workflow.spec.ts` (full browser workflow).
7. **Step 7 — Comprehensive Documentation:** Create all 7 required Phase 22 documentation files.

