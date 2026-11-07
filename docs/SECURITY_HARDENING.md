# AI Editorial Workspace — Production Security Hardening & Threat Model

This document outlines the security architecture, defensive mitigations, and compliance postures implemented in the AI Editorial Workspace to protect tenant data, prevent server-side attacks, and maintain cryptographic hygiene.

---

## 1. Threat Model & Mitigations Matrix

| Threat Category | Attack Vector | Technical Mitigation | Implementation File |
| :--- | :--- | :--- | :--- |
| **SSRF (Server-Side Request Forgery)** | Malicious URL ingestion probing `169.254.169.254`, `localhost`, or private subnets | Pre-fetch DNS resolution validation; blocking IPv4/IPv6 private ranges, cloud metadata, link-local, loopback, and carrier-grade NAT | `backend/app/utils/security.py` |
| **Credential & Secret Leakage** | Default/weak JWT secrets committed to version control or running in production | Startup invariant validator rejecting known weak keys and secrets under 32 characters in production mode | `backend/app/core/config.py` |
| **Credential-at-Rest Exposure** | Plaintext API keys stored in PostgreSQL | Cryptographic encryption at rest using Fernet (AES-128-CBC + HMAC-SHA256) with independent key isolation | `backend/app/services/ai/manager.py` |
| **Clickjacking & MIME Confusion** | Embedding application in malicious iframes; MIME sniffing | Security headers middleware enforcing `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` | `backend/app/main.py` |
| **DoS / Resource Exhaustion** | High-frequency API request spamming | Token-bucket sliding window rate limiter (`180 req/min/IP`) returning HTTP 429 with retry backoff headers | `backend/app/main.py` |
| **Malicious Payload Injection** | Oversized file uploads, zip bombs, or endless redirect loops | Enforced 2MB maximum payload limit, 100K char caps, 4 max redirects, and strict file extension & signature checking | `backend/app/services/research/extraction_service.py` |
| **Cross-Tenant Data Leakage** | IDOR attacks accessing other organization's research or drafts | Strict tenant isolation in DB queries: `organization_id` required and verified against authenticated JWT context | `backend/app/api/deps.py` |

---

## 2. SSRF Protection Architecture

The extraction engine prevents SSRF through a multi-stage validation pipeline:
1. **Scheme Validation:** Only `http` and `https` schemes are accepted.
2. **Host Blacklisting:** Immediate rejection of reserved names (`localhost`, `metadata.google.internal`, `169.254.169.254`, `100.100.100.200`, `.local`, `.internal`, `.lan`, `.home.arpa`).
3. **DNS Pre-Resolution & Subnet Inspection:** Resolves hostnames to IP addresses before initiating HTTP connections. Verifies IP against:
   - `ip.is_private` (RFC 1918)
   - `ip.is_loopback` (`127.0.0.0/8`, `::1`)
   - `ip.is_link_local` (`169.254.0.0/16`, AWS/GCP/Azure instance metadata)
   - Carrier-grade NAT (`100.64.0.0/10`)
   - Test nets and limited broadcast ranges (`255.255.255.255/32`)
4. **Redirect Re-validation:** Every redirect destination is re-validated through the entire SSRF filter before being followed.

---

## 3. Cryptographic Key Lifecycle

### JWT Authentication Secret
- Algorithm: HMAC-SHA256 (`HS256`)
- Generation: Cryptographically secure pseudo-random bytes (`secrets.token_urlsafe(32)`).
- Scope: Signed into Bearer tokens with 24-hour expiration.

### Data-at-Rest Encryption (Fernet)
- Specification: URL-safe base64-encoded 32-byte key executing AES-128-CBC with PKCS7 padding and HMAC-SHA256 authentication.
- Storage: Injected strictly via environment variable (`ENCRYPTION_KEY`). Never persisted to the database.

---

## 4. Container Security Hardening

- **Non-Root Execution:** Backend containers run as non-privileged `appuser` (UID 10001) in `appgroup` (GID 10001).
- **Minimal Image Footprint:** Built on Debian Slim (`python:3.11-slim`) and Alpine (`nginx:alpine`) with compiler tools stripped in builder stages.
- **Health Verification:** Native liveness probes monitor internal endpoints without exposing unauthenticated administrative controls.

