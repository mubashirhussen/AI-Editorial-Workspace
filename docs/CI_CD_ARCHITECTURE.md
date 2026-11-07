# AI Editorial Workspace — CI/CD Pipeline & GitHub Actions Architecture

This document outlines the Continuous Integration and Continuous Deployment (CI/CD) pipelines designed for high reliability, automated regression testing, container artifact publishing, and production deployment.

---

## 1. Pipeline Topology & Triggers

The CI/CD system comprises two decoupled, hardened workflows aligned with GitOps principles:

```
[ Git Push / Pull Request / Schedule / Workflow Dispatch ]
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Continuous Integration (.github/workflows/ci.yml)       │
├─────────────────────────┬───────────────────────────────┤
│ 1. Lint & Typecheck     │ Python bytecode & TypeScript  │
│ 2. Backend Tests        │ Pytest + PostgreSQL + Redis   │
│ 3. Frontend Build       │ Vite production bundle        │
│ 4. Docker Verification  │ Multi-stage container builds  │
└─────────────────────────┴───────────────────────────────┘
                           │ (On Merge to 'main')
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Continuous Deployment (.github/workflows/cd.yml)        │
├─────────────────────────┬───────────────────────────────┤
│ 1. Staging Deploy       │ Push GHCR image + Health check│
│ 2. Production Deploy    │ Tagged releases + DB migrate  │
│ 3. Probe Verification   │ /health/startup & ready check │
└─────────────────────────┴───────────────────────────────┘
```

### Supported Event Triggers
- **`push`:** Triggers on `main`, `master`, and feature branches (`feat/**`).
- **`pull_request`:** Executes against pull requests targeting `main` and `master`.
- **`schedule`:** Recurring cron schedule (`0 4 * * 1`) executing weekly automated health and security checks.
- **`workflow_dispatch`:** Manual operational execution permitting parameterized deployments to `staging` or `production`.

---

## 2. Continuous Integration Workflow Details (`ci.yml`)

### Job 1: `lint-and-typecheck`
- Sets up Python 3.11 and Node.js 20 with dependency caching (`pip` and `npm`).
- Compiles Python syntax across `backend/app`, `backend/tests`, and `scripts` via `compileall`.
- Enforces TypeScript type safety without generating output (`npx tsc --noEmit`).

### Job 2: `backend-tests`
- Spawns real ephemeral container services:
  - **PostgreSQL 15:** Validates production database compatibility with connection pooling.
  - **Redis 7:** Validates background task queue and distributed caching.
- Runs database migrations via `alembic upgrade head`.
- Runs full regression test suite with JUnit XML reporting and artifact upload.

### Job 3: `frontend-build`
- Executes `npm ci` with clean dependency resolution.
- Compiles production bundle with tree-shaking, minification, and chunk splitting.
- Uploads compiled `dist/` bundle as an artifact with a 7-day retention period.

### Job 4: `docker-build-verification`
- Uses Docker Buildx with layer caching.
- Builds backend and frontend production images to guarantee containerization sanity before merge.

---

## 3. Continuous Deployment Workflow Details (`cd.yml`)

### Job 1: `deploy-staging`
- Automatically triggered on push to `main` or manual selection.
- Tags container images with git commit SHA and `staging`.
- Authenticates against GitHub Container Registry (`ghcr.io`).
- Pushes images and executes staging health verification.

### Job 2: `deploy-production`
- Gated by GitHub Environment approvals (`environment: production`).
- Publishes semantic version tags (`latest`, `v${{ github.run_number }}`).
- Executes non-destructive schema migrations via `alembic upgrade head`.
- Verifies Kubernetes SRE health probes (`/health/startup`, `/health/ready`, `/health/live`) before completing rollout.

---

## 4. Rollback & Disaster Protocol

In the event of a deployment anomaly:
1. Re-run `workflow_dispatch` selecting the prior known-good run number or commit SHA tag.
2. In the target cluster, rollback using Kubernetes:
   ```bash
   kubectl rollout undo deployment/editorial-backend
   kubectl rollout undo deployment/editorial-frontend
   ```
3. If database schema rollback is required, execute target revision downgrade:
   ```bash
   alembic -c backend/alembic.ini downgrade <prior_revision_id>
   ```

