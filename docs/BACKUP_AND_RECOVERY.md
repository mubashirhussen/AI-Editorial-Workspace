# AI Editorial Workspace — Disaster Recovery, Backup & Restoration Guide

This document defines the automated backup procedures, integrity verification protocols, retention policies, and recovery steps required to safeguard database state and maintain continuous operations.

---

## 1. Recovery Objectives (RTO & RPO)

- **Recovery Point Objective (RPO):** $< 24$ hours (nightly automated snapshots). Critical environments may configure hourly delta backups.
- **Recovery Time Objective (RTO):** $< 15$ minutes (automated schema validation and atomic database restore).

---

## 2. Backup Utility Architecture (`scripts/backup_db.py`)

The backup utility automates database exports, cryptographic checksum generation, and manifest writing:

1. **Storage Engine Identification:**
   - **PostgreSQL:** Invokes `pg_dump -Fc` producing custom compressed binary archives with complete schema and table data.
   - **SQLite:** Executes file-level copy using `shutil.copy2` with database connection quiescence.
2. **SHA256 Cryptographic Checksum:**
   - Computes a 64-character SHA256 hash across the generated backup file.
3. **Metadata Manifest:**
   - Generates a sidecar `<backup_file>.json` manifest containing:
     - `backup_path`: Path to the backup archive.
     - `sha256`: Cryptographic checksum.
     - `timestamp`: UTC creation timestamp.
     - `table_count`: Number of verified public tables.
     - `status`: Completion state.
4. **Automated Pruning:**
   - Inspects the backup directory and purges files older than `RETENTION_DAYS` (default: 7 days).

### Manual Backup Execution
```bash
python scripts/backup_db.py
```

---

## 3. Restoration Utility Architecture (`scripts/restore_db.py`)

The restoration utility ensures zero corruption risk through pre-execution integrity checks:

1. **Integrity & Checksum Verification:**
   - Reads the sidecar `.json` manifest.
   - Computes the SHA256 hash of the target backup file and verifies it matches the expected hash.
   - Aborts immediately if a checksum mismatch or corrupted byte stream is detected.
2. **Dry-Run Mode (`--dry-run`):**
   - Validates checksum, permissions, and file readability without modifying or overwriting active database files.
3. **Atomic Restore Execution:**
   - **SQLite:** Restores to a temporary file (`.tmp`) before performing an atomic replace.
   - **PostgreSQL:** Executes `pg_restore -c -d <DATABASE_URL>` to clean and restore objects.
4. **Post-Restore Health Check:**
   - Automatically invokes `check_db_health()` to verify database connectivity, schema validity, and query latency.

### Dry-Run Verification Command
```bash
python scripts/restore_db.py backend/backups/editorial_backup_20261107_120000.db --dry-run
```

### Full Restore Command
```bash
python scripts/restore_db.py backend/backups/editorial_backup_20261107_120000.db
```

---

## 4. Disaster Recovery Checklist

In the event of database failure or corrupted state:
1. Stop backend application containers to prevent active write contention:
   ```bash
   docker compose stop backend
   ```
2. Locate the most recent valid backup and verify manifest integrity:
   ```bash
   ls -lat backend/backups/
   cat backend/backups/editorial_backup_<latest>.json
   ```
3. Execute dry-run restore to confirm checksum passes:
   ```bash
   python scripts/restore_db.py backend/backups/editorial_backup_<latest>.dump --dry-run
   ```
4. Execute full restoration:
   ```bash
   python scripts/restore_db.py backend/backups/editorial_backup_<latest>.dump
   ```
5. Restart application services and verify `/health/ready` probe:
   ```bash
   docker compose start backend
   curl -f http://localhost:8000/health/ready
   ```

