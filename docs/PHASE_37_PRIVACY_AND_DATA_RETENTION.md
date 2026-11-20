# Phase 37: Analytics Privacy Controls & Data Retention Architecture

**Project:** AI Editorial Workspace — This Week in AI  
**Scope:** Data Minimization, Cryptographic Pseudonymization, User Privacy Controls & Retention  
**Compliance Level:** Enterprise Zero-Leakage First-Party Standard  

---

## 1. Privacy First Principles

The **AI Editorial Workspace** is designed for publishing teams handling confidential research, proprietary trade analysis, and pre-release technological briefs. Product analytics must never act as a backdoor for exfiltrating sensitive editorial content or credentials.

### Absolute Red Lines (Never Captured in Analytics)
- **Raw AI Prompts:** Negative constraints, system prompts, or customized instructions.
- **Source Documents:** Ingested PDF text, web page bodies, or full arXiv articles.
- **Editorial Text:** Draft sections, revision histories, or unapproved commentary.
- **Authentication Secrets:** Passwords, password hashes, JWT access tokens, API keys, bearer tokens.
- **Personally Identifiable Information (PII):** User email addresses, personal phone numbers, physical locations, real names.
- **Unsanitized URLs:** URLs containing access tokens, session identifiers, or query parameters.

---

## 2. Privacy Implementation Layers

```
   Client Action / Server Operation
                 │
                 ▼
 ┌────────────────────────────────┐
 │ 1. Opt-Out & DNT Pre-Check     │ ──► User opted out? Drop immediately (0 DB writes)
 └────────────────────────────────┘
                 │ (Allowed)
                 ▼
 ┌────────────────────────────────┐
 │ 2. Cryptographic Pseudonymizer │ ──► user_id ──► HMAC-SHA256(secret_key) ──► usr_<hex>
 └────────────────────────────────┘
                 │
                 ▼
 ┌────────────────────────────────┐
 │ 3. Property Allowlist & Filter │ ──► Strips forbidden keys (prompt, text, token, email)
 └────────────────────────────────┘     Caps strings at 120 chars; enforces scalar types
                 │
                 ▼
 ┌────────────────────────────────┐
 │ 4. Idempotency & Deduplicator  │ ──► SHA-256(org:event:workflow:session:minute)
 └────────────────────────────────┘     Matches in 5-min window? Drop duplicate
                 │
                 ▼
 ┌────────────────────────────────┐
 │ 5. Durable Storage & Retention │ ──► analytics_events table (90-day retention purge)
 └────────────────────────────────┘
```

### 2.1 Cryptographic User Pseudonymization
Instead of persisting `user_id` or `email`, user identity is hashed using HMAC-SHA256 with the application `SECRET_KEY`:
```python
salt = getattr(settings, "SECRET_KEY", "editorial-workspace-analytics-salt")
h = hmac.new(salt.encode("utf-8"), user_id.encode("utf-8"), hashlib.sha256)
user_pseudonym = f"usr_{h.hexdigest()[:24]}"
```
- **Irreversibility:** An evaluator or attacker inspecting the analytics database cannot reverse `user_pseudonym` to discover the underlying email or identity without the cluster's secret key.
- **Journey Consistency:** A single user produces the same pseudonym across sessions within a single deployment, allowing accurate active user calculations without identity leakage.

### 2.2 Property Allowlist & Forbidden Key Stripping
Implemented in `AnalyticsService.sanitize_properties()`:
```python
FORBIDDEN_KEY_PATTERNS = {
    "prompt", "content", "text", "body", "password", "token", "secret", "key",
    "email", "authorization", "cookie", "credential", "bearer", "private", "ssn",
    "url", "document", "raw", "phone", "address"
}
```
Any property whose key matches a forbidden substring is dropped. Strings longer than 120 characters or containing JWT header indicators (`eyJ...`) or API key prefixes (`sk-...`, `ghp_...`) are rejected.

### 2.3 User Privacy Preferences & Opt-Out
- Table: `analytics_privacy_preferences`
- Columns: `user_id`, `organization_id`, `analytics_opt_out`, `do_not_track`, `updated_at`.
- When `analytics_opt_out = True`, all subsequent events for that user are acknowledged and immediately dropped without persistence.
- Users can toggle this preference directly via the UI toggle on the Product Analytics Dashboard or via `PUT /api/v1/analytics/privacy-preference`.

---

## 3. Data Retention & Safe Rotation Lifecycle

### 3.1 Policy Configuration
- **Standard Retention Window:** 90 calendar days.
- **Target Tables:** `analytics_events`, `usage_events`.
- **Absolute Preservation:** Core application entities (`research_projects`, `sources`, `source_analyses`, `research_briefs`, `writing_drafts`, `editorial_outputs`, `editorial_reviews`, `user_feedbacks`, `users`, `organizations`) are **NEVER touched** by analytics retention routines.

### 3.2 Scheduled / On-Demand Purge
- Endpoint: `POST /api/v1/analytics/retention/cleanup?retention_days=90`
- Query:
  ```python
  cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
  deleted = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at < cutoff).delete(synchronize_session=False)
  ```
- All retention purge operations emit audit logs with the exact count of records deleted and duration.
