# AI Editorial Workspace — Backup & Disaster Recovery Guide

This document details automated backup procedures, manual recovery steps, and Recovery Point/Time Objectives (RPO/RTO) for production deployments.

---

## 1. Objectives & Metrics

- **Recovery Point Objective (RPO):** Maximum 1 hour (daily full backup + hourly incremental/WAL logs).
- **Recovery Time Objective (RTO):** Maximum 15 minutes from incident declaration to restored operations.
- **Data Protection Guarantee:** Zero silent data corruption (SHA-256 checksums verified before and after restoration).

---

## 2. Automated Backup Utility (`backend/app/scripts/backup_db.py`)

The workspace includes a dedicated backup tool supporting SQLite and PostgreSQL:

### Usage

```bash
# Generate a verified backup
python backend/app/scripts/backup_db.py --action backup --dir /var/backups/editorial

# Restore from an existing backup
python backend/app/scripts/backup_db.py --action restore --file /var/backups/editorial/editorial_20261102_053859.db
```

### Verification Safeguards
1. **Source Pre-Check:** Executes `PRAGMA integrity_check` on the active database before taking the snapshot.
2. **Online Backup API:** Uses SQLite's online backup API to copy pages incrementally without blocking readers.
3. **Target Integrity Check:** Validates the backup file immediately with `PRAGMA integrity_check`.
4. **Checksum Hashing:** Computes and logs the SHA-256 checksum for audit trails.
5. **Pre-Restore Snapshot:** Preserves current state as `.pre_restore_bak` before applying a backup.

---

## 3. Production PostgreSQL Backup & Restore

In Docker Compose or Cloud Kubernetes environments using PostgreSQL:

### Scheduled Backup (Cron Example)
Add to system crontab (`crontab -e`):
```cron
# Daily full backup at 02:00 AM UTC
0 2 * * * docker exec editorial-postgres pg_dump -U editorial_user -Fc editorial_workspace > /backups/editorial_$(date +\%Y\%m\%d_\%H\%M\%S).dump
# Remove backups older than 30 days
0 3 * * * find /backups -type f -name "editorial_*.dump" -mtime +30 -delete
```

### Disaster Recovery Steps (Restoring to PostgreSQL)

1. **Stop Application Backend to Prevent Writes:**
   ```bash
   docker stop editorial-backend
   ```

2. **Drop Existing Corrupted Database & Recreate:**
   ```bash
   docker exec -i editorial-postgres psql -U editorial_user -d postgres -c "DROP DATABASE IF EXISTS editorial_workspace;"
   docker exec -i editorial-postgres psql -U editorial_user -d postgres -c "CREATE DATABASE editorial_workspace OWNER editorial_user;"
   ```

3. **Restore Database from Dump:**
   ```bash
   docker exec -i editorial-postgres pg_restore -U editorial_user -d editorial_workspace < /backups/editorial_20261102_020000.dump
   ```

4. **Verify Schema & Migrations:**
   ```bash
   docker start editorial-backend
   docker exec -it editorial-backend alembic -c backend/alembic.ini current
   ```

5. **Verify Application Health:**
   ```bash
   curl -f http://localhost:8000/health/ready
   ```

---

## 4. Disaster Recovery Testing Playbook

Annual disaster recovery exercises should execute this sequence on a staging server:
1. Simulate catastrophic data loss by zeroing the test database.
2. Trigger the restore command using the latest automated snapshot.
3. Verify that the 104-test regression suite passes against the restored database.
4. Verify that user accounts, research projects, source extractions, and style guides match the snapshot state.
