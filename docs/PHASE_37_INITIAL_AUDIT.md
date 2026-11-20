# Phase 37 Initial Repository Audit: Product Analytics & User Journey Intelligence

**Project:** AI Editorial Workspace — This Week in AI  
**Audit Date:** November 2026  
**Auditor:** Senior Product Analytics & Forward Deployed Engineer  
**Target Branch:** `feat/phase37-product-analytics-user-journeys`

---

## 1. Executive Summary

This initial audit evaluates the existing codebase of the **AI Editorial Workspace** against the requirements of **Phase 37: Advanced Product Analytics, User Journey Intelligence, Feature Adoption & Privacy-Conscious Metrics**.

While Phase 36 established operational health monitoring, error categorization, correlation IDs, and an in-app user feedback system, the platform currently lacks a dedicated, privacy-preserving, durable product analytics and user journey intelligence architecture. Existing analytics capabilities are limited to a prototype `UsageEvent` model and basic funnel counters that lack session tracking, pseudonymous user journeys, event deduplication, workflow transition states, and frontend visualization.

---

## 2. Existing Repository State & Component Audit

### 2.1 Backend Architecture & API Routes
- **FastAPI Core:** `backend/app/main.py` mounts API routes under `settings.API_V1_PREFIX` (`/api/v1`).
- **Existing Analytics Route:** `backend/app/api/routes/analytics.py` provides 3 rudimentary endpoints:
  - `GET /api/v1/analytics/funnel`
  - `GET /api/v1/analytics/events`
  - `POST /api/v1/analytics/track`
- **Existing Service:** `backend/app/services/analytics_service.py` provides basic tracking to the `UsageEvent` table. It uses a naive dictionary counter and lacks workflow lifecycle semantics (e.g. `started`, `completed`, `failed`, `abandoned`), time-to-completion distributions, and feature adoption ratios.
- **Missing Endpoints:**
  - `POST /api/v1/analytics/events` (standardized first-party event ingestion with schema validation and deduplication)
  - `GET /api/v1/analytics/overview` (high-level executive product metrics)
  - `GET /api/v1/analytics/workflows` (workflow lifecycle metrics for research, writing, and editorial journeys)
  - `GET /api/v1/analytics/funnels` (stage-by-stage funnel progression rates)
  - `GET /api/v1/analytics/features` (feature adoption metrics and failure rates)
  - `GET /api/v1/analytics/trends` (time-series usage distributions)
  - `GET /api/v1/analytics/health` (subsystem health, ingestion stats, and privacy enforcement metrics)
  - `POST /api/v1/analytics/retention/cleanup` (enforcement of data retention policies)
  - `GET / PUT /api/v1/analytics/privacy-preference` (user-level analytics opt-out)

### 2.2 Database Schema & Migration Status
- **Current Alembic Head:** `ae5f6a7b8c9d` (`ae5f6a7b8c9d_add_user_feedback_table.py` from Phase 36).
- **Existing Entity (`UsageEvent`):**
  - Minimal schema: `id`, `organization_id`, `metric_name`, `metric_value`, `tags_json`, `timestamp`.
  - Missing critical product analytics dimensions:
    - `event_version`
    - `user_pseudonym` (cryptographically salted pseudonym for journey correlation without PII)
    - `project_id` foreign key
    - `workflow_type` ('research', 'writing', 'editorial', etc.)
    - `workflow_id` (journey instance correlation ID)
    - `session_id` (client session reference)
    - `source` ('backend' vs 'frontend')
    - `status` ('started', 'completed', 'failed', 'abandoned')
    - `duration_ms` (operation/journey elapsed execution time)
    - `dedup_hash` (idempotency key for preventing duplicate event ingestion)
- **Required New Model & Migration:**
  - A production-grade `AnalyticsEvent` table with appropriate composite indexes (`ix_analytics_org_workflow`, `ix_analytics_event_time`, `ix_analytics_pseudonym_time`, `ix_analytics_dedup`).
  - An `AnalyticsPrivacyPreference` table supporting privacy controls (opt-out).
  - A formal Alembic migration script (`bf6a7b8c9d0e_add_analytics_event_and_privacy_tables.py`).

### 2.3 Frontend Architecture & Navigation
- **Routing:** `frontend/src/App.tsx` configures routes for Dashboard, Research, Writing, Editorial, Projects, Organization, Observability, Profile, and Settings.
- **Navigation:** `frontend/src/components/layout/Sidebar.tsx` currently has no entry for "Product Analytics".
- **Observability vs Analytics Separation:**
  - `/observability` focuses strictly on infrastructure, server error logs, request rate, and database uptime (Phase 36).
  - No dedicated UI currently exists for **Product Analytics**, **Funnel Conversion**, **User Journey Bottlenecks**, or **Feature Adoption**.
- **Missing Frontend Artifacts:**
  - `frontend/src/pages/AnalyticsPage.tsx`: Interactive product analytics dashboard with time-range filtering, funnel visualization, feature adoption matrices, and friction analysis.
  - `frontend/src/services/analyticsService.ts`: Type-safe client library communicating with `/api/v1/analytics/*`.
  - Non-blocking client-side analytics tracker (`frontend/src/utils/analyticsTracker.ts`) with opt-out checks and duplicate suppression.

### 2.4 Privacy & Security Risks
- **Data Leakage Risk:** Client and server-side tracking must never capture raw document text, LLM prompts, user emails, passwords, API keys, or private source URLs.
- **Tenant Isolation:** Cross-tenant analytics querying must be strictly blocked at the database query level using the authenticated user's active `organization_id`.
- **Client Spoofing:** Critical workflow completion metrics must rely on authoritative **server-side** events rather than trusting arbitrary client payloads.
- **Denial of Service & DB Bloat:** Without deduplication and configurable retention policies, repetitive actions could inflate the database.

---

## 3. Implementation Strategy for Phase 37

1. **Database Schema & Migration:**
   - Define `AnalyticsEvent` and `AnalyticsPrivacyPreference` in `backend/app/models/base.py`.
   - Author Alembic migration `backend/alembic/versions/bf6a7b8c9d0e_add_analytics_event_and_privacy_tables.py`.
   - Upgrade database to head and update `test_phase3_database_integrity.py`.
2. **Standardized Event Taxonomy & Privacy Engine:**
   - Implement pseudonym generation via SHA-256 HMAC of `user_id`.
   - Implement strict property allowlisting and sensitive field rejection (`prompt`, `content`, `text`, `password`, `token`, `secret`, `key`, `email`).
   - Implement event deduplication via SHA-256 idempotency hash.
3. **Backend Service & API Routes:**
   - Extend `backend/app/services/analytics_service.py` with multi-tenant filtering, workflow aggregations, funnel calculators, and retention cleanup.
   - Expand `backend/app/api/routes/analytics.py` with the complete set of required endpoints.
   - Author authoritative server-side event tracking hooks into core workflows (Research source ingestion & brief synthesis, Writing draft creation & AI improvement, Editorial generation, review, & approval).
4. **Frontend Implementation:**
   - Build `frontend/src/services/analyticsService.ts`.
   - Build `frontend/src/pages/AnalyticsPage.tsx` with responsive KPI cards, funnel progression diagrams, feature adoption graphs, and workflow friction analysis.
   - Integrate route `/analytics` in `frontend/src/App.tsx` and navigation item in `frontend/src/components/layout/Sidebar.tsx`.
5. **Testing & Verification:**
   - Write comprehensive backend tests in `backend/tests/test_phase37_product_analytics.py`.
   - Verify frontend production build (`npm --prefix frontend run build`).
   - Execute all 310+ test cases to confirm 100% regression stability.
6. **Documentation Deliverables:**
   - `docs/PHASE_37_INITIAL_AUDIT.md` (this file)
   - `docs/PHASE_37_ANALYTICS_EVENT_TAXONOMY.md`
   - `docs/PHASE_37_PRODUCT_METRICS_DEFINITION.md`
   - `docs/PHASE_37_PRIVACY_AND_DATA_RETENTION.md`
   - `docs/PHASE_37_USER_JOURNEY_ANALYSIS.md`
   - `docs/PHASE_37_ANALYTICS_SECURITY_AUDIT.md`
   - `docs/PHASE_37_IMPLEMENTATION_REPORT.md`
