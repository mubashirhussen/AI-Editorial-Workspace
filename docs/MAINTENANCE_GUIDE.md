# AI Editorial Workspace — Maintenance, Operations & Disaster Recovery Guide

**Document:** System Administration, Maintenance Runbook & Disaster Recovery  
**Target:** DevOps Engineers, System Administrators & Forward Deployed Engineers  

---

## 1. Health Monitoring & Observability Probes

The backend exposes three standardized health and telemetry endpoints:

| Endpoint | Probe Type | Healthy Status | Action on Failure |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/health/live` | Container Liveness | `200 OK {"status": "alive"}` | Process hung; trigger container restart. |
| `GET /api/v1/health/ready` | Readiness Probe | `200 OK {"database": "connected"}` | Database pool full or SQLite locked; inspect DB connections. |
| `GET /api/v1/health` | Comprehensive Telemetry | `200 OK {uptime, ai_telemetry, events}` | Monitor token consumption trends and error spikes. |

---

## 2. Database Backup & Disaster Recovery Procedures

### 2.1 SQLite Production Backups (WAL Checkpoint)
When running on SQLite, active transactions write to the `-wal` file. To create an atomic, uncorrupted backup:

1. **Trigger WAL Checkpoint:**
   ```powershell
   backend\venv\Scripts\python -c "from backend.app.core.database import engine; from sqlalchemy import text; engine.connect().execute(text('PRAGMA wal_checkpoint(TRUNCATE)'))"
   ```
2. **Atomic Copy:**
   ```powershell
   Copy-Item "editorial.db" -Destination "backend\backups\editorial_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
   ```

### 2.2 PostgreSQL Backup & Restoration (Docker / Cloud)
1. **Create Backup:**
   ```bash
   docker exec -t editorial-postgres pg_dump -U editorial_user -d editorial_workspace -F c -b -v -f /var/lib/postgresql/data/backup.dump
   ```
2. **Restore Database:**
   ```bash
   docker exec -i editorial-postgres pg_restore -U editorial_user -d editorial_workspace -v -c /var/lib/postgresql/data/backup.dump
   ```

---

## 3. Secret Management & Credential Rotation

### Rotating `SECRET_KEY` (JWT Invalidation)
1. Generate a cryptographically secure 64-character secret:
   ```powershell
   backend\venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `SECRET_KEY` in `.env` (or cloud environment manager).
3. Restart backend workers. Existing JWT tokens will be rejected, forcing all users to re-authenticate with fresh sessions.

### Rotating AI Provider API Keys
- API keys (`GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) can be updated dynamically via the **Settings $\rightarrow$ AI Engine** UI tab or in `.env`.
- If keys expire or are revoked, the backend automatically falls back to `FallbackAdapter` with zero customer downtime.

---

## 4. Routine Dependency Auditing & Security Scanning

Run weekly dependency vulnerability audits:
```powershell
# Python security audit
backend\venv\Scripts\pip install pip-audit
backend\venv\Scripts\pip-audit -r backend/requirements.txt

# Node.js frontend audit
npm audit --prefix frontend
```

