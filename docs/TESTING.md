# End-to-End Testing & User Acceptance Testing Documentation

This document describes the testing architecture, automated test suites, execution procedures, and quality verification standards implemented for the **AI Editorial Workspace** (`Editorial AI`) at *This Week in AI*.

---

## 1. Testing Architecture Overview

The workspace adheres to a multi-tiered testing strategy ensuring deterministic verification across backend business logic, database transactions, AI heuristics, and frontend user flows:

```
                  ┌─────────────────────────────────────────┐
                  │    Playwright Browser Acceptance (6)    │
                  │  (Chromium, Accessibility, UX Flows)    │
                  ├─────────────────────────────────────────┤
                  │    Backend User Acceptance E2E (4)      │
                  │ (Full User Journeys & Invariant Checks) │
                  ├─────────────────────────────────────────┤
                  │   Integration & Feature Tests (25)      │
                  │ (Routes, Services, DB Isolation, Logs)  │
                  ├─────────────────────────────────────────┤
                  │       Unit Tests & Heuristics (8)       │
                  │ (Readability Math, SSRF Guard, Sanitiz) │
                  └─────────────────────────────────────────┘
```

Total Automated Test Count: **43 Automated Tests** (37 Backend Pytest + 6 Frontend Playwright E2E).

---

## 2. Test Environment Setup & Isolation

All automated tests execute in strictly isolated environments to prevent accidental modification of development or production databases:

- **Isolated Test Database**: Pytest fixtures construct temporary SQLite databases (`sqlite:///./test_phase19_ci.db` or in-memory tables) created cleanly on test startup and wiped on teardown.
- **Deterministic AI Heuristics**: When `OPENAI_API_KEY=""` (offline mode), the system switches deterministically to heuristic fallback engines:
  - Claim classification (Facts vs. Analysis vs. Speculation via linguistic markers).
  - Editorial draft synthesis (300–500 words with bracketed source references `[Source Title]`).
  - Readability auditing (Flesch Reading Ease, sentence length counters, passive voice heuristics, filler phrase matching).
- **Network Isolation**: External HTTP calls and website scraping are mocked or intercepted (`httpx.AsyncClient` mocks and Playwright `page.route` intercepts).
- **SSRF Defense Enforced**: Localhost (`127.0.0.1`), loopback, cloud metadata (`169.254.169.254`), and private subnets (`10.0.0.0/8`, `192.168.0.0/16`) are strictly rejected.

---

## 3. Test Suite Execution Commands

### 3.1 Backend Acceptance & Integration Tests (Pytest)

Ensure your Python virtual environment is activated:

```powershell
# Windows PowerShell
cd backend
$env:PYTHONPATH=".."
.\venv\Scripts\pytest -v
```

```bash
# Linux / macOS
cd backend
export PYTHONPATH=".."
source venv/bin/activate
pytest -v
```

To run **only** the Phase 19 End-to-End Acceptance suite:

```powershell
cd backend
$env:PYTHONPATH=".."
.\venv\Scripts\pytest tests/test_phase19_e2e_acceptance.py -v --tb=short
```

### 3.2 Frontend Browser Automation Tests (Playwright)

```bash
cd frontend
# Install Playwright Chromium browser if running for the first time
npx playwright install chromium

# Run all browser E2E specs
npm run test:e2e
```

To view HTML reports:

```bash
npx playwright show-report
```

---

## 4. End-to-End User Acceptance Test Suites

### 4.1 Research Assistant Complete Journey (`test_e2e_research_assistant_complete_journey`)
1. **Project Creation**: Dispatches `POST /api/v1/projects` with research domain; verifies `201 Created` with project ID.
2. **Multi-Source Ingestion**: Ingests 3 distinct technical sources covering AI hardware, hyperscaler capex, and immersion cooling.
3. **Extraction & Claim Analysis**: Executes `POST /api/v1/sources/{id}/analyze` on all 3 sources; validates linguistic categorization of reported facts, technical analysis, and industry speculation.
4. **Synthesis**: Calls `POST /api/v1/projects/{id}/research/synthesize`; verifies structured brief schema (`summary`, `key_findings`, `newsletter_angles`, `evidence`, `brief_content`).
5. **SSRF Guard Invariant**: Attempts extracting an internal address (`http://127.0.0.1:9090/admin-leak`); verifies immediate extraction failure with `"Security violation"` error message.

### 4.2 Writing Assistant Complete Journey (`test_e2e_writing_assistant_complete_journey`)
1. **Draft Ingestion**: Creates draft with verbose passive sentences and filler words.
2. **Quality Audit**: Runs 6 deterministic checks (Flesch score, sentence length, passive voice, filler phrases, repetition, complexity).
3. **Interactive Resolution**:
   - Accepts suggestion 1 (e.g., replaces `"In order to"` with `"To"`).
   - Rejects suggestion 2.
4. **Diff Verification**: Compares original vs. revised draft; asserts that original remains 100% immutable while revised draft reflects accepted rewrite with improved readability delta.
5. **Idempotency**: Submits duplicate accept requests; asserts idempotency (`200 OK` without duplicating text or corrupting draft).

### 4.3 Editorial Studio Complete Journey (`test_e2e_editorial_studio_complete_journey`)
1. **Headline Ingestion**: Generates and selects newsletter-style headline.
2. **Article Generation**: Calls `POST /api/v1/editorial/generate` with minimum 300 and maximum 500 word bounds.
3. **Citation Audit**: Verifies bracketed citations `[SemiAnalysis 2026 Capex]` and asserts exact link to ingested sources.
4. **Multi-Format Export**: Verifies Markdown (`.md`), Plain Text (`.txt`), and HTML5 (`.html`) with XSS entity escaping (`<article>`, `&lt;script&gt;` sanitization).

### 4.4 Failure Paths & Security Invariants (`test_e2e_failure_paths_and_invariants`)
- Ingestion of malformed/empty URLs.
- Synthesis rejection when fewer than 3 sources are ingested (`HTTP 400`).
- Cross-project source leakage prevention.
- Invalid export format rejection (`HTTP 422`).
- 404 handling on nonexistent drafts and missing projects.

---

## 5. Playwright Browser Automation Suites

| Spec File | Purpose | Assertion Focus |
| :--- | :--- | :--- |
| `frontend/e2e/navigation.spec.ts` | Shell Navigation | Workspace layout, sidebar links, route redirects, active module indicators. |
| `frontend/e2e/writing.spec.ts` | Writing Quality Audit | Deterministic issue detection, badge rendering, Accept & Apply rewrite, Reject flow, Compare diff drawer. |
| `frontend/e2e/editorial.spec.ts` | Editorial Production | Project loading, headline generation, 300–500 word composition, export modal with MD/TXT/HTML tabs. |
| `frontend/e2e/accessibility.spec.ts` | A11y & Responsiveness | Keyboard tab order, mobile viewport (375x667) fluid layout, zero uncaught JavaScript page exceptions. |

---

## 6. Continuous Integration Workflow

GitHub Actions runs automated tests on every push and pull request via `.github/workflows/e2e-tests.yml`:
- **Job 1: `backend-e2e`**: Runs Python 3.10 setup, dependency caching, and full pytest acceptance tests.
- **Job 2: `frontend-e2e`**: Runs Node.js 20, npm ci, Playwright browser installation, and browser automation test execution with artifact uploads.

