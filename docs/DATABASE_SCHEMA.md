# Database Schema Reference

Complete schema specification of all 34 tables in the **AI Editorial Workspace** as of Phase 4 (`3b7c9f1e8a2d`).

---

## 1. User & Identity Management

### `users`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Unique UUID v4 identifier |
| `email` | `VARCHAR(255)` | Unique, Not Null, Index | User login and notification address |
| `hashed_password` | `VARCHAR(255)` | Not Null | Bcrypt salted password hash |
| `full_name` | `VARCHAR(255)` | Not Null | Editor / reviewer display name |
| `is_active` | `BOOLEAN` | Not Null, Default True | Account active status flag |
| `is_verified` | `BOOLEAN` | Not Null, Default True | Email verification flag |
| `deleted_at` | `DATETIME` | Nullable | Soft deletion timestamp |
| `created_at` | `DATETIME` | Not Null | Creation timestamp (UTC) |
| `updated_at` | `DATETIME` | Not Null | Last update timestamp (UTC) |

### `organizations`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Workspace identifier |
| `name` | `VARCHAR(255)` | Not Null | Workspace publication name |
| `slug` | `VARCHAR(255)` | Unique, Not Null, Index | URL-safe workspace slug |
| `created_at` | `DATETIME` | Not Null | Creation timestamp (UTC) |
| `updated_at` | `DATETIME` | Not Null | Modification timestamp (UTC) |

### `organization_memberships`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Membership UUID |
| `organization_id` | `VARCHAR(36)` | FK(`organizations.id` CASCADE), Not Null, Index | Organization reference |
| `user_id` | `VARCHAR(36)` | FK(`users.id` CASCADE), Not Null, Index | Member reference |
| `role` | `VARCHAR(50)` | Not Null, Default 'EDITOR' | Role: OWNER, ADMIN, EDITOR, REVIEWER, VIEWER |
| `joined_at` | `DATETIME` | Not Null | Timestamp of acceptance |
* **Composite Index**: `uq_org_user` on `(organization_id, user_id)` [UNIQUE]

### `organization_invitations`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Invitation UUID |
| `organization_id` | `VARCHAR(36)` | FK(`organizations.id` CASCADE), Not Null, Index | Target organization |
| `email` | `VARCHAR(255)` | Not Null, Index | Invited email address |
| `role` | `VARCHAR(50)` | Not Null | Invited role level |
| `token` | `VARCHAR(255)` | Unique, Not Null, Index | Secure invitation token |
| `invited_by_id` | `VARCHAR(36)` | FK(`users.id` SET NULL), Nullable | Inviting user |
| `expires_at` | `DATETIME` | Not Null | Token expiration timestamp |
| `accepted_at` | `DATETIME` | Nullable | Timestamp of redemption |
| `created_at` | `DATETIME` | Not Null | Issuance timestamp |

### `user_sessions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Session UUID |
| `user_id` | `VARCHAR(36)` | FK(`users.id` CASCADE), Not Null, Index | Authenticated user |
| `token_hash` | `VARCHAR(255)` | Unique, Not Null, Index | SHA-256 hash of refresh token |
| `ip_address` | `VARCHAR(50)` | Nullable | Client connection IP |
| `user_agent` | `VARCHAR(255)` | Nullable | Client browser agent |
| `expires_at` | `DATETIME` | Not Null | Session expiration |
| `is_revoked` | `BOOLEAN` | Not Null, Default False | Explicit revocation flag |
| `created_at` | `DATETIME` | Not Null | Session start |
| `updated_at` | `DATETIME` | Not Null | Activity timestamp |

### `password_reset_tokens` & `email_verification_tokens`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Token UUID |
| `user_id` | `VARCHAR(36)` | FK(`users.id` CASCADE), Not Null | Associated user |
| `token_hash` | `VARCHAR(255)` | Unique, Not Null, Index | Cryptographic token hash |
| `expires_at` | `DATETIME` | Not Null | Validity period cutoff |
| `is_used` | `BOOLEAN` | Not Null, Default False | Consumption flag |
| `created_at` | `DATETIME` | Not Null | Creation timestamp |

---

## 2. Research Management

### `research_projects`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Project UUID |
| `organization_id` | `VARCHAR(36)` | FK(`organizations.id` CASCADE), Nullable, Index | Tenant boundary |
| `title` | `VARCHAR(255)` | Not Null, Index | Investigation title |
| `name` | `VARCHAR(255)` | Nullable, Index | Project alias |
| `description` | `TEXT` | Nullable | Research objective |
| `status` | `VARCHAR(50)` | Not Null, Index | Status: draft, in_progress, completed |
| `deleted_at` | `DATETIME` | Nullable, Index | Soft deletion timestamp |
| `created_at` | `DATETIME` | Not Null, Index | Creation timestamp |
| `updated_at` | `DATETIME` | Not Null, Index | Modification timestamp |

### `sources`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Source UUID |
| `project_id` | `VARCHAR(36)` | FK(`research_projects.id` CASCADE), Not Null, Index | Parent project |
| `title` | `VARCHAR(255)` | Not Null | Article or document title |
| `url` | `VARCHAR(1024)` | Nullable, Index | Canonical source URL |
| `source_type` | `VARCHAR(50)` | Not Null | URL, TEXT, PDF, DOCX, IMAGE |
| `raw_content` | `TEXT` | Nullable | Unprocessed ingested content |
| `extracted_content` | `TEXT` | Nullable | Parsed clean text |
| `summary` | `TEXT` | Nullable | Short extract summary |
| `author` | `VARCHAR(255)` | Nullable | Publisher / author attribution |
| `published_at` | `VARCHAR(100)` | Nullable | Original publication date |
| `extraction_status` | `VARCHAR(50)` | Not Null, Index | PENDING, EXTRACTING, COMPLETED, FAILED |
| `error_message` | `TEXT` | Nullable | Diagnostic error info |
| `deleted_at` | `DATETIME` | Nullable, Index | Soft deletion timestamp |
| `created_at` | `DATETIME` | Not Null, Index | Ingestion timestamp |

### `source_analyses`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Analysis UUID |
| `source_id` | `VARCHAR(36)` | FK(`sources.id` CASCADE), Unique, Not Null, Index | Target source |
| `summary` | `TEXT` | Nullable | Structural summary |
| `key_points` | `JSON` | Not Null, Default `[]` | Extracted bullet items |
| `reported_facts` | `JSON` | Not Null, Default `[]` | Verifiable fact items |
| `analysis` | `JSON` | Not Null, Default `[]` | Analytical deductions |
| `founder_implications` | `JSON` | Not Null, Default `{}` | Business takeaways |
| `uncertainties` | `JSON` | Not Null, Default `[]` | Speculative / open claims |
| `newsletter_angles` | `JSON` | Not Null, Default `[]` | Proposed editorial hooks |
| `created_at` | `DATETIME` | Not Null, Index | Analysis timestamp |

### `research_briefs`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Brief UUID |
| `project_id` | `VARCHAR(36)` | FK(`research_projects.id` CASCADE), Not Null, Index | Parent project |
| `title` | `VARCHAR(255)` | Not Null | Synthesis headline |
| `executive_summary` | `TEXT` | Not Null | Cross-source briefing |
| `key_developments` | `JSON` | Not Null | Major events |
| `strategic_implications` | `JSON` | Not Null | Executive takeaways |
| `newsletter_angles` | `JSON` | Not Null | Ranked pitch angles |
| `source_references` | `JSON` | Not Null | Direct citations |
| `created_at` | `DATETIME` | Not Null, Index | Generation timestamp |
| `updated_at` | `DATETIME` | Not Null, Index | Last revision timestamp |

### `research_entities`, `research_claims`, `research_evidence`, `research_relationships`, `research_contradictions`, `research_trends`
| Table | Key Columns | Relationships |
| :--- | :--- | :--- |
| `research_entities` | `name`, `entity_type`, `confidence` | FK(`research_projects.id`), FK(`sources.id`) |
| `research_claims` | `claim_text`, `evidence_classification`, `confidence` | FK(`research_projects.id`), FK(`sources.id`) |
| `research_evidence` | `excerpt`, `fact_type`, `verified`, `confidence` | FK(`research_projects.id`), FK(`sources.id`), FK(`research_claims.id`) |
| `research_relationships` | `source_entity_name`, `target_entity_name`, `relationship_type` | FK(`research_projects.id`), FK(`sources.id`) |
| `research_contradictions` | `claim_a_text`, `claim_b_text`, `disagreement_nature` | FK(`research_projects.id`) |
| `research_trends` | `theme`, `category`, `evidence_summary`, `is_prediction` | FK(`research_projects.id`) |

---

## 3. Writing & Editorial Management

### `writing_drafts`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Draft UUID |
| `project_id` | `VARCHAR(36)` | FK(`research_projects.id` SET NULL), Nullable, Index | Associated project |
| `author_id` | `VARCHAR(36)` | FK(`users.id` SET NULL), Nullable, Index | Authoring user |
| `title` | `VARCHAR(255)` | Not Null | Working article headline |
| `original_content` | `TEXT` | Not Null | Untouched author draft |
| `revised_content` | `TEXT` | Not Null | Current active copy |
| `final_content` | `TEXT` | Nullable | Final accepted copy |
| `word_count` | `INTEGER` | Not Null, Default 0 | Word count |
| `readability_score` | `FLOAT` | Nullable | Flesch Reading Ease score |
| `style_profile_id` | `VARCHAR(36)` | FK(`editorial_style_profiles.id` SET NULL), Nullable | Linked style profile |
| `style_score` | `FLOAT` | Nullable | Style intelligence score (0-100) |
| `status` | `VARCHAR(50)` | Not Null, Index | DRAFT, REVISED, AUDITED, APPROVED |
| `deleted_at` | `DATETIME` | Nullable, Index | Soft deletion timestamp |
| `created_at` | `DATETIME` | Not Null, Index | Creation timestamp |
| `updated_at` | `DATETIME` | Not Null, Index | Modification timestamp |

### `editorial_versions`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | PK, Index | Snapshot UUID |
| `organization_id` | `VARCHAR(36)` | FK(`organizations.id` CASCADE), Nullable, Index | Tenant boundary |
| `document_type` | `VARCHAR(50)` | Not Null, Index | WRITING_DRAFT, RESEARCH_BRIEF, EDITORIAL_OUTPUT |
| `document_id` | `VARCHAR(36)` | Not Null, Index | Document ID |
| `version_number` | `INTEGER` | Not Null | Monotonic version (1, 2, 3...) |
| `title` | `VARCHAR(255)` | Nullable | Title at snapshot time |
| `content_snapshot` | `TEXT` | Not Null | Full verbatim content |
| `change_summary` | `TEXT` | Not Null | Explanation of changes |
| `change_type` | `VARCHAR(50)` | Not Null | INITIAL, MANUAL_EDIT, AI_REVISION, RESTORE |
| `created_by` | `VARCHAR(36)` | FK(`users.id` SET NULL), Nullable, Index | Author of change |
| `created_at` | `DATETIME` | Not Null, Index | Snapshot timestamp |

### `editorial_outputs`, `editorial_reviews`, `editorial_comments`, `writing_suggestions`, `editorial_style_profiles`
* `editorial_outputs`: Final publication newsletter editions with version numbers, source references, and AI review results.
* `editorial_reviews`: Review statuses (`APPROVED`, `CHANGES_REQUESTED`, `HUMAN_REVIEW_PENDING`) and overall feedback.
* `editorial_comments`: Specific line-by-line editor comments and suggested revisions.
* `writing_suggestions`: Quality auditor suggestions (filler words, passive voice, long sentences, jargon, dense paragraphs).
* `editorial_style_profiles`: Publication style specifications (tone, audience, reading level, forbidden words, glossary).

---

## 4. AI, Integrations & Telemetry Management

* `ai_provider_configs`: Provider settings (OpenAI, Gemini, Anthropic, Groq) with encrypted API credentials.
* `integration_connections`: Live integration connections with masked key views and sync statuses.
* `provider_usage_records`: Fine-grained token metrics (prompt, completion, total), latencies, and execution costs.
* `integration_health_records`: Continuous heartbeat ping records for AI provider endpoints.
* `background_jobs`: Async queue state (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`) with payloads and error records.
* `user_activity_logs`: User interaction events for workspace activity feeds.
* `audit_logs`: Immutable security audit events for compliance.
* `notifications`: In-app user notifications with read tracking.
* `usage_events`: High-frequency metric aggregations for rate limits and dashboard charts.
