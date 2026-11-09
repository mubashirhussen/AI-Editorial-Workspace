# AI Editorial Workspace — UI & Functional Audit Report

**Date:** 2026-11-09  
**Branch:** `feat/phase12-ui-ux-backend-integration`  
**Auditor:** Senior Forward Deployed Engineer & UI/UX Architect  
**Objective:** Complete functional audit of all 8 application modules, cross-referencing UI screenshots against actual backend routes, database entities, and client-side state.

---

## 1. Executive Findings Summary

| Issue ID | Screen / Module | Component | Severity | Description & Root Cause | Target Fix |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **AUD-01** | Global Application Shell | `Header.tsx` / `HealthService` | **CRITICAL** | `Backend unavailable` displayed on all pages when backend is offline or slow; no retry backoff, no local recovery. | Centralized `HealthContext` with exponential backoff, immediate reconnect on click, clear offline state handling. |
| **AUD-02** | Writing Assistant | `WritingPage.tsx` / `ArticleImprovementsPanel.tsx` | **CRITICAL** | Editor contains prose but displays `0 words`, fallback `14 sentences`, `60s reading time`, and hardcoded `72/100` score because metrics were only updated on backend response. | Pure client-side `textAnalysis.ts` calculating exact word, sentence, reading time, Flesch score, and complexity in real-time. |
| **AUD-03** | Writing Assistant | `WritingPage.tsx` Save Indicator | **HIGH** | "Saved" indicator rendered even when backend was unreachable or saving failed. | Enforce discrete save states: `UNSAVED`, `SAVING`, `SAVED`, `SAVE_FAILED`, `OFFLINE_LOCAL`. Only display `SAVED` upon HTTP 200 confirmation. |
| **AUD-04** | AI Observability | `ObservabilityPage.tsx` | **HIGH** | Static metrics (153 requests, $1.75, 248.3K tokens) lacked clear distinction between baseline evaluation data and live server telemetry. | Live telemetry toggle, explicit "Demonstration Baseline" label when unpopulated, and integrated "Run Live 34-Case Benchmark" button. |
| **AUD-05** | Research Assistant | `ResearchPage.tsx` / `LocalLibraryView.tsx` | **HIGH** | Empty sources library blocks brief generation without clear guidance; URL/PDF/Text ingestion needs robust status and duplicate feedback. | Support all 3 ingestion paths, real-time status transitions (`PENDING` -> `PROCESSING` -> `COMPLETED`), duplicate detection, and quick sample loader. |
| **AUD-06** | Editorial Studio | `EditorialPage.tsx` | **HIGH** | "No Research Projects Available" displayed when backend unlinked; missing seamless brief-to-editorial generation pipeline. | Project & brief selector, 300–500 words adherence config, citation preservation, and multi-format export (Markdown, TXT). |
| **AUD-07** | Research Projects | `ProjectsPage.tsx` | **MEDIUM** | Project list showed empty state when backend was disconnected; deletion lacked confirmation and undo safety. | Reconnect to live `/api/v1/research/projects`, add search, status filter, and confirmation dialogs. |
| **AUD-08** | Organization | `OrganizationPage.tsx` | **MEDIUM** | 0 members / 0 invitations rendered; invitation modal disconnected from backend invitations API. | Connect to `/api/v1/organizations/{id}/members` and `/invitations` with role update and revoke actions. |
| **AUD-09** | Settings | `SettingsPage.tsx` | **MEDIUM** | Theme and appearance preferences did not persist consistently in `localStorage` across page reloads. | Persistent settings engine for theme (Light/Dark/System), table density, and live backend configuration status. |

---

## 2. Detailed Screen-by-Screen Audit Matrix

### 2.1 Dashboard (`/dashboard`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Backend Indicator** | Red badge `(!) Backend unavailable` | Live connection monitor with auto-reconnect | `GET /api/v1/health` | **CRITICAL (AUD-01)** |
| **Project Summary Cards** | Shows empty or static counters | Displays real counts (Total Projects, Active Investigations, Briefs, Drafts) | `GET /api/v1/research/dashboard/stats` | **HIGH (AUD-05)** |
| **Recent Activity Feed** | Empty state when disconnected | Renders chronological user actions (source ingested, brief created, draft audited) | `GET /api/v1/dashboard/activities` | **MEDIUM** |
| **Quick Action Buttons** | "New Research", "Audit Draft", "Editorial Studio" | Direct deep-links with pre-populated project context | Client Router (`/research`, `/writing`, `/editorial`) | **VERIFIED** |

### 2.2 Research Assistant (`/research`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Source Ingestion Bar** | URL, PDF/Docx, Paste Text tabs | Validate URLs against SSRF/private IPs, parse PDF/TXT/MD, compute content hash | `POST /api/v1/sources/` | **HIGH (AUD-05)** |
| **Sources Library** | "0 Verified Sources - Requires 3 more sources" | List ingested sources with status badges (`INGESTED`, `PARSING`, `COMPLETED`), word count, domain, delete | `GET /api/v1/sources/?project_id={id}` | **HIGH (AUD-05)** |
| **Brief Synthesizer** | "Generate Brief" disabled until 3 sources | Triggers multi-source epistemic synthesis, extracts claims, contradictions, and editorial angles | `POST /api/v1/research/synthesize` | **HIGH** |
| **Evidence Alignment Tab** | Empty state | Displays claims mapped to verbatim source passages, credibility score, and deep links | `GET /api/v1/research/projects/{id}/claims` | **HIGH** |
| **Facts vs Speculation Tab** | Empty state | Triangulates assertions into Verified Facts, Partially Supported, and Speculative Claims | `GET /api/v1/research/projects/{id}/claims` | **MEDIUM** |
| **Knowledge Graph Tab** | Decorative empty state | Interactive visualization of discovered entities and cross-source relationships | `GET /api/v1/research/intelligence/graph` | **MEDIUM** |

### 2.3 Writing Assistant & Auditor (`/writing`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Editor Statistics** | Shows `0 words`, `14 sentences`, `60s reading time` while text is present | Real-time client-side calculation: exact word count, sentences, reading time, avg sentence length | `textAnalysis.ts` (client-side) | **CRITICAL (AUD-02)** |
| **Quality Score** | Hardcoded `Good 72/100` | Deterministic Flesch Reading Ease + sentence complexity calculation with explanation | `textAnalysis.ts` + `/api/v1/writing/analyze` | **HIGH (AUD-02)** |
| **Save / Autosave** | Displays `Saved` even when offline | Show `Unsaved`, `Saving...`, `Saved` (only on HTTP 200), or `Offline (saved locally)` | `PUT /api/v1/writing/drafts/{id}` | **HIGH (AUD-03)** |
| **Floating Action Menu** | Simplify, Cite Reference, Fix Grammar | Contextual text modification chips that replace selected text with revision history | `POST /api/v1/writing/transform` | **VERIFIED** |
| **Afforai Cite Modal** | Multi-source reference manager | Modal search across ingested sources, multi-select citation chips, insert footnote | `GET /api/v1/sources/` | **VERIFIED** |
| **Article Improvements Panel** | Readability suggestions, SEO, tone | Displays flagged sentences with one-click rewrite chips | `/api/v1/writing/suggestions` | **VERIFIED** |

### 2.4 Editorial Studio (`/editorial`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Project Selector** | Shows "No Research Projects Available" when offline | Dynamic dropdown populated from active projects with completed briefs | `GET /api/v1/research/projects` | **HIGH (AUD-06)** |
| **Target Word Count** | Badge `300–500 Words` | Strict word-count adherence bar with visual color feedback (amber < 300, green 300–500, red > 500) | Client calculation | **MEDIUM** |
| **Generation Engine** | Generates newsletter / explainer / opinion | Uses research brief evidence, preserving source citations `[^1]` | `POST /api/v1/editorial/generate` | **HIGH (AUD-06)** |
| **Export Action** | Basic copy | Multi-format export: Markdown (`.md`), Plain Text (`.txt`), and JSON with citations | Client-side export helper | **MEDIUM** |

### 2.5 Research Projects (`/projects`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Project Cards** | Empty state when backend is disconnected | List projects with status (`draft`, `in_progress`, `completed`), source count, brief status | `GET /api/v1/research/projects` | **MEDIUM (AUD-07)** |
| **Search & Filter** | Search input | Instant client-side search by title or description; status filter pills | Client-side state | **LOW** |
| **Destructive Actions** | Direct delete | `ConfirmDialog` modal before deleting; project duplication | `DELETE /api/v1/research/projects/{id}` | **MEDIUM** |

### 2.6 Organization Management (`/organization`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Member List** | Shows 0 members | Lists active members with avatars, emails, role badges (Owner, Admin, Editor, Reviewer, Viewer) | `GET /api/v1/organizations/{id}/members` | **MEDIUM (AUD-08)** |
| **Invitations Table** | Shows 0 pending invitations | Shows invited email, role, expiration date, copy token, and revoke action | `GET /api/v1/organizations/{id}/invitations` | **MEDIUM (AUD-08)** |
| **Invite Modal** | Static modal | Validates email, sends invite via API, updates table without full-page reload | `POST /api/v1/organizations/{id}/invitations` | **MEDIUM** |

### 2.7 AI Reliability & Observability (`/observability`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Telemetry Cards** | 153 requests, 88.9% success, $1.75 cost, 248.3K tokens | Pull from `/api/v1/observability/llm-tracking` or clearly label as "Demonstration Baseline Data" | `GET /api/v1/observability/stats` | **HIGH (AUD-04)** |
| **Benchmark Suite** | "Run 34-Case Benchmark" button | Executes live benchmark runner and updates evaluation table with live pass/fail stats | `POST /api/v1/observability/run-benchmark` | **HIGH (AUD-04)** |
| **Trace Details** | Tool Spans, Claim Verification | Drill-down view into prompt tokens, latency p95/p99, error categories | `GET /api/v1/observability/traces` | **MEDIUM** |

### 2.8 Settings (`/settings`)
| Component | Current Observation | Required Behavior | Backend / API Endpoint | Status & Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Appearance** | Theme switches | Persists selection (`light`, `dark`, `system`) in `localStorage` and `document.documentElement` | Client `localStorage` | **MEDIUM (AUD-09)** |
| **AI Provider Config** | Provider radios (Groq, OpenAI, Anthropic, Gemini) | Read/update active provider; mask API keys; show fallback status | `GET /api/v1/ai/providers` | **MEDIUM** |
| **Security & SSRF** | Read-only security parameters | Displays active SSRF blocklists, allowed protocols, max payload sizes | Client config display | **LOW** |

---

## 3. Implementation Plan & Priority Queue

1. **P0 (Immediate Fixes):**
   - Create `frontend/src/utils/textAnalysis.ts` with comprehensive unit tests for real-time word count, sentence count, reading time, and Flesch score calculation.
   - Refactor `WritingPage.tsx` and `ArticleImprovementsPanel.tsx` to compute statistics synchronously from text, removing all hardcoded `0 words`, `14 sentences`, and `72/100` fallbacks.
   - Implement `frontend/src/context/HealthContext.tsx` with exponential backoff, auto-reconnect, and multi-state connectivity (`CONNECTED`, `CONNECTING`, `UNAVAILABLE`, `DEGRADED`, `AUTH_REQUIRED`).
   - Fix save states in `WritingPage.tsx` so "Saved" is only shown after HTTP 200 persistence confirmation.
2. **P1 (Core Product Workflows):**
   - Wire Research Assistant with robust source ingestion (URL with SSRF validation, PDF/TXT upload, pasted text), status badges, and brief synthesis.
   - Complete Editorial Studio pipeline: link active projects, enforce 300–500 words target bar, preserve citations, and support export.
3. **P2 (Management & Observability):**
   - Wire Projects page search, filter, and delete confirmation.
   - Wire Organization members and invitations API.
   - Label Observability baseline metrics clearly, connect to live backend telemetry, and ensure the 34-case benchmark runner can be triggered.
   - Wire Settings appearance persistence (Light/Dark/System).
4. **P3 (Testing & Documentation):**
   - Create `docs/FRONTEND_BACKEND_API_MAPPING.md` and `docs/KNOWN_ISSUES.md`.
   - Run backend tests, frontend build, and full regression verification.
