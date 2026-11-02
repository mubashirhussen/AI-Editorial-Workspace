# Database Audit & Schema Verification

**Database Engine:** SQLite (Local Dev / CI) & PostgreSQL 15 (Production)  
**ORM:** SQLAlchemy 2.0  
**Migration Tool:** Alembic  
**Current Revision:** `3b7c9f1e8a2d` (Head)  
**Revision Chain:** `base` &rarr; `fe217d474c9d` &rarr; `0d95531a1a07` &rarr; `3b7c9f1e8a2d` (head)  

---

## 1. Schema Overview

The database contains **34 normalized tables** (33 mapped ORM models + `alembic_version`) organized into 8 functional domains:
1. **Identity & Multi-Tenancy:** `users`, `organizations`, `organization_memberships`, `organization_invitations`, `user_sessions`, `password_reset_tokens`, `email_verification_tokens`.
2. **Research Ingestion:** `research_projects`, `sources`, `source_analyses`.
3. **Research Intelligence:** `research_briefs`, `research_entities`, `research_claims`, `research_evidence`, `research_relationships`, `research_contradictions`, `research_trends`.
4. **Writing & Revision:** `writing_drafts`, `writing_suggestions`.
5. **Editorial Production & Review:** `editorial_outputs`, `editorial_reviews`, `editorial_comments`.
6. **Style & Document Versioning:** `editorial_style_profiles`, `editorial_versions`.
7. **AI & Integrations:** `ai_provider_configs`, `provider_usage_records`, `integration_connections`, `integration_health_records`.
8. **Operations & Telemetry:** `background_jobs`, `audit_logs`, `user_activity_logs`, `usage_events`, `notifications`.

---

## 2. Table Catalog (Selected Core Models)

| Table Name | Primary Key | Foreign Keys | Key Indexes | Cascading & Nullable Protections |
| :--- | :--- | :--- | :--- | :--- |
| `users` | `id` (VARCHAR 36) | None | `ix_users_email` (UNIQUE) | `email`, `hashed_password`, `full_name` non-null |
| `organizations` | `id` (VARCHAR 36) | None | `ix_organizations_slug` (UNIQUE) | `name`, `slug` non-null |
| `organization_memberships` | `id` (VARCHAR 36) | `organization_id` &rarr; `organizations.id`, `user_id` &rarr; `users.id` | `uq_org_user` (UNIQUE) | `role` defaults to `VIEWER`, CASCADE on delete |
| `research_projects` | `id` (VARCHAR 36) | `organization_id` &rarr; `organizations.id` | `ix_research_projects_organization_id` | CASCADE on org delete |
| `sources` | `id` (VARCHAR 36) | `project_id` &rarr; `research_projects.id` | `ix_sources_project_created` | `title`, `source_type` non-null, CASCADE delete |
| `source_analyses` | `id` (VARCHAR 36) | `source_id` &rarr; `sources.id` | `ix_source_analyses_source_id` | CASCADE on source delete |
| `research_briefs` | `id` (VARCHAR 36) | `project_id` &rarr; `research_projects.id` | `ix_briefs_project_created` | `content` non-null |
| `research_claims` | `id` (VARCHAR 36) | `project_id`, `source_id` | `ix_claims_project_classification` | `evidence_classification` (`verified_fact`, `editorial_analysis`, `speculation`) |
| `writing_drafts` | `id` (VARCHAR 36) | `project_id`, `style_profile_id` | `ix_drafts_project_created` | `original_content` immutable, `revised_content` mutable |
| `writing_suggestions` | `id` (VARCHAR 36) | `draft_id` &rarr; `writing_drafts.id` | `ix_suggestions_draft_status` | `category`, `status` non-null, CASCADE delete |
| `editorial_style_profiles` | `id` (VARCHAR 36) | `organization_id` | `ix_style_org_default` | Default seed profile auto-provisioned |
| `editorial_outputs` | `id` (VARCHAR 36) | `project_id` &rarr; `research_projects.id` | `ix_editorial_project_created` | `content` non-null |
| `editorial_versions` | `id` (VARCHAR 36) | `organization_id`, `created_by` | `ix_editorial_versions_doc` | `content_snapshot`, `document_type` non-null |
| `ai_provider_configs` | `id` (VARCHAR 36) | `organization_id` &rarr; `organizations.id` | `ix_ai_configs_org_provider` | `encrypted_api_key` encrypted via AES-128 Fernet |
| `provider_usage_records`| `id` (VARCHAR 36) | `organization_id`, `user_id` | `ix_provider_usage_org_created` | `prompt_tokens`, `completion_tokens`, `cost_usd` |
| `background_jobs` | `id` (VARCHAR 36) | `organization_id`, `user_id` | `ix_background_jobs_status` | `job_type`, `status` (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`) |
| `audit_logs` | `id` (VARCHAR 36) | `organization_id`, `user_id` | `ix_audit_logs_action_created` | Immutable audit trail for all sensitive operations |

---

## 3. Migration Chain & Integrity Guarantee

1. **`fe217d474c9d_initial_7_tables_migration.py`:** Baseline schema for research projects, sources, source analyses, research briefs, writing drafts, suggestions, and editorial outputs.
2. **`0d95531a1a07_add_multi_tenant_and_newer_tables.py`:** Multi-tenant organizations, invitations, research intelligence (entities, claims, relationships, trends, contradictions), style profiles, and version snapshots.
3. **`3b7c9f1e8a2d_phase4_database_architecture.py`:** Enterprise extensions: background jobs, audit logs, provider configs, token usage tracking, and integration connections.

### Idempotency & Zero Data Loss Strategy
- Every migration step verifies table and column existence using `sa.inspect(op.get_bind())` before issuing `op.create_table` or `op.add_column`.
- Upgrades run seamlessly on both fresh databases and populated databases without throwing `Table already exists` or `Duplicate column` errors.
- SQLite backup and recovery utility (`backend/app/scripts/backup_db.py`) creates verified snapshots with SHA-256 integrity validation and `PRAGMA integrity_check == ok`.
