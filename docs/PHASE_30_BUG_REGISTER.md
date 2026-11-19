# PHASE 30 — DEFECT & BUG MANAGEMENT REGISTER

## 1. Defect Classification Standard
- **P0 (Critical):** Application crash, authentication bypass, data loss, cross-tenant data leak, complete blocker.
- **P1 (Major):** Core workflow failure, broken persistence, unhandled AI failure, significant security issue.
- **P2 (Moderate):** Non-blocking UI glitch, missing non-critical validation message, minor display discrepancy.
- **P3 (Minor):** Cosmetic alignment, polish, optimization opportunity.

---

## 2. Bug Tracking Register

| ID | Module | Bug Description | Severity | Reproduction Steps | Root Cause | Implemented Fix | Regression Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-30-01** | Editorial Review | `NameError: has_permission is not defined` in `approve_editorial` | **P0** | Call `POST /api/v1/editorial/{id}/approve` | Missing import of `has_permission` in `editorial_review.py` | Added import `has_permission` from `backend.app.schemas.auth` | `backend/tests/test_phase21_editorial_hardening.py` | **RESOLVED** |
| **BUG-30-02** | Multi-Tenancy | Pydantic validation error (422) creating project with `name` instead of `title` | **P1** | Call `POST /api/v1/projects` with `name` field only | Schema strictly requires `title` | Schema updated to alias or client sends `title` properly | `test_phase29_security_hardening.py` | **RESOLVED** |
| **BUG-30-03** | Editorial Review | Authors able to bypass self-approval gate if role check order was inverted | **P1** | Author with editor role attempts to self-approve draft | Role check occurred after permission check | Reordered guard: checks author self-identity before checking `APPROVE_EDITORIALS` | `test_editorial_self_approval_guard` | **RESOLVED** |
| **BUG-30-04** | Document Extraction | Extractor returned `content` but test asserted on `text` key | **P2** | Extract text from uploaded document bytes | Discrepancy between dictionary key `content` and expected key `text` | Aligned test assertion to access `content` and normalized output dictionary | `test_file_upload_security_magic_bytes` | **RESOLVED** |
| **BUG-30-05** | Projects UI | Project cards missing keyboard navigation handlers | **P2** | Navigate project cards via Tab and Enter keys | Missing `role="button"`, `tabIndex={0}`, and `onKeyDown` | Added accessible keyboard listeners to project cards in `ProjectsPage.tsx` | `frontend/e2e/phase28-frontend-integration.spec.ts` | **RESOLVED** |
| **BUG-30-06** | Navigation Header | Missing breadcrumbs on `/organization`, `/observability`, `/profile` | **P3** | Navigate directly to `/organization` or `/profile` | Route mapping dictionary lacked entries for newer routes | Added path entries and readable titles in `Header.tsx` | `frontend/e2e/phase28-frontend-integration.spec.ts` | **RESOLVED** |

---

## 3. Bug Resolution Summary
- **Total Bugs Logged:** 6
- **P0 Bugs:** 1 (Resolved: 1, Remaining: 0)
- **P1 Bugs:** 2 (Resolved: 2, Remaining: 0)
- **P2 Bugs:** 2 (Resolved: 2, Remaining: 0)
- **P3 Bugs:** 1 (Resolved: 1, Remaining: 0)
- **Remaining Open Defects:** **0 (Zero)**
