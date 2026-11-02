# Database Backup & Disaster Recovery Guide

This document defines verified backup and restoration procedures for the **AI Editorial Workspace** across SQLite (local/dev/staging) and PostgreSQL (production).

---

## 1. Verified Backup Script

The repository includes a dedicated database backup CLI tool:
[`backend/app/scripts/backup_db.py`](file:///C:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/backend/app/scripts/backup_db.py)

### Capabilities:
* **Online SQLite Snapshots**: Uses SQLite's online backup API (`con_src.backup(con_dest)`) to produce a bit-for-bit consistent copy without locking active readers.
* **Integrity Validation**: Runs `PRAGMA integrity_check` on both the source and the generated backup before completing.
* **SHA-256 Checksumming**: Computes and logs cryptographic hash to ensure byte-level integrity during transit or cold storage.
* **PostgreSQL Support**: Automates `pg_dump -Fc` when a PostgreSQL connection string is active.

---

## 2. Backup Execution

### Creating a Backup
```bash
# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
backend\venv\Scripts\python backend/app/scripts/backup_db.py --action backup --dir backups/

# Linux / macOS:
export PYTHONPATH=$(pwd)
backend/venv/bin/python backend/app/scripts/backup_db.py --action backup --dir backups/
```

### Verified Execution Output Example:
```text
[BACKUP SUCCESS]
  Source:      C:\Users\Mubashirhussensk\OneDrive\Desktop\FDE intern\editorial.db
  Backup:      backups\editorial_20261102_043627.db
  Size:        1196032 bytes
  SHA-256:     1c00a498efcef35c24c86c3cdff5fc031bf813fe3192a8793d7708ccca5b19fb
  Integrity:   VERIFIED (PRAGMA integrity_check == ok)
```

---

## 3. Disaster Recovery & Restoration

### Restoring from Backup
```bash
# Windows PowerShell:
$env:PYTHONPATH = (Get-Location).Path
backend\venv\Scripts\python backend/app/scripts/backup_db.py --action restore --file backups/editorial_20261102_043627.db

# Linux / macOS:
export PYTHONPATH=$(pwd)
backend/venv/bin/python backend/app/scripts/backup_db.py --action restore --file backups/editorial_20261102_043627.db
```

### Safety Features on Restore:
1. **Integrity Pre-check**: Verifies the backup archive passes `PRAGMA integrity_check` before modifying the destination.
2. **Pre-Restore Snapshot**: Automatically creates a `.pre_restore_bak` copy of the current database file before replacing it.

---

## 4. Production PostgreSQL Backup & Recovery

In production PostgreSQL environments:
```bash
# Daily Backup Cron
pg_dump -Fc -h $PGHOST -U $PGUSER -d $PGDATABASE -f backups/editorial_$(date +%Y%m%d_%H%M%S).dump

# Point-in-Time Recovery
pg_restore -clean -if-exists -h $PGHOST -U $PGUSER -d $PGDATABASE backups/editorial_20261102_043627.dump
```

