# API Integration & Contract Matrix

**Base URL:** `/api/v1`  
**Authentication Scheme:** `Bearer <JWT>` (Optional fallback to default workspace owner in local dev mode)  
**Standard Response Headers:** `X-Request-ID`, `Content-Type: application/json`

---

## Endpoint Catalog

| Method | Endpoint | Description | Auth Level | Request Schema | Response Schema | Frontend Consumer |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/health` | Application & DB health status | Public | None | `HealthStatus` | `Header.tsx`, `healthService.ts` |
| `GET` | `/health/live` | Process liveness probe | Public | None | `{"status": "live"}` | Kubernetes / Docker probes |
| `POST` | `/auth/register` | User registration & org creation | Public | `UserRegisterRequest` | `AuthResponse` | `AuthContext.tsx`, `authService.ts` |
| `POST` | `/auth/login` | Email/password JWT login | Public | `UserLoginRequest` | `AuthResponse` | `AuthContext.tsx`, `authService.ts` |
| `GET` | `/auth/me` | Current user profile & orgs | Authenticated | None | `UserProfileResponse` | `AuthContext.tsx`, `UserProfileMenu.tsx` |
| `POST` | `/auth/logout` | Token revocation / sign-out | Authenticated | None | `{"message": "Logged out"}` | `UserProfileMenu.tsx`, `authService.ts` |
| `GET` | `/organizations` | List user organizations | Authenticated | None | `List[OrganizationResponse]` | `OrganizationSwitcher.tsx` |
| `POST` | `/organizations` | Create new organization | Authenticated | `OrganizationCreateRequest`| `OrganizationResponse` | `OrganizationPage.tsx` |
| `GET` | `/projects` | List research projects | Authenticated | None | `List[ProjectResponse]` | `DashboardPage.tsx`, `ProjectsPage.tsx` |
| `POST` | `/projects` | Create research project | Authenticated | `ProjectCreate` | `ProjectResponse` | `ProjectsPage.tsx`, `ResearchPage.tsx` |
| `GET` | `/projects/{id}` | Get research project by ID | Authenticated | None | `ProjectDetailResponse` | `ResearchPage.tsx`, `EditorialPage.tsx` |
| `POST` | `/research/projects/{id}/sources` | Ingest source (URL or text) | Authenticated | `SourceCreate` | `SourceResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `PUT` | `/sources/{id}` | Update source content / title | Authenticated | `SourceUpdate` | `SourceResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `DELETE`| `/sources/{id}` | Remove source from project | Authenticated | None | `{"success": true}` | `ResearchPage.tsx`, `researchService.ts` |
| `POST` | `/sources/{id}/extract` | Re-trigger content extraction | Authenticated | None | `SourceResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `POST` | `/research/projects/{id}/generate-brief` | Synthesize research brief | Authenticated | None | `ResearchBriefResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `GET` | `/research/projects/{id}/brief` | Get generated research brief | Authenticated | None | `ResearchBriefResponse` | `ResearchPage.tsx`, `EditorialPage.tsx` |
| `POST` | `/research/projects/{id}/intelligence` | Cross-source graph analysis | Authenticated | None | `IntelligenceGraphResponse`| `ResearchIntelligenceDashboard.tsx` |
| `GET` | `/writing/drafts` | List drafts | Authenticated | None | `List[WritingDraftResponse]` | `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/analyze` | Execute 6-check writing audit | Authenticated | `WritingAnalysisRequest`| `WritingAnalysisResponse` | `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/drafts/{id}/suggestions/{s_id}/accept` | Accept rewrite suggestion | Authenticated | None | `SuggestionAcceptResponse`| `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/drafts/{id}/suggestions/{s_id}/reject` | Reject rewrite suggestion | Authenticated | None | `SuggestionRejectResponse`| `WritingPage.tsx`, `writingService.ts` |
| `GET` | `/editorial` | List editorial outputs | Authenticated | None | `List[EditorialResponse]` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial/generate` | Generate 300–500w editorial | Authenticated | `EditorialGenerateRequest` | `EditorialResponse` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial/{id}/review` | Trigger AI review | Authenticated | None | `EditorialResponse` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial-review/{id}/status` | Transition workflow status | Authenticated | `StatusTransitionRequest` | `EditorialResponse` | `EditorialReviewWorkflow.tsx` |
| `POST` | `/editorial-review/{id}/comments` | Add reviewer comment | Authenticated | `ReviewCommentRequest` | `ReviewCommentResponse` | `EditorialReviewWorkflow.tsx` |
| `GET` | `/styles` | List style profiles | Authenticated | None | `List[StyleProfileResponse]`| `SettingsPage.tsx`, `styleService.ts` |
| `POST` | `/styles` | Create style profile | Authenticated | `StyleProfileCreate` | `StyleProfileResponse` | `SettingsPage.tsx`, `styleService.ts` |
| `GET` | `/documents/{type}/{id}/versions` | Get version timeline | Authenticated | None | `List[VersionResponse]` | `VersionHistoryPanel.tsx` |
| `GET` | `/documents/{type}/{id}/compare` | Compute text Myers diff | Authenticated | None | `VersionComparisonResponse`| `VersionComparison.tsx` |
| `POST` | `/documents/{type}/{id}/versions/{v}/restore` | Non-destructive rollback | Authenticated | None | `VersionRestoreResponse` | `VersionHistoryPanel.tsx` |
