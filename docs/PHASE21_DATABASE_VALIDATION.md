# Phase 21 — Database Architecture & Integrity Validation

**Database Engine:** PostgreSQL 16 / SQLite (Local Test Harness)  
**ORM Framework:** SQLAlchemy 2.0  
**Schema Scope:** `ResearchProject`, `EditorialArticle`, `EditorialReviewRecord`, `EditorialCommentRecord`, `Organization`, `OrganizationMember`, `User`  
**Integrity Checks:** Foreign Keys, Multi-Tenant Scoping, Cascading Deletion, Immutability Constraints  

---

## 1. Relational Schema & Entity Relationships

```mermaid
erDiagram
    ORGANIZATION ||--o{ RESEARCH_PROJECT : owns
    ORGANIZATION ||--o{ ORGANIZATION_MEMBER : has
    USER ||--o{ ORGANIZATION_MEMBER : joins
    RESEARCH_PROJECT ||--o{ EDITORIAL_ARTICLE : generates
    EDITORIAL_ARTICLE ||--o{ EDITORIAL_REVIEW : receives
    EDITORIAL_ARTICLE ||--o{ EDITORIAL_COMMENT : has

    ORGANIZATION {
        string id PK
        string name
        string slug UK
        datetime created_at
    }

    ORGANIZATION_MEMBER {
        string id PK
        string organization_id FK
        string user_id FK
        string role "OWNER, ADMIN, EDITOR, VIEWER"
    }

    RESEARCH_PROJECT {
        string id PK
        string title
        string organization_id FK
        json sources
        datetime created_at
    }

    EDITORIAL_ARTICLE {
        string id PK
        string project_id FK
        string headline
        text content
        integer word_count
        string status "DRAFT_CREATED, IN_REVIEW, CHANGES_REQUESTED, APPROVED, FINALIZED"
        json source_references
        datetime created_at
        datetime updated_at
    }

    EDITORIAL_REVIEW {
        string id PK
        string editorial_id FK
        string reviewer_name
        string status "APPROVED, CHANGES_REQUESTED, COMMENT"
        text notes
        integer score
        datetime created_at
    }

    EDITORIAL_COMMENT {
        string id PK
        string editorial_id FK
        string author_name
        text comment
        datetime created_at
    }
```

---

## 2. Integrity Rules & Constraint Verification

### 2.1 Multi-Tenant Isolation via Foreign Keys
- `ResearchProject.organization_id` links directly to `Organization.id`.
- Every editorial query filters via `ResearchProject.organization_id.in_(user_org_ids)`.
- When an organization is queried, projects outside the tenant are never joined or returned.

### 2.2 Referential Integrity & Cascade Deletion
- Deleting an `EditorialArticle` cascades to delete related `EditorialReviewRecord` and `EditorialCommentRecord` entities, preventing orphaned reviews in the database.
- Deleting a `ResearchProject` cascades to clean up associated briefs and editorial drafts.

### 2.3 Status Lifecycle & Immutability Rules
The `EditorialArticle.status` column manages state transitions:
1. `DRAFT_CREATED`: Initial synthesis state, mutable by author and editors.
2. `IN_REVIEW`: Submitted for peer or AI review, mutable with version tracking.
3. `CHANGES_REQUESTED`: Review completed with feedback, editable by author.
4. `APPROVED`: Validated by peer reviewer, awaiting final release authorization.
5. `FINALIZED`: Publication release locked. **No further updates or deletions are permitted.** Attempted modifications fail at the ORM service layer with HTTP `409 Conflict`.

---

## 3. Database Validation Test Execution

Database integrity was verified via automated integration tests in `backend/tests/test_phase21_editorial_hardening.py`:

1. **Cross-Tenant Isolation:**
   - User A (Org A) created an editorial in Project A.
   - User B (Org B) attempted to read `GET /editorial/{id}` and write `PUT /editorial/{id}`.
   - Database layer prevented unauthorized access, returning HTTP `403 Forbidden` / `404 Not Found`.

2. **Finalized Immutability Guard:**
   - Editorial was transitioned to `FINALIZED`.
   - Update request was dispatched to `PUT /editorial/{id}` with new content.
   - Service raised `409 Conflict`, and database content remained intact.
   - Delete request was dispatched to `DELETE /editorial/{id}`.
   - Service raised `409 Conflict`, and database row remained persisted.

3. **Dashboard Aggregate Integrity:**
   - Tested `get_dashboard_stats` across multiple organizations.
   - Metrics (e.g., `total_editorials`, `pending_human_reviews`) strictly tallied items matching the authenticated user's organization memberships.

All database operations demonstrated zero data leakage, correct foreign key cascade behavior, and strict enforcement of state immutability.

