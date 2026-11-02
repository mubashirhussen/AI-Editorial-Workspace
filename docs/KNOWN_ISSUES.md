# AI Editorial Workspace — Known Issues, Technical Debt & Risk Log

**Audit Date:** November 2026  
**Auditor:** Senior Full-Stack Architect, AI Engineer & QA Lead  
**Repository:** [https://github.com/mubashirhussen/AI-Editorial-Workspace](https://github.com/mubashirhussen/AI-Editorial-Workspace)  
**Branch:** `main`  

---

## 1. Prioritized Issues Matrix

| Issue ID | Severity | Subsystem | Description | Impact | Mitigation / Status | Target Resolution |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **SEC-01** | **High** | Secret Management / Encryption | In PR #1 (`fix/production-secret-hardening`), `SECRET_KEY` alias is set to `JWT_SECRET`. `encryption.py` derives its Fernet key from `SECRET_KEY`. Rotating `JWT_SECRET` would silently break decryption of all previously stored AI provider keys. | Severe: Provider keys fail decryption after secret rotation. | Decouple `ENCRYPTION_KEY` in `config.py` and `encryption.py`. Check `ENCRYPTION_KEY` first, fallback to `SECRET_KEY`. | **Phase 3** |
| **RES-01** | **Medium** | Research Ingestion | Complex JavaScript Single-Page Applications (SPAs) without SSR return empty DOM containers when fetched via basic HTTP scrapers. | Medium: Initial URL scrape may yield low word count on SPA pages. | **Mitigated:** Enhanced 4-tier extraction pipeline (Trafilatura $\rightarrow$ BS4 DOM $\rightarrow$ Meta tags $\rightarrow$ Raw paste) and inline "Paste Text" UI button. | **Phase 8** |
| **COL-01** | **Medium** | Real-Time Collaboration | Document versioning relies on append-only snapshot diffing and REST restoration rather than live operational transformation / WebSockets. | Low-Medium: Concurrent typing by two editors in the same draft requires manual version comparison. | Plan real-time CRDT / Yjs WebSockets server for future multi-editor roadmap. | **Phase 10** |
| **AI-01** | **Low** | Editorial Studio | Token generation in some endpoints executes synchronously or batch-accumulates before returning JSON instead of Server-Sent Events (SSE) streaming. | Low: User sees progress spinner for 2–4s rather than typewriter effect. | Add FastAPI `StreamingResponse` for SSE token streaming. | **Phase 11** |
| **DEP-01** | **Low** | Test Invariants | Starlette deprecation warnings in pytest logs for `HTTP_422_UNPROCESSABLE_ENTITY` in favor of `HTTP_422_UNPROCESSABLE_CONTENT`. | Negligible: Fully functional, produces 5 deprecation warnings in test suite. | Replace status enum with `status.HTTP_422_UNPROCESSABLE_CONTENT` across exception handlers. | **Phase 5** |

---

## 2. Root Cause Analysis of PR #1 Risk (SEC-01)

### The Vulnerability:
In `backend/app/core/encryption.py`:
```python
def _get_fernet_instance() -> Fernet:
    """Derives a deterministic 32-byte url-safe base64 key from settings.SECRET_KEY."""
    raw_key = getattr(settings, "SECRET_KEY", "editorial-workspace-encryption-key-production-seed-32bytes")
    derived_hash = hashlib.sha256(raw_key.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(derived_hash)
    return Fernet(b64_key)
```

In `backend/app/core/config.py` of PR #1:
```python
SECRET_KEY: str = Field(
    default=_DEVELOPMENT_SECRET_KEY,
    validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
)
```
When an operator deploys to production and sets `JWT_SECRET=super_secure_random_jwt_string_1234567890`, any existing database credentials that were encrypted using a different `SECRET_KEY` will fail to decrypt with:
```text
cryptography.fernet.InvalidToken
```

### The Architectural Solution:
1. Support `ENCRYPTION_KEY: Optional[str] = None` in `Settings`.
2. In `encryption.py`, resolve key as:
   ```python
   raw_key = getattr(settings, "ENCRYPTION_KEY", None) or getattr(settings, "SECRET_KEY", "default-fallback-key")
   ```
3. This allows independent rotation of `JWT_SECRET` (for user session security) without invalidating database-encrypted AI provider keys.
