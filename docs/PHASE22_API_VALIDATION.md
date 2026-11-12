# Phase 22 — Research Assistant API Contracts & Validation Register

**Target Application:** AI Editorial Workspace  
**API Prefix:** `/api/v1/research` & `/api/v1/sources`  
**Authentication:** Bearer JWT Header (`Authorization: Bearer <token>`)  
**Status:** Validated & Deployed  

---

## 1. Overview

Phase 22 implements full-lifecycle API capabilities for the Research Assistant, closing previous gaps in in-place brief editing, version tracking, multi-format export, and project lifecycle management.

All endpoints strictly enforce tenant isolation, input schema validation via Pydantic v2, and standardized error envelopes.

---

## 2. Comprehensive Endpoint Inventory

### 2.1 Project Lifecycle & Scoping

| Method | Route | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/projects` | List tenant research projects with pagination, sorting, and status filter. | `200 OK` | `401` |
| `POST` | `/projects` | Create a new research project with rich scope metadata. | `201 Created` | `400, 401, 422` |
| `GET` | `/projects/{id}` | Retrieve project details, including full source list and brief metadata. | `200 OK` | `401, 403, 404` |
| `PUT` | `/projects/{id}` | Update project metadata, title, topic, or scope. | `200 OK` | `401, 403, 404, 422` |
| `DELETE` | `/projects/{id}` | Cascade delete project and associated sources/briefs. | `200 OK` | `401, 403, 404` |
| `POST` | `/projects/{id}/archive` | Transition project status to `archived`. | `200 OK` | `401, 403, 404` |
| `POST` | `/projects/{id}/reopen` | Transition project status back to `active`. | `200 OK` | `401, 403, 404` |

#### Sample Payload: `POST /projects`
```json
{
  "title": "Autonomous AI Verification & Grounding",
  "topic": "Test-Time Compute & Verification",
  "research_objective": "Evaluate factual reasoning architectures and citation grounding in enterprise systems.",
  "target_audience": "founders, builders, and operators",
  "research_scope": "Q4 2025 - Q1 2026 technical releases",
  "keywords": ["reasoning", "verification", "citations", "grounding"]
}
```

---

### 2.2 Source Ingestion & Management

| Method | Route | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/projects/{id}/sources` | Ingest web URL with strict SSRF defense. | `201 Created` | `400, 401, 403, 404, 422` |
| `POST` | `/projects/{id}/sources/upload` | Upload document (PDF/DOCX/TXT) with magic byte validation (max 10MB). | `201 Created` | `400, 401, 403, 404, 413` |
| `POST` | `/projects/{id}/sources/text` | Ingest raw text snippet with title and curation note. | `201 Created` | `401, 403, 404, 422` |
| `GET` | `/projects/{id}/sources` | List all verified sources for a project. | `200 OK` | `401, 403, 404` |
| `POST` | `/sources/{source_id}/retry` | Re-trigger content extraction on failed or incomplete source. | `200 OK` | `401, 403, 404` |
| `DELETE` | `/sources/{source_id}` | Remove source from investigation. | `200 OK` | `401, 403, 404` |

---

### 2.3 Research Brief Synthesis, Editing & Export

| Method | Route | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/projects/{id}/brief` | Synthesize cross-source research brief ($\ge 3$ sources required). | `201 Created` | `400, 401, 403, 404` |
| `GET` | `/projects/{id}/brief` | Fetch latest research brief with evidence grounding map. | `200 OK` | `401, 403, 404` |
| `PUT` | `/projects/{id}/brief` | Save in-place user edits, creating a version snapshot. | `200 OK` | `400, 401, 403, 404, 422` |
| `GET` | `/projects/{id}/brief/history` | Retrieve full immutable version lineage of the research brief. | `200 OK` | `401, 403, 404` |
| `GET` | `/projects/{id}/brief/export` | Export brief formatted in Markdown, Plain Text, or JSON. | `200 OK` | `400, 401, 403, 404` |
| `GET` | `/projects/{id}/evidence` | List verified evidence items with epistemic status pills. | `200 OK` | `401, 403, 404` |

#### Sample Payload: `PUT /projects/{id}/brief`
```json
{
  "title": "Autonomous AI Verification & Grounding (Edited)",
  "executive_summary": "Test-time compute verified with deterministic epistemic guardrails.",
  "user_notes": "Phase 22 audit notes: Validated against 3 authoritative sources.",
  "what_happened": "Frontier AI labs published new architectures with programmatic verification.",
  "why_it_matters": "Publishing desks require deterministic source citations."
}
```

#### Sample Response: `GET /projects/{id}/brief/export?format=markdown`
```json
{
  "project_id": "proj-phase22-1",
  "brief_id": "brief-phase22-test",
  "title": "Autonomous AI Verification & Grounding",
  "markdown_content": "# Autonomous AI Verification & Grounding\n\n## Executive Summary\n...",
  "plain_text_content": "AUTONOMOUS AI VERIFICATION & GROUNDING\n\nEXECUTIVE SUMMARY:\n...",
  "json_content": "{\n  \"id\": \"brief-phase22-test\", ...\n}",
  "format": "markdown",
  "exported_at": "2026-11-12T16:01:00.000Z"
}
```

---

## 3. Automated Route Validation Results

All routes verified via `backend/tests/test_phase22_research_assistant.py`:
- `test_phase22_project_crud_and_lifecycle`: Passed (100%)
- `test_phase22_ssrf_prevention`: Passed (100%)
- `test_phase22_document_extractor_and_signature_checks`: Passed (100%)
- `test_phase22_brief_synthesis_and_evidence_traceability`: Passed (100%)
- `test_phase22_brief_update_versioning_and_export`: Passed (100%)
- `test_phase22_cross_tenant_isolation`: Passed (100%)

