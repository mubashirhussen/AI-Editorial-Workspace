# Frontend-to-Backend API Mapping Specification

**Project:** AI Editorial Workspace  
**Date:** 2026-11-09  
**Branch:** `feat/phase12-ui-ux-backend-integration`  

This document provides a comprehensive traceability mapping between every frontend user interface component, its HTTP API invocation, the corresponding FastAPI backend route, and the underlying SQLAlchemy database model.

---

## 1. Application Shell & Health Management

| Feature | Frontend Component | API Method | Backend Route | Database Entity / Service | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **System Health Diagnostics** | `HealthContext.tsx`, `Header.tsx` | `GET` | `/api/v1/health` | `monitoring_service`, DB connection probe | **VERIFIED** |
| **Platform Liveness Probe** | `HealthContext.tsx` | `GET` | `/health/live` | Process runtime check | **VERIFIED** |
| **Platform Readiness Probe** | `HealthContext.tsx` | `GET` | `/health/ready` | SQLite / PostgreSQL pool probe | **VERIFIED** |
| **Platform Startup Probe** | Kubernetes / Docker Engine | `GET` | `/health/startup` | Alembic schema verification | **VERIFIED** |

---

## 2. Authentication & Multi-Tenancy

| Feature | Frontend Component | API Method | Backend Route | Database Entity | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **User Sign In** | `AuthPage.tsx` | `POST` | `/api/v1/auth/login` | `User`, `UserSession` | **VERIFIED** |
| **User Registration** | `AuthPage.tsx` | `POST` | `/api/v1/auth/register` | `User`, `Organization` | **VERIFIED** |
| **Organization Switcher** | `OrganizationSwitcher.tsx` | `GET` | `/api/v1/organizations` | `Organization`, `OrganizationMembership` | **VERIFIED** |
| **List Team Members** | `OrganizationPage.tsx` | `GET` | `/api/v1/organizations/{id}/members` | `OrganizationMembership`, `User` | **VERIFIED** |
| **Update Member Role** | `OrganizationPage.tsx` | `PUT` | `/api/v1/organizations/{id}/members/{uid}/role` | `OrganizationMembership` | **VERIFIED** |
| **Remove Member** | `OrganizationPage.tsx` | `DELETE` | `/api/v1/organizations/{id}/members/{uid}` | `OrganizationMembership` | **VERIFIED** |
| **List Pending Invites** | `OrganizationPage.tsx` | `GET` | `/api/v1/organizations/{id}/invitations` | `OrganizationInvitation` | **VERIFIED** |
| **Create Invitation** | `OrganizationPage.tsx` | `POST` | `/api/v1/organizations/{id}/invitations` | `OrganizationInvitation` | **VERIFIED** |
| **Revoke Invitation** | `OrganizationPage.tsx` | `DELETE` | `/api/v1/organizations/{id}/invitations/{iid}` | `OrganizationInvitation` | **VERIFIED** |
| **Accept Invitation** | `AuthPage.tsx` | `POST` | `/api/v1/organizations/invitations/{tok}/accept` | `OrganizationMembership` | **VERIFIED** |

---

## 3. Research Assistant & Local Library

| Feature | Frontend Component | API Method | Backend Route | Database Entity | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **List Projects** | `ProjectsPage.tsx`, `DashboardPage.tsx` | `GET` | `/api/v1/research/projects` | `ResearchProject` | **VERIFIED** |
| **Create Project** | `ProjectsPage.tsx`, `ResearchPage.tsx` | `POST` | `/api/v1/research/projects` | `ResearchProject` | **VERIFIED** |
| **Get Project Details** | `ResearchPage.tsx` | `GET` | `/api/v1/research/projects/{id}` | `ResearchProject`, `Source` | **VERIFIED** |
| **Delete Project** | `ProjectsPage.tsx` | `DELETE` | `/api/v1/research/projects/{id}` | `ResearchProject` (cascade) | **VERIFIED** |
| **Ingest URL Source** | `ResearchPage.tsx` | `POST` | `/api/v1/sources/` | `Source`, `SourceAnalysis` | **VERIFIED** |
| **Upload Document** | `ResearchPage.tsx`, `LocalLibraryView.tsx` | `POST` | `/api/v1/sources/upload` | `Source`, File Storage | **VERIFIED** |
| **Ingest Text Snippet** | `ResearchPage.tsx` | `POST` | `/api/v1/sources/` | `Source` | **VERIFIED** |
| **Delete Source** | `ResearchPage.tsx` | `DELETE` | `/api/v1/sources/{id}` | `Source` | **VERIFIED** |
| **Synthesize Brief** | `ResearchPage.tsx` | `POST` | `/api/v1/research/synthesize` | `ResearchBrief`, `ResearchEvidence` | **VERIFIED** |
| **Fetch Evidence Alignment**| `ResearchPage.tsx` | `GET` | `/api/v1/research/projects/{id}/claims` | `ResearchClaim`, `ResearchEvidence` | **VERIFIED** |
| **Knowledge Graph** | `ResearchIntelligenceDashboard.tsx` | `GET` | `/api/v1/research/intelligence/graph` | `ResearchEntity`, `ResearchRelationship`| **VERIFIED** |
| **Dashboard KPI Metrics** | `DashboardPage.tsx` | `GET` | `/api/v1/research/dashboard/stats` | Aggregated Project/Source Stats | **VERIFIED** |

---

## 4. Writing Assistant & Editorial Studio

| Feature | Frontend Component | API Method | Backend Route | Database Entity | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Real-time Statistics** | `WritingPage.tsx`, `ArticleImprovementsPanel.tsx` | Client Sync | Client `textAnalysis.ts` | Deterministic Client Model | **VERIFIED** |
| **Quality Audit & Linter**| `WritingPage.tsx`, `InlineReadabilityLinter.tsx` | `POST` | `/api/v1/writing/analyze` | `WritingDraft`, `WritingSuggestion` | **VERIFIED** |
| **Save / Autosave Draft** | `WritingPage.tsx` | `PUT` / `POST` | `/api/v1/writing/drafts/{id}` | `WritingDraft` | **VERIFIED** |
| **Version History** | `VersionHistoryPanel.tsx` | `GET` | `/api/v1/writing/drafts/{id}/versions` | `EditorialVersion` | **VERIFIED** |
| **Revert Version** | `VersionHistoryPanel.tsx` | `POST` | `/api/v1/writing/drafts/{id}/versions/{vid}/revert` | `WritingDraft`, `EditorialVersion` | **VERIFIED** |
| **Contextual Rewrite** | `WritingPage.tsx`, `InlineReadabilityLinter.tsx` | `POST` | `/api/v1/writing/transform` | AI Provider Engine | **VERIFIED** |
| **Generate Editorial** | `EditorialPage.tsx` | `POST` | `/api/v1/editorial/generate` | `EditorialOutput` | **VERIFIED** |
| **Save Editorial Article** | `EditorialPage.tsx` | `POST` / `PUT` | `/api/v1/editorial/outputs` | `EditorialOutput` | **VERIFIED** |
| **List Saved Editorials** | `EditorialPage.tsx` | `GET` | `/api/v1/editorial/projects/{id}/outputs` | `EditorialOutput` | **VERIFIED** |
| **Export Formats** | `EditorialToolbar.tsx` | Client Helper | Local Blob Download (`.md`, `.txt`, `.json`) | `EditorialOutput` | **VERIFIED** |

---

## 5. AI Reliability & Observability

| Feature | Frontend Component | API Method | Backend Route | Database Entity | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **LLM Tracking Metrics** | `ObservabilityPage.tsx` | `GET` | `/api/v1/observability/ai-metrics` | `ProviderUsageRecord` | **VERIFIED** |
| **Operations Telemetry** | `ObservabilityPage.tsx` | `GET` | `/api/v1/observability/operations` | `ProviderUsageRecord` | **VERIFIED** |
| **Prompt Version Registry** | `ObservabilityPage.tsx` | `GET` | `/api/v1/observability/prompts` | `prompt_registry` (code-managed) | **VERIFIED** |
| **Run 34-Case Benchmark** | `ObservabilityPage.tsx`, `SettingsPage.tsx` | `POST` | `/api/v1/observability/evaluate` | `EvaluationRunner` | **VERIFIED** |
| **Fact Claim Verification**| `ObservabilityPage.tsx` | `POST` | `/api/v1/observability/verify-claim` | `unu_claim_service` | **VERIFIED** |

---

## 6. Settings & Configuration

| Feature | Frontend Component | API Method | Backend Route | Database Entity | Status |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Appearance Preferences** | `SettingsPage.tsx` | Local Sync | `localStorage` (`editorial_theme`, etc.) | Client Storage | **VERIFIED** |
| **Active AI Connections** | `SettingsPage.tsx` | `GET` | `/api/v1/ai/connections` | `AIProviderConfig` | **VERIFIED** |
| **Test AI Connection** | `SettingsPage.tsx` | `POST` | `/api/v1/ai/connections/{id}/test` | AI Provider Probe | **VERIFIED** |
| **Rotate AI API Key** | `SettingsPage.tsx` | `POST` | `/api/v1/ai/connections/{id}/rotate` | `AIProviderConfig` | **VERIFIED** |
| **Health Diagnostics** | `SettingsPage.tsx` | `GET` | `/health` | DB, Redis, AI Diagnostics | **VERIFIED** |
