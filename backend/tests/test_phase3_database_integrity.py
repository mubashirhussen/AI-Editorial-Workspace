import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from backend.app.core.database import SessionLocal, engine
from backend.app.models.base import (
    Base,
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    Source,
    ResearchBrief,
    WritingDraft,
    EditorialOutput,
    AuditLog,
)


@pytest.fixture
def db_session():
    """Provides a transactional database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestDatabaseIntegrity:
    """Phase 3 Automated Database Integrity and Migrations Test Suite."""

    def test_sqlite_foreign_key_pragmas_enabled(self, db_session):
        """Verify that SQLite foreign key enforcement is strictly active."""
        if engine.dialect.name == "sqlite":
            result = db_session.execute(text("PRAGMA foreign_keys")).scalar()
            assert result == 1, "PRAGMA foreign_keys must be enabled (1) for SQLite."

    def test_alembic_head_revision_matches_latest(self, db_session):
        """Verify that the database schema is at Alembic migration head."""
        result = db_session.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert result == "5e9a2f1b4c3d", f"Database must be at head revision '5e9a2f1b4c3d', found '{result}'"

    def test_unique_constraint_user_email(self, db_session):
        """Verify that unique constraints on user emails prevent duplicate entries."""
        unique_email = f"test_db_user_{uuid.uuid4().hex[:8]}@example.com"
        user1 = User(
            id=str(uuid.uuid4()),
            email=unique_email,
            hashed_password="hashedpassword123",
            full_name="User One",
            is_active=True,
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            id=str(uuid.uuid4()),
            email=unique_email,
            hashed_password="hashedpassword456",
            full_name="User Two",
            is_active=True,
        )
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

        # Clean up user1
        db_session.delete(user1)
        db_session.commit()

    def test_unique_constraint_organization_membership(self, db_session):
        """Verify that a user cannot have duplicate active memberships in the same organization."""
        user = User(
            id=str(uuid.uuid4()),
            email=f"mem_test_{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="hashed_test_pass",
            full_name="Membership Test User",
            is_active=True
        )
        org = Organization(
            id=str(uuid.uuid4()),
            name=f"Org {uuid.uuid4().hex[:6]}",
            slug=f"org-{uuid.uuid4().hex[:6]}"
        )
        db_session.add_all([user, org])
        db_session.commit()

        mem1 = OrganizationMembership(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            user_id=user.id,
            role="MEMBER"
        )
        db_session.add(mem1)
        db_session.commit()

        mem2 = OrganizationMembership(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            user_id=user.id,
            role="ADMIN"
        )
        db_session.add(mem2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

        # Clean up
        db_session.delete(mem1)
        db_session.delete(org)
        db_session.delete(user)
        db_session.commit()

    def test_cascade_deletion_project_to_children(self, db_session):
        """Verify that deleting a ResearchProject cascades to sources and briefs without orphans."""
        org = Organization(
            id=str(uuid.uuid4()),
            name=f"Cascade Org {uuid.uuid4().hex[:6]}",
            slug=f"cascade-org-{uuid.uuid4().hex[:6]}"
        )
        db_session.add(org)
        db_session.commit()

        project = ResearchProject(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            title="Cascade Test Project",
            name="Cascade Test Project",
            status="draft"
        )
        db_session.add(project)
        db_session.commit()

        source = Source(
            id=str(uuid.uuid4()),
            project_id=project.id,
            title="Cascade Child Source",
            source_type="URL",
            url=f"https://example.com/test-{uuid.uuid4().hex[:6]}",
            extraction_status="completed"
        )
        brief = ResearchBrief(
            id=str(uuid.uuid4()),
            project_id=project.id,
            executive_summary="Cascade Child Brief Summary"
        )
        db_session.add_all([source, brief])
        db_session.commit()

        source_id = source.id
        brief_id = brief.id
        project_id = project.id

        # Delete the project
        db_session.delete(project)
        db_session.commit()

        # Verify children are deleted (cascade)
        orphaned_source = db_session.query(Source).filter(Source.id == source_id).first()
        orphaned_brief = db_session.query(ResearchBrief).filter(ResearchBrief.id == brief_id).first()
        assert orphaned_source is None, "Child source must be cascade deleted with project"
        assert orphaned_brief is None, "Child brief must be cascade deleted with project"

        # Clean up org
        db_session.delete(org)
        db_session.commit()

    def test_transaction_rollback_integrity(self, db_session):
        """Verify that failed multi-step operations roll back completely."""
        test_email = f"rollback_{uuid.uuid4().hex[:8]}@example.com"
        
        try:
            user = User(
                id=str(uuid.uuid4()),
                email=test_email,
                hashed_password="pw",
                full_name="Rollback Test",
                is_active=True
            )
            db_session.add(user)
            db_session.flush()

            # Trigger deliberate integrity failure: duplicate ID
            duplicate_user = User(
                id=user.id,
                email=f"other_{uuid.uuid4().hex[:8]}@example.com",
                hashed_password="pw",
                full_name="Duplicate ID",
                is_active=True
            )
            db_session.add(duplicate_user)
            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # Verify the first user was NOT committed due to rollback
        persisted = db_session.query(User).filter(User.email == test_email).first()
        assert persisted is None, "Transaction rollback must ensure zero partial writes."

    def test_organization_data_isolation(self, db_session):
        """Verify organization-level query isolation."""
        org_a = Organization(
            id=str(uuid.uuid4()),
            name="Org Alpha",
            slug=f"org-alpha-{uuid.uuid4().hex[:6]}"
        )
        org_b = Organization(
            id=str(uuid.uuid4()),
            name="Org Beta",
            slug=f"org-beta-{uuid.uuid4().hex[:6]}"
        )
        db_session.add_all([org_a, org_b])
        db_session.commit()

        proj_a = ResearchProject(
            id=str(uuid.uuid4()),
            organization_id=org_a.id,
            title="Alpha Project",
            name="Alpha Project"
        )
        proj_b = ResearchProject(
            id=str(uuid.uuid4()),
            organization_id=org_b.id,
            title="Beta Project",
            name="Beta Project"
        )
        db_session.add_all([proj_a, proj_b])
        db_session.commit()

        # Query projects for Org A only
        a_projects = db_session.query(ResearchProject).filter(ResearchProject.organization_id == org_a.id).all()
        assert len(a_projects) == 1
        assert a_projects[0].id == proj_a.id
        assert a_projects[0].title == "Alpha Project"

        # Clean up
        db_session.delete(proj_a)
        db_session.delete(proj_b)
        db_session.delete(org_a)
        db_session.delete(org_b)
        db_session.commit()

    def test_composite_indexes_exist(self, db_session):
        """Verify critical performance composite indexes exist in SQLite schema."""
        result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='index'")).fetchall()
        index_names = {row[0] for row in result}

        critical_indexes = [
            "ix_sources_project_created",
            "ix_briefs_project_created",
            "ix_drafts_project_created",
            "ix_editorial_project_created",
            "ix_suggestions_draft_status",
            "ix_audit_logs_user_id",
            "ix_editorial_versions_organization_id",
            "ix_notifications_organization_id",
            "ix_organization_invitations_organization_id",
            "ix_research_claims_source_id",
            "ix_research_evidence_claim_id",
            "ix_users_email",
        ]
        for idx in critical_indexes:
            assert idx in index_names, f"Critical index '{idx}' must exist in active database."
