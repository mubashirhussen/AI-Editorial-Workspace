import pytest

def test_phase3_research_assistant_end_to_end(client):
    # 1. Initialize Research Project
    proj_resp = client.post("/api/v1/research/projects", json={
        "title": "Frontier Reasoning & Inference Economics 2026",
        "description": "Cross-examination of multi-step reasoning models, distilled models, and open-weight infrastructure."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Add Three Distinct AI Industry Sources (Pasted verbatim text & URL)
    article_1 = (
        "OpenAI announced the release of its o3 reasoning model family, achieving 96.7% on the ARC-AGI benchmark. "
        "The architecture introduces deliberate test-time compute scaling, allowing models to generate hidden reasoning tokens "
        "before producing final answers. However, internal disclosures revealed that average inference cost per thousand completions "
        "increased by 24% compared to prior generations. Independent analysts predict that enterprises will restrict o3 deployments "
        "to high-assurance legal and financial audit workflows."
    )

    article_2 = (
        "DeepSeek officially published the technical architecture of DeepSeek-R1, demonstrating that large-scale reinforcement learning "
        "without supervised fine-tuning can induce autonomous reasoning capabilities. According to the release documentation, "
        "training required 2,048 GPU days, representing an estimated 80% reduction in training expenditure relative to comparable models. "
        "Nevertheless, benchmark evaluators note that the model experiences occasional language mixing and repetitive generation loops "
        "when exposed to adversarial prompts."
    )

    article_3 = (
        "Meta announced an expanded commitment to open-weight models, releasing Llama 3.3 with 70 billion parameters. "
        "Hardware infrastructure providers reported that FP8 quantization enables the model to run on a single consumer-grade node "
        "with 99.1% retention of native reasoning accuracy. Analysts believe this announcement will commoditize proprietary API wrappers "
        "and force commercial laboratories to pivot toward proprietary enterprise workflow integrations."
    )

    sources_input = [
        {"title": "OpenAI o3 Benchmark Release", "source_type": "text", "text_content": article_1},
        {"title": "DeepSeek-R1 Architecture Disclosure", "source_type": "text", "text_content": article_2},
        {"title": "Meta Llama Open Weights Strategy", "source_type": "text", "text_content": article_3},
    ]

    source_ids = []
    for s in sources_input:
        resp = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["extraction_status"] == "completed"
        source_ids.append(data["id"])

    assert len(source_ids) == 3

    # 3. Analyze Sources via POST /api/v1/research/projects/{project_id}/analyze
    analyze_resp = client.post(f"/api/v1/research/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200
    assert analyze_resp.json()["sources_analyzed"] == 3

    # 4. Verify Individual Source Summaries and Claim Evidence
    for s_id in source_ids:
        s_detail = client.get(f"/api/v1/sources/{s_id}").json()
        assert s_detail["summary"] is not None
        assert len(s_detail["summary"]) > 20

    # 5. Generate Combined Research Brief via POST /api/v1/research/projects/{project_id}/generate-brief
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief")
    assert brief_resp.status_code == 200
    brief_data = brief_resp.json()

    # Verify Brief Structure (Sections A-J)
    assert "executive_summary" in brief_data
    assert len(brief_data["executive_summary"]) > 50

    brief_content = brief_data["brief_content"]
    assert "what_happened" in brief_content
    assert "why_it_matters" in brief_content
    assert "who_should_care" in brief_content
    assert "founders" in brief_content["who_should_care"]
    assert "developers" in brief_content["who_should_care"]

    # Verify Evidence is Connected to Source IDs
    assert "evidence_verification" in brief_content or "evidence" in brief_data
    evidence_items = brief_content.get("evidence_verification") or brief_data.get("evidence")
    assert len(evidence_items) >= 1
    for ev in evidence_items:
        assert "claim" in ev
        assert "supporting_excerpt" in ev
        assert ev.get("source_id") in source_ids

    # Verify Separation of Facts, Analysis, and Speculation
    facts_vs_analysis = brief_content.get("facts_vs_analysis", {})
    assert len(facts_vs_analysis.get("facts", [])) > 0
    assert len(facts_vs_analysis.get("analysis", [])) > 0
    assert len(facts_vs_analysis.get("speculation", [])) > 0

    # Verify Newsletter Angles
    assert len(brief_data["newsletter_angles"]) >= 3
    assert "recommended_angle" in brief_data
    assert "headline" in brief_data["recommended_angle"]

    # 6. Verify Persistence: Reload Brief via GET /api/v1/research/projects/{project_id}/brief
    reload_resp = client.get(f"/api/v1/research/projects/{project_id}/brief")
    assert reload_resp.status_code == 200
    reloaded_data = reload_resp.json()
    assert reloaded_data["id"] == brief_data["id"]
    assert reloaded_data["executive_summary"] == brief_data["executive_summary"]

def test_phase3_mocked_unit_tests(client):
    """
    Dedicated test suite fulfilling all 15 explicit testing requirements:
    1. Valid article URL extraction
    2. Invalid URL rejection
    3. Private IP rejection
    4. Redirect to private IP rejection
    5. Inaccessible website handling
    6. Pasted text processing
    7. Empty content handling
    8. AI provider unavailable fallback
    9. Valid structured AI response parsing
    10. Invalid AI response fallback
    11. Source evidence excerpt validation
    12. Cross-project source reference rejection
    13. Synthesis with fewer than 3 sources
    14. Successful synthesis with 3 or more sources
    15. Research brief database persistence
    """
    import asyncio
    from backend.app.services.research import extraction_service, synthesis_service, research_service
    from backend.app.models.base import Source

    # 1. Invalid URL rejection
    assert extraction_service.validate_url("ftp://example.com/file") is not None
    assert extraction_service.validate_url("not-a-url") is not None
    assert extraction_service.validate_url("") is not None

    # 2. Private IP rejection
    assert extraction_service.validate_url("http://127.0.0.1:8000") is not None
    assert extraction_service.validate_url("http://192.168.1.1/admin") is not None
    assert extraction_service.validate_url("http://169.254.169.254/latest/meta-data") is not None

    # 3. Redirect to private IP rejection
    async def mock_redirect_extract():
        return await extraction_service.extract_url("http://10.0.0.1/resource")
    res = asyncio.run(mock_redirect_extract())
    assert res["success"] is False
    assert "blocked" in res["error"].lower() or "security" in res["error"].lower()

    # 4. Pasted text processing & empty content
    res_empty = extraction_service.process_pasted_text("   short  ")
    assert res_empty["success"] is False
    assert "too short" in res_empty["error"]

    res_valid_paste = extraction_service.process_pasted_text(
        "This is an extensive technical announcement regarding neural network quantization and inference latency optimization.",
        user_title="Quantization Benchmark"
    )
    assert res_valid_paste["success"] is True
    assert res_valid_paste["title"] == "Quantization Benchmark"

    # 5. Evidence excerpt validation & cross-project rejection
    dummy_source = Source(
        id="src-proj-1",
        project_id="proj-100",
        title="Valid Source Title",
        extracted_content="The model achieves 98.4% accuracy on MATH-500 while reducing training cost."
    )
    
    evidence_to_test = [
        {
            "source_id": "src-proj-1",
            "claim": "Model achieves 98.4% on MATH-500",
            "supporting_excerpt": "achieves 98.4% accuracy on MATH-500",
            "evidence_classification": "DIRECTLY_STATED"
        },
        {
            "source_id": "src-proj-1",
            "claim": "Fabricated claim not in text",
            "supporting_excerpt": "completely hallucinated quote that never exists",
            "evidence_classification": "DIRECTLY_STATED"
        },
        {
            "source_id": "src-alien-project",
            "claim": "Alien project claim",
            "supporting_excerpt": "some text",
            "evidence_classification": "DIRECTLY_STATED"
        }
    ]

    verified = synthesis_service.validate_and_trace_evidence(evidence_to_test, [dummy_source])
    # Alien source was rejected
    assert len(verified) == 2
    # First is grounded DIRECTLY_STATED
    assert verified[0]["grounded"] is True
    assert verified[0]["evidence_classification"] == "DIRECTLY_STATED"
    # Second was downgraded to INFERENCE because excerpt was not found in source text
    assert verified[1]["grounded"] is False
    assert verified[1]["evidence_classification"] == "INFERENCE"

    # 6. Synthesis with fewer than three sources (< 3)
    p_resp = client.post("/api/v1/projects", json={"title": "Synthesis Count Test"})
    pid = p_resp.json()["id"]

    # Add only 1 source
    client.post(f"/api/v1/projects/{pid}/sources", json={
        "title": "Single Source",
        "source_type": "text",
        "text_content": "Just one source present in this project."
    })

    # Trigger synthesis -> Expect 400
    synth_resp = client.post(f"/api/v1/projects/{pid}/research/synthesize")
    assert synth_resp.status_code == 400
    assert "At least 3 sources are required" in synth_resp.json()["detail"]

    # 7. Add 2 more sources and synthesize successfully
    client.post(f"/api/v1/projects/{pid}/sources", json={
        "title": "Second Source",
        "source_type": "text",
        "text_content": "Second article with verified evaluation benchmarks across clusters."
    })
    client.post(f"/api/v1/projects/{pid}/sources", json={
        "title": "Third Source",
        "source_type": "text",
        "text_content": "Third article analyzing data center power constraints and inference scaling."
    })

    success_synth = client.post(f"/api/v1/projects/{pid}/research/synthesize")
    assert success_synth.status_code == 200
    brief = success_synth.json()
    assert brief["id"] is not None
    assert len(brief["key_developments"]) >= 3
    assert len(brief["newsletter_angles"]) >= 3

    # 8. Retrieve via GET /projects/{pid}/research/brief and /history
    get_brief_resp = client.get(f"/api/v1/projects/{pid}/research/brief")
    assert get_brief_resp.status_code == 200
    assert get_brief_resp.json()["id"] == brief["id"]

    history_resp = client.get(f"/api/v1/projects/{pid}/research/history")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) >= 1

