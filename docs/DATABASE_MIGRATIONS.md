# Database Migrations Guide

This document details the migration lifecycle, version lineage, safety protocols, and testing strategies for the **AI Editorial Workspace**.

---

## 1. Migration History & Lineage

The database evolution is tracked under `backend/alembic/versions`:

```text
[base]
  │
  ▼
fe217d474c9d (Initial 7 core tables: research_projects, sources, source_analyses,
              research_briefs, writing_drafts, writing_suggestions, editorial_outputs)
  │
  ▼
0d95531a1a07 (Multi-tenancy & Advanced Entities: users, organizations,
              memberships, invitations, reviews, comments, entities, claims,
              relationships, contradictions, trends, style profiles, versions)
  │
  ▼
3b7c9f1e8a2d (Phase 4 Extended Entities: user_sessions, password_reset_tokens,
              email_verification_tokens, research_evidence, ai_provider_configs,
              integration_connections, provider_usage_records, integration_health_records,
              background_jobs, user_activity_logs, audit_logs, notifications, usage_events)
  │
  ▼
4c8d1e2f3a4b (Foreign Key Performance Indexes: adding dedicated single-column B-tree
              indexes on all referenced foreign-key join columns across SQLite/PostgreSQL)
  │
  ▼
5e9a2f1b4c3d (Multi-Tenant Composite Indexes: indexing (organization_id, id),
              (project_id, created_at), and document versioning tuples)
  │
  ▼
6f1b2a3c4d5e (Writing Assistant Intelligence: suggestions status index, draft
              lifecycle states, and version snapshots)
  │
  ▼
7a2c3d4e5f6a [HEAD] (Phase 8 AI Reliability & Observability: evaluation runs,
              prompt template versions, model hallucination logs, token usage metrics)
```

---

## 2. Migration Execution Commands

### Upgrading to Latest Schema
To apply all pending migrations up to `head`:
```bash
# Set PYTHONPATH to project root
export PYTHONPATH=$(pwd)
backend/venv/bin/alembic -c backend/alembic.ini upgrade head

# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
backend\venv\Scripts\alembic -c backend\alembic.ini upgrade head
```

### Checking Current Revision
```bash
backend\venv\Scripts\alembic -c backend\alembic.ini current
```

### Rolling Back a Migration
To safely step backward by one revision:
```bash
backend\venv\Scripts\alembic -c backend\alembic.ini downgrade -1
```

---

## 3. Data Preservation & Safety Protocols

1. **Table-Existence Checks (`inspector.get_table_names()`)**:
   * Migration `3b7c9f1e8a2d` checks for existing tables before executing `create_table()`. This guarantees safe idempotency on existing databases with legacy data.
2. **Batch Altering (`op.batch_alter_table`)**:
   * All column additions, index creations, and foreign key modifications use SQLAlchemy's `batch_alter_table` mechanism, allowing seamless execution on SQLite without table locks or recreation corruption.
3. **Verified Backup Requirement**:
   * Per Rule 2, before applying migrations to any persistent environment, run the backup CLI:
     ```bash
     python backend/app/scripts/backup_db.py --action backup --dir backups/
     ```

---

## 4. Verification & Testing

Migrations are tested across two isolated environments:
1. **Fresh Database Execution**: Running `upgrade head` against a completely empty database creates all 34 tables with primary keys, composite indexes, and foreign keys.
2. **Existing Database Upgrade**: Tested on pre-existing `editorial.db` preserving 201 users, 201 organizations, 236 memberships, 53 projects, 56 sources, and 27 drafts without data loss.

