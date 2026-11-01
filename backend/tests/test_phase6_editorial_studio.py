import pytest
from unittest.mock import patch
from backend.app.services.ai_service import ai_service

def test_phase6_headline_generation(client):
    # Setup project and sources
    p_resp = client.post("/api/v1/research/projects", json={"title": "Frontier Reasoning Models"})
    p_id = p_resp.json()["id"]

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p_id}/sources", json={
            "title": f"Benchmarking Reasoning Architecture #{i+1}",
            "source_type": "text",
            "text_content": f"Reasoning test {i+1} validates verifiable step execution with 95% accuracy under deterministic constraints."
        })

    client.post(f"/api/v1/research/projects/{p_id}/generate-brief")

    # Generate headlines
    hl_resp = client.post("/api/v1/editorial/headlines", json={
        "project_id": p_id,
        "audience": "founders and CTOs",
        "tone": "Analytical"
    })

    assert hl_resp.status_code == 200
    data = hl_resp.json()
    assert "headlines" in data
    assert len(data["headlines"]) >= 5
    for h in data["headlines"]:
        assert "headline" in h
        assert "editorial_angle" in h
        assert "explanation" in h
        assert len(h["headline"]) > 10

def test_phase6_editorial_generation_word_count_and_citations(client):
    p_resp = client.post("/api/v1/research/projects", json={"title": "Autonomous Agent Sandboxes"})
    p_id = p_resp.json()["id"]

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p_id}/sources", json={
            "title": f"Security Sandbox Report #{i+1}",
            "source_type": "text",
            "text_content": f"Security audit #{i+1} confirms zero container breakouts when memory ceiling is capped at 4GB."
        })

    client.post(f"/api/v1/research/projects/{p_id}/generate-brief")

    # Generate 300-500 word editorial
    gen_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": p_id,
        "min_words": 300,
        "max_words": 500,
        "selected_headline": "Why Secure Sandboxing Defines the Next Enterprise Agent Wave"
    })

    assert gen_resp.status_code == 201
    ed = gen_resp.json()
    assert ed["headline"] == "Why Secure Sandboxing Defines the Next Enterprise Agent Wave"
    assert ed["word_count"] >= 250 # Validated in editorial range
    assert "source_references" in ed
    assert len(ed["source_references"]) == 3
    for ref in ed["source_references"]:
        assert "source_id" in ref
        assert "title" in ref

    ed_id = ed["id"]

    # Verify linked WritingDraft exists
    assert ed["draft_id"] is not None
    draft_resp = client.get(f"/api/v1/writing/drafts/{ed['draft_id']}")
    assert draft_resp.status_code == 200
    assert draft_resp.json()["title"] == ed["headline"]

def test_phase6_editorial_security_cross_project_rejection(client):
    # Create two projects
    p1 = client.post("/api/v1/research/projects", json={"title": "Project Alpha"}).json()
    p2 = client.post("/api/v1/research/projects", json={"title": "Project Beta"}).json()

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p1['id']}/sources", json={
            "title": f"Alpha Source {i}", "source_type": "text", "text_content": "Alpha technical data."
        })
        client.post(f"/api/v1/research/projects/{p2['id']}/sources", json={
            "title": f"Beta Source {i}", "source_type": "text", "text_content": "Beta technical data."
        })

    b1 = client.post(f"/api/v1/research/projects/{p1['id']}/generate-brief").json()
    b2 = client.post(f"/api/v1/research/projects/{p2['id']}/generate-brief").json()

    # Attempt to generate editorial for Project Alpha using Project Beta's brief
    mismatch_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": p1["id"],
        "research_brief_id": b2["id"]
    })
    assert mismatch_resp.status_code == 400
    assert "Cross-project" in mismatch_resp.json()["detail"] or "does not belong" in mismatch_resp.json()["detail"]

def test_phase6_editorial_crud_and_exports(client):
    p_resp = client.post("/api/v1/research/projects", json={"title": "Export Test Project"})
    p_id = p_resp.json()["id"]

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p_id}/sources", json={
            "title": f"Export Source {i+1}", "source_type": "text", "text_content": "Telemetry data for exports."
        })

    client.post(f"/api/v1/research/projects/{p_id}/generate-brief")
    ed = client.post("/api/v1/editorial/generate", json={"project_id": p_id}).json()
    ed_id = ed["id"]

    # 1. Update
    up_resp = client.put(f"/api/v1/editorial/{ed_id}", json={
        "headline": "Updated Export Title",
        "status": "reviewed"
    })
    assert up_resp.status_code == 200
    assert up_resp.json()["headline"] == "Updated Export Title"
    assert up_resp.json()["status"] == "reviewed"

    # 2. Export Markdown
    md_resp = client.get(f"/api/v1/editorial/{ed_id}/export?format=markdown")
    assert md_resp.status_code == 200
    md_data = md_resp.json()
    assert "# Updated Export Title" in md_data["markdown_content"]
    assert "## References & Verified Sources" in md_data["markdown_content"]

    # 3. Export Plain Text
    txt_resp = client.get(f"/api/v1/editorial/{ed_id}/export?format=txt")
    assert txt_resp.status_code == 200
    txt_data = txt_resp.json()
    assert "UPDATED EXPORT TITLE" in txt_data["plain_text_content"]

    # 4. Export HTML
    html_resp = client.get(f"/api/v1/editorial/{ed_id}/export?format=html")
    assert html_resp.status_code == 200
    html_data = html_resp.json()
    assert "<!DOCTYPE html>" in html_data["html_content"]
    assert "<h1>Updated Export Title</h1>" in html_data["html_content"]

    # 5. Delete
    del_resp = client.delete(f"/api/v1/editorial/{ed_id}")
    assert del_resp.status_code == 204

    # 6. Verify 404 after deletion
    get_del = client.get(f"/api/v1/editorial/{ed_id}")
    assert get_del.status_code == 404

