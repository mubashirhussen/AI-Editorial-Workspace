# AI Editorial Workspace — Environment Variables & Configuration Reference

This document serves as the master specification for all environment variables supported by the AI Editorial Workspace across development, staging, and production environments.

---

## 1. Production Invariant Enforcement

In `production` mode (`ENVIRONMENT=production` or `ENV=production`), the application automatically validates the following security invariants on startup:

| Variable | Invariant Requirement | Enforcement Failure Behavior |
| :--- | :--- | :--- |
| `SECRET_KEY` | Length $\ge$ 32 characters, cannot match any known default/weak secret | Process exits immediately with `ValueError` |
| `ALLOW_ANONYMOUS_DEV` | Must be set to `false` | Process exits immediately with `ValueError` |
| `ENCRYPTION_KEY` | Must decode to exactly 32 bytes (Fernet URL-safe base64 standard) | Process exits immediately with `ValueError` |

---

## 2. Core Application Settings

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | String | `development` | Deployment environment: `development`, `testing`, `staging`, `production`. |
| `TESTING` | Boolean | `false` | When `true`, rate limiting and auth barriers are relaxed for automated test harnesses. |
| `APP_NAME` | String | `AI Editorial Workspace` | Application branding displayed in health and telemetry endpoints. |
| `API_V1_PREFIX` | String | `/api/v1` | URL routing prefix for all REST API endpoints. |
| `LOG_LEVEL` | String | `INFO` | Logging threshold: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |

---

## 3. Cryptography & Authentication

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` / `JWT_SECRET` | String | Dev default string | Cryptographic secret used for signing and verifying HMAC-SHA256 JWT access tokens. Must be generated using `scripts/generate_secrets.py`. |
| `ENCRYPTION_KEY` | String | None | 32-byte URL-safe base64 key used for AES-128-CBC / Fernet data-at-rest encryption of provider API keys. |
| `ALGORITHM` | String | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `1440` (24h) | JWT access token lifespan before re-authentication is required. |
| `ALLOW_ANONYMOUS_DEV` | Boolean | `true` (dev only) | Allows unauthenticated requests in local developer sandbox. Strictly disallowed in production. |

---

## 4. Database & Storage

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | `sqlite:///./editorial.db` | SQLAlchemy connection string. In production, use PostgreSQL: `postgresql://user:pass@host:5432/dbname`. |
| `POSTGRES_USER` | String | `editorial_user` | PostgreSQL username (used by Docker Compose). |
| `POSTGRES_PASSWORD` | String | None | PostgreSQL password. |
| `POSTGRES_DB` | String | `editorial_workspace` | PostgreSQL database name. |
| `BACKUP_DIR` | String | `backend/backups` | Target directory where `scripts/backup_db.py` writes dump files and checksum manifests. |
| `BACKUP_RETENTION_DAYS` | Integer | `7` | Retention window for automated pruning of expired backups. |

---

## 5. Background Task Queue & Caching

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `REDIS_URL` / `CELERY_BROKER_URL` | String | None | Redis connection URL (`redis://redis:6379/0`). If omitted, task queue automatically falls back to in-memory async execution. |

---

## 6. Networking & CORS

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ALLOWED_ORIGINS` | Comma-delimited String / List | Localhost origins | Permitted HTTP origins for Cross-Origin Resource Sharing (CORS). Example: `https://app.editorial.com,https://admin.editorial.com`. |
| `FRONTEND_ORIGIN` | String | `http://localhost:5173` | Primary frontend application URL used for links and redirect validations. |

---

## 7. AI Provider Integrations

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GROQ_API_KEY` | String | None | API key for high-speed Groq LPU inference. |
| `OPENAI_API_KEY` | String | None | API key for OpenAI GPT models. |
| `ANTHROPIC_API_KEY` | String | None | API key for Anthropic Claude models. |
| `GOOGLE_AI_API_KEY` | String | None | API key for Google Gemini models. |
| `DEFAULT_AI_PROVIDER` | String | `groq` | Primary fallback provider when none is specified. |
| `DEFAULT_AI_MODEL` | String | `openai/gpt-oss-20b` | Default model identifier. |

---

## 8. Extraction Limits & Security Bounds

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `MAX_EXTRACTION_BYTES` | Integer | `2097152` (2MB) | Maximum payload size permitted for downloaded web/document sources. |
| `MAX_CONTENT_CHARS` | Integer | `100000` | Maximum character length retained per source article. |
| `EXTRACTION_TIMEOUT_SECONDS`| Integer | `12` | Bounded HTTP connection and read timeout. |
| `MAX_REDIRECTS` | Integer | `4` | Maximum allowable HTTP redirects before aborting to prevent loops. |

