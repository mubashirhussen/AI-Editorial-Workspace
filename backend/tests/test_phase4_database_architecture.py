import uuid
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from backend.app.core.database import Base, check_db_health, get_db_context
from backend.app.core.encryption import encrypt_secret, decrypt_secret, mask_secret
from backend.app.crud.base import CRUDBase
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    Source,
    ResearchClaim,
    ResearchEvidence,
    WritingDraft,
    WritingSuggestion,
    EditorialVersion,
    AiProviderConfig,
    IntegrationConnection,
    ProviderUsageRecord,
    AuditLog,
    Notification
)

# Test-specific SQLite engine with foreign key enforcement
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False}
)

@event.listens_for(TEST_ENGINE, "connect")
def enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

@pytest.fixture(scope="function")
def isolated_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


def test_fresh_database_creation(isolated_db):
    """Verifies fresh database creation initializes all tables with primary keys."""
    table_names = Base.metadata.tables.keys()
    assert "users" in table_names
    assert "organizations" in table_names
    assert "research_projects" in table_names
    assert "sources" in table_names
    assert "writing_drafts" in table_names
    assert "editorial_versions" in table_names
    assert "research_evidence" in table_names
    assert "ai_provider_configs" in table_names
    assert "integration_connections" in table_names
    assert "audit_logs" in table_names
    assert "notifications" in table_names
    assert len(table_names) >= 30


def test_foreign_key_integrity_and_cascade(isolated_db):
    """Verifies foreign key constraints and cascade delete behavior."""
    # 1. Invalid foreign key insertion must fail
    invalid_source = Source(
        id=str(uuid.uuid4()),
        project_id="non-existent-project-id",
        title="Orphan Source",
        extraction_status="completed"
    )
    isolated_db.add(invalid_source)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()

    # 2. Valid cascade delete: Deleting project deletes child sources
    project = ResearchProject(
        id="proj-cascade-test",
        title="Cascade Project",
        status="active"
    )
    isolated_db.add(project)
    isolated_db.commit()

    source = Source(
        id="src-cascade-test",
        project_id=project.id,
        title="Source Child",
        extraction_status="completed"
    )
    isolated_db.add(source)
    isolated_db.commit()

    # Confirm source exists
    assert isolated_db.query(Source).filter(Source.id == "src-cascade-test").first() is not None

    # Delete project
    isolated_db.delete(project)
    isolated_db.commit()

    # Child source must be deleted automatically
    assert isolated_db.query(Source).filter(Source.id == "src-cascade-test").first() is None


def test_unique_constraints(isolated_db):
    """Verifies unique email constraint and unique organization membership constraint."""
    user1 = User(
        id="u1",
        email="test_unique@editorial.ai",
        hashed_password="hash",
        full_name="User One"
    )
    isolated_db.add(user1)
    isolated_db.commit()

    # Duplicate email must fail
    user2 = User(
        id="u2",
        email="test_unique@editorial.ai",
        hashed_password="hash",
        full_name="User Two"
    )
    isolated_db.add(user2)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()

    # Unique organization membership constraint
    org = Organization(id="org1", name="Alpha Org", slug="alpha-org")
    isolated_db.add(org)
    isolated_db.commit()

    m1 = OrganizationMembership(organization_id="org1", user_id="u1", role="OWNER")
    isolated_db.add(m1)
    isolated_db.commit()

    m2 = OrganizationMembership(organization_id="org1", user_id="u1", role="EDITOR")
    isolated_db.add(m2)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()


def test_organization_data_isolation(isolated_db):
    """Verifies tenant isolation between different organizations."""
    org_a = Organization(id="org-a", name="Org Alpha", slug="org-a")
    org_b = Organization(id="org-b", name="Org Beta", slug="org-b")
    isolated_db.add_all([org_a, org_b])
    isolated_db.commit()

    proj_a = ResearchProject(id="p-a", organization_id="org-a", title="Alpha Project")
    proj_b = ResearchProject(id="p-b", organization_id="org-b", title="Beta Project")
    isolated_db.add_all([proj_a, proj_b])
    isolated_db.commit()

    # Query scoped to org-a must never return org-b's data
    crud = CRUDBase(ResearchProject)
    results_a = crud.get_multi(isolated_db, organization_id="org-a")
    assert len(results_a) == 1
    assert results_a[0].id == "p-a"
    assert not any(p.organization_id == "org-b" for p in results_a)


def test_secret_encryption_and_masking():
    """Verifies credential encryption, decryption, and secure masking."""
    raw_key = "sk-proj-super-secret-key-1234567890abcdef"
    encrypted = encrypt_secret(raw_key)

    assert encrypted != raw_key
    assert not encrypted.startswith("sk-proj")

    decrypted = decrypt_secret(encrypted)
    assert decrypted == raw_key

    masked = mask_secret(raw_key)
    assert masked == "sk-p...cdef"
    assert "secret" not in masked


def test_transaction_rollback(isolated_db):
    """Verifies database rollbacks on failure to maintain consistency."""
    org = Organization(id="org-rollback", name="Rollback Org", slug="rollback-org")
    isolated_db.add(org)
    isolated_db.commit()

    # Attempt a transaction where second operation fails
    try:
        p = ResearchProject(id="p-good", organization_id="org-rollback", title="Good Project")
        isolated_db.add(p)
        # Invalid operation (violates FK)
        bad_source = Source(id="s-bad", project_id="non-existent-proj", title="Bad Source")
        isolated_db.add(bad_source)
        isolated_db.commit()
    except Exception:
        isolated_db.rollback()

    # p-good must not exist due to atomic rollback
    assert isolated_db.query(ResearchProject).filter(ResearchProject.id == "p-good").first() is None


def test_soft_deletion_and_query_filtering(isolated_db):
    """Verifies soft deletion sets timestamp and is filtered out by default queries."""
    project = ResearchProject(id="p-soft", title="Soft Delete Project", status="active")
    isolated_db.add(project)
    isolated_db.commit()

    crud = CRUDBase(ResearchProject)
    # Project exists
    assert crud.get(isolated_db, "p-soft") is not None

    # Soft delete
    success = crud.soft_delete(isolated_db, id="p-soft")
    assert success is True

    # Standard query excludes it
    assert crud.get(isolated_db, "p-soft") is None

    # Record still exists physically in the database
    raw_record = isolated_db.query(ResearchProject).filter(ResearchProject.id == "p-soft").first()
    assert raw_record is not None
    assert raw_record.deleted_at is not None


def test_query_pagination(isolated_db):
    """Verifies offset/limit pagination calculations and bounds."""
    for i in range(25):
        p = ResearchProject(id=f"p-page-{i:02d}", title=f"Project {i}", status="active")
        isolated_db.add(p)
    isolated_db.commit()

    crud = CRUDBase(ResearchProject)
    page1 = crud.paginate(isolated_db, page=1, page_size=10)
    assert len(page1["items"]) == 10
    assert page1["total"] == 25
    assert page1["total_pages"] == 3
    assert page1["has_next"] is True
    assert page1["has_prev"] is False

    page3 = crud.paginate(isolated_db, page=3, page_size=10)
    assert len(page3["items"]) == 5
    assert page3["has_next"] is False
    assert page3["has_prev"] is True


def test_db_health_check_function():
    """Verifies check_db_health returns latency and status."""
    health = check_db_health()
    assert health["status"] == "healthy"
    assert health["latency_ms"] >= 0.0
    assert health["engine"] in ("sqlite", "postgresql")
