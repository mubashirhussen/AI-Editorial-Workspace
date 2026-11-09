# AI Editorial Workspace — Complete Frontend-to-Backend Integration Traceability

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Phase:** Phase 13 — Complete System Integration & Functional Bug Elimination  
**Date:** November 2026  
**Auditor:** Senior Full-Stack Architect  
**Status:** **VERIFIED**

---

## 1. Integration Traceability Architecture

Every user action across the 8 primary application modules flows through a deterministic 5-step pathway:
$$\text{Frontend Component} \longrightarrow \text{API Client Function} \longrightarrow \text{FastAPI Endpoint} \longrightarrow \text{Domain Service} \longrightarrow \text{SQLAlchemy Model & DB Operation}$$

---

## 2. Comprehensive Traceability Matrix

### 2.1 Workspace Overview & Dashboard
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Workspace Stats** | `DashboardPage.tsx` | `projectService.getStats()` | `GET /api/v1/dashboard/metrics` | `dashboard_service.py` | `ResearchProject`, `Source`, `WritingDraft` (Count queries scoped to org) |
| **Editorial Breakdown** | `DashboardPage.tsx` | `editorialService.getDashboardStats()` | `GET /api/v1/editorial/stats` | `editorial_service.py` | `EditorialOutput`, `EditorialReview` (Aggregate queries) |
| **Recent Activity Feed** | `DashboardPage.tsx` | `auditService.getRecentActivity()` | `GET /api/v1/dashboard/activity` | `audit_service.py` | `AuditLog`, `UserActivityLog` (Ordered by `created_at DESC` limit 10) |

### 2.2 Research Assistant & Source Ingestion
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ingest Article URL** | `ResearchPage.tsx` | `sourceService.createFromUrl()` | `POST /api/v1/sources` | `source_service.py` + `extraction_service.py` | `Source` (Insert with `extraction_status='PENDING'`) |
| **Upload Document (PDF/DOCX)**| `ResearchPage.tsx` | `sourceService.uploadFile()` | `POST /api/v1/sources/upload` | `source_service.py` + `document_parser.py` | `Source` (Insert binary metadata & parsed text) |
| **Paste Raw Text** | `ResearchPage.tsx` | `sourceService.createFromText()` | `POST /api/v1/sources` | `source_service.py` | `Source` (Insert `raw_content` and extract entities) |
| **List Ingested Sources** | `LocalLibraryView.tsx`| `sourceService.getByProject()` | `GET /api/v1/sources?project_id=...` | `source_service.py` | `Source` (List filtered by `project_id`, `deleted_at IS NULL`) |
| **Generate Research Brief** | `ResearchPage.tsx` | `researchService.generateBrief()` | `POST /api/v1/research/briefs` | `synthesis_service.py` | `ResearchBrief` (Create summary, key points, newsletter angles) |
| **Evidence Alignment** | `ResearchPage.tsx` | `researchService.getClaims()` | `GET /api/v1/research/claims` | `unu_claim_service.py` | `ResearchClaim`, `ResearchEvidence` (Fetch verified facts & excerpts) |
| **Knowledge Graph** | `KnowledgeGraphModal.tsx`| `researchService.getEntities()` | `GET /api/v1/research-intelligence/entities` | `research_intelligence.py` | `ResearchEntity`, `ResearchRelationship` (Read nodes & edges) |

### 2.3 Writing Assistant & Quality Auditor
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Create Writing Draft** | `WritingPage.tsx` | `writingService.createDraft()` | `POST /api/v1/drafts` | `writing_service.py` | `WritingDraft` (Insert title, initial content, word count) |
| **Fetch Draft & Suggestions**| `WritingPage.tsx` | `writingService.getDraft()` | `GET /api/v1/drafts/{id}` | `writing_service.py` | `WritingDraft`, `WritingSuggestion` (Read draft & active lint items) |
| **Save Draft Updates** | `WritingPage.tsx` | `writingService.updateDraft()` | `PUT /api/v1/drafts/{id}` | `writing_service.py` | `WritingDraft` (Update `revised_content`, `updated_at`, recalculate stats) |
| **Execute Hemingway Audit** | `WritingPage.tsx` | `writingService.auditQuality()` | `POST /api/v1/drafts/{id}/audit` | `writing_analyzer.py` | `WritingSuggestion` (Bulk insert detected hard sentences, passive voice) |
| **Accept Rewrite Suggestion** | `WritingPage.tsx` | `writingService.acceptSuggestion()` | `POST /api/v1/drafts/{id}/suggestions/{s_id}` | `writing_service.py` | `WritingSuggestion` (Set `status='ACCEPTED'`), `WritingDraft` (Update text) |
| **Snapshot Version** | `WritingPage.tsx` | `writingService.createVersion()` | `POST /api/v1/drafts/{id}/versions` | `version_service.py` | `EditorialVersion` (Insert version snapshot, diff summary) |
| **List Version History** | `VersionHistoryPanel.tsx`| `writingService.getVersions()` | `GET /api/v1/drafts/{id}/versions` | `version_service.py` | `EditorialVersion` (List ordered by `version_number DESC`) |
| **Restore Version** | `VersionHistoryPanel.tsx`| `writingService.restoreVersion()` | `POST /api/v1/drafts/{id}/versions/{v_id}/restore` | `version_service.py` | `WritingDraft` (Rollback `revised_content` to snapshot) |

### 2.4 Editorial Studio & Publishing
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Assemble Editorial Edition** | `EditorialPage.tsx` | `editorialService.generate()` | `POST /api/v1/editorial/generate` | `editorial_generator.py` | `EditorialOutput` (Create 300-500 word draft with verified citations) |
| **Submit for Peer Review** | `EditorialApprovalModal.tsx`| `editorialService.submitReview()` | `POST /api/v1/editorial-reviews` | `review_service.py` | `EditorialReview` (Create review ticket, set status `IN_REVIEW`) |
| **Approve / Reject Edition** | `EditorialApprovalModal.tsx`| `editorialService.updateReview()` | `PUT /api/v1/editorial-reviews/{id}` | `review_service.py` | `EditorialReview` (Update status to `APPROVED` or `REJECTED`) |
| **Export Formats (MD/HTML/JSON)**| `ExportModal.tsx` | `editorialService.exportDraft()` | `GET /api/v1/editorial/{id}/export?format=...` | `editorial_service.py` | `EditorialOutput` (Read and format structured payload) |

### 2.5 Research Projects Management
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Create Project** | `ProjectsPage.tsx` | `projectService.create()` | `POST /api/v1/projects` | `research_service.py` | `ResearchProject` (Insert title, org_id, status `ACTIVE`) |
| **List Projects** | `ProjectsPage.tsx` | `projectService.getAll()` | `GET /api/v1/projects` | `research_service.py` | `ResearchProject` (List filtered by `organization_id`) |
| **Filter by Status** | `ProjectsPage.tsx` | `projectService.getAll(status)` | `GET /api/v1/projects?status=...` | `research_service.py` | `ResearchProject` (Filtered query) |
| **Delete Project** | `ProjectsPage.tsx` | `projectService.delete()` | `DELETE /api/v1/projects/{id}` | `research_service.py` | `ResearchProject` (Delete; cascade deletes child sources/drafts) |

### 2.6 Workspace, Members & RBAC
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **List User Organizations** | `OrganizationSwitcher.tsx`| `organizationService.getUserOrgs()` | `GET /api/v1/organizations` | `organization_service.py`| `OrganizationMembership`, `Organization` (Join query on `user_id`) |
| **Invite Member** | `OrganizationPage.tsx` | `organizationService.inviteMember()` | `POST /api/v1/organizations/{id}/invitations` | `organization_service.py`| `OrganizationInvitation` (Insert token, role, expiry) |
| **Change Member Role** | `OrganizationPage.tsx` | `organizationService.updateMember()` | `PUT /api/v1/organizations/{id}/members/{m_id}` | `organization_service.py`| `OrganizationMembership` (Update `role`; requires `OWNER`/`ADMIN`) |
| **Remove Member** | `OrganizationPage.tsx` | `organizationService.removeMember()` | `DELETE /api/v1/organizations/{id}/members/{m_id}`| `organization_service.py`| `OrganizationMembership` (Delete; prevents removing last `OWNER`) |

### 2.7 AI Reliability & Observability Center
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fetch Live Telemetry** | `ObservabilityPage.tsx` | `observabilityService.getTelemetry()` | `GET /api/v1/observability/telemetry` | `monitoring_service.py` | `ProviderUsageRecord` (Aggregate tokens, cost, latency) |
| **Trigger Live 34-Case Evals**| `ObservabilityPage.tsx` | `observabilityService.runEvaluation()` | `POST /api/v1/observability/evaluate` | `dt_evals_service.py` | `ProviderUsageRecord`, `AuditLog` (Record test run outputs) |
| **List AI Providers** | `ObservabilityPage.tsx` | `aiService.getProviders()` | `GET /api/v1/ai/providers` | `ai_provider_service.py`| `AiProviderConfig` (Read active providers, masked keys) |

### 2.8 Style Intelligence & Application Settings
| Feature / User Action | Frontend Component | API Client Function | FastAPI Endpoint | Backend Service Class | SQLAlchemy Model & Operation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **List Style Profiles** | `SettingsPage.tsx` | `settingsService.getStyles()` | `GET /api/v1/styles` | `style_analyzer.py` | `EditorialStyleProfile` (List default and custom org profiles) |
| **Create Custom Profile** | `SettingsPage.tsx` | `settingsService.createStyle()` | `POST /api/v1/styles` | `style_analyzer.py` | `EditorialStyleProfile` (Insert preferred terminology & rules) |
| **Theme / Sidebar Persistence**| `SettingsPage.tsx` | Client `localStorage` | *Client-Side Local Storage* | *Browser Storage Engine* | Synchronized with `document.documentElement.classList` |
