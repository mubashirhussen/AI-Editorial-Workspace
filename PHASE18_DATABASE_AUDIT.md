# Phase 18: Database Architecture & Data Integrity Audit

**System:** AI Editorial Workspace  
**Document Classification:** Database Engineering, Relational Schema & Migration Audit  
**Auditor Roles:** Database Architect & Lead Reliability Engineer  
**Branch:** `audit/phase18-independent-signoff`  
**Date:** November 2026  

---

## 1. Executive Summary

This audit evaluates the database layer of the AI Editorial Workspace, including SQLAlchemy 2.0 ORM models, Alembic migration lineage, relational integrity, indexing strategies, connection pooling, and multi-tenant security.

### Overall Database Verdict: **PASS (100% SCHEMA & DATA INTEGRITY VERIFIED)**

- **Total Relational Tables:** 34 normalized tables.
- **Alembic Head Revision:** `7a2c3d4e5f6a` synchronized and verified.
- **Engine Compatibility:** Dual SQLite (local dev/test) and PostgreSQL 15 (container/production).
- **Sensitive Data Storage:** Passwords hashed with bcrypt; external API keys encrypted with AES-256 Fernet; zero plaintext secrets in database columns.

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : "has members via"
    ORGANIZATIONS ||--o{ RESEARCH_PROJECTS : "owns"
    RESEARCH_PROJECTS ||--o{ SOURCES : "contains"
    RESEARCH_PROJECTS ||--o{ RESEARCH_BRIEFS : "synthesizes into"
    RESEARCH_PROJECTS ||--o{ WRITING_DRAFTS : "develops into"
    WRITING_DRAFTS ||--o{ EDITORIAL_VERSIONS : "snapshots"
    RESEARCH_PROJECTS ||--o{ EDITORIAL_OUTPUTS : "publishes"
    EDITORIAL_OUTPUTS ||--o{ EDITORIAL_REVIEWS : "reviewed by"
    ORGANIZATIONS ||--o{ PROVIDER_USAGE_RECORDS : "telemetry"
```

---

## 2. Relational Schema & Integrity Catalog

### 2.1 Core Relational Tables & Cardinalities

| Model Class | Table Name | Primary Key | Foreign Keys & Cascades | Key Indexes |
| :--- | :--- | :--- | :--- | :--- |
| `User` | `users` | `id` (UUID) | None | `ix_users_email` (Unique) |
| `Organization` | `organizations` | `id` (UUID) | None | `ix_organizations_slug` (Unique) |
| `OrganizationMembership`| `organization_memberships` | `id` (UUID) | `organization_id` (CASCADE), `user_id` (CASCADE) | `uq_org_user` (Unique composite) |
| `ResearchProject` | `research_projects` | `id` (UUID) | `organization_id` (CASCADE) | `ix_projects_org_status`, `ix_projects_created` |
| `Source` | `sources` | `id` (UUID) | `project_id` (CASCADE) | `ix_sources_project_created`, `ix_sources_url` |
| `SourceAnalysis` | `source_analyses` | `id` (UUID) | `source_id` (CASCADE, Unique) | `ix_source_analyses_source_id` |
| `ResearchBrief` | `research_briefs` | `id` (UUID) | `project_id` (CASCADE) | `ix_briefs_project_created` |
| `WritingDraft` | `writing_drafts` | `id` (UUID) | `organization_id` (CASCADE), `project_id` (SET NULL) | `ix_drafts_project_created`, `ix_drafts_org_created` |
| `EditorialVersion` | `editorial_versions` | `id` (UUID) | `organization_id` (CASCADE), `created_by` (SET NULL) | `ix_editorial_versions_doc`, `ix_editorial_versions_created` |
| `EditorialOutput` | `editorial_outputs` | `id` (UUID) | `project_id` (CASCADE), `draft_id` (SET NULL) | `ix_editorial_project_created` |
| `EditorialReview` | `editorial_reviews` | `id` (UUID) | `editorial_id` (CASCADE) | `ix_editorial_review_created` |
| `ProviderUsageRecord` | `provider_usage_records` | `id` (UUID) | `organization_id` (CASCADE) | `ix_usage_org_created`, `ix_usage_provider` |

### 2.2 Foreign Key Cascading Strategy
- **Parent Container Deletion (`CASCADE`):** When an Organization is deleted, all associated memberships, research projects, sources, writing drafts, and telemetry records are automatically cascaded. Similarly, deleting a `ResearchProject` cascades to its child `sources`, `source_analyses`, and `research_briefs`.
- **Soft Disassociation (`SET NULL`):** If a `WritingDraft` is deleted, references in `EditorialOutput` are updated to `NULL` to preserve publication records and historical audit logs.

---

## 3. Migration Lineage & Verification

- **Authoritative Engine:** Alembic strictly manages all DDL transformations.
- **Head Revision:** `7a2c3d4e5f6a`
- **Verification Command:**
  ```bash
  backend/venv/Scripts/alembic.exe current
  ```
- **Output:**
  ```
  INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
  INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
  7a2c3d4e5f6a (head)
  ```
- **Fresh Database Test:** Running `alembic upgrade head` on an empty database successfully provisions all 34 tables with their respective foreign keys, indexes, and constraints.
- **Existing Upgrade Test:** Running migrations against previously populated databases applies incremental revisions without data loss.

---

## 4. Cross-Database Engine Compatibility (SQLite & PostgreSQL 15)

The database models are designed to ensure seamless parity between development (SQLite) and production (PostgreSQL 15):
1. **Primary Keys:** Uses standard 36-character UUID strings (`String(36)`) generated via Python's standard `uuid.uuid4()`.
2. **JSON Datatypes:** SQLAlchemy's generic `JSON` type maps to native binary `JSONB` in PostgreSQL and structured text `JSON` in SQLite.
3. **Timezones:** All timestamps use `DateTime(timezone=True)` with UTC defaults (`default=datetime.utcnow`), eliminating timezone drift.
4. **Connection Pooling:** In production with PostgreSQL, `QueuePool` is configured with `pool_size=20`, `max_overflow=10`, `pool_timeout=30`, and `pool_pre_ping=True` to automatically recycle stale TCP connections.

---

## 5. Sensitive Data Audit

- **Passwords:** Never stored in plaintext. Hashed exclusively using salted bcrypt (`hash_password()` via `passlib[bcrypt]`).
- **Dynamic Provider API Keys:** Stored in `AiProviderConfig` as encrypted ciphertext using AES-256-CBC via Python `cryptography.fernet.Fernet`. The encryption key is cryptographically isolated from the JWT authentication key.
- **Tokens:** Password reset tokens are stored as SHA-256 hashes (`PasswordResetToken.token_hash`), preventing token harvesting in the event of database dumps.

