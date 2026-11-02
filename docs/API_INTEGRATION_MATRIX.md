# API Integration & Contract Matrix

**Base URL:** `/api/v1`  
**Authentication Scheme:** `Bearer <JWT>` (Session header or Authorization Bearer)  
**Standard Response Headers:** `X-Request-ID`, `Content-Type: application/json`  

---

## Complete API Route Catalog

| Method | Endpoint | Description | Auth Level | Request Schema | Response Schema | Frontend Consumer / Caller |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/health` | Deep application & DB health probe | Public | None | `HealthStatus` | `Header.tsx`, `healthService.ts` |
| `GET` | `/health/live` | Process liveness probe | Public | None | `{"status": "live"}` | Docker & Kubernetes probes |
| `GET` | `/health/ready` | Deep database connectivity check | Public | None | `{"status": "ready"}` | Load balancers |
| `POST` | `/auth/register` | User registration & org creation | Public | `UserRegisterRequest` | `AuthResponse` | `AuthPage.tsx`, `authService.ts` |
| `POST` | `/auth/login` | Email/password JWT login | Public | `UserLoginRequest` | `AuthResponse` | `AuthPage.tsx`, `authService.ts` |
| `POST` | `/auth/refresh` | Rotate and refresh access token | Authenticated | `TokenRefreshRequest` | `AuthResponse` | Axios response interceptor |
| `GET` | `/auth/me` | Current user profile & organizations | Authenticated | None | `UserProfileResponse` | `AuthContext.tsx`, `UserProfileMenu.tsx` |
| `POST` | `/auth/logout` | Token revocation & session termination | Authenticated | None | `{"message": "Logged out"}` | `UserProfileMenu.tsx`, `authService.ts` |
| `POST` | `/auth/reset-password` | Request password reset token | Public | `PasswordResetRequest` | `{"message": "..."}` | `AuthPage.tsx` |
| `POST` | `/auth/change-password` | Update user password | Authenticated | `PasswordChangeRequest` | `{"message": "..."}` | `SettingsPage.tsx` |
| `GET` | `/organizations` | List organizations user belongs to | Authenticated | None | `List[OrganizationResponse]` | `OrganizationSwitcher.tsx` |
| `POST` | `/organizations` | Create new organization workspace | Authenticated | `OrganizationCreateRequest`| `OrganizationResponse` | `OrganizationPage.tsx` |
| `GET` | `/projects` | List research projects | Authenticated | None | `List[ProjectResponse]` | `DashboardPage.tsx`, `ProjectsPage.tsx` |
| `POST` | `/projects` | Create research project | Authenticated | `ProjectCreate` | `ProjectResponse` | `ProjectsPage.tsx`, `ResearchPage.tsx` |
| `GET` | `/projects/{id}` | Get research project details | Authenticated | None | `ProjectDetailResponse` | `ResearchPage.tsx`, `EditorialPage.tsx` |
| `POST` | `/research/projects/{id}/sources` | Ingest source (Web URL or text) | Authenticated | `SourceCreate` | `SourceResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `POST` | `/sources/extract` | Trigger socket-level SSRF scrape | Authenticated | `SourceExtractRequest` | `SourceResponse` | `ResearchPage.tsx`, `extraction_service.py` |
| `PUT` | `/sources/{id}` | In-place update (Paste text fallback) | Authenticated | `SourceUpdate` | `SourceResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `DELETE`| `/sources/{id}` | Remove source from project | Authenticated | None | `{"success": true}` | `ResearchPage.tsx`, `researchService.ts` |
| `POST` | `/research/projects/{id}/generate-brief` | Synthesize 10-section brief | Authenticated | None | `ResearchBriefResponse` | `ResearchPage.tsx`, `researchService.ts` |
| `GET` | `/research/projects/{id}/brief` | Retrieve generated brief | Authenticated | None | `ResearchBriefResponse` | `ResearchPage.tsx`, `EditorialPage.tsx` |
| `POST` | `/research/projects/{id}/intelligence` | Cross-source graph analysis | Authenticated | None | `IntelligenceGraphResponse`| `ResearchIntelligenceDashboard.tsx` |
| `GET` | `/writing/drafts` | List drafts in workspace | Authenticated | None | `List[WritingDraftResponse]` | `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/drafts` | Create new writing draft | Authenticated | `DraftCreate` | `WritingDraftResponse` | `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/analyze` | Execute 6-check writing audit | Authenticated | `WritingAnalysisRequest`| `WritingAnalysisResponse` | `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/drafts/{id}/suggestions/{s_id}/accept` | Accept rewrite suggestion | Authenticated | None | `SuggestionAcceptResponse`| `WritingPage.tsx`, `writingService.ts` |
| `POST` | `/writing/drafts/{id}/suggestions/{s_id}/reject` | Reject rewrite suggestion | Authenticated | None | `SuggestionRejectResponse`| `WritingPage.tsx`, `writingService.ts` |
| `GET` | `/editorial` | List publication editorials | Authenticated | None | `List[EditorialResponse]` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial/generate` | Generate 300–500w editorial | Authenticated | `EditorialGenerateRequest` | `EditorialResponse` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial/{id}/review` | Trigger AI review | Authenticated | None | `EditorialResponse` | `EditorialPage.tsx`, `editorialService.ts` |
| `POST` | `/editorial-review/{id}/status` | Transition review state machine | Authenticated | `StatusTransitionRequest` | `EditorialResponse` | `EditorialReviewWorkflow.tsx` |
| `POST` | `/editorial-review/{id}/comments` | Add inline reviewer comment | Authenticated | `ReviewCommentRequest` | `ReviewCommentResponse` | `EditorialReviewWorkflow.tsx` |
| `GET` | `/styles` | List style profiles | Authenticated | None | `List[StyleProfileResponse]`| `SettingsPage.tsx`, `styleService.ts` |
| `POST` | `/styles` | Create custom style guide | Authenticated | `StyleProfileCreate` | `StyleProfileResponse` | `SettingsPage.tsx`, `styleService.ts` |
| `GET` | `/documents/{type}/{id}/versions` | Get version timeline | Authenticated | None | `List[VersionResponse]` | `VersionHistoryPanel.tsx` |
| `GET` | `/documents/{type}/{id}/compare` | Compute Myers visual diff | Authenticated | None | `VersionComparisonResponse`| `VersionComparison.tsx` |
| `POST` | `/documents/{type}/{id}/versions/{v}/restore` | Non-destructive rollback | Authenticated | None | `VersionRestoreResponse` | `VersionHistoryPanel.tsx` |
| `GET` | `/dashboard/metrics` | Real-time database metrics | Authenticated | None | `DashboardMetricsResponse` | `DashboardPage.tsx` |
| `GET` | `/dashboard/activity` | Activity event feed | Authenticated | None | `List[ActivityEventResponse]`| `DashboardPage.tsx` |
| `GET` | `/integrations/providers` | List AI providers & status | Authenticated | None | `List[ProviderConfigResponse]`| `SettingsPage.tsx` |
| `POST` | `/integrations/providers/{p}/config` | Save encrypted provider key | Authenticated | `ProviderConfigSave` | `ProviderConfigResponse` | `SettingsPage.tsx` |
| `POST` | `/integrations/providers/{p}/validate` | Live connection validation | Authenticated | None | `{"valid": bool}` | `SettingsPage.tsx` |
| `GET` | `/ai/providers` | Active AI provider metadata | Authenticated | None | `AIProviderMetadata` | `SettingsPage.tsx`, `AIRouter` |
