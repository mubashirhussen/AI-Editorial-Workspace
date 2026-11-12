import pytest
import uuid
import io
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.utils.security import is_safe_url
from backend.app.services.research.document_extractor import extract_from_bytes, MAX_FILE_BYTES


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


def _register_tenant(client: TestClient, org_name: str, email_prefix: str):
    suffix = uuid.uuid4().hex[:6]
    email = f"{email_prefix}_{suffix}@example.com"
    pwd = "HardenedPassword2026!#"

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
    return {"token": token, "user_id": user_id, "org_id": org_id, "headers": headers}


def test_phase22_project_crud_and_lifecycle(api_client):
    tenant = _register_tenant(api_client, "Research Lab Alpha", "researcher")
    headers = tenant["headers"]

    # 1. Create Project with rich Phase 22 metadata
    payload = {
        "title": "Autonomous AI Verification & Governance",
        "topic": "Test-Time Reasoning Verification",
        "description": "Evaluation of factual grounding and hallucination mitigation in multi-hop models",
        "research_objective": "Benchmark citation accuracy across 3 primary technical reports",
        "target_audience": "founders, builders, and operators",
        "research_scope": "Q4 2025 to 2026 releases",
        "keywords": ["verification", "reasoning", "citations", "grounding"],
        "preferred_source_types": ["URL", "DOCUMENT", "TEXT"],
        "organization_id": tenant["org_id"],
    }

    create_res = api_client.post("/api/v1/research/projects", json=payload, headers=headers)
    assert create_res.status_code == 201, create_res.text
    project_data = create_res.json()
    project_id = project_data["id"]
    assert project_data["title"] == "Autonomous AI Verification & Governance"
    assert project_data["topic"] == "Test-Time Reasoning Verification"
    assert project_data["status"] == "draft"

    # 2. Update Project Details
    update_res = api_client.put(
        f"/api/v1/research/projects/{project_id}",
        json={"description": "Updated research description for production audit."},
        headers=headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated research description for production audit."

    # 3. Archive Project
    archive_res = api_client.post(f"/api/v1/research/projects/{project_id}/archive", headers=headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "archived"

    # 4. Reopen Project
    reopen_res = api_client.post(f"/api/v1/research/projects/{project_id}/reopen", headers=headers)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "in_progress"


def test_phase22_ssrf_prevention():
    # 1. Loopback addresses
    assert is_safe_url("http://127.0.0.1/admin") is False
    assert is_safe_url("http://localhost:8000/metrics") is False
    assert is_safe_url("http://0.0.0.0:5000") is False

    # 2. Cloud metadata IP (AWS/GCP/Azure)
    assert is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert is_safe_url("http://100.100.100.200/latest/meta-data/") is False

    # 3. Private IP Subnets (RFC 1918)
    assert is_safe_url("http://10.0.0.1/internal") is False
    assert is_safe_url("http://192.168.1.1/router") is False
    assert is_safe_url("http://172.16.0.5/api") is False

    # 4. Forbidden schemes
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://example.com/file.txt") is False
    assert is_safe_url("gopher://internal-server") is False

    # 5. Legitimate public URLs
    assert is_safe_url("https://deepmind.google/technologies/gemini/") is True
    assert is_safe_url("https://en.wikipedia.org/wiki/Large_language_model") is True
    assert is_safe_url("https://arxiv.org/abs/1706.03762") is True


def test_phase22_document_extractor_and_signature_checks():
    # 1. Valid plain text extraction
    text_content = b"Deterministic verification architecture eliminates multi-turn reasoning degradation."
    res = extract_from_bytes(text_content, "verification_notes.txt", "text/plain")
    assert res["success"] is True
    assert res["source_type"] == "TEXT"
    assert "Deterministic verification" in res["content"]
    assert res["content_hash"] is not None

    # 2. Reject empty file
    empty_res = extract_from_bytes(b"", "empty.txt", "text/plain")
    assert empty_res["success"] is False
    assert "empty" in empty_res["error"].lower()

    # 3. Reject file exceeding 10MB
    oversized = b"A" * (MAX_FILE_BYTES + 1024)
    size_res = extract_from_bytes(oversized, "huge.txt", "text/plain")
    assert size_res["success"] is False
    assert "exceeds maximum allowed size" in size_res["error"]

    # 4. Corrupt PDF check (missing %PDF- magic signature)
    corrupt_pdf = b"This is plain text pretending to be a PDF"
    pdf_res = extract_from_bytes(corrupt_pdf, "fake.pdf", "application/pdf")
    assert pdf_res["success"] is False
    assert "invalid file signature" in pdf_res["error"].lower() or "corrupt" in pdf_res["error"].lower()

    # 5. Corrupt DOCX check (missing PK\x03\x04 zip header)
    corrupt_docx = b"Not a zip archive docx"
    docx_res = extract_from_bytes(corrupt_docx, "fake.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert docx_res["success"] is False
    assert "invalid file signature" in docx_res["error"].lower() or "corrupt" in docx_res["error"].lower()


def test_phase22_brief_synthesis_and_evidence_traceability(api_client):
    tenant = _register_tenant(api_client, "Intelligence Desk", "analyst")
    headers = tenant["headers"]

    # Create project
    proj_res = api_client.post(
        "/api/v1/research/projects",
        json={"title": "Frontier AI Reasoning Verification", "organization_id": tenant["org_id"]},
        headers=headers,
    )
    project_id = proj_res.json()["id"]

    # Ingest 2 sources (less than 3)
    s1_res = api_client.post(
        f"/api/v1/research/projects/{project_id}/sources",
        json={
            "source_type": "text",
            "title": "DeepSeek-R1 Technical Overview",
            "text_content": "DeepSeek-R1 introduces test-time compute scaling and verifiable reasoning chains. Empirical findings show a 44% gain in mathematical citation rigor."
        },
        headers=headers,
    )
    assert s1_res.status_code == 201

    s2_res = api_client.post(
        f"/api/v1/research/projects/{project_id}/sources",
        json={
            "source_type": "text",
            "title": "Model Context Protocol Specifications",
            "text_content": "The Model Context Protocol standardizes multi-agent context distribution, eliminating memory leaks across external database tool calls."
        },
        headers=headers,
    )
    assert s2_res.status_code == 201

    # Attempt brief generation with only 2 sources -> should fail with HTTP 400
    brief_fail = api_client.post(f"/api/v1/research/projects/{project_id}/brief", headers=headers)
    assert brief_fail.status_code == 400
    assert "at least 3 sources" in brief_fail.json()["detail"].lower()

    # Ingest 3rd source
    s3_res = api_client.post(
        f"/api/v1/research/projects/{project_id}/sources",
        json={
            "source_type": "text",
            "title": "Attention & Test-Time Grounding Benchmark",
            "text_content": "Verifiable transformer architectures reduce multi-turn hallucination accumulation by 65%. Independent replication confirms reliable performance."
        },
        headers=headers,
    )
    assert s3_res.status_code == 201

    # Generate brief now that 3 sources exist
    brief_res = api_client.post(f"/api/v1/research/projects/{project_id}/brief", headers=headers)
    assert brief_res.status_code == 200, brief_res.text
    brief_data = brief_res.json()
    assert brief_data["executive_summary"] != ""
    assert len(brief_data["newsletter_angles"]) >= 1

    # Validate evidence verification structure and statuses
    evidence = brief_data.get("evidence", [])
    assert len(evidence) >= 1
    for ev in evidence:
        assert ev["status"] in ("SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "NOT_VERIFIABLE")
        assert "claim" in ev
        assert "source_title" in ev


def test_phase22_brief_update_versioning_and_export(api_client):
    tenant = _register_tenant(api_client, "Editorial Corp", "editor")
    headers = tenant["headers"]

    # Create project and 3 sources
    proj = api_client.post("/api/v1/research/projects", json={"title": "Verification Systems 2026", "organization_id": tenant["org_id"]}, headers=headers).json()
    project_id = proj["id"]

    for i in range(1, 4):
        api_client.post(
            f"/api/v1/research/projects/{project_id}/sources",
            json={"source_type": "text", "title": f"Source {i}", "text_content": f"Factual statement number {i} regarding verification and system reliability."},
            headers=headers
        )

    # Generate initial brief
    initial_brief = api_client.post(f"/api/v1/research/projects/{project_id}/brief", headers=headers).json()
    assert initial_brief["version"] == 1
    assert initial_brief["is_user_edited"] is False

    # 1. Update brief with user edits
    update_res = api_client.put(
        f"/api/v1/research/projects/{project_id}/brief",
        json={
            "title": "Refined Editorial Brief: Verification Systems",
            "executive_summary": "Hand-edited executive summary emphasizing operational resilience for enterprise CTOs.",
            "what_happened": "Enterprise engineering teams have adopted deterministic evaluation harnesses.",
            "why_it_matters": "Token economics shift toward verifiable small reasoning models.",
            "user_notes": "Prioritize operational benchmarks over synthetic marketing benchmarks."
        },
        headers=headers
    )
    assert update_res.status_code == 200, update_res.text
    updated_data = update_res.json()
    assert updated_data["title"] == "Refined Editorial Brief: Verification Systems"
    assert updated_data["is_user_edited"] is True
    assert updated_data["version"] >= 2
    assert updated_data["user_notes"] == "Prioritize operational benchmarks over synthetic marketing benchmarks."

    # 2. Verify brief version history
    history_res = api_client.get(f"/api/v1/research/projects/{project_id}/brief/history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1

    # 3. Verify multi-format exports
    # Markdown
    export_md = api_client.get(f"/api/v1/research/projects/{project_id}/brief/export?format=markdown", headers=headers)
    assert export_md.status_code == 200
    md_body = export_md.json()
    assert "# Refined Editorial Brief" in md_body["markdown_content"]
    assert "## Executive Summary" in md_body["markdown_content"]

    # Plain text
    export_txt = api_client.get(f"/api/v1/research/projects/{project_id}/brief/export?format=text", headers=headers)
    assert export_txt.status_code == 200
    txt_body = export_txt.json()
    assert "RESEARCH BRIEF:" in txt_body["plain_text_content"]

    # JSON
    export_json = api_client.get(f"/api/v1/research/projects/{project_id}/brief/export?format=json", headers=headers)
    assert export_json.status_code == 200
    json_body = export_json.json()
    assert "project_id" in json_body["json_content"]


def test_phase22_cross_tenant_isolation(api_client):
    tenant_a = _register_tenant(api_client, "Tenant Alpha", "tenant_a")
    tenant_b = _register_tenant(api_client, "Tenant Beta", "tenant_b")

    headers_a = tenant_a["headers"]
    headers_b = tenant_b["headers"]

    # Tenant A creates project
    proj_a = api_client.post(
        "/api/v1/research/projects",
        json={"title": "Tenant A Secret Investigation", "organization_id": tenant_a["org_id"]},
        headers=headers_a
    ).json()
    project_id = proj_a["id"]

    # Tenant B attempts to read Tenant A's project -> 403 or 404 (tenant isolated)
    read_res = api_client.get(f"/api/v1/research/projects/{project_id}", headers=headers_b)
    assert read_res.status_code in (403, 404)

    # Tenant B attempts to add a source to Tenant A's project -> 403 or 404
    add_source_res = api_client.post(
        f"/api/v1/research/projects/{project_id}/sources",
        json={"source_type": "text", "title": "Injected Source", "text_content": "Malicious payload"},
        headers=headers_b
    )
    assert add_source_res.status_code in (403, 404)

    # Tenant B attempts to export Tenant A's brief -> 403 or 404
    export_res = api_client.get(f"/api/v1/research/projects/{project_id}/brief/export", headers=headers_b)
    assert export_res.status_code in (403, 404)
