# AI Editorial Workspace — Security Audit & Threat Model

**Audit Date:** November 2026  
**Audited Target:** Main Application Stack (FastAPI, React, PostgreSQL/SQLite)  
**Security Posture:** Hardened / Production Grade  

---

## 1. Threat Modeling & Scope

The AI Editorial Workspace processes external untrusted inputs, including:
1. User-supplied web URLs for automated content extraction.
2. User-uploaded document files (PDF, DOCX, TXT, images).
3. Third-party AI API credentials (OpenAI, Anthropic, Gemini, Groq).
4. User authentication tokens and workspace collaboration payloads.

### Threat Matrix & Mitigations

| Threat Vector | Potential Impact | Implementation Mitigation | Verification Status |
| :--- | :--- | :--- | :--- |
| **Server-Side Request Forgery (SSRF)** | Internal cloud metadata exfiltration (AWS IAM tokens, GCP metadata), internal port scanning. | `extraction_service.py` validates protocol (only `http`/`https`), resolves DNS host, and rejects RFC 1918 private subnets, loopback `127.0.0.1`, and link-local `169.254.169.254`. | **VERIFIED** (Passes test suite `test_scenario_f_security_and_ssrf_guardrails`) |
| **Credential Storage Compromise** | Exposure of organization AI API keys stored in database. | Keys encrypted with AES-128 via Fernet symmetric cryptography before writing to database. Serialization masks all keys (`••••••••`). | **VERIFIED** (Tested in `test_phase5_ai_integration.py`) |
| **Authentication & Session Hijacking** | Unauthorized workspace access. | Passwords hashed using `bcrypt` (12 rounds). Tokens signed with HS256 JWT, short expiry (15m default), secure refresh endpoint. | **VERIFIED** (Passes `test_phase21_security_hardening.py`) |
| **Denial of Service (DoS)** | Resource exhaustion via excessive API requests or large files. | In-memory sliding window rate limiting (120 req/min/IP). Strict 10MB payload size limits on file uploads and content extraction. | **VERIFIED** (Tested in `test_phase17_observability.py`) |
| **Cross-Site Scripting (XSS)** | Execution of malicious scripts in editor or dashboard. | React automatic output escaping; Nginx security headers (`X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, strict CSP). | **VERIFIED** (Passed frontend typecheck & bundle) |
| **SQL Injection** | Unauthorized database manipulation or exfiltration. | 100% ORM-bound queries via SQLAlchemy with parameterized execution. Zero raw SQL string concatenation. | **VERIFIED** (All 34 models strictly mapped) |

---

## 2. Network & SSRF Defenses

The extraction pipeline enforces defense-in-depth:

```python
FORBIDDEN_SUBNETS = [
    ipaddress.ip_network("127.0.0.0/8"),    # IPv4 loopback
    ipaddress.ip_network("10.0.0.0/8"),     # Private network RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),  # Private network RFC 1918
    ipaddress.ip_network("192.168.0.0/16"), # Private network RFC 1918
    ipaddress.ip_network("169.254.0.0/16"), # Link-local / Cloud metadata
    ipaddress.ip_network("::1/128"),        # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),       # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),      # IPv6 link-local
]
```

Every incoming URL is verified:
1. URL parsed to extract hostname and scheme.
2. Scheme must be `http` or `https`.
3. Hostname resolved to IPv4/IPv6 address via socket lookup.
4. Resolved IP tested against all forbidden subnets.
5. If match found, immediately raises HTTP 400 Bad Request: `Target URL resolves to a protected or private IP address.`

---

## 3. Cryptographic Standards

- **Passwords:** Salted `bcrypt` hash generated using Python's `bcrypt` library with a minimum work factor of 12.
- **JWT Authentication:** Tokens signed using HMAC-SHA256 (`HS256`) with a cryptographically random secret key (`SECRET_KEY`).
- **Encrypted Provider Keys:** Keys encrypted using `cryptography.fernet` (AES-128 in CBC mode with HMAC-SHA256 authentication).
- **Masking:** Any read endpoint returns `mask_api_key(key)` producing `••••••••` followed by the last 4 characters, preventing screen-sharing leakage.

---

## 4. Container & Operating System Hardening

- Container images run as unprivileged user `appuser` (UID 10001, GID 10001).
- Root filesystem is read-only except designated storage directories (`/app/backend/data`, `/app/backend/backups`).
- No compilation toolchains (`gcc`, `g++`, `make`) persist in the final runtime container image.
- `.dockerignore` strictly excludes `.git`, `.env`, temporary caches, and local databases.
