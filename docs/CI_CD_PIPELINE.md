# AI Editorial Workspace — Enterprise CI/CD Pipeline Specification

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Phase:** Phase 14 — Production Readiness & Release Candidate Validation  
**Date:** November 2026  
**Auditor:** Senior DevSecOps Engineer  
**Status:** **ACTIVE & ENFORCED**

---

## 1. Pipeline Architecture Overview

The repository features automated GitHub Actions workflows enforcing continuous integration, multi-stage testing against PostgreSQL and Redis, container builds, and security auditing across branches `main`, `release/**`, and `feat/**`.

```
[ Push / Pull Request ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 1: Checkout & Runtime Environment Setup          │
│ • Python 3.10/3.11 & Node.js 20.x                      │
│ • Dependency caching (pip cache + npm cache)           │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 2: Code Quality, Linting & Type Checking         │
│ • Python bytecode verification (compileall)            │
│ • Frontend TypeScript compilation (tsc -b --noEmit)    │
│ • Formatting & style validation                        │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 3: Automated Test Execution                      │
│ • Live PostgreSQL 15 & Redis 7 container services     │
│ • 208 Backend Automated Pytest Tests (100% Passing)    │
│ • 34 Offline AI Reliability Benchmarks                 │
│ • Client-side text analysis test suite                 │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 4: Database Migration Invariants                 │
│ • Fresh PostgreSQL upgrade: alembic upgrade head       │
│ • Schema assertion: 34 tables created                  │
│ • Rollback safety verification                         │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 5: DevSecOps Vulnerability & SSRF Scanning       │
│ • Dependency audits (pip-audit, npm audit)             │
│ • Secret scanning (trufflehog / gitleaks)              │
│ • SSRF destination boundary unit tests                 │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 6: Multi-Stage Production Container Builds       │
│ • Frontend Nginx image build (Vite static assets)      │
│ • Backend Python runner build (non-root UID 10001)     │
│ • Image layer vulnerability scanning                   │
└────────────────────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Stage 7: Release Staging & Deployment Gate             │
│ • Tagging of Release Candidate (v1.0.0)                │
│ • Environment gate validation                          │
└────────────────────────────────────────────────────────┘
```

---

## 2. Active GitHub Actions Workflow Inventory

| Workflow File | Purpose | Trigger Events | Primary Jobs |
| :--- | :--- | :--- | :--- |
| [`.github/workflows/ci.yml`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/.github/workflows/ci.yml) | Continuous Integration | `push`, `pull_request`, `workflow_dispatch` | Lint, Typecheck, Backend Pytest (Postgres), Frontend Build, Docker Build |
| [`.github/workflows/devsecops.yml`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/.github/workflows/devsecops.yml) | DevSecOps Pipeline | `push`, `pull_request`, `schedule` | 7-Stage pipeline: SAST, Secret Scanning, Dependency Audit, SSRF bounds |
| [`.github/workflows/backend-ci.yml`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/.github/workflows/backend-ci.yml) | Backend Focused CI | `push`, `pull_request` | Fast backend verification & migration regression |
| [`.github/workflows/frontend-ci.yml`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/.github/workflows/frontend-ci.yml) | Frontend Focused CI | `push`, `pull_request` | Vite production build & asset bundle budgeting |
| [`.github/workflows/cd.yml`](file:///c:/Users/Mubashirhussensk/OneDrive/Desktop/FDE%20intern/.github/workflows/cd.yml) | Continuous Delivery | Push to `main` or release tag | Container registry publish & staging deploy hook |

---

## 3. Strict Pipeline Integrity Invariants

1. **Zero Fake Passes:** Tests must genuinely pass with returncode 0. Converting failures into warnings (`|| true`) is strictly prohibited on test assertions.
2. **Real PostgreSQL Service:** Backend tests in CI run against live containerized PostgreSQL 15, validating real relational behavior, foreign key cascades, and connection pool behavior.
3. **Secret Security:** All production deployment secrets are managed exclusively through GitHub Actions Secrets (`PROD_DATABASE_URL`, `PROD_JWT_SECRET`, `PROD_ENCRYPTION_KEY`). Secrets are never printed in job logs.

