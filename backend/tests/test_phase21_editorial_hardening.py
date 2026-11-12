"""
Phase 21 - Editorial Studio Security Hardening, Multi-Tenant Isolation & Functional Validation.
Verifies:
1. Multi-tenant access controls across all editorial routes (cross-tenant 404 / 403)
2. Finalized immutability protection (HTTP 409 on update or deletion of finalized content)
3. Server-side reviewer identity verification (cannot spoof reviewer name)
4. Multi-format exports including Markdown, Plain Text, HTML, and JSON
5. Tenant-scoped workflow dashboard statistics
"""

import pytest
import uuid
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.editorial_review import WorkflowStatus

@pytest.fixture
def api_client():
    return TestClient(app)

def _register_and_create_project(client: TestClient, org_name: str, email_prefix: str):
    suffix = uuid.uuid4().hex[:6]
    email = f"{email_prefix}_{suffix}@example.com"
    pwd = "HardenedPassword2026!#"

    # Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "confirm_password": pwd,
        "full_name": f"{email_prefix.capitalize()} Lead",
        "organization_name": org_name,
        "terms_accepted": True
    })
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]
    org_id = reg_resp.json()["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}

    # Create project
    proj_resp = client.post("/api/v1/projects", json={
        "title": f"Investigation: {org_name}",
        "description": "Multi-tenant verification project"
    }, headers=headers)
    assert proj_resp.status_code == 201, proj_resp.text
    project_id = proj_resp.json()["id"]

    # Ingest 3 sources
    for i in range(1, 4):
        src_resp = client.post(f"/api/v1/projects/{project_id}/sources", json={
            "title": f"Verified Source Document #{i}",
            "url": f"https://example.com/doc-{i}",
            "text_content": f"Evidence record #{i} proves deterministic enterprise execution across distributed nodes."
        }, headers=headers)
        assert src_resp.status_code == 201, src_resp.text

    # Generate research brief
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief", headers=headers)
    assert brief_resp.status_code == 200, brief_resp.text

    return {
        "headers": headers,
        "token": token,
        "user_id": user_id,
        "org_id": org_id,
        "project_id": project_id,
        "user_name": f"{email_prefix.capitalize()} Lead"
    }

def test_phase21_multi_tenant_editorial_isolation(api_client: TestClient):
    """Verifies that Tenant B cannot read, update, delete, or export Tenant A's editorials."""
    tenant_a = _register_and_create_project(api_client, "Cybersecurity Gazette", "gazette")
    tenant_b = _register_and_create_project(api_client, "BioTech Weekly", "biotech")

    # Tenant A generates an editorial
    gen_resp = api_client.post("/api/v1/editorial/generate", json={
        "project_id": tenant_a["project_id"],
        "headline": "Zero-Day Sandboxing Strategies for Critical Infrastructure",
        "min_words": 300,
        "max_words": 500
    }, headers=tenant_a["headers"])
    assert gen_resp.status_code == 201, gen_resp.text
    editorial_a_id = gen_resp.json()["id"]

    # 1. Tenant B attempts to read Tenant A's editorial -> 404 Not Found (Cross-tenant protected)
    read_resp = api_client.get(f"/api/v1/editorial/{editorial_a_id}", headers=tenant_b["headers"])
    assert read_resp.status_code in (404, 403), f"Expected 404/403, got {read_resp.status_code}"

    # 2. Tenant B attempts to update Tenant A's editorial -> 404 / 403
    upd_resp = api_client.put(f"/api/v1/editorial/{editorial_a_id}", json={
        "headline": "Hacked Headline"
    }, headers=tenant_b["headers"])
    assert upd_resp.status_code in (404, 403)

    # 3. Tenant B attempts to export Tenant A's editorial -> 404 / 403
    exp_resp = api_client.get(f"/api/v1/editorial/{editorial_a_id}/export?format=markdown", headers=tenant_b["headers"])
    assert exp_resp.status_code in (404, 403)

    # 4. Tenant B attempts to delete Tenant A's editorial -> 404 / 403
    del_resp = api_client.delete(f"/api/v1/editorial/{editorial_a_id}", headers=tenant_b["headers"])
    assert del_resp.status_code in (404, 403)

def test_phase21_finalized_editorial_immutability(api_client: TestClient):
    """Verifies that finalized articles are completely locked from modification or deletion."""
    tenant = _register_and_create_project(api_client, "FinTech Review", "fintech")

    # Generate editorial
    gen_resp = api_client.post("/api/v1/editorial/generate", json={
        "project_id": tenant["project_id"],
        "headline": "Autonomous Clearing Houses and Factual Settlement",
        "min_words": 300,
        "max_words": 500
    }, headers=tenant["headers"])
    assert gen_resp.status_code == 201
    ed_id = gen_resp.json()["id"]

    # Submit for review -> Approve -> Finalize
    api_client.post(f"/api/v1/editorial/{ed_id}/submit-review", headers=tenant["headers"])
    api_client.post(f"/api/v1/editorial/{ed_id}/approve", json={
        "reviewer_name": "Any Name",
        "approval_notes": "Meets compliance specifications."
    }, headers=tenant["headers"])

    fin_resp = api_client.post(f"/api/v1/editorial/{ed_id}/finalize", json={
        "finalized_by": "Senior Publisher",
        "publication_notes": "Lock for distribution."
    }, headers=tenant["headers"])
    assert fin_resp.status_code == 200
    assert fin_resp.json()["status"] == WorkflowStatus.FINALIZED

    # 1. Attempt to update finalized editorial -> 409 Conflict
    upd_resp = api_client.put(f"/api/v1/editorial/{ed_id}", json={
        "headline": "Tampered Final Headline",
        "content": "Tampered content after final publication lock."
    }, headers=tenant["headers"])
    assert upd_resp.status_code == 409, f"Expected 409 Conflict on finalized update, got {upd_resp.status_code}"
    assert "locked and immutable" in upd_resp.json()["detail"].lower()

    # 2. Attempt to delete finalized editorial -> 409 Conflict
    del_resp = api_client.delete(f"/api/v1/editorial/{ed_id}", headers=tenant["headers"])
    assert del_resp.status_code == 409, f"Expected 409 Conflict on finalized delete, got {del_resp.status_code}"
    assert "locked and cannot be deleted" in del_resp.json()["detail"].lower()

def test_phase21_reviewer_identity_server_enforcement(api_client: TestClient):
    """Verifies that reviewer identity is tied to the authenticated user and cannot be forged."""
    tenant = _register_and_create_project(api_client, "Medical AI Journal", "medjournal")

    gen_resp = api_client.post("/api/v1/editorial/generate", json={
        "project_id": tenant["project_id"],
        "headline": "Clinical Trial Evidence Synthesis Protocols",
        "min_words": 300,
        "max_words": 500
    }, headers=tenant["headers"])
    ed_id = gen_resp.json()["id"]

    # Submit for review
    sub_resp = api_client.post(f"/api/v1/editorial/{ed_id}/submit-review", headers=tenant["headers"])
    assert sub_resp.status_code == 200

    # User attempts to pass fake reviewer name
    app_resp = api_client.post(f"/api/v1/editorial/{ed_id}/approve", json={
        "reviewer_name": "Spoofed Fake Identity",
        "approval_notes": "Approved."
    }, headers=tenant["headers"])
    assert app_resp.status_code == 200
    # Server must bind the reviewer name to the authenticated user's actual name!
    assert app_resp.json()["reviewer"] == tenant["user_name"]

def test_phase21_multi_format_exports(api_client: TestClient):
    """Verifies export to Markdown, Plain Text, HTML5, and JSON formats."""
    tenant = _register_and_create_project(api_client, "Robotics Quarterly", "robotics")

    gen_resp = api_client.post("/api/v1/editorial/generate", json={
        "project_id": tenant["project_id"],
        "selected_headline": "Kinematic Synthesis and Precision Actuation",
        "min_words": 300,
        "max_words": 500
    }, headers=tenant["headers"])
    ed_id = gen_resp.json()["id"]

    # 1. Markdown Export
    exp_md = api_client.get(f"/api/v1/editorial/{ed_id}/export?format=markdown", headers=tenant["headers"])
    assert exp_md.status_code == 200
    assert "Kinematic Synthesis" in exp_md.json()["markdown_content"]
    assert "## References" in exp_md.json()["markdown_content"]

    # 2. Plain Text Export
    exp_txt = api_client.get(f"/api/v1/editorial/{ed_id}/export?format=txt", headers=tenant["headers"])
    assert exp_txt.status_code == 200
    assert "KINEMATIC SYNTHESIS" in exp_txt.json()["plain_text_content"]

    # 3. HTML Export
    exp_html = api_client.get(f"/api/v1/editorial/{ed_id}/export?format=html", headers=tenant["headers"])
    assert exp_html.status_code == 200
    assert "<" in exp_html.json()["html_content"]

    # 4. JSON Export
    exp_json = api_client.get(f"/api/v1/editorial/{ed_id}/export?format=json", headers=tenant["headers"])
    assert exp_json.status_code == 200
    assert exp_json.json()["json_content"] is not None
    import json
    parsed = json.loads(exp_json.json()["json_content"])
    assert parsed["id"] == ed_id
    assert parsed["headline"] == "Kinematic Synthesis and Precision Actuation"

def test_phase21_dashboard_stats_tenant_scoping(api_client: TestClient):
    """Verifies workflow stats are strictly scoped to the requesting tenant's workspace."""
    tenant_x = _register_and_create_project(api_client, "Tenant X Newsroom", "tenantx")
    tenant_y = _register_and_create_project(api_client, "Tenant Y Media", "tenanty")

    # Tenant X creates an editorial
    api_client.post("/api/v1/editorial/generate", json={
        "project_id": tenant_x["project_id"],
        "headline": "Tenant X Exclusive Editorial",
        "min_words": 300,
        "max_words": 500
    }, headers=tenant_x["headers"])

    # Stats for Tenant X
    stats_x = api_client.get("/api/v1/editorial/dashboard/stats", headers=tenant_x["headers"]).json()
    assert stats_x["total_editorials"] >= 1

    # Stats for Tenant Y
    stats_y = api_client.get("/api/v1/editorial/dashboard/stats", headers=tenant_y["headers"]).json()
    # Tenant Y has 0 editorials
    assert stats_y["total_editorials"] == 0
