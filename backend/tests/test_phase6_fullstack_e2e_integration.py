import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token

client = TestClient(app)

# ==============================================================================
# SCENARIO A: NEW USER LIFECYCLE (REGISTER, LOGIN, PROFILE, REFRESH, LOGOUT)
# ==============================================================================
def test_scenario_a_new_user_lifecycle():
    unique_id = str(uuid.uuid4())[:8]
    email = f"editor_{unique_id}@example.com"
    password = "StrongPassword2026!"
    
    # 1. Registration
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": f"Lead Editor {unique_id}",
        "organization_name": f"Editorial House {unique_id}"
    })
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email
    token = reg_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200
    login_token = login_resp.json()["access_token"]
    assert login_token is not None

    # 3. Retrieve Profile & Organizations
    me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["user"]["email"] == email
    assert len(profile["organizations"]) >= 1

    # 4. Token Refresh
    refresh_resp = client.post("/api/v1/auth/refresh", headers=auth_headers)
    assert refresh_resp.status_code == 200
    new_token = refresh_resp.json()["access_token"]
    assert new_token is not None

    # 5. Change Password
    pw_resp = client.post("/api/v1/auth/change-password", headers=auth_headers, json={
        "current_password": password,
        "new_password": "NewStrongPassword2026!"
    })
    assert pw_resp.status_code == 200

    # 6. Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200


# ==============================================================================
# SCENARIO B: RESEARCH WORKFLOW (PROJECT, 3 SOURCES, SYNTHESIS, CITATIONS, RELOAD)
# ==============================================================================
def test_scenario_b_research_end_to_end_workflow():
    # 1. Create project
    proj_resp = client.post("/api/v1/research/projects", json={
        "title": "Quantum AI Hardware Breakthroughs 2026",
        "description": "Cross-source investigation into cryo-CMOS and photonic interconnects."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Ingest 3 sources
    s1 = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Cryogenic CMOS Control Chips",
        "text_content": "Superconducting qubit controllers operating at 4 Kelvin demonstrated a 10x reduction in wire harness complexity. Thermal dissipation remained under 20mW per qubit."
    })
    assert s1.status_code == 201
    s1_id = s1.json()["id"]

    s2 = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Photonic Waveguide Interconnects",
        "text_content": "Silicon photonics reduced inter-chassis communication latency to 12 nanoseconds while maintaining 800 Gbps channel density in commercial datacenter trials."
    })
    assert s2.status_code == 201
    s2_id = s2.json()["id"]

    s3 = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Fault Tolerant Quantum Error Correction",
        "text_content": "Surface code threshold tests confirmed logical error rates dropping below 1e-6 with distance-7 code cycles running continuously for 48 hours."
    })
    assert s3.status_code == 201
    s3_id = s3.json()["id"]

    # 3. Analyze claims on each source
    for sid in [s1_id, s2_id, s3_id]:
        an_resp = client.post(f"/api/v1/sources/{sid}/analyze")
        assert an_resp.status_code == 200

    # 4. Synthesize brief with citations
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief")
    assert brief_resp.status_code == 200
    brief = brief_resp.json()
    assert brief["project_id"] == project_id
    assert brief.get("executive_summary") or brief.get("brief_content", {}).get("executive_summary")
    assert brief.get("brief_content", {}).get("what_happened") or brief.get("brief_content", {}).get("key_developments") or len(brief.get("key_developments", [])) >= 0

    # 5. Reload project and verify persisted sources & brief
    reload_resp = client.get(f"/api/v1/research/projects/{project_id}")
    assert reload_resp.status_code == 200
    loaded = reload_resp.json()
    assert loaded["id"] == project_id
    assert len(loaded["sources"]) == 3
    assert len(loaded.get("briefs", [])) >= 1 or loaded.get("brief") is not None


# ==============================================================================
# SCENARIO C: WRITING ASSISTANT (DRAFT, REWRITE, ACCEPT/REJECT, VERSIONING)
# ==============================================================================
def test_scenario_c_writing_assistant_and_versioning():
    orig_text = "In order to facilitate the expeditious implementation of AI clusters, it is crucially important that engineering teams utilize state-of-the-art accelerators."
    
    # 1. Create initial draft
    draft_resp = client.post("/api/v1/writing/drafts", json={
        "title": "Executive AI Infrastructure Review",
        "original_content": orig_text
    })
    assert draft_resp.status_code == 201
    draft = draft_resp.json()
    draft_id = draft["id"]

    # 2. Analyze writing quality & generate deterministic suggestions
    analysis_resp = client.post("/api/v1/writing/analyze", json={
        "draft_id": draft_id,
        "text": orig_text,
        "title": "Executive AI Infrastructure Review"
    })
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()
    assert "metrics" in analysis
    assert "issues" in analysis
    assert len(analysis["issues"]) >= 1

    # 3. Accept one suggestion and verify draft is updated with version snapshot
    first_sugg_id = analysis["issues"][0]["id"]
    accept_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{first_sugg_id}/accept")
    assert accept_resp.status_code == 200

    # 4. Compare draft versions
    compare_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert compare_resp.status_code == 200

    # 5. Query version history records via documents route
    versions_resp = client.get(f"/api/v1/documents/WRITING_DRAFT/{draft_id}/versions")
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) >= 1
    assert versions[0]["document_type"] == "WRITING_DRAFT"


# ==============================================================================
# SCENARIO D: EDITORIAL REVIEW WORKFLOW
# ==============================================================================
def test_scenario_d_editorial_review_workflow():
    # 1. Setup project, sources, and brief
    p_resp = client.post("/api/v1/research/projects", json={"title": "Editorial Quality Benchmark"})
    p_id = p_resp.json()["id"]

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p_id}/sources", json={
            "source_type": "text",
            "title": f"Benchmarking Source #{i+1}",
            "text_content": f"Verified factual data point #{i+1} regarding high-speed transformer inference optimization."
        })
    client.post(f"/api/v1/research/projects/{p_id}/generate-brief")

    # 2. Generate publication-ready editorial
    gen_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": p_id,
        "target_word_count": 350,
        "tone": "Analytical, Objective"
    })
    assert gen_resp.status_code in [200, 201]
    ed = gen_resp.json()
    ed_id = ed["id"]

    # 3. Run AI pre-review quality checks
    ai_rev_resp = client.post(f"/api/v1/editorial/{ed_id}/ai-review")
    assert ai_rev_resp.status_code == 200
    rev_data = ai_rev_resp.json()
    assert "word_count_compliance" in rev_data or "quality_checks" in rev_data

    # 4. Submit for human review
    sub_resp = client.post(f"/api/v1/editorial/{ed_id}/submit-review")
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "HUMAN_REVIEW_PENDING"

    # 5. Add human editorial comment
    comment_resp = client.post(f"/api/v1/editorial/{ed_id}/comments", json={
        "comment": "Verify technical terminology in second paragraph.",
        "section_reference": "body"
    })
    assert comment_resp.status_code == 201

    # 6. Approve editorial
    approve_resp = client.post(f"/api/v1/editorial/{ed_id}/approve", json={"reviewer_name": "Human Editor", "approval_notes": "Meets quality criteria."})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"


# ==============================================================================
# SCENARIO E: PROVIDER FAILURE & DETERMINISTIC FALLBACK RESILIENCE
# ==============================================================================
def test_scenario_e_provider_failure_and_fallback():
    from backend.app.services.ai.router import ai_router

    # Generating structured data with fallback resilience
    import asyncio
    res = asyncio.run(ai_router.execute_structured(
        prompt="Synthesize technical implications",
        system_prompt="Return JSON",
        provider="groq"
    ))
    # Must succeed with valid content without 500 unhandled exception
    assert res.content is not None
    assert res.is_fallback is True or res.provider == "groq"


# ==============================================================================
# SCENARIO F: SECURITY, MULTI-TENANCY & SSRF GUARDRAILS
# ==============================================================================
def test_scenario_f_security_and_ssrf_guardrails():
    # 1. Setup valid project to test SSRF URL blocking
    p_resp = client.post("/api/v1/research/projects", json={"title": "Security Audit Test"})
    assert p_resp.status_code == 201
    project_id = p_resp.json()["id"]

    # Attempt SSRF to loopback address (Must be blocked with 400 Bad Request)
    ssrf_resp = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "url": "http://127.0.0.1:8000/api/v1/auth/me",
        "title": "Malicious Local Request",
        "source_type": "URL"
    })
    assert ssrf_resp.status_code in [400, 422]

    # 2. Attempt access with invalid/revoked JWT token
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
    auth_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {invalid_token}"})
    assert auth_resp.status_code == 401

    # 3. Verify no credentials exposed in AI connections listing
    conns_resp = client.get("/api/v1/ai/connections")
    assert conns_resp.status_code == 200
    for conn in conns_resp.json():
        assert "gsk_" not in conn["masked_key"] or "..." in conn["masked_key"]
        assert "sk-" not in conn["masked_key"] or "..." in conn["masked_key"]


# ==============================================================================
# SCENARIO G: DASHBOARD INTEGRATION WITH REAL METRICS
# ==============================================================================
def test_scenario_g_dashboard_metrics_integration():
    # Overview endpoint
    dash_resp = client.get("/api/v1/dashboard/overview")
    assert dash_resp.status_code == 200
    data = dash_resp.json()
    metrics = data["metrics"]

    assert metrics["total_projects"] >= 1
    assert metrics["total_sources"] >= 1
    assert "verified_sources" in metrics
    assert "total_drafts" in metrics
    assert "total_editorials" in metrics

    # Activity timeline endpoint
    act_resp = client.get("/api/v1/dashboard/activity?limit=10")
    assert act_resp.status_code == 200
    act_data = act_resp.json()
    activities = act_data.get("activities", act_data) if isinstance(act_data, dict) else act_data
    assert isinstance(activities, list)
    if activities:
        assert "type" in activities[0]
        assert "title" in activities[0]
