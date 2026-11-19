# PHASE 28: FRONTEND-TO-BACKEND API INTEGRATION MATRIX

**Project:** AI Editorial Workspace  
**Target Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Target Branch:** `feat/phase28-frontend-api-integration`  
**Production URL:** `https://ai-editorial-workspace-blue.vercel.app/`  
**Status:** FULLY INTEGRATED & VERIFIED  

---

## 1. Overview

This document maps every primary user journey and interactive frontend component to its corresponding backend API service, REST endpoint, HTTP method, payload structures, authentication requirements, and test statuses.

---

## 2. API Integration Mapping Table

| Feature Domain | UI Component | Frontend Service | Backend Route Path | Method | Request Payload / Params | Response Schema | Auth | Test Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth / Login** | `AuthPage.tsx` | `authService.login` | `/api/v1/auth/login` | POST | `{ email, password, remember_me }` | `{ access_token, user, organization }` | None | `PRODUCTION_VERIFIED` |
| **Auth / Signup** | `AuthPage.tsx` | `authService.register` | `/api/v1/auth/register` | POST | `{ email, password, full_name, organization_name }` | `{ access_token, user, organization }` | None | `PRODUCTION_VERIFIED` |
| **Auth / User Profile** | `UserProfileMenu.tsx` | `authService.getMe` | `/api/v1/auth/me` | GET | None | `{ user, organizations }` | Bearer | `PRODUCTION_VERIFIED` |
| **Auth / Logout** | `UserProfileMenu.tsx` | `authService.logout` | `/api/v1/auth/logout` | POST | None | `{ success, message }` | Bearer | `PRODUCTION_VERIFIED` |
| **Dashboard / Stats** | `DashboardPage.tsx` | `projectService.getStats` | `/api/v1/research/dashboard/stats` | GET | None | `{ total_projects, total_sources, total_drafts, total_editorial }` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Dashboard / Workflow**| `DashboardPage.tsx` | `editorialService.getDashboardStats` | `/api/v1/editorial/dashboard/stats` | GET | None | `{ in_progress, under_review, approved, finalized }` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Projects / List** | `ProjectsPage.tsx` | `researchApi.getProjects` | `/api/v1/projects` | GET | `?skip=0&limit=50` | `ProjectListResponse: { items, total }` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Projects / Create** | `ProjectsPage.tsx`, `Modal.tsx` | `researchApi.createProject` | `/api/v1/projects` | POST | `{ title, description }` | `ProjectResponse` | Bearer | `PRODUCTION_VERIFIED` |
| **Projects / Delete** | `ProjectsPage.tsx`, `ConfirmDialog.tsx` | `researchApi.deleteProject` | `/api/v1/projects/{id}` | DELETE | None | `204 No Content` / `{ status }` | Bearer | `PRODUCTION_VERIFIED` |
| **Research / Get Project**| `ResearchPage.tsx` | `researchApi.getProject` | `/api/v1/projects/{id}` | GET | None | `ProjectResponse: { id, title, sources }` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Research / Add Source** | `ResearchPage.tsx` | `researchApi.addSource` | `/api/v1/projects/{id}/sources` | POST | `{ title, url, source_type }` | `SourceResponse: { id, extraction_status }` | Bearer | `PRODUCTION_VERIFIED` |
| **Research / Retry Extraction**| `ResearchPage.tsx` | `researchApi.extractSource` | `/api/v1/sources/{id}/extract` | POST | None | `SourceResponse` | Bearer | `PRODUCTION_VERIFIED` |
| **Research / Delete Source** | `ResearchPage.tsx` | `researchApi.deleteSource` | `/api/v1/sources/{id}` | DELETE | None | `204 No Content` | Bearer | `PRODUCTION_VERIFIED` |
| **Research / Synthesize Brief**| `ResearchPage.tsx` | `researchApi.generateBrief` | `/api/v1/projects/{id}/brief` | POST | `{ project_id, target_audience }` | `ResearchBriefResponse` | Bearer | `PRODUCTION_VERIFIED` |
| **Research / Get Brief** | `ResearchPage.tsx` | `researchApi.getBrief` | `/api/v1/projects/{id}/brief` | GET | None | `ResearchBriefResponse` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Research / Evidence Graph** | `ResearchPage.tsx` | `researchApi.getEvidence` | `/api/v1/projects/{id}/evidence` | GET | None | `List[VerifiedEvidenceItem]` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Writing / Create Draft** | `WritingPage.tsx` | `writingService.createDraft` | `/api/v1/writing/drafts` | POST | `{ title, original_content, project_id }` | `WritingDraft: { id, word_count, readability_score }` | Bearer | `PRODUCTION_VERIFIED` |
| **Writing / Save Draft** | `WritingPage.tsx` | `writingService.updateDraft` | `/api/v1/writing/drafts/{id}` | PUT | `{ title, original_content }` | `WritingDraft: { id, updated_at }` | Bearer | `PRODUCTION_VERIFIED` |
| **Writing / AI Generation**| `WritingPage.tsx` | `writingService.generateDraft` | `/api/v1/writing/generate` | POST | `{ project_id, topic, style_profile_id }` | `WritingDraft` | Bearer | `PRODUCTION_VERIFIED` |
| **Writing / Style Check** | `WritingPage.tsx` | `writingService.checkStyle` | `/api/v1/writing/drafts/{id}/style-check` | POST | `{ draft_id, content, style_profile_id }` | `StyleCheckResponse: { style_score, issues }` | Bearer | `PRODUCTION_VERIFIED` |
| **Writing / Version History**| `VersionHistoryPanel.tsx` | `versionService.getDraftVersions` | `/api/v1/writing/drafts/{id}/versions` | GET | None | `List[EditorialVersion]` | Bearer / Dev | `PRODUCTION_VERIFIED` |
| **Editorial / Generate Article**| `EditorialPage.tsx` | `editorialService.generateEditorial` | `/api/v1/editorial/generate` | POST | `{ project_id, brief_id, target_word_count }` | `EditorialOutput` | Bearer | `PRODUCTION_VERIFIED` |
| **Editorial / Submit Review**| `EditorialReviewPanel.tsx` | `editorialService.submitReview` | `/api/v1/editorial/outputs/{id}/review` | POST | `{ decision, notes, change_requests }` | `EditorialReview` | Bearer | `PRODUCTION_VERIFIED` |
| **Editorial / Export** | `ExportMenu.tsx` | `editorialService.exportEditorial` | `/api/v1/editorial/outputs/{id}/export` | GET | `?format=markdown|html|txt|json` | `EditorialExportResponse` | Bearer | `PRODUCTION_VERIFIED` |
| **Organization / Members**| `OrganizationPage.tsx` | `authService.getMembers` | `/api/v1/organizations/{id}/members` | GET | None | `List[Membership]` | Bearer | `PRODUCTION_VERIFIED` |
| **Organization / Invite** | `OrganizationPage.tsx` | `authService.inviteMember` | `/api/v1/organizations/{id}/invite` | POST | `{ email, role }` | `Invitation` | Bearer | `PRODUCTION_VERIFIED` |
| **Profile / Update** | `ProfilePage.tsx` | `authService.updateProfile` | `/api/v1/users/me` | PUT | `{ full_name, profile_image }` | `User` | Bearer | `PRODUCTION_VERIFIED` |
| **Profile / Password** | `ProfilePage.tsx` | `authService.changePassword` | `/api/v1/users/me/password` | PUT | `{ current_password, new_password }` | `{ success, message }` | Bearer | `PRODUCTION_VERIFIED` |
| **Settings / Health Probe**| `SettingsPage.tsx` | `healthService.getReadiness` | `/api/v1/health/ready` | GET | None | `{ status, database, db_latency_ms }` | None | `PRODUCTION_VERIFIED` |
| **Observability / Metrics**| `ObservabilityPage.tsx` | `observabilityService.getMetrics` | `/api/v1/reliability/metrics` | GET | None | `AIMetricsResponse` | Bearer / Dev | `PRODUCTION_VERIFIED` |

---

## 3. Interaction & Error Handling Guarantees

1. **Deterministic Error Decoding:** The central Axios client interceptor in `frontend/src/services/api.ts` parses standard backend error envelopes (`error`, `detail`, `request_id`, `code`), maps Pydantic array locations into readable strings, and surfaces friendly toast alerts.
2. **Session Expiry Dispatch:** If any protected API responds with HTTP 401 Unauthorized, a custom `session-expired` event is broadcast, clearing stale local storage credentials and prompting the user to re-authenticate cleanly.
3. **In-Flight Request Deduplication:** Identical GET requests issued simultaneously are deduplicated using a promise map, avoiding redundant network roundtrips.
4. **Zero Silent Failures:** All mutation calls (create, update, delete, review) trigger sonner toasts upon completion and display error modals/toasts upon rejection.
