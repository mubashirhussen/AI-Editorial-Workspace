# Phase 22 — Database Schema Evolution & Alembic Migration Specification

**Target Application:** AI Editorial Workspace  
**Database Engines:** SQLite (Local & Testing) / PostgreSQL (Production)  
**Migration ID:** `9c4d5e6f7a8b`  
**Down Revision:** `8b3c4d5e6f7a`  
**Status:** Applied & Verified  

---

## 1. Overview & Rationale

Phase 22 enhances the intelligence model of the AI Editorial Workspace by introducing structured research project scopes (objective, target audience, topic, keywords) and immutable brief versioning snapshots with support for in-place user edits.

To support these features, the database schema underwent an Alembic migration (`9c4d5e6f7a8b`), adding 6 metadata columns to `research_projects` and 3 edit/versioning columns to `research_briefs`.

---

## 2. Model Evolution (`backend/app/models/base.py`)

### 2.1 `ResearchProject` Schema Additions
```python
class ResearchProject(Base):
    __tablename__ = "research_projects"

    # ... Existing primary keys, title, description, timestamps ...

    # Phase 22 Structured Research Metadata:
    topic = Column(String(500), nullable=True)
    research_objective = Column(Text, nullable=True)
    target_audience = Column(String(255), nullable=True)
    research_scope = Column(String(255), nullable=True)
    keywords = Column(JSON, nullable=True, default=list)
    preferred_source_types = Column(JSON, nullable=True, default=list)
```

### 2.2 `ResearchBrief` Schema Additions
```python
class ResearchBrief(Base):
    __tablename__ = "research_briefs"

    # ... Existing project_id, summary, findings, brief_content ...

    # Phase 22 User Edits & Version Lineage:
    is_user_edited = Column(Boolean, default=False, nullable=False)
    user_notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
```

---

## 3. Alembic Migration Implementation

**Migration File:** `backend/alembic/versions/9c4d5e6f7a8b_phase22_research_project_fields_and_brief_edits.py`

### 3.1 Upgrade Execution (`upgrade()`)
```python
def upgrade():
    # 1. Add fields to research_projects
    op.add_column('research_projects', sa.Column('topic', sa.String(length=500), nullable=True))
    op.add_column('research_projects', sa.Column('research_objective', sa.Text(), nullable=True))
    op.add_column('research_projects', sa.Column('target_audience', sa.String(length=255), nullable=True))
    op.add_column('research_projects', sa.Column('research_scope', sa.String(length=255), nullable=True))
    op.add_column('research_projects', sa.Column('keywords', sa.JSON(), nullable=True))
    op.add_column('research_projects', sa.Column('preferred_source_types', sa.JSON(), nullable=True))

    # 2. Add fields to research_briefs
    op.add_column('research_briefs', sa.Column('is_user_edited', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('research_briefs', sa.Column('user_notes', sa.Text(), nullable=True))
    op.add_column('research_briefs', sa.Column('version', sa.Integer(), server_default='1', nullable=False))
```

### 3.2 Downgrade Execution (`downgrade()`)
```python
def downgrade():
    op.drop_column('research_briefs', 'version')
    op.drop_column('research_briefs', 'user_notes')
    op.drop_column('research_briefs', 'is_user_edited')

    op.drop_column('research_projects', 'preferred_source_types')
    op.drop_column('research_projects', 'keywords')
    op.drop_column('research_projects', 'research_scope')
    op.drop_column('research_projects', 'target_audience')
    op.drop_column('research_projects', 'research_objective')
    op.drop_column('research_projects', 'topic')
```

---

## 4. Multi-Tenant Integrity & Foreign Keys

1. **Foreign Key Enforcement:** SQLite strictly enforces `PRAGMA foreign_keys = ON;`. Deleting a `ResearchProject` triggers cascade deletion of associated `Source`, `ResearchBrief`, and `ArticleDraft` records.
2. **Organization Isolation:** All queries for projects filter by `organization_id`. `check_project_tenant_access` prevents cross-tenant data leakage by returning `403 Forbidden` or `404 Not Found`.

---

## 5. Verification & Migration Status

- Applied locally via `alembic upgrade head`.
- Validated via `backend/tests/test_phase3_database_integrity.py::TestDatabaseIntegrity::test_alembic_head_revision_matches_latest` confirming head revision matches `'9c4d5e6f7a8b'`.
- Validated via `backend/tests/test_phase22_research_assistant.py::test_phase22_project_crud_and_lifecycle`.

