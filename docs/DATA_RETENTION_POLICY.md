# Data Retention & Privacy Policy

This document defines data lifecycle, retention schedules, sanitization, and privacy policies for the **AI Editorial Workspace**.

---

## 1. Data Classification & Retention Matrix

| Data Category | Tables Involved | Retention Period | Deletion / Archive Policy | Encryption / Privacy |
| :--- | :--- | :--- | :--- | :--- |
| **User Identity** | `users`, `user_sessions`, `password_reset_tokens` | Active account duration + 30 days upon deletion request | Soft-delete (`deleted_at`); sessions revoked immediately | Bcrypt password hash; session token SHA-256 hashed |
| **Organizations & Access** | `organizations`, `organization_memberships`, `invitations` | Indefinite while organization is active | Hard delete on workspace closure | Cascading deletion across organization projects |
| **Research Sources & Raw Copy** | `sources`, `source_analyses` | Indefinite or until user initiates removal | Soft-delete (`deleted_at`); purged from active index | SSRF filtering on ingest; raw HTML sanitized |
| **Research Synthesis & Claims** | `research_briefs`, `research_claims`, `research_evidence` | Indefinite | Retained for citation audits; cascaded on project deletion | Deterministic NLP claim extraction |
| **Editorial Drafts & Versions** | `writing_drafts`, `editorial_versions`, `editorial_outputs` | Indefinite (Immutable version history) | Append-only; soft-delete on draft hides from active editor | Version snapshots are never overwritten |
| **AI Provider Credentials** | `ai_provider_configs`, `integration_connections` | Indefinite until revoked or deleted by admin | Hard delete on connection removal | **AES-128-CBC / Fernet encrypted at rest**; UI displays masked `sk-...4e2f` |
| **Audit Logs & Activity** | `audit_logs`, `user_activity_logs` | **365 days** (1 year) | Archived to cold storage after 365 days | Actor IP & user agent logged; credentials strictly omitted |
| **AI Telemetry & Token Usage** | `provider_usage_records`, `usage_events` | **90 days** fine-grained; aggregated monthly thereafter | Rolled up into monthly summary metrics | No prompt payloads stored in usage records |
| **Background Job Records** | `background_jobs` | **30 days** after completion or failure | Automatic rotation of completed jobs | Error traces sanitized for sensitive data |

---

## 2. Privacy & Secret Handling Guarantees

1. **No Plaintext Secrets at Rest**:
   * All API keys (OpenAI, Gemini, Anthropic, Groq) and webhook secrets are encrypted using AES/Fernet encryption via `backend/app/core/encryption.py`.
2. **Zero-Secret Logging**:
   * API request/response logging middleware and error handlers redact `Authorization`, `X-API-Key`, passwords, and token fields.
3. **Data Subject Rights (GDPR / CCPA Compliant)**:
   * **Right to Erasure**: Soft-deletes user accounts and cascades session revocations.
   * **Right to Portability**: Workspace exports format research briefs and drafts into standardized JSON / Markdown bundles.

