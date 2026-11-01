import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models.base import ResearchProject, EditorialOutput, WritingDraft

def test_phase7_complete_16_step_e2e_workflow(client):
    """
    Executes the comprehensive 16-step integration workflow covering:
    Project -> Ingestion -> Extraction -> Analysis -> Synthesis -> Angles ->
    Drafting -> Writing Quality Audit -> Suggestion Accept -> Suggestion Reject ->
    Immutability Verification -> Diff Comparison -> Save -> Persistence Reload -> Export.
    """

    # TEST 1: Create a research project
    p_resp = client.post("/api/v1/research/projects", json={
        "title": "Autonomous Agent Infrastructure & Security Benchmarks",
        "description": "Comprehensive investigation into sandboxing, tool verification, and latency bounds."
    })
    assert p_resp.status_code == 201
    project = p_resp.json()
    project_id = project["id"]
    assert project["title"] == "Autonomous Agent Infrastructure & Security Benchmarks"

    # TEST 2: Add three valid source texts/URLs
    s1_text = (
        "OpenAI announced updated evaluation benchmarks for autonomous software agents, reporting a 31% reduction "
        "in out-of-bounds tool calls when constrained by deterministic validation middleware. "
        "However, multi-step execution latency averaged 4.8 seconds per turn. "
        "Security researchers predict that unauthenticated model tool execution will emerge as the primary enterprise vector in 2026."
    )
    s2_text = (
        "Anthropic published findings on constitutional agent orchestration, demonstrating that hierarchical supervisors "
        "mitigate 94% of prompt injection attempts in customer-facing workflows. "
        "Training costs for the supervisor architecture totaled $1.2 million across dedicated compute clusters according to internal disclosures. "
        "Independent evaluators noted that reasoning latency increases by 18% when multi-tier supervision is active."
    )
    s3_text = (
        "Enterprise survey data from 400 engineering directors indicated that 72% have deployed retrieval-augmented generation systems, "
        "while 55% are actively piloting tool-use agents with write permissions. "
        "Hardware providers reported that FP8 quantization allows hosting these workflows on commodity server racks with 99.4% uptime. "
        "Analysts believe that software wrappers lacking domain-specific verification layers will face rapid pricing commoditization."
    )

    sources_payload = [
        {"title": "OpenAI Agent Tool Benchmark", "source_type": "text", "text_content": s1_text},
        {"title": "Anthropic Supervision Report", "source_type": "text", "text_content": s2_text},
        {"title": "Enterprise Agent Security Survey", "source_type": "text", "text_content": s3_text},
    ]

    source_ids = []
    for s in sources_payload:
        s_resp = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
        assert s_resp.status_code == 201
        source_ids.append(s_resp.json()["id"])
    assert len(source_ids) == 3

    # TEST 3: Extract source content
    for s_id in source_ids:
        ext_resp = client.post(f"/api/v1/sources/{s_id}/extract")
        assert ext_resp.status_code == 200
        assert ext_resp.json()["extraction_status"] == "completed"
        assert len(ext_resp.json()["extracted_content"]) > 50

    # TEST 4: Generate source summaries
    analyze_resp = client.post(f"/api/v1/research/projects/{project_id}/analyze")
    assert analyze_resp.status_code == 200
    assert analyze_resp.json()["sources_analyzed"] == 3

    for s_id in source_ids:
        s_data = client.get(f"/api/v1/sources/{s_id}").json()
        assert s_data["summary"] is not None
        assert len(s_data["summary"]) > 20

    # TEST 5: Generate evidence-backed research brief
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief")
    assert brief_resp.status_code == 200
    brief = brief_resp.json()
    assert "executive_summary" in brief
    assert len(brief["executive_summary"]) > 50

    # TEST 6: Verify facts, analysis, and speculation
    brief_content = brief["brief_content"]
    facts_vs_analysis = brief_content["facts_vs_analysis"]
    assert len(facts_vs_analysis["facts"]) > 0
    assert len(facts_vs_analysis["analysis"]) > 0
    assert len(facts_vs_analysis["speculation"]) > 0

    # Verify evidence items are strictly mapped to source IDs
    evidence_items = brief["evidence"]
    assert len(evidence_items) > 0
    for ev in evidence_items:
        assert ev["source_id"] in source_ids
        assert len(ev["supporting_excerpt"]) > 10

    # TEST 7: Generate newsletter angles
    angles = brief["newsletter_angles"]
    assert len(angles) >= 3
    for a in angles:
        assert "headline" in a
        assert "target_audience" in a
        assert "angle_pitch" in a
    selected_angle = brief["recommended_angle"]["headline"]
    assert selected_angle is not None

    # TEST 8: Create newsletter draft from angle
    gen_editorial_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": project_id,
        "angle_headline": selected_angle
    })
    assert gen_editorial_resp.status_code == 201
    editorial = gen_editorial_resp.json()
    editorial_id = editorial["id"]
    draft_id = editorial["draft_id"]
    assert editorial["headline"] == selected_angle
    assert editorial["word_count"] >= 150
    assert len(editorial["source_references"]) >= 1

    # TEST 9: Analyze draft through Writing Assistant
    writing_audit_resp = client.post("/api/v1/writing/analyze", json={
        "draft_id": draft_id,
        "text": editorial["content"],
        "title": editorial["headline"]
    })
    assert writing_audit_resp.status_code == 200
    audit_data = writing_audit_resp.json()
    issues = audit_data["issues"]
    assert len(issues) >= 2
    assert audit_data["metrics"]["word_count"] > 100

    # Pick two distinct issues for accept & reject
    issue_to_accept = issues[0]
    issue_to_reject = issues[1]

    original_draft_before = client.get(f"/api/v1/writing/drafts/{draft_id}").json()["original_content"]

    # TEST 10: Accept one suggestion
    accept_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{issue_to_accept['id']}/accept")
    assert accept_resp.status_code == 200
    revised_after_accept = accept_resp.json()["revised_content"]

    # TEST 11: Reject another suggestion
    reject_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{issue_to_reject['id']}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
    assert reject_resp.json()["revised_content"] == revised_after_accept

    # TEST 12: Verify original content remains completely unchanged
    draft_after = client.get(f"/api/v1/writing/drafts/{draft_id}").json()
    assert draft_after["original_content"] == original_draft_before
    assert draft_after["revised_content"] != original_draft_before or issue_to_accept["suggested_rewrite"] in original_draft_before

    # TEST 13: Compare original and revised versions
    comp_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["accepted_count"] >= 1
    assert comp_data["rejected_count"] >= 1
    assert comp_data["original_content"] == original_draft_before
    assert comp_data["revised_content"] == revised_after_accept

    # TEST 14: Save final article
    save_resp = client.put(f"/api/v1/editorial/{editorial_id}", json={
        "headline": f"[Final Approved] {selected_angle}",
        "content": revised_after_accept,
        "status": "published"
    })
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "published"
    assert save_resp.json()["headline"] == f"[Final Approved] {selected_angle}"

    # TEST 15: Reload application & verify database persistence
    reloaded_editorial = client.get(f"/api/v1/editorial/{editorial_id}").json()
    assert reloaded_editorial["id"] == editorial_id
    assert reloaded_editorial["status"] == "published"
    assert reloaded_editorial["content"] == revised_after_accept

    # TEST 16: Export Markdown article
    export_resp = client.get(f"/api/v1/editorial/{editorial_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "markdown_content" in export_data
    assert "plain_text_content" in export_data
    assert f"# [Final Approved] {selected_angle}" in export_data["markdown_content"]
    assert "## References & Verified Sources" in export_data["markdown_content"]

