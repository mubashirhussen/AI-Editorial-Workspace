# AI Editorial Workspace — Known Issues & Resolutions Log

**Audit Phase:** Phase 12 (UI/UX Audit, Backend Integration & Production Refinement)  
**Date:** 2026-11-09  
**Branch:** `feat/phase12-ui-ux-backend-integration`  

---

## 1. Issue Resolution Records

### Issue 1: Backend Unavailable Indicator Across All Screens (P0)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** Red `(!) Backend unavailable` indicator rendered in header on every page. Frontend behaved as if the backend was completely unreachable, and empty fallback states were shown everywhere.
- **Root Cause:**
  1. The local FastAPI server (`uvicorn`) was not running continuously in the development shell.
  2. Health detection had no bounded exponential backoff, manual retry, or network recovery detection.
  3. No centralized React context managed connection state across the application shell.
- **Files Changed:**
  - `frontend/src/context/HealthContext.tsx` (Created)
  - `frontend/src/components/layout/Header.tsx`
  - `frontend/src/App.tsx`
  - `frontend/src/services/api.ts`
- **Fix Implemented:**
  - Created centralized `HealthProvider` with exponential backoff (3s -> 6s -> 12s -> 24s), immediate recheck on window focus, and multi-state indicators (`CONNECTED`, `CONNECTING`, `DEGRADED`, `UNAVAILABLE`, `AUTH_REQUIRED`).
  - Added interactive "Retry" button directly in the status pill.
  - Kept backend process active as background service.
- **Test Performed:**
  - HTTP probe to `/health` and `/api/v1/health` via Vite proxy.
  - Stopped server and verified graceful transition to `UNAVAILABLE`, restarted server and verified instant auto-recovery to `CONNECTED (DB: connected)`.
- **Test Result:** **PASSED.**

---

### Issue 2: Writing Assistant Statistics Inconsistency — 0 Words Displayed (P0)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** In the Writing Assistant, the text editor visibly contained paragraphs of technical prose, but the statistics panel displayed `0 words`, fallback `14 sentences`, `60s reading time`, and hardcoded `72/100` score.
- **Root Cause:**
  - `metrics` was a state variable only populated asynchronously after an HTTP request to `/api/v1/writing/analyze` finished.
  - When the page mounted or before "Audit Quality" was clicked, `metrics` was null.
  - `ArticleImprovementsPanel.tsx` had hardcoded fallbacks: `metrics?.sentence_count ?? 14`, `Math.round((metrics?.reading_time_minutes ?? 1) * 60)`, and `metrics?.readability_score ?? 72`.
- **Files Changed:**
  - `frontend/src/utils/textAnalysis.ts` (Created)
  - `frontend/src/utils/textAnalysis.test.ts` (Created)
  - `frontend/src/pages/WritingPage.tsx`
  - `frontend/src/components/writing/ArticleImprovementsPanel.tsx`
- **Fix Implemented:**
  - Created deterministic client-side text analysis engine calculating exact words, syllables, sentences, paragraphs, reading time, and Flesch Reading Ease score synchronously from the editor text.
  - Wired `useMemo` in `WritingPage.tsx` to derive `liveMetrics` on every keystroke.
  - Removed all hardcoded fallback values (`14`, `72`, `60s`) from `ArticleImprovementsPanel.tsx`.
- **Test Performed:**
  - Automated unit test suite `textAnalysis.test.ts` verifying empty text, single sentences, long sentences, and markdown formatting.
- **Test Result:** **PASSED (100% test pass rate).**

---

### Issue 3: False "Saved" State Displayed While Offline (P0)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** Writing Assistant displayed a green `Saved` badge even when the backend was disconnected or the draft was never actually persisted to the database.
- **Root Cause:**
  - Indicator was based on a simple boolean `!isDirty` (where `isDirty = text !== savedContent`).
  - On page load, `text === savedContent` was true, falsely showing `Saved`.
- **Files Changed:**
  - `frontend/src/pages/WritingPage.tsx`
- **Fix Implemented:**
  - Implemented discrete save state machine: `UNSAVED`, `SAVING`, `SAVED`, `SAVE_FAILED`, `OFFLINE`.
  - Only show `Saved at HH:MM` after receiving HTTP 200 persistence confirmation from the backend.
  - Added automatic local preservation in `localStorage` when offline.
- **Test Performed:**
  - Verified unsaved changes indicator upon typing.
  - Tested successful save displaying timestamp.
  - Tested simulated offline save displaying `Offline (saved locally)`.
- **Test Result:** **PASSED.**

---

### Issue 4: AI Observability Fabricated Metrics Confusion (P0)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** Observability page showed 153 requests, 88.9% success rate, $1.75 cost, and 248.3K tokens without clear distinction between reference benchmark data and live system telemetry.
- **Root Cause:**
  - `ObservabilityPage.tsx` used hardcoded nullish coalescing defaults (`metrics?.total_operations ?? 153`, etc.) whenever live backend telemetry had 0 operations.
- **Files Changed:**
  - `frontend/src/pages/ObservabilityPage.tsx`
- **Fix Implemented:**
  - Added clear mode selector: `Live System Telemetry` vs `Demonstration Baseline Reference Data`.
  - When live telemetry has 0 operations, accurately display 0 requests, 100% success, $0.00 cost, and 0 tokens.
  - Added a prominent badge and a 1-click "Run Live 34-Case Benchmark" button to populate real database telemetry.
- **Test Performed:**
  - Verified live 0-state display and switching to baseline reference mode.
  - Verified live benchmark execution calling `POST /api/v1/observability/evaluate`.
- **Test Result:** **PASSED.**

---

### Issue 5: Research Projects Missing Management Workflows (P1)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** Projects page lacked creation dialog, status filters, and duplicate operations.
- **Root Cause:**
  - Incomplete page controls; project creation was only accessible from the Research page.
- **Files Changed:**
  - `frontend/src/pages/ProjectsPage.tsx`
- **Fix Implemented:**
  - Added "New Project" modal directly on the Projects page.
  - Added status filtering tabs: `All Projects`, `Completed`, `Draft`, `In Progress`.
  - Added project duplication capability.
  - Added confirmation dialog for project deletion.
- **Test Performed:**
  - Verified project filtering, creation modal, and duplication.
- **Test Result:** **PASSED.**

---

### Issue 6: Settings Appearance Preferences Non-Persistent (P2)
- **Status:** **FIXED AND VERIFIED**
- **Issue Description:** Interface theme (System / Light / Dark), transparent sidebar, and table density preferences reset to defaults upon browser refresh.
- **Root Cause:**
  - State was held only in React memory and was not synced to `localStorage`.
- **Files Changed:**
  - `frontend/src/pages/SettingsPage.tsx`
- **Fix Implemented:**
  - Added `localStorage` persistence for `editorial_theme`, `editorial_transparent_sidebar`, `editorial_table_view`, and `editorial_sidebar_feature`.
  - Added mount `useEffect` to apply the stored theme to `document.documentElement` on initial application load.
- **Test Performed:**
  - Changed theme to Dark, refreshed page, verified Dark theme persisted.
  - Changed theme to Light, refreshed page, verified Light theme persisted.
- **Test Result:** **PASSED.**
