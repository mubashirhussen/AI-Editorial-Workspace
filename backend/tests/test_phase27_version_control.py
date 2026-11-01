import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.core.database import get_db, Base
from backend.app.models.base import (
    WritingDraft,
    EditorialOutput,
    ResearchBrief,
    ResearchProject,
    EditorialVersion,
    User,
    Organization,
    OrganizationMembership
)
from backend.app.services.version_control.version_service import version_service
from backend.app.services.version_control.diff_engine import diff_engine
from backend.app.services.writing_service import writing_service

def test_diff_engine_metrics_and_highlighting():
    """Verify DiffEngine accurately calculates word counts and additions/deletions."""
    text_a = "The AI architecture uses vector search."
    text_b = "The AI architecture utilizes dense vector search with accelerated throughput."

    res = diff_engine.compare_texts(text_a, text_b)
    assert res["word_count_a"] == 6
    assert res["word_count_b"] == 10
    assert res["word_count_diff"] == 4
    assert res["additions_count"] > 0
    assert len(res["word_diff_chunks"]) > 0

    # Ensure added and deleted segments are properly tagged
    types = {chunk["type"] for chunk in res["word_diff_chunks"]}
    assert "equal" in types
    assert "insert" in types or "delete" in types

def test_initial_and_automatic_snapshots(client: TestClient, db_session: Session):
    """Verify initial snapshot creation and automatic snapshot generation on edits and suggestions."""
    # 1. Create a draft via API
    payload = {
        "title": "Reasoning Engine Overview",
        "original_content": "Initial introductory draft content for testing.",
        "project_id": None
    }
    create_res = client.post("/api/v1/writing/drafts", json=payload)
    assert create_res.status_code == 201
    draft_data = create_res.json()
    draft_id = draft_data["id"]

    # Check versions via API
    versions_res = client.get(f"/api/v1/documents/WRITING_DRAFT/{draft_id}/versions")
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert versions[0]["change_type"] == "INITIAL"
    assert "Initial" in versions[0]["content_snapshot"]

    # 2. Duplicate snapshot prevention: updating with same content should not create version 2
    client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "revised_content": "Initial introductory draft content for testing."
    })
    versions_res_dup = client.get(f"/api/v1/documents/WRITING_DRAFT/{draft_id}/versions")
    assert len(versions_res_dup.json()) == 1

    # 3. Meaningful edit creates version 2
    client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "revised_content": "Second revision with refined terminology."
    })
    versions_res_v2 = client.get(f"/api/v1/documents/WRITING_DRAFT/{draft_id}/versions")
    v2_list = versions_res_v2.json()
    assert len(v2_list) == 2
    assert v2_list[0]["version_number"] == 2
    assert v2_list[0]["change_type"] == "MANUAL_EDIT"
    assert "Second revision" in v2_list[0]["content_snapshot"]

def test_version_comparison_endpoint(client: TestClient, db_session: Session):
    """Verify comparison between two versions returns diff chunks and word count deltas."""
    draft = WritingDraft(
        title="Comparison Test Draft",
        original_content="Base content version one.",
        revised_content="Base content version one."
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)

    # Version 1
    version_service.create_snapshot(
        db=db_session,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        content="Base content version one.",
        title=draft.title,
        change_type="INITIAL",
        force=True
    )
    # Version 2
    version_service.create_snapshot(
        db=db_session,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        content="Base content version two with extended explanation and analysis.",
        title=draft.title,
        change_type="MANUAL_EDIT",
        force=True
    )

    compare_res = client.get(
        f"/api/v1/documents/WRITING_DRAFT/{draft.id}/compare?from_version=1&to_version=2"
    )
    assert compare_res.status_code == 200
    comp = compare_res.json()
    assert comp["document_type"] == "WRITING_DRAFT"
    assert comp["word_count_a"] == 4
    assert comp["word_count_b"] == 9
    assert comp["word_count_diff"] == 5
    assert comp["additions_count"] > 0
    assert len(comp["word_diff_chunks"]) > 0

def test_restore_version_behavior_and_original_preservation(client: TestClient, db_session: Session):
    """
    Verify restoring a previous version:
    1. Does not delete later versions.
    2. Creates a NEW version (version 3) marked as RESTORE.
    3. Updates revised_content.
    4. Leaves original_content untouched.
    """
    orig_text = "Original permanent content that must never be altered."
    v2_text = "Second version rewritten entirely with new claims."

    draft = WritingDraft(
        title="Restore Test Draft",
        original_content=orig_text,
        revised_content=orig_text
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)

    v1 = version_service.create_snapshot(
        db=db_session,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        content=orig_text,
        title=draft.title,
        change_type="INITIAL",
        force=True
    )

    v2 = version_service.create_snapshot(
        db=db_session,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        content=v2_text,
        title=draft.title,
        change_type="MANUAL_EDIT",
        force=True
    )
    draft.revised_content = v2_text
    db_session.commit()

    # Restore Version 1
    restore_res = client.post(
        f"/api/v1/documents/WRITING_DRAFT/{draft.id}/restore/{v1.id}",
        json={"confirm": True, "note": "Reverting back to first draft"}
    )
    assert restore_res.status_code == 200
    res_data = restore_res.json()
    assert res_data["success"] is True
    assert res_data["restored_from_version"] == 1
    assert res_data["new_version"]["version_number"] == 3
    assert res_data["new_version"]["change_type"] == "RESTORE"

    # Verify history integrity: all 3 versions must exist
    versions_res = client.get(f"/api/v1/documents/WRITING_DRAFT/{draft.id}/versions")
    assert versions_res.status_code == 200
    vers = versions_res.json()
    assert len(vers) == 3
    assert [v["version_number"] for v in vers] == [3, 2, 1]

    # Verify draft state in database:
    db_session.refresh(draft)
    assert draft.revised_content == orig_text  # restored
    assert draft.original_content == orig_text  # immutable original preserved

def test_cross_document_and_cross_tenant_isolation(client: TestClient, db_session: Session):
    """Verify that restoring or viewing a version belonging to another document or tenant is rejected."""
    draft_a = WritingDraft(title="Draft A", original_content="Content A", revised_content="Content A")
    draft_b = WritingDraft(title="Draft B", original_content="Content B", revised_content="Content B")
    db_session.add_all([draft_a, draft_b])
    db_session.commit()

    v_a = version_service.create_snapshot(
        db=db_session,
        document_type="WRITING_DRAFT",
        document_id=draft_a.id,
        content="Content A",
        title=draft_a.title,
        change_type="INITIAL",
        force=True
    )

    # Attempt to restore draft_a's version into draft_b -> must be rejected (400/404)
    invalid_restore = client.post(
        f"/api/v1/documents/WRITING_DRAFT/{draft_b.id}/restore/{v_a.id}",
        json={"confirm": True}
    )
    assert invalid_restore.status_code in [400, 404]

    # Unsupported document type check
    bad_type = client.get(f"/api/v1/documents/INVALID_TYPE/{draft_a.id}/versions")
    assert bad_type.status_code == 400

def test_editorial_output_version_lifecycle(client: TestClient, db_session: Session):
    """Verify version control for EditorialOutput documents."""
    project = ResearchProject(
        title="Hardware Constraints Project",
        description="Analysis of AI compute boundaries."
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    output = EditorialOutput(
        project_id=project.id,
        headline="AI Chip Scaling Constraints",
        content="Initial editorial newsletter publication content [1].",
        word_count=7
    )
    db_session.add(output)
    db_session.commit()
    db_session.refresh(output)

    # Create initial version
    version_service.create_snapshot(
        db=db_session,
        document_type="EDITORIAL_OUTPUT",
        document_id=output.id,
        content=output.content,
        title=output.headline,
        change_type="INITIAL",
        force=True
    )

    # Update editorial content
    client.put(f"/api/v1/editorial/{output.id}", json={
        "content": "Updated editorial newsletter with expanded market analysis [1], [2]."
    })

    versions_res = client.get(f"/api/v1/documents/EDITORIAL_OUTPUT/{output.id}/versions")
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[0]["change_type"] == "MANUAL_EDIT"
