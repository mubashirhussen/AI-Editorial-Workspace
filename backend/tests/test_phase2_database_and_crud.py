import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models.base import ResearchProject, Source, WritingDraft
from backend.app.schemas.research import ProjectCreate, ProjectUpdate
from backend.app.schemas.source import SourceCreate
from backend.app.schemas.writing import WritingDraftCreate, WritingDraftUpdate
from backend.app.services.project_service import project_service
from backend.app.services.source_service import source_service
from backend.app.services.writing_service import writing_service
from fastapi import HTTPException

def test_database_connection_and_crud(db_session):
    # 1. Project creation
    proj_in = ProjectCreate(title="Phase 2 Architectural Test", description="Testing CRUD and FK integrity")
    project = project_service.create_project(db_session, proj_in)
    assert project.id is not None
    assert project.title == "Phase 2 Architectural Test"
    assert project.status == "draft"

    # 2. Project retrieval
    fetched_proj = project_service.get_project(db_session, project.id)
    assert fetched_proj.id == project.id

    # 3. Project update
    updated_proj = project_service.update_project(db_session, project.id, ProjectUpdate(title="Updated Title"))
    assert updated_proj.title == "Updated Title"

    # 4. Source creation & Foreign-key relationships
    source_in = SourceCreate(
        title="Verified AI Research Paper",
        source_type="text",
        text_content="Direct benchmark evaluation showing 99.8% precision across evaluated tasks."
    )
    # Synchronously run source addition
    import asyncio
    source = asyncio.run(source_service.add_source(db_session, project.id, source_in))
    assert source.id is not None
    assert source.project_id == project.id
    assert source.extraction_status == "completed"

    # 5. Duplicate source validation
    dup_url_source = SourceCreate(
        url="https://arxiv.org/abs/2401.00001",
        source_type="url",
        title="Duplicate Paper"
    )
    asyncio.run(source_service.add_source(db_session, project.id, dup_url_source))
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(source_service.add_source(db_session, project.id, dup_url_source))
    assert exc_info.value.status_code == 400

    # 6. Draft creation & updating
    draft_in = WritingDraftCreate(
        project_id=project.id,
        title="Newsletter Draft Edition",
        original_content="Initial raw text regarding benchmark precision."
    )
    draft = writing_service.create_draft(db_session, draft_in)
    assert draft.id is not None
    assert draft.original_content == "Initial raw text regarding benchmark precision."

    updated_draft = writing_service.update_draft(
        db_session,
        draft.id,
        WritingDraftUpdate(revised_content="Polished text with active voice.", status="in_review")
    )
    assert updated_draft.revised_content == "Polished text with active voice."
    assert updated_draft.original_content == "Initial raw text regarding benchmark precision." # Immutable!

    # 7. Missing record handling (404)
    with pytest.raises(HTTPException) as not_found_proj:
        project_service.get_project(db_session, "non-existent-uuid-999")
    assert not_found_proj.value.status_code == 404

    with pytest.raises(HTTPException) as not_found_source:
        source_service.get_source(db_session, "non-existent-source-uuid")
    assert not_found_source.value.status_code == 404

    # 8. Project deletion & cascade behavior
    deleted = project_service.delete_project(db_session, project.id)
    assert deleted is True

    # Confirm project is gone
    with pytest.raises(HTTPException):
        project_service.get_project(db_session, project.id)

    # Confirm cascaded source was deleted
    with pytest.raises(HTTPException):
        source_service.get_source(db_session, source.id)

def test_sqlite_restart_persistence(tmp_path):
    """
    Verifies actual database persistence across engine restarts:
    Creates a record, disposes the engine/session, re-opens the same SQLite file,
    and asserts the persisted record remains intact.
    """
    db_file = tmp_path / "persistence_test.db"
    db_url = f"sqlite:///{db_file}"

    # Engine session 1: Initialize & insert
    engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    Session1 = sessionmaker(bind=engine1)
    session1 = Session1()

    proj = ResearchProject(
        id="persistent-uuid-42",
        title="Persistent Cross-Session Investigation",
        description="Must survive engine teardown and restart",
        status="active"
    )
    session1.add(proj)
    session1.commit()
    session1.close()
    engine1.dispose()

    # Engine session 2: Restart from disk and retrieve
    engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
    Session2 = sessionmaker(bind=engine2)
    session2 = Session2()

    retrieved = session2.query(ResearchProject).filter(ResearchProject.id == "persistent-uuid-42").first()
    assert retrieved is not None
    assert retrieved.title == "Persistent Cross-Session Investigation"
    assert retrieved.status == "active"
    session2.close()
    engine2.dispose()

def test_phase2_endpoints_crud(client):
    """
    Directly tests the Phase 2 API v1 endpoints:
    /api/v1/projects
    /api/v1/projects/{project_id}/sources
    /api/v1/sources/{source_id}
    /api/v1/writing/drafts
    /api/v1/editorial
    """
    # 1. Create project
    proj_resp = client.post("/api/v1/projects", json={
        "title": "Phase 2 Endpoint Evaluation",
        "description": "Validating full REST CRUD coverage"
    })
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()
    proj_id = proj_data["id"]
    assert proj_data["title"] == "Phase 2 Endpoint Evaluation"

    # 2. List projects & Get project by ID
    list_resp = client.get("/api/v1/projects")
    assert list_resp.status_code == 200
    assert any(p["id"] == proj_id for p in list_resp.json())

    get_resp = client.get(f"/api/v1/projects/{proj_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == proj_id

    # 3. Update project
    put_resp = client.put(f"/api/v1/projects/{proj_id}", json={
        "title": "Phase 2 Endpoint Evaluation - Updated",
        "status": "in_progress"
    })
    assert put_resp.status_code == 200
    assert put_resp.json()["title"] == "Phase 2 Endpoint Evaluation - Updated"
    assert put_resp.json()["status"] == "in_progress"

    # 4. Add source to project & List project sources
    source_resp = client.post(f"/api/v1/projects/{proj_id}/sources", json={
        "title": "Sample AI Paper",
        "source_type": "text",
        "text_content": "Quantization results on 70B parameter models."
    })
    assert source_resp.status_code == 201
    source_id = source_resp.json()["id"]

    src_list_resp = client.get(f"/api/v1/projects/{proj_id}/sources")
    assert src_list_resp.status_code == 200
    assert len(src_list_resp.json()) >= 1

    # 5. Get source by ID & Update source
    get_src_resp = client.get(f"/api/v1/sources/{source_id}")
    assert get_src_resp.status_code == 200
    assert get_src_resp.json()["title"] == "Sample AI Paper"

    put_src_resp = client.put(f"/api/v1/sources/{source_id}", json={
        "title": "Sample AI Paper - Revised Title"
    })
    assert put_src_resp.status_code == 200
    assert put_src_resp.json()["title"] == "Sample AI Paper - Revised Title"

    # 6. Writing draft CRUD: create, list, get, update
    draft_resp = client.post("/api/v1/writing/drafts", json={
        "project_id": proj_id,
        "title": "Evaluation Article Draft",
        "original_content": "In order to optimize inference latency, engineers deployed FP8 quantization."
    })
    assert draft_resp.status_code == 201
    draft_id = draft_resp.json()["id"]

    drafts_list = client.get("/api/v1/writing/drafts")
    assert drafts_list.status_code == 200
    assert any(d["id"] == draft_id for d in drafts_list.json())

    get_draft_resp = client.get(f"/api/v1/writing/drafts/{draft_id}")
    assert get_draft_resp.status_code == 200

    put_draft_resp = client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "revised_content": "To optimize inference latency, engineers deployed FP8 quantization."
    })
    assert put_draft_resp.status_code == 200
    assert "To optimize" in put_draft_resp.json()["revised_content"]

    # 7. Editorial output CRUD: create, list, get, update
    ed_resp = client.post("/api/v1/editorial", json={
        "project_id": proj_id,
        "draft_id": draft_id,
        "headline": "The Great Quantization Revolution",
        "content": "Why FP8 is transforming model inference economics across enterprise deployments [1]."
    })
    assert ed_resp.status_code == 201
    ed_id = ed_resp.json()["id"]

    ed_list_resp = client.get("/api/v1/editorial")
    assert ed_list_resp.status_code == 200
    assert any(e["id"] == ed_id for e in ed_list_resp.json())

    get_ed_resp = client.get(f"/api/v1/editorial/{ed_id}")
    assert get_ed_resp.status_code == 200
    assert get_ed_resp.json()["headline"] == "The Great Quantization Revolution"

    put_ed_resp = client.put(f"/api/v1/editorial/{ed_id}", json={
        "headline": "The Great Quantization Revolution (Updated)"
    })
    assert put_ed_resp.status_code == 200
    assert put_ed_resp.json()["headline"] == "The Great Quantization Revolution (Updated)"

    # 8. Missing record 404 tests
    assert client.get("/api/v1/projects/non-existent-proj-id").status_code == 404
    assert client.get("/api/v1/sources/non-existent-source-id").status_code == 404
    assert client.get("/api/v1/writing/drafts/non-existent-draft-id").status_code == 404
    assert client.get("/api/v1/editorial/non-existent-editorial-id").status_code == 404

    # 9. Deletions
    assert client.delete(f"/api/v1/editorial/{ed_id}").status_code == 204
    assert client.delete(f"/api/v1/writing/drafts/{draft_id}").status_code == 204
    assert client.delete(f"/api/v1/sources/{source_id}").status_code in (200, 204)
    assert client.delete(f"/api/v1/projects/{proj_id}").status_code == 204

    # Verify project is gone
    assert client.get(f"/api/v1/projects/{proj_id}").status_code == 404

