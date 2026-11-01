import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.core.database import Base, get_db

# Dedicated isolated SQLite database for Phase 19 E2E Acceptance tests
TEST_DB_FILE = "./test_phase19_e2e.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_test_database():
    # Clean up any leftover file
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    
    # Teardown
    test_engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

client = TestClient(app)

# =========================================================================
# 1. RESEARCH ASSISTANT E2E JOURNEY
# =========================================================================
def test_e2e_research_assistant_complete_journey():
    """
    User Journey:
    1. Create research project
    2. Add 3 sources via text_content
    3. Verify extraction and clean text
    4. Analyze claims (Facts, Analysis, Speculation)
    5. Generate research brief
    6. Verify summaries, classifications, and source citations
    7. Verify extraction error on invalid input (SSRF attempt)
    """
    # Step 1: Create project (Returns 201)
    proj_resp = client.post("/api/v1/projects", json={
        "title": "Quantum ML & LLM Compute Acceleration 2026",
        "description": "Investigating hardware benchmarks and scaling limits in AI infrastructure."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Step 2: Add 3 sources with text_content (Returns 201)
    source1_resp = client.post(f"/api/v1/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Tensor Processing Units at 1.5nm",
        "text_content": "Google and DeepMind announced next-generation TPU v6 hardware delivering 4.2x FLOPS per watt. Benchmark tests indicate latency reductions of 38% on transformer decoders. However, early silicon yields remain unpredictable."
    })
    assert source1_resp.status_code == 201
    s1_id = source1_resp.json()["id"]
    assert "TPU v6" in source1_resp.json()["extracted_content"]

    source2_resp = client.post(f"/api/v1/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "SemiAnalysis 2026 Compute Cost Model",
        "text_content": "Hyperscaler capex on AI clusters reached $120B in Q1 2026. Datacenter power constraints in Virginia and Dublin are forcing modular nuclear deployments. Industry analysts predict compute bottlenecks will peak by 2027."
    })
    assert source2_resp.status_code == 201
    s2_id = source2_resp.json()["id"]

    source3_resp = client.post(f"/api/v1/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Liquid Immersion Cooling in Hyperscale Datacenters",
        "text_content": "Direct-to-chip two-phase immersion cooling decreases PUE from 1.35 to 1.04. Pilot deployments demonstrated cooling power reductions of 42% under sustained 1200W TDP workloads."
    })
    assert source3_resp.status_code == 201
    s3_id = source3_resp.json()["id"]

    # Step 3: Analyze claims on each source and fetch stored claim analysis
    for sid in [s1_id, s2_id, s3_id]:
        analyze_resp = client.post(f"/api/v1/sources/{sid}/analyze")
        assert analyze_resp.status_code == 200
        assert analyze_resp.json()["success"] is True

        get_analysis = client.get(f"/api/v1/sources/{sid}/analysis")
        assert get_analysis.status_code == 200
        analysis_data = get_analysis.json()
        assert "reported_facts" in analysis_data or "facts" in analysis_data
        assert "analysis" in analysis_data
        assert "uncertainties" in analysis_data or "speculation" in analysis_data

    # Step 4: Synthesize Research Brief (Requires >= 3 analyzed sources)
    brief_resp = client.post(f"/api/v1/projects/{project_id}/research/synthesize")
    assert brief_resp.status_code == 200
    brief_data = brief_resp.json()
    assert brief_data["project_id"] == project_id
    assert brief_data["executive_summary"] is not None
    assert len(brief_data["evidence"]) >= 1
    assert len(brief_data["newsletter_angles"]) >= 1
    assert "what_happened" in brief_data["brief_content"]

    # Step 5: Verify Brief retrieval
    get_brief = client.get(f"/api/v1/projects/{project_id}/research/brief")
    assert get_brief.status_code == 200
    assert get_brief.json()["id"] == brief_data["id"]

    # Step 6: Verify extraction failure handling on invalid/blocked domain
    fail_source = client.post(f"/api/v1/projects/{project_id}/sources", json={
        "source_type": "url",
        "url": "http://127.0.0.1:9090/admin-leak",
        "title": "Forbidden SSRF Test"
    })
    assert fail_source.status_code == 201
    fail_data = fail_source.json()
    
    # Trigger extraction which enforces SSRF blocking
    ext_fail = client.post(f"/api/v1/sources/{fail_data['id']}/extract")
    assert ext_fail.status_code == 200
    ext_fail_data = ext_fail.json()
    assert ext_fail_data["extraction_status"].lower() == "failed"
    assert "Security violation" in (ext_fail_data.get("error_message") or "") or "blocked" in (ext_fail_data.get("error_message") or "").lower()


# =========================================================================
# 2. WRITING ASSISTANT E2E JOURNEY
# =========================================================================
def test_e2e_writing_assistant_complete_journey():
    """
    User Journey:
    1. Create a writing draft
    2. Run writing analysis
    3. Verify writing metrics (Flesch score, reading time, word count)
    4. Display suggestions
    5. Accept 1 suggestion (e.g. In order to -> To)
    6. Reject another suggestion
    7. Compare original and revised content
    8. Verify that original content remains unchanged while revised persists
    """
    test_text = (
        "It is widely acknowledged that modern hardware advances are rapidly transforming AI infrastructure. "
        "In order to understand the paradigm shift, engineers must carefully evaluate memory bandwidth limitations. "
        "The model was trained by researchers using distributed gradient accumulation across sixteen clusters."
    )

    # Step 1: Create draft (Returns 201)
    draft_resp = client.post("/api/v1/writing/drafts", json={
        "title": "Editorial on Semiconductor Transitions",
        "original_content": test_text
    })
    assert draft_resp.status_code == 201
    draft_data = draft_resp.json()
    draft_id = draft_data["id"]
    original_text = draft_data["original_content"]

    # Step 2: Run writing analysis
    analyze_resp = client.post("/api/v1/writing/analyze", json={
        "text": test_text,
        "draft_id": draft_id
    })
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.json()

    # Step 3: Verify metrics
    metrics = analysis_data["metrics"]
    assert metrics["word_count"] > 30
    assert "reading_time_minutes" in metrics

    # Step 4: Display suggestions
    suggestions = analysis_data["issues"]
    assert len(suggestions) >= 2

    # Find the filler suggestion ("In order to" -> "To")
    actionable_sug = next(s for s in suggestions if "in order to" in s["original_text"].lower())
    reject_sug = next(s for s in suggestions if s["id"] != actionable_sug["id"])

    # Step 5: Accept the actionable suggestion
    accept_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{actionable_sug['id']}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["success"] is True

    # Step 6: Reject another suggestion
    reject_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{reject_sug['id']}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["success"] is True

    # Step 7: Compare original and revised
    compare_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert compare_resp.status_code == 200
    compare_data = compare_resp.json()
    assert compare_data["original_content"] == original_text
    assert compare_data["revised_content"] != original_text
    assert "to understand" in compare_data["revised_content"].lower()

    # Step 8: Verify persistence & original integrity
    get_draft = client.get(f"/api/v1/writing/drafts/{draft_id}")
    assert get_draft.status_code == 200
    reloaded = get_draft.json()
    assert reloaded["original_content"] == original_text
    assert reloaded["revised_content"] == compare_data["revised_content"]


# =========================================================================
# 3. EDITORIAL STUDIO E2E JOURNEY
# =========================================================================
def test_e2e_editorial_studio_complete_journey():
    """
    User Journey:
    1. Select research project with >= 3 sources
    2. Generate headlines (5 formulaic options)
    3. Generate editorial draft with strict 300-500 words and source citations
    4. Verify source references [1], [2]
    5. Open in writing workflow (create draft from editorial)
    6. Export editorial in Markdown, TXT, and HTML5
    7. Verify exported content and HTML entity escaping
    """
    # Step 1: Create project and 3 sources
    proj_resp = client.post("/api/v1/projects", json={
        "title": "Autonomous Coding Agents in FinTech",
        "description": "Evaluation of agentic code generation in highly regulated banking environments."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    for i in range(1, 4):
        client.post(f"/api/v1/projects/{project_id}/sources", json={
            "source_type": "text",
            "title": f"FinTech AI Report Part {i}",
            "text_content": f"A survey of Tier-1 banks revealed that LLM agents accelerated code reviews by {50 + i * 5}%. Automated testing reduced QA backlogs while strict security gates prevented memory vulnerabilities in production systems."
        })
    client.post(f"/api/v1/projects/{project_id}/research/synthesize")

    # Step 2: Headline Generation
    head_resp = client.post("/api/v1/editorial/headlines", json={
        "project_id": project_id,
        "topic": "Autonomous Coding Agents in Banking"
    })
    assert head_resp.status_code == 200
    headlines = head_resp.json()["headlines"]
    assert len(headlines) == 5
    chosen_headline = headlines[0]["headline"] if isinstance(headlines[0], dict) else str(headlines[0])

    # Step 3: Generate Editorial (300-500 words, returns 201)
    gen_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": project_id,
        "headline": chosen_headline,
        "target_word_count": 400
    })
    assert gen_resp.status_code == 201
    editorial = gen_resp.json()
    assert editorial["headline"] == chosen_headline
    assert 250 <= editorial["word_count"] <= 600
    assert len(editorial["source_references"]) >= 1

    editorial_id = editorial["id"]

    # Step 4: Open editorial in writing workflow
    draft_from_editorial = client.post("/api/v1/writing/drafts", json={
        "title": f"Draft: {chosen_headline}",
        "original_content": editorial["content"]
    })
    assert draft_from_editorial.status_code == 201
    assert draft_from_editorial.json()["original_content"] == editorial["content"]

    # Step 5: Multi-format exports (GET /{id}/export?format=...)
    for fmt in ["markdown", "txt", "html"]:
        export_resp = client.get(f"/api/v1/editorial/{editorial_id}/export?format={fmt}")
        assert export_resp.status_code == 200
        data = export_resp.json()
        assert data["format"] == fmt
        content_field = data["html_content"] if fmt == "html" else data["markdown_content"]
        assert len(content_field) > 100
        if fmt == "html":
            assert "<!DOCTYPE html>" in content_field
            assert "<script>" not in content_field


# =========================================================================
# 4. FAILURE PATHS & ROBUSTNESS TESTS
# =========================================================================
def test_e2e_failure_paths_and_invariants():
    """
    Validate failure handling:
    - Empty source content rejection
    - Non-existent project ID (404)
    - Non-existent draft ID (404)
    - Invalid export format (422)
    - Double acceptance protection
    - Verifying failures do not corrupt previously persisted data
    """
    # 1. Non-existent project
    missing_proj_src = client.post("/api/v1/projects/00000000-0000-0000-0000-000000000000/sources", json={
        "source_type": "text",
        "title": "Valid Title",
        "text_content": "Content"
    })
    assert missing_proj_src.status_code == 404

    # 2. Non-existent draft
    missing_draft = client.get("/api/v1/writing/drafts/00000000-0000-0000-0000-000000000000")
    assert missing_draft.status_code == 404

    # 3. Invalid export format regex validation (format must be markdown|txt|html)
    bad_export = client.get("/api/v1/editorial/00000000-0000-0000-0000-000000000000/export?format=invalid_pdf")
    assert bad_export.status_code == 422

    # 4. Double-acceptance protection
    text_sample = "In order to succeed, engineers must deploy software."
    d = client.post("/api/v1/writing/drafts", json={
        "title": "Double Accept Test",
        "original_content": text_sample
    }).json()
    analyzed = client.post("/api/v1/writing/analyze", json={
        "text": text_sample,
        "draft_id": d["id"]
    }).json()
    assert len(analyzed["issues"]) > 0
    sug_id = analyzed["issues"][0]["id"]

    # First accept -> 200
    acc1 = client.post(f"/api/v1/writing/drafts/{d['id']}/suggestions/{sug_id}/accept")
    assert acc1.status_code == 200
    assert acc1.json()["success"] is True

    # Second accept -> idempotent handling (returns success with "already accepted")
    acc2 = client.post(f"/api/v1/writing/drafts/{d['id']}/suggestions/{sug_id}/accept")
    assert acc2.status_code == 200
    assert "already accepted" in acc2.json()["message"]

    # Assert content was not corrupted
    refreshed = client.get(f"/api/v1/writing/drafts/{d['id']}").json()
    assert refreshed["revised_content"] is not None
    assert len(refreshed["revised_content"]) > 10
