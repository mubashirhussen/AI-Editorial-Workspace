# AI Editorial Workspace — CI/CD Pipeline Guide

The AI Editorial Workspace enforces quality, security, and migration checks via GitHub Actions.

---

## 1. Pipeline Overview

```
Push / Pull Request
   │
   ├── Backend CI (.github/workflows/backend-ci.yml)
   │     ├── Python 3.10 & 3.11 Matrix
   │     ├── Bytecode Compilation (compileall)
   │     ├── Alembic Migration on Isolated DB
   │     └── Pytest Execution (104 tests) with JUnit XML
   │
   ├── Frontend CI (.github/workflows/frontend-ci.yml)
   │     ├── Node 18 & 20 Matrix
   │     ├── TypeScript Type Check (tsc -b)
   │     └── Production Vite Build (npm run build)
   │
   ├── Security Checks (.github/workflows/security-checks.yml)
   │     ├── Forbidden .env File Detector
   │     ├── Secret Pattern Scanner (OpenAI keys, AWS keys, RSA keys)
   │     └── Dependency CVE Scans (npm audit, pip-audit)
   │
   └── E2E Tests (.github/workflows/e2e-tests.yml)
         └── End-to-end integration across workflow modules
```

---

## 2. Workflow Specifications

### 2.1. Backend CI (`backend-ci.yml`)
- **Triggers:** Push or PR touching `backend/**`, `requirements.txt`, or workflow file.
- **Environment:** Clean `ubuntu-latest` with temporary SQLite database (`ci_test.db`).
- **Steps:**
  1. Installs pinned dependencies from `backend/requirements.txt`.
  2. Runs `python -m compileall backend/app backend/tests` to detect syntax errors before test execution.
  3. Executes `alembic -c backend/alembic.ini upgrade head` on an empty database to guarantee migration chain integrity.
  4. Runs full Pytest suite generating JUnit XML test artifacts uploaded for review.

### 2.2. Frontend CI (`frontend-ci.yml`)
- **Triggers:** Push or PR touching `frontend/**` or `package.json`.
- **Environment:** Clean `ubuntu-latest` across Node 18.x and 20.x.
- **Steps:**
  1. Runs `npm ci` to strictly install from `package-lock.json`.
  2. Runs `npx tsc -b` to enforce TypeScript compilation without type-widening or loose anys.
  3. Executes `npm run build` to verify production bundling and asset chunking.
  4. Uploads production `dist/` artifact on Node 20.x runs.

### 2.3. Security & Secret Scanner (`security-checks.yml`)
- Prevents accidental check-in of `.env` files.
- Regex scans all committed files for leaked API keys, tokens, or private certificates.
- Runs automated CVE audits on dependencies using `pip-audit` and `npm audit`.

---

## 3. Local Pre-Commit Verification

Before opening a pull request or pushing to `main`, developers should run:

```bash
# 1. Backend tests and compilation
python -m compileall backend/app backend/tests
pytest backend/tests -v

# 2. Frontend typecheck and build
cd frontend
npx tsc -b
npm run build
```
