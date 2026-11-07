# Alembic Database Migration Guide

This comprehensive guide details the schema migration architecture, revision lineage, operational procedures, rollback strategies, and verification workflows for the **AI Editorial Workspace**.

---

## 1. Authoritative Migration Lineage

The database evolution is tracked under `backend/alembic/versions/` using forward-only, idempotent revisions managed through Alembic:

```text
[base]
  │
  ▼
fe217d474c9d  (Initial 7 core tables: research_projects, sources, source_analyses,
               research_briefs, writing_drafts, writing_suggestions, editorial_outputs)
  │
  ▼
0d95531a1a07  (Multi-tenancy & Advanced Entities: users, organizations,
               memberships, invitations, reviews, comments, entities, claims,
               relationships, contradictions, trends, style profiles, versions)
  │
  ▼
3b7c9f1e8a2d  (Phase 4 Extended Entities: user_sessions, password_reset_tokens,
               email_verification_tokens, research_evidence, ai_provider_configs,
               integration_connections, provider_usage_records, integration_health_records,
               background_jobs, user_activity_logs, audit_logs, notifications, usage_events)
  │
  ▼
4c8d1e2f3a4b  (Foreign Key Performance Indexes: adding dedicated single-column B-tree
               indexes on all referenced foreign-key join columns across SQLite/PostgreSQL)
  │
  ▼
5e9a2f1b4c3d  (Multi-Tenant Composite Indexes: indexing (organization_id, id),
               (project_id, created_at), and document versioning tuples)
  │
  ▼
6f1b2a3c4d5e  (Writing Assistant Intelligence: suggestions status index, draft
               lifecycle states, and version snapshots)
  │
  ▼
7a2c3d4e5f6a  [HEAD] (Phase 8 AI Reliability & Observability: evaluation runs,
               prompt template versions, model hallucination logs, token usage metrics)
```

---

## 2. Standard Operational Commands

Always ensure virtual environment packages and the project root are on your Python path:

### Apply All Pending Migrations to Head
```bash
# Linux / macOS:
export PYTHONPATH=$(pwd)
backend/venv/bin/alembic -c backend/alembic.ini upgrade head

# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
backend\venv\Scripts\alembic -c backend\alembic.ini upgrade head
```

### Inspect Migration Status & Current Revision
```bash
# Verify current applied revision vs head:
backend\venv\Scripts\alembic -c backend\alembic.ini current

# Display full chronological history:
backend\venv\Scripts\alembic -c backend\alembic.ini history --verbose
```

### Safely Downgrade / Rollback
```bash
# Rollback single revision:
backend\venv\Scripts\alembic -c backend\alembic.ini downgrade -1

# Rollback to a specific stable revision tag:
backend\venv\Scripts\alembic -c backend\alembic.ini downgrade 3b7c9f1e8a2d
```

---

## 3. Pre-Migration Safety & Data Backup

Before applying any migration to persistent local or production databases:

1. **Execute Snapshot Backup**:
   ```bash
   backend\venv\Scripts\python backend/app/scripts/backup_db.py --action backup --dir backups/
   ```
2. **Inspect Existing Tables**:
   Alembic revisions are programmed with table-existence guards (`inspector.get_table_names()`) and batch alterations (`op.batch_alter_table`) to guarantee idempotency across SQLite and PostgreSQL.
3. **Run Dry-Run Verification**:
   Verify migration on an ephemeral SQLite database before touching production storage:
   ```bash
   backend\venv\Scripts\python -c "
   import tempfile, os
   from alembic import command
   from alembic.config import Config
   cfg = Config('backend/alembic.ini')
   cfg.set_main_option('sqlalchemy.url', 'sqlite:///temp_check.db')
   command.upgrade(cfg, 'head')
   os.remove('temp_check.db')
   print('Migration dry-run successful!')
   "
   ```

---

## 4. PostgreSQL Production Deployment

When deploying to PostgreSQL in production environments:
* Ensure connection pooling parameters in `.env`:
  ```ini
  DATABASE_URL=postgresql://fde_user:secure_pass@db.internal:5432/editorial_prod
  DB_POOL_SIZE=10
  DB_MAX_OVERFLOW=20
  DB_POOL_TIMEOUT=30
  DB_POOL_RECYCLE=1800
  ```
* Database user `fde_user` must hold `CREATE`, `ALTER`, `DROP`, and `INDEX` privileges on the target schema.
* Zero-downtime guidelines:
  1. Additive changes (new tables, new nullable columns, non-unique indexes) are applied first without disruption.
  2. Multi-column and unique constraints are populated in follow-up transactional scripts.

