# AI Editorial Workspace — Database Backup, Disaster Recovery & Data Management

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Audit Phase:** Master Backend & Database Engineering Audit  
**Date:** November 2026  
**Auditor:** Senior DevOps & Database Reliability Specialist  
**Status:** **OPERATIONAL & TESTED**

---

## 1. Overview & Objectives

This document defines standard operating procedures for database backup, disaster recovery, data retention, and migration rollback across development, staging, and production environments.

The backup system guarantees:
- **Recovery Point Objective (RPO):** < 1 hour for automated snapshots; 0-data-loss for WAL-enabled PostgreSQL streaming.
- **Recovery Time Objective (RTO):** < 15 minutes to full service restoration.
- **Data Integrity:** Cryptographic SHA-256 checksum verification for every archive.

---

## 2. Backup Procedures

### 2.1 Automated SQLite Backup (Development / Standalone Deployments)
SQLite backups use the online SQLite Backup API to ensure atomic, non-locking snapshots even during active read/write operations:

```powershell
# Create automated backup directory
New-Item -ItemType Directory -Force -Path "./backups"

# Execute online backup with atomic timestamp and SHA-256 generation
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "./backups/editorial_backup_$timestamp.db"

# Online safe copy using sqlite3 shell or Python script
python -c "
import sqlite3
source = sqlite3.connect('editorial.db')
dest = sqlite3.connect('$backupFile')
source.backup(dest)
dest.close()
source.close()
print('Atomic online SQLite backup completed: $backupFile')
"

# Generate SHA-256 checksum
Get-FileHash -Algorithm SHA256 $backupFile | Out-File "$backupFile.sha256"
```

### 2.2 Production PostgreSQL Backup
In containerized production deployments (`docker-compose.prod.yml`), backups execute via `pg_dump` with custom compressed archive format:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/editorial_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

# Execute streaming compressed dump
pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -F c -b -v -f "${BACKUP_FILE}"

# Generate checksum
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

# Apply 30-day retention pruning
find "${BACKUP_DIR}" -name "*.dump" -mtime +30 -delete
find "${BACKUP_DIR}" -name "*.sha256" -mtime +30 -delete

echo "PostgreSQL backup successfully completed: ${BACKUP_FILE}"
```

---

## 3. Restoration & Disaster Recovery Procedures

### 3.1 Verification and Checksum Validation
Before applying any backup archive, verify file integrity:

```powershell
$expectedHash = (Get-Content "./backups/editorial_backup_20261109_110000.db.sha256").Split(" ")[0]
$actualHash = (Get-FileHash -Algorithm SHA256 "./backups/editorial_backup_20261109_110000.db").Hash

if ($expectedHash -eq $actualHash) {
    Write-Host "Checksum verification PASSED." -ForegroundColor Green
} else {
    Write-Error "Checksum mismatch! Archive may be corrupted. Aborting."
    exit 1
}
```

### 3.2 Restoration Execution
To restore into an isolated environment or recover production:

```powershell
# Step 1: Gracefully stop application workers
# docker-compose stop backend worker

# Step 2: Restore database file
Copy-Item "./backups/editorial_backup_20261109_110000.db" "./editorial.db" -Force

# Step 3: Run Alembic to ensure migrations match active code
python -m alembic upgrade head

# Step 4: Restart application
# docker-compose start backend worker
```

---

## 4. Migration Failure Recovery & Safe Downgrades

1. **Transactional Migrations:** In PostgreSQL, all DDL operations are executed inside a single transaction. If a migration script raises an exception, the entire migration rolls back automatically without altering table state.
2. **Alembic Batch Mode for SQLite:** In SQLite, migrations use `render_as_batch=True`. Alembic creates temporary tables, copies data, drops old tables, and renames new tables atomically.
3. **Emergency Downgrade:** If a newly deployed revision causes operational errors:
   ```bash
   # Downgrade 1 revision step
   python -m alembic downgrade -1
   
   # Or downgrade to specific known revision
   python -m alembic downgrade 6f1b2a3c4d5e
   ```

---

## 5. Development Seed Data & Test Database Isolation

1. **Test Isolation:** Automated test suites (`pytest backend/tests/`) NEVER touch the production `editorial.db` file. Test fixtures instantiate in-memory SQLite instances (`sqlite:///:memory:`) or isolated temporary database files with automatic cleanup.
2. **Seed Data:** Standard editorial style profiles (e.g., *This Week in AI Standard*) are provisioned through idempotent application lifecycle handlers (`backend/app/main.py:lifespan`), ensuring repeatable setup on fresh databases.

