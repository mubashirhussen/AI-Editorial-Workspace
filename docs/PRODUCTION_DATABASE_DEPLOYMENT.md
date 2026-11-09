# AI Editorial Workspace — Production Database Deployment Runbook

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Phase:** Phase 14 — Production Readiness & Release Candidate Validation  
**Date:** November 2026  
**Auditor:** Senior Database Administrator & Site Reliability Engineer  
**Status:** **OPERATIONAL & VERIFIED**

---

## 1. Production Database Architecture Overview

In production, the AI Editorial Workspace connects to **PostgreSQL 15+** with production connection pooling, transaction isolation, and linear migration tracking via Alembic:

- **Database Engine:** PostgreSQL 15 (Alpine container or managed AWS RDS / Cloud SQL).
- **Migration Manager:** Alembic 1.14.0.
- **Current Revision Head:** `7a2c3d4e5f6a` (Phase 8 AI Reliability, Observability & Cost Tracking).
- **Total Tables:** 34 normalized tables (33 mapped domain entities + `alembic_version`).
- **Isolation:** Multi-tenant scoping via indexed `organization_id` columns across all business models.

---

## 2. Connection Pooling & Engine Configuration

Configured in [`backend/app/core/database.py`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/backend/app/core/database.py):

```python
# PostgreSQL Connection Pool Specifications
engine_kwargs = {
    "pool_pre_ping": True,       # Tests connection liveness before checking out from pool
    "pool_size": 10,             # Persistent pool connections per worker process
    "max_overflow": 20,          # Maximum surge connections under heavy traffic spikes
    "pool_timeout": 30,          # Seconds to wait for a connection before raising TimeoutError
    "pool_recycle": 1800,        # Recycles connections every 30 minutes to prevent stale TCP drops
}
```

---

## 3. Production Migration Protocol & Safety Invariants

### 3.1 Strict Production Invariant
> **CRITICAL RULE:** In production (`ENVIRONMENT=production`), automatic schema generation via `Base.metadata.create_all()` is **strictly disabled**. All schema changes MUST proceed through reviewed, linear Alembic migration scripts.

### 3.2 Single-Replica Migration Execution
Never execute migrations concurrently from multiple application replicas. During Kubernetes or container rollouts:
1. Run migrations in an isolated CI/CD deployment step or Kubernetes `initContainer` / Helm `pre-upgrade` hook.
2. Only after `alembic upgrade head` returns code 0 should application worker pods scale up.

```bash
# Execute production migration in single dedicated task
python -m alembic -c backend/alembic.ini upgrade head
```

---

## 4. Fresh Database Initialization vs Existing Upgrade

### 4.1 Fresh Database Upgrade Verification
To verify that a fresh PostgreSQL instance initializes cleanly without missing foreign keys or indexes:

```bash
# Step 1: Connect to blank database
export DATABASE_URL="postgresql://editorial_user:secret@db:5432/editorial_workspace"

# Step 2: Apply migration lineage from base to head
alembic upgrade head

# Step 3: Verify all 34 tables exist
psql "${DATABASE_URL}" -c "\dt"
```

### 4.2 Existing Database In-Place Upgrade
To upgrade an existing database without data loss:
1. Take a pre-migration snapshot (see Section 5).
2. Execute `alembic upgrade head`.
3. Check table constraints and row counts:
   ```sql
   SELECT count(*) FROM users;
   SELECT count(*) FROM research_projects;
   SELECT count(*) FROM writing_drafts;
   SELECT version_num FROM alembic_version;
   ```

---

## 5. Automated Backup, Verification & Recovery

### 5.1 Automated PostgreSQL Backup Script
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/editorial_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

# Execute custom-format compressed binary dump
pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -F c -b -v -f "${BACKUP_FILE}"

# Compute cryptographic checksum
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

echo "Backup complete: ${BACKUP_FILE}"
```

### 5.2 Restoration & Rollback Runbook
```bash
# Step 1: Stop API traffic
docker-compose -f docker-compose.prod.yml stop backend

# Step 2: Validate checksum
sha256sum -c "/var/backups/postgres/editorial_20261109_120000.dump.sha256"

# Step 3: Restore database
pg_restore -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists -v "/var/backups/postgres/editorial_20261109_120000.dump"

# Step 4: Verify Alembic revision
alembic current

# Step 5: Restart backend
docker-compose -f docker-compose.prod.yml start backend
```

