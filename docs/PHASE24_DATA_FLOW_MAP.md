# Phase 24 — Entity Relationship, Data Flow & Transaction Boundaries

## Overview

This document formalizes the entity relationships, foreign key constraints, cascading deletion rules, and transaction boundaries across all database models in the **AI Editorial Workspace**.

---

## 1. Entity Relationship Model

```
 ┌───────────────┐
 │ Organization  │
 └───────┬───────┘
         │ 1:N (CASCADE)
         ├─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
 ┌───────────────────────┐                 ┌───────────────┐
 │OrganizationMembership│                 │ResearchProject│
 └───────────────────────┘                 └───────┬───────┘
                                                   │ 1:N (CASCADE)
                         ┌─────────────────────────┼─────────────────────────┐
                         ▼                         ▼                         ▼
                  ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
                  │    Source    │          │ResearchBrief │          │WritingDraft  │
                  └──────┬───────┘          └──────┬───────┘          └──────┬───────┘
                         │ 1:1                     │                         │ 1:1
                         ▼                         │                         ▼
                  ┌──────────────┐                 │                  ┌──────────────┐
                  │SourceAnalysis│                 │                  │EditorialOut  │
                  └──────────────┘                 │                  └──────┬───────┘
                                                   │                         │ 1:N
                                                   │                         ▼
                                                   │                  ┌──────────────┐
                                                   │                  │EditorialRev  │
                                                   │                  └──────┬───────┘
                                                   │                         │ 1:N
                                                   ▼                         ▼
                                            ┌──────────────┐          ┌──────────────┐
                                            │EditorialVers │          │EditorialComm │
                                            └──────────────┘          └──────────────┘
```

---

## 2. Foreign Key & Integrity Specifications

| Parent Model | Child Model | Foreign Key Column | On Delete Action | Tenant Isolation Key |
| :--- | :--- | :--- | :--- | :--- |
| `Organization` | `OrganizationMembership` | `organization_id` | `CASCADE` | Direct |
| `Organization` | `ResearchProject` | `organization_id` | `CASCADE` | Direct |
| `Organization` | `WritingDraft` | `organization_id` | `CASCADE` | Direct |
| `Organization` | `EditorialStyleProfile` | `organization_id` | `CASCADE` | Direct |
| `ResearchProject` | `Source` | `project_id` | `CASCADE` | Inherited via Project |
| `ResearchProject` | `ResearchBrief` | `project_id` | `CASCADE` | Inherited via Project |
| `ResearchProject` | `EditorialOutput` | `project_id` | `CASCADE` | Inherited via Project |
| `WritingDraft` | `WritingSuggestion` | `draft_id` | `CASCADE` | Inherited via Draft |
| `EditorialOutput` | `EditorialReview` | `editorial_id` | `CASCADE` | Inherited via Editorial |
| `EditorialReview` | `EditorialComment` | `review_id` | `CASCADE` | Inherited via Review |

---

## 3. Transaction Boundaries & Atomicity

### 3.1 Brief Generation Pipeline
- **Boundary:** Single database session transaction (`db.commit()` on completion).
- **Operations:**
  1. Validates that project has $\ge 3$ sources.
  2. Runs heuristic or AI extraction analysis for any pending sources.
  3. Inserts `ResearchBrief` record.
  4. Inserts relational `ResearchEvidence` entries mapped to verified sources.
  5. Records version snapshot in `EditorialVersion` (`document_type="RESEARCH_BRIEF"`).
  6. Tracks analytics event `brief_generated`.
- **Failure Guarantee:** Any error during synthesis rolls back the brief transaction, avoiding orphaned evidence items.

### 3.2 Editorial Approval & Finalization Lock
- **Boundary:** Guarded single transaction.
- **Operations:**
  1. Verifies caller holds `APPROVE_EDITORIALS` permission.
  2. Enforces peer review constraint (rejects author self-approval).
  3. Transitions status from `HUMAN_REVIEW_PENDING` $\to$ `APPROVED` $\to$ `FINALIZED`.
  4. Creates version snapshot in `EditorialVersion` documenting transition notes and reviewer identity.
  5. Subsequent write operations are rejected with HTTP 400 (`Cannot revise finalized editorial`).
