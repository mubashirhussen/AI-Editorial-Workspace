# AI Editorial Workspace — Production Docker Architecture Guide

This document provides a technical overview of the container architecture, multi-stage Dockerfiles, Docker Compose service topology, security controls, and optimization strategies employed by the AI Editorial Workspace.

---

## 1. Container Topology Architecture

The containerized stack implements a three-tier decoupled architecture:

```
[ User Browser / Client ]
           │
           │ HTTP (Port 80/443)
           ▼
┌──────────────────────────────────────────────┐
│  editorial-frontend (Nginx 1.25 Alpine)      │
│  - Serves React SPA (Vite static build)      │
│  - Reverse-proxies /api/ to editorial-backend │
│  - Enforces Security Headers & Gzip Caching │
└──────────────────────┬───────────────────────┘
                       │ HTTP (Port 8000)
                       ▼
┌──────────────────────────────────────────────┐
│  editorial-backend (Python 3.11 Slim)        │
│  - FastAPI REST API & Async Worker           │
│  - Non-root user (uid: 10001, gid: 10001)     │
│  - Entrypoint executes Alembic head upgrade  │
└──────────────┬───────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │
│  15-Alpine   │ │   7-Alpine   │
│  Persistent  │ │ Task Broker  │
│  Volume      │ │ & Cache      │
└──────────────┘ └──────────────┘
```

---

## 2. Multi-Stage Dockerfile Specifications

### Backend (`backend/Dockerfile`)
- **Stage 1 (Builder):** Uses `python:3.11-slim` with build dependencies (`gcc`, `libpq-dev`). Compiles dependencies to a clean `--prefix=/install` layer, keeping the final runtime image free of compilers and headers.
- **Stage 2 (Runner):** Minimal `python:3.11-slim` with runtime libraries (`curl` for container health checks, `libpq5` for PostgreSQL client driver).
- **Security Hardening:**
  - Dedicated non-root user and group (`appuser:appgroup`, UID 10001).
  - Explicit file ownership (`chown -R appuser:appgroup /app`).
  - Read-only container root support with mounted volumes for `/app/backend/data` and `/app/backend/backups`.
  - Built-in `HEALTHCHECK` probing `GET /health/live` every 30s.

### Frontend (`frontend/Dockerfile`)
- **Stage 1 (Builder):** Uses `node:20-alpine`. Copies `package*.json`, runs `npm ci` with immutable package locks, passes build arguments (`VITE_API_BASE_URL`), and compiles production assets via `npm run build`.
- **Stage 2 (Runner):** `nginx:alpine` serving compiled assets from `/usr/share/nginx/html`.
- **Reverse Proxy:** Routes `/api/` upstream to `http://backend:8000` and `/health` to `http://backend:8000/health`.

---

## 3. Docker Compose Configuration Profiles

The application provides two compose configurations:

1. **Development Stack (`docker-compose.yml`):**
   - Exposes ports for local debugging (`5432` for DB, `6379` for Redis, `8000` for backend, `80` for frontend).
   - Fast restart policies (`unless-stopped`).

2. **Production Hardened Stack (`docker-compose.prod.yml`):**
   - **Isolated Networking:** Internal services (`db`, `redis`, `backend`) do not expose host ports. Only frontend binds to host ports `80` and `443`.
   - **Resource Quotas:** Strict CPU and memory limits on every container:
     - PostgreSQL: 2.0 CPUs, 2048MB memory limit
     - Redis: 1.0 CPUs, 1024MB memory limit with `volatile-lru` eviction
     - Backend: 2.0 CPUs, 2048MB memory limit
     - Frontend: 1.0 CPUs, 512MB memory limit
   - **Log Rotation:** Docker daemon `json-file` logging driver with `max-size: 20m` and `max-file: 5` to prevent disk exhaustion.
   - **Service Dependencies:** Backend startup waits for `db` and `redis` health checks to pass before initiating migrations and binding port 8000.

---

## 4. Operational Commands

### Launch Production Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Inspect Container Health & Status
```bash
docker compose -f docker-compose.prod.yml ps
```

### Stream Production Logs
```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

### Graceful Shutdown
```bash
docker compose -f docker-compose.prod.yml down
```

