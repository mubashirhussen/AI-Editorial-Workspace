# AI Editorial Workspace — Production Environment Configuration Guide

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Phase:** Phase 14 — Production Readiness & Release Candidate Validation  
**Date:** November 2026  
**Auditor:** Senior Cloud Architect & Security Engineer  
**Status:** **OPERATIONAL & SECURE**

---

## 1. Overview & Security Rules

All configuration in the AI Editorial Workspace adheres to **Twelve-Factor App** principles. Environment variables strictly separate application logic from deployment secrets:

1. **Zero Secret Leakage:** Never commit `.env` or production credentials to Git. `.gitignore` strictly ignores `.env`, `*.pem`, `*.key`, and `credentials.json`.
2. **Frontend Bundle Hygiene:** The client bundle only receives variables prefixed with `VITE_` (e.g., `VITE_API_BASE_URL`). Backend database connection strings, JWT secrets, and AI provider API keys are **never** injected into the frontend build.
3. **Cryptographic Decoupling:** JWT session signing (`SECRET_KEY`) and database-at-rest credential encryption (`ENCRYPTION_KEY`) use separate, independent cryptographic keys. Rotating session tokens never corrupts stored AI provider keys.
4. **Production Rejection of Weak Defaults:** Startup checks immediately terminate the FastAPI process if `SECRET_KEY` uses a known default or is shorter than 32 characters when `ENVIRONMENT=production`.

---

## 2. Environment Variables Catalog

| Variable Name | Environment Scope | Default (Development) | Production Requirement | Description |
| :--- | :---: | :--- | :--- | :--- |
| **`ENVIRONMENT`** | Runtime | `development` | `production` | Activates strict production validation & disables auto-schema generation |
| **`TESTING`** | Runtime | `false` | `false` | When `true`, rate limits are bypassed for test suites |
| **`API_V1_PREFIX`** | Both | `/api/v1` | `/api/v1` | Global API route prefix |
| **`SECRET_KEY`** | Backend | `_DEFAULT_DEV_SECRET` | **REQUIRED (>= 32 chars)** | HMAC-SHA256 signing secret for user authentication JWT tokens |
| **`ENCRYPTION_KEY`** | Backend | `None` | **REQUIRED (32-byte b64)** | Fernet symmetric key for encrypting provider API keys at rest |
| **`ALGORITHM`** | Backend | `HS256` | `HS256` | JWT signing algorithm |
| **`ACCESS_TOKEN_EXPIRE_MINUTES`** | Backend | `1440` (24h) | `1440` | JWT token lifetime before re-authentication is required |
| **`ALLOW_ANONYMOUS_DEV`**| Backend | `true` | **`false`** | Strictly disables unauthenticated fallback accounts |
| **`DATABASE_URL`** | Backend | `sqlite:///./editorial.db` | `postgresql://...` | Connection URL for PostgreSQL 15+ database cluster |
| **`POSTGRES_USER`** | Docker | `editorial_user` | Strong username | Database cluster owner |
| **`POSTGRES_PASSWORD`** | Docker | `change_this...` | High-entropy password | Database master password |
| **`POSTGRES_DB`** | Docker | `editorial_workspace` | Database name | Target database |
| **`REDIS_URL`** | Backend | *None* | `redis://redis:6379/0` | Redis instance for async caching and background task execution |
| **`LOG_LEVEL`** | Backend | `INFO` | `INFO` or `WARNING` | Application logging verbosity |
| **`ALLOWED_ORIGINS`** | Backend | `http://localhost:5173` | Comma-separated domains | Trusted CORS origins |
| **`FRONTEND_ORIGIN`** | Backend | `http://localhost:5173` | Deployed frontend domain | Canonical client origin |
| **`MAX_EXTRACTION_BYTES`** | Backend | `2097152` (2MB) | `2097152` | Maximum HTTP body download size for source ingestion |
| **`MAX_CONTENT_CHARS`** | Backend | `100000` | `100000` | Maximum character length for extracted article text |
| **`EXTRACTION_TIMEOUT_SECONDS`**| Backend | `12` | `12` | Socket timeout for scraping external articles |
| **`MAX_REDIRECTS`** | Backend | `4` | `4` | Maximum HTTP redirect depth allowed during scraping |
| **`DEFAULT_AI_PROVIDER`** | Backend | `groq` | `groq` or `openai` | Default provider for synthesis and linters |
| **`DEFAULT_AI_MODEL`** | Backend | `openai/gpt-oss-20b` | Production model name | Active foundation model identifier |
| **`GROQ_API_KEY`** | Backend | Optional | User credential | LPU inference key (Groq Cloud) |
| **`OPENAI_API_KEY`** | Backend | Optional | User credential | OpenAI API key |
| **`ANTHROPIC_API_KEY`** | Backend | Optional | User credential | Anthropic Claude API key |
| **`GOOGLE_AI_API_KEY`** | Backend | Optional | User credential | Google Gemini API key |
| **`VITE_API_BASE_URL`** | Frontend | `/api/v1` | `/api/v1` | Reverse proxy API root path |

---

## 3. Cryptographic Key Generation Procedures

To generate production secrets, execute the provided Python utility script or shell one-liners:

```powershell
# 1. Generate 32-character High-Entropy JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Generate Fernet-Compatible Credential Encryption Key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 4. Environment Matrix Comparison

```
========================================================================================================
Setting                  Development Mode            Staging Environment         Production Environment
========================================================================================================
ENVIRONMENT              development                 staging                     production
ALLOW_ANONYMOUS_DEV      true                        false                       false
DATABASE_URL             sqlite:///./editorial.db    postgresql://...:5432/test  postgresql://...:5432/prod
SECRET_KEY               dev_secret_key              high-entropy 32+ chars      high-entropy 32+ chars
ENCRYPTION_KEY           auto-derived fallback       explicit Fernet key         explicit Fernet key
MIGRATION ENFORCEMENT    auto-detect (dev seed)      alembic upgrade head        alembic upgrade head
REDIS                    optional (in-memory)        redis container             managed Redis cluster
CORS ORIGINS             localhost:5173, 3000        staging.yourdomain.com      app.yourdomain.com
LOGGING VERBOSITY        DEBUG / INFO                INFO                        INFO / WARNING
========================================================================================================
```

