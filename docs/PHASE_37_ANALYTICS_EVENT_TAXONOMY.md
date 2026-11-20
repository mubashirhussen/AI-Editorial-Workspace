# Phase 37: Product Analytics Event Taxonomy & Schema Specification

**Project:** AI Editorial Workspace — This Week in AI  
**Version:** 1.0.0  
**Security Level:** First-Party Privacy-Conscious Architecture  
**Author:** Forward Deployed Engineer & Senior Product Analytics Architect  

---

## 1. Overview & Event Philosophy

The **AI Editorial Workspace** product analytics architecture implements a strict **first-party, privacy-preserving event taxonomy**. Unlike generic client trackers that flood event logs with unstructured DOM events and PII, our system enforces:

1. **Authoritative Server-Side Milestones:** High-value product metrics (e.g., project creation, source processing, brief synthesis, draft generation, editorial approval) are recorded directly on the backend during legitimate business operations.
2. **Deterministic Data Minimization:** Events never capture raw research bodies, prompts, drafts, tokens, emails, or credentials.
3. **Cryptographic Pseudonymization:** User IDs are converted via salted HMAC-SHA256 into pseudonyms (`usr_<hex>`), decoupling behavioral telemetry from personal identity.
4. **Idempotency & Deduplication:** Events carry composite deduplication keys preventing duplicate counting from double-clicks or network retries.

---

## 2. Standard Event Payload Schema

```json
{
  "event_id": "c7a8b9d0-1e2f-4a3b-9c8d-7e6f5a4b3c2d",
  "event_name": "research_brief_generation_completed",
  "event_version": 1,
  "occurred_at": "2026-11-20T14:30:00.000Z",
  "user_reference": "usr_9f8e7d6c5b4a3a2b1c0d9e8f",
  "organization_reference": "org_alpha_production",
  "project_reference": "proj_deepseek_investigation",
  "workflow_reference": "wf_journey_8819",
  "session_reference": "sess_client_4492",
  "source": "backend",
  "status": "completed",
  "duration_ms": 1420,
  "properties": {
    "sources_count": 4,
    "format": "markdown",
    "status": "success",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet"
  }
}
```

---

## 3. Comprehensive Event Taxonomy

### 3.1 Authentication & Session Lifecycle
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `signup_completed` | Backend | User account creation completed | `format`, `status` |
| `login_completed` | Backend | User authentication token generated | `format`, `status` |
| `session_started` | Frontend | User opens workspace application session | `view_mode`, `format` |

### 3.2 Project Management Lifecycle
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `project_created` | Backend | New investigation project created | `status`, `workflow_type` |
| `project_opened` | Frontend | Project workspace opened by user | `view_mode` |
| `project_updated` | Backend | Project metadata or topic edited | `status` |
| `project_archived` | Backend | Project moved to archived state | `status` |
| `project_deleted` | Backend | Project deleted | `status` |

### 3.3 Research Assistant Journey
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `research_workspace_opened` | Frontend | User enters Research Assistant module | `view_mode` |
| `research_source_added` | Backend | Source URL or text added to project | `source_type`, `status` |
| `research_source_processing_started` | Backend | Content extraction and SSRF validation initiated | `source_type`, `step` |
| `research_source_processing_completed` | Backend | Source text extracted and analyzed | `source_type`, `duration_ms`, `status` |
| `research_source_processing_failed` | Backend | Extraction failed or blocked by SSRF filter | `error_code`, `status` |
| `research_brief_generation_started` | Backend | AI synthesis of structured brief initiated | `sources_count`, `model`, `provider` |
| `research_brief_generation_completed` | Backend | Research brief successfully synthesized | `sources_count`, `duration_ms`, `status` |
| `research_brief_generation_failed` | Backend | Synthesis aborted or failed | `error_code`, `retries` |
| `research_brief_updated` | Backend | Editor customized or modified brief | `action`, `status` |
| `research_brief_exported` | Backend | Research brief exported | `format`, `status` |

### 3.4 Writing Assistant Journey
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `writing_workspace_opened` | Frontend | User enters Writing Assistant module | `view_mode` |
| `writing_draft_created` | Backend | New drafting canvas initialized | `workflow_type`, `status` |
| `writing_assistance_requested` | Backend | Deterministic or AI improvement triggered | `step`, `target_tone` |
| `writing_assistance_completed` | Backend | Linguistic check or rewrite finished | `duration_ms`, `word_count`, `flesch_score` |
| `writing_assistance_failed` | Backend | Improvement request failed | `error_code`, `status` |
| `writing_suggestion_accepted` | Backend | User accepted rewrite suggestion | `category`, `action` |
| `writing_suggestion_rejected` | Backend | User declined rewrite suggestion | `category`, `action` |
| `writing_draft_saved` | Backend | Draft content saved to database | `word_count`, `flesch_score`, `reading_ease` |
| `writing_draft_exported` | Backend | Draft exported to file | `format`, `status` |

### 3.5 Editorial Studio Journey
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `editorial_workspace_opened` | Frontend | User enters Editorial Studio | `view_mode` |
| `editorial_generation_started` | Backend | Bundling brief & sources into newsletter | `sources_count`, `edition_number` |
| `editorial_generation_completed` | Backend | Publication draft generated | `duration_ms`, `citations_count`, `status` |
| `editorial_generation_failed` | Backend | Generation failed | `error_code`, `status` |
| `editorial_review_started` | Backend | Draft submitted for peer review | `status` |
| `editorial_review_completed` | Backend | Review feedback submitted | `status`, `action` |
| `editorial_status_changed` | Backend | Editorial status transitioned | `status`, `action` |
| `editorial_approved` | Backend | Formal publication approval granted | `status`, `citations_count` |
| `editorial_finalized` | Backend | Edition locked and sealed for syndication | `status`, `edition_number` |
| `editorial_exported` | Backend | Newsletter published or exported | `format`, `status` |

### 3.6 Product Experience & Feedback
| Event Name | Source | Description | Allowed Properties |
| :--- | :--- | :--- | :--- |
| `feature_discovered` | Frontend | User navigates to a new capability | `feature_id` |
| `feature_used` | Both | General feature invocation | `feature_id`, `action` |
| `feedback_submitted` | Backend | User submitted bug or feature report | `category`, `severity`, `feature_id` |
| `workflow_completed` | Backend | Full multi-step journey concluded | `workflow_type`, `duration_ms` |
| `workflow_failed` | Backend | Workflow terminated by unrecoverable error | `workflow_type`, `error_code` |
| `workflow_abandoned` | Client/Inferred| Workflow left unfinished after timeout | `workflow_type`, `step` |

---

## 4. Property Allowlist & Forbidden Key Enforcement

- **Strict Allowlist:** `status`, `category`, `format`, `duration_ms`, `word_count`, `error_code`, `step`, `model`, `provider`, `count`, `score`, `target_tone`, `citations_count`, `sources_count`, `source_type`, `action`, `feature_id`, `edition_number`, `tokens_used`, `flesch_score`, `reading_ease`, `sentence_count`, `retries`, `workflow_type`, `view_mode`.
- **Absolute Forbidden Pattern Rejection:** Any property key or value containing `prompt`, `content`, `text`, `body`, `password`, `token`, `secret`, `key`, `email`, `authorization`, `cookie`, `credential`, `bearer`, `private`, `ssn`, `url`, `document`, `raw`, `phone`, or `address` is automatically stripped by `AnalyticsService.sanitize_properties()`.
