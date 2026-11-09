# AI Editorial Workspace — API Contract & Database Mapping Matrix

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Audit Phase:** Master Backend & Database Engineering Audit  
**Date:** November 2026  
**Auditor:** Senior API Engineer & Database Architect  
**Status:** **VERIFIED**

---

## 1. Overview

This document maps every primary API endpoint in the AI Editorial Workspace to its corresponding HTTP method, application service class, SQLAlchemy database model, and database operation (CRUD). All endpoints strictly enforce organization tenant isolation and request/response schema validation.

---

## 2. Comprehensive Endpoint to Database Mapping

| API Endpoint | Method | Service / Handler Class | SQLAlchemy Model | Operation | Description |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **System & Health** | | | | | |
| `/api/v1/health` | GET | `monitoring_service` | *N/A (In-memory & Ping)* | Read | Full system diagnostics, DB ping latency, AI status |
| `/api/v1/health/ready` | GET | `backend.app.core.database` | *N/A (`SELECT 1` ping)* | Read | Kubernetes readiness check |
| `/api/v1/health/live` | GET | `backend.app.main` | *N/A* | Read | Platform liveness probe |
| **Authentication & Users** | | | | | |
| `/api/v1/auth/register` | POST | `auth_service.py` | `User`, `Organization`, `OrganizationMembership` | Create | Register user, provision default org & owner role |
| `/api/v1/auth/login` | POST | `auth_service.py` | `User`, `UserSession` | Create/Read | Authenticate credentials, issue JWT, record session |
| `/api/v1/auth/me` | GET | `auth_service.py` | `User`, `OrganizationMembership` | Read | Fetch current user profile & memberships |
| `/api/v1/auth/logout` | POST | `auth_service.py` | `UserSession` | Update | Revoke active user session token |
| **Organizations & Tenants** | | | | | |
| `/api/v1/organizations` | GET | `organization_service.py` | `Organization`, `OrganizationMembership` | List | List organizations current user belongs to |
| `/api/v1/organizations` | POST | `organization_service.py` | `Organization`, `OrganizationMembership` | Create | Create new tenant workspace |
| `/api/v1/organizations/{id}/members` | GET | `organization_service.py` | `OrganizationMembership`, `User` | List | List members and assigned RBAC roles |
| `/api/v1/organizations/{id}/invitations` | POST | `organization_service.py` | `OrganizationInvitation` | Create | Invite member to organization |
| **Research Management** | | | | | |
| `/api/v1/projects` | GET | `research_service.py` | `ResearchProject` | List | List research projects for active organization |
| `/api/v1/projects` | POST | `research_service.py` | `ResearchProject` | Create | Create new investigation project |
| `/api/v1/projects/{id}` | GET | `research_service.py` | `ResearchProject` | Read | Fetch project details by ID |
| `/api/v1/projects/{id}` | PUT | `research_service.py` | `ResearchProject` | Update | Update project title or description |
| `/api/v1/projects/{id}` | DELETE | `research_service.py` | `ResearchProject` | Delete | Soft/Hard delete project and cascade child items |
| `/api/v1/sources` | GET | `source_service.py` | `Source` | List | List ingested sources for active project |
| `/api/v1/sources` | POST | `source_service.py` | `Source` | Create | Ingest URL (SSRF checked) or raw text source |
| `/api/v1/sources/{id}` | GET | `source_service.py` | `Source`, `SourceAnalysis` | Read | Fetch source text and extracted analysis |
| `/api/v1/sources/{id}` | DELETE | `source_service.py` | `Source` | Delete | Delete source and cascade analysis |
| `/api/v1/research/briefs` | POST | `synthesis_service.py` | `ResearchBrief` | Create | Synthesize multi-source research brief |
| `/api/v1/research/briefs/{project_id}` | GET | `synthesis_service.py` | `ResearchBrief` | Read | Fetch active synthesized brief for project |
| `/api/v1/research/claims` | GET | `unu_claim_service.py` | `ResearchClaim`, `ResearchEvidence` | List | List extracted claims and supporting citations |
| **Writing & Auditor Studio** | | | | | |
| `/api/v1/drafts` | GET | `writing_service.py` | `WritingDraft` | List | List writing drafts for active organization |
| `/api/v1/drafts` | POST | `writing_service.py` | `WritingDraft` | Create | Create new editorial draft |
| `/api/v1/drafts/{id}` | GET | `writing_service.py` | `WritingDraft`, `WritingSuggestion` | Read | Fetch draft content and audit suggestions |
| `/api/v1/drafts/{id}` | PUT | `writing_service.py` | `WritingDraft` | Update | Update draft text, calculate metrics, bump timestamp |
| `/api/v1/drafts/{id}/audit` | POST | `writing_analyzer.py` | `WritingDraft`, `WritingSuggestion` | Create/Update | Run Hemingway 6-check auditor & persist suggestions |
| `/api/v1/drafts/{id}/suggestions/{s_id}` | POST | `writing_service.py` | `WritingSuggestion`, `WritingDraft` | Update | Accept or reject sentence rewrite suggestion |
| `/api/v1/drafts/{id}/versions` | POST | `version_service.py` | `EditorialVersion` | Create | Snapshot draft version with changelog summary |
| `/api/v1/drafts/{id}/versions` | GET | `version_service.py` | `EditorialVersion` | List | List all saved versions and diffs for draft |
| **Editorial Studio Production** | | | | | |
| `/api/v1/editorial/generate` | POST | `editorial_generator.py`| `EditorialOutput` | Create | Generate 300-500 word publication newsletter |
| `/api/v1/editorial/{id}` | GET | `editorial_service.py` | `EditorialOutput` | Read | Fetch generated editorial and citations |
| `/api/v1/editorial-reviews` | POST | `review_service.py` | `EditorialReview` | Create | Submit editorial draft for peer review |
| `/api/v1/editorial-reviews/{id}/comments`| POST | `review_service.py` | `EditorialComment` | Create | Add inline review annotation / comment |
| **Styles & Intelligence** | | | | | |
| `/api/v1/styles` | GET | `style_analyzer.py` | `EditorialStyleProfile` | List | List active organization style profiles |
| `/api/v1/styles` | POST | `style_analyzer.py` | `EditorialStyleProfile` | Create | Create custom publication style guide |
| `/api/v1/styles/{id}` | PUT | `style_analyzer.py` | `EditorialStyleProfile` | Update | Update sentence length and terminology rules |
| **AI Reliability & Observability** | | | | | |
| `/api/v1/observability/telemetry` | GET | `monitoring_service.py` | `ProviderUsageRecord` | Read | Fetch aggregate tokens, cost, latency, error rate |
| `/api/v1/observability/evaluate` | POST | `dt_evals_service.py` | `ProviderUsageRecord`, `AuditLog` | Create | Execute automated 34-benchmark test suite |
| `/api/v1/ai/providers` | GET | `ai_provider_service.py`| `AiProviderConfig` | List | List configured providers (keys masked) |
| `/api/v1/ai/providers` | POST | `ai_provider_service.py`| `AiProviderConfig` | Create | Store encrypted AI credentials via Fernet |
| **Audit Logs & Dashboard** | | | | | |
| `/api/v1/dashboard/metrics` | GET | `dashboard_service.py` | `ResearchProject`, `WritingDraft`, `Source` | Read | Calculate active workspace metrics |
| `/api/v1/dashboard/activity` | GET | `audit_service.py` | `AuditLog`, `UserActivityLog` | List | List recent user and system actions |

---

## 3. Request-Response Mapping Verification

All endpoints serialize output using Pydantic models in `backend/app/schemas/`:
1. Sensitive fields (`hashed_password`, `encrypted_api_key`) are stripped from response schemas via `Field(exclude=True)` or dedicated public schemas (`UserPublic`, `AiProviderConfigRead`).
2. Paginated responses use `skip` and `limit` query parameters, returning standard structure `{ "items": [...], "total": int, "page": int, "size": int }`.
3. Multi-tenant scoping filters all queries by `organization_id == current_org.id`, preventing cross-tenant leakage.
