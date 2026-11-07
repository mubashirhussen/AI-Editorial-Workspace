import io
import uuid
import pytest
from fastapi.testclient import TestClient

def get_auth_headers(client):
    unique_email = f"lead_editor_{uuid.uuid4().hex[:8]}@editorial.ai"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "StrongPassword123!",
            "full_name": "Lead Test Editor",
            "organization_name": "Editorial Intelligence Org"
        }
    )
    if reg_resp.status_code == 201:
        data = reg_resp.json()
        token = data.get("access_token")
        org_id = data.get("organization", {}).get("id")
        return {
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": org_id
        }
    # Fallback to empty for anonymous dev mode
    return {}

def test_draft_crud_and_duplication(client):
    headers = get_auth_headers(client)

    # 1. Create Draft
    create_payload = {
        "title": "Quantum Memory Architecture Review",
        "original_content": "Superconducting qubits require ultra-low thermal noise environments. In order to achieve fault tolerance, cryogenic packaging must be optimized.",
        "content_type": "technology",
        "target_audience": "Hardware engineers and architects",
        "tone": "Analytical, technical, rigorous",
        "desired_length": 600
    }
    res = client.post("/api/v1/writing/drafts", json=create_payload, headers=headers)
    assert res.status_code == 201
    draft_data = res.json()
    draft_id = draft_data["id"]
    assert draft_data["title"] == "Quantum Memory Architecture Review"
    assert draft_data["content_type"] == "technology"
    assert draft_data["target_audience"] == "Hardware engineers and architects"
    assert draft_data["word_count"] > 0

    # 2. Get Draft
    res = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == draft_id

    # 3. List Drafts with Search and Filter
    res = client.get("/api/v1/writing/drafts?search=Quantum", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert any(d["id"] == draft_id for d in items)

    # 4. Update Draft (Autosave / Edit)
    update_payload = {
        "title": "Quantum Memory Architecture & Control Review",
        "revised_content": "Superconducting qubits require ultra-low thermal noise. Cryogenic CMOS packaging achieves fault tolerance [1].",
        "status": "in_review"
    }
    res = client.put(f"/api/v1/writing/drafts/{draft_id}", json=update_payload, headers=headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "Quantum Memory Architecture & Control Review"
    assert updated["status"] == "in_review"

    # 5. Duplicate Draft
    res = client.post(f"/api/v1/writing/drafts/{draft_id}/duplicate", headers=headers)
    assert res.status_code == 201
    dupe = res.json()
    assert dupe["id"] != draft_id
    assert "Copy of" in dupe["title"]

    # 6. Delete Draft
    res = client.delete(f"/api/v1/writing/drafts/{dupe['id']}", headers=headers)
    assert res.status_code == 204

def test_generate_editorial_draft_from_research(client):
    headers = get_auth_headers(client)

    # 1. Setup a research project with 3 sources and brief
    p_res = client.post("/api/v1/research/projects", json={"title": "Frontier Attention Mechanisms"}, headers=headers)
    assert p_res.status_code in (200, 201)
    project_id = p_res.json()["id"]

    # Ingest 3 sources
    client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Sparse Attention & KV-Cache Optimization",
        "text_content": "Sparse attention reduces quadratic memory overhead in long-context transformer architectures. FlashAttention benchmarks report 3x throughput improvements."
    }, headers=headers)
    client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Multi-Head Latent Attention in DeepSeek",
        "text_content": "Multi-head latent attention compresses key-value representations into low-rank projections, mitigating memory bandwidth bottlenecks during generation."
    }, headers=headers)
    client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "source_type": "text",
        "title": "Hardware Accelerated Attention Kernels",
        "text_content": "Custom Triton and CUDA kernels fuse softmax and reduction operations directly in SRAM to avoid high-latency HBM roundtrips."
    }, headers=headers)

    # Generate research brief
    b_res = client.post(f"/api/v1/research/projects/{project_id}/generate-brief", headers=headers)
    assert b_res.status_code == 200
    brief_data = b_res.json()
    brief_id = brief_data.get("id")

    # 2. Call AI Editorial Draft Generator
    gen_req = {
        "project_id": project_id,
        "brief_id": brief_id,
        "content_type": "editorial_analysis",
        "target_audience": "Founders and AI architects",
        "tone": "Authoritative, analytical, objective",
        "desired_length": 800,
        "editorial_instructions": "Focus on memory bottlenecks and practical serving trade-offs."
    }
    res = client.post("/api/v1/writing/drafts/generate", json=gen_req, headers=headers)
    assert res.status_code == 201
    data = res.json()

    assert data["draft_id"] is not None
    assert len(data["headline"]) > 10
    assert len(data["content"]) > 100
    assert data["content_type"] == "editorial_analysis"
    assert data["word_count"] > 50
    assert len(data["sections"]) >= 3
    assert data["grounding_score"] >= 80.0
    assert len(data["key_takeaways"]) >= 2
    assert len(data["evidence_citations"]) >= 1

    # Verify persisted in database
    draft_check = client.get(f"/api/v1/writing/drafts/{data['draft_id']}", headers=headers)
    assert draft_check.status_code == 200
    assert draft_check.json()["title"] == data["headline"]

def test_selection_rewriting_operations(client):
    headers = get_auth_headers(client)

    sample_text = "In order to understand the model benchmarks, it is important to note that many tests were run."

    # Test improve_clarity
    res = client.post("/api/v1/writing/rewrite-selection", json={
        "selected_text": sample_text,
        "operation": "improve_clarity"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["operation"] == "improve_clarity"
    assert "in order to" not in data["rewritten_text"].lower()

    # Test strengthen_headline
    h_res = client.post("/api/v1/writing/rewrite-selection", json={
        "selected_text": "Reasoning Models and Inference Scaling",
        "operation": "strengthen_headline"
    }, headers=headers)
    assert h_res.status_code == 200
    assert len(h_res.json()["rewritten_text"]) > len("Reasoning Models and Inference Scaling")

    # Test preserve citations
    cite_sample = "FlashAttention v3 yields significant throughput gains [1] across H100 clusters."
    c_res = client.post("/api/v1/writing/rewrite-selection", json={
        "selected_text": cite_sample,
        "operation": "simplify_complex_sentences"
    }, headers=headers)
    assert c_res.status_code == 200
    assert "[1]" in c_res.json()["rewritten_text"]

def test_research_grounding_audit(client):
    headers = get_auth_headers(client)

    # Create draft with mixed grounded and ungrounded statements
    content = (
        "FlashAttention benchmarks report 3x throughput improvements [1]. "
        "Consequently, decoupled memory systems optimize GPU utilization. "
        "Alien spacecraft were detected landing in central Paris yesterday."
    )
    draft_res = client.post("/api/v1/writing/drafts", json={
        "title": "Grounding Audit Test Article",
        "original_content": content
    }, headers=headers)
    draft_id = draft_res.json()["id"]

    res = client.get(f"/api/v1/writing/drafts/{draft_id}/grounding-audit", headers=headers)
    assert res.status_code == 200
    audit = res.json()
    assert audit["draft_id"] == draft_id
    assert audit["total_claims"] >= 2
    assert audit["grounded_count"] >= 1
    assert audit["unsupported_count"] >= 1
    assert len(audit["actionable_recommendations"]) >= 1

def test_content_quality_and_readability_metrics(client):
    headers = get_auth_headers(client)

    text = (
        "In order to understand the architecture of frontier AI models, "
        "it is important to note that extensive benchmarking was conducted by the team. "
        "Basically, the system demonstrates high performance across standard benchmarks."
    )
    res = client.post("/api/v1/writing/analyze", json={"text": text}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    metrics = data["metrics"]

    assert metrics["word_count"] > 0
    assert metrics["sentence_count"] >= 2
    assert metrics["readability_score"] is not None
    assert metrics["flesch_kincaid_grade"] is not None
    assert metrics["automated_readability_index"] is not None
    assert metrics["gunning_fog_index"] is not None
    assert len(data["issues"]) > 0

def test_multi_format_export(client):
    headers = get_auth_headers(client)

    draft_res = client.post("/api/v1/writing/drafts", json={
        "title": "Export Test Draft Article",
        "original_content": "# Export Test\n\nThis is an editorial article with verified evidence [1].\n\n- Key point A\n- Key point B"
    }, headers=headers)
    draft_id = draft_res.json()["id"]

    # 1. Markdown Export
    res_md = client.get(f"/api/v1/writing/drafts/{draft_id}/export?format=markdown", headers=headers)
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert "title:" in res_md.text

    # 2. Plain Text Export
    res_txt = client.get(f"/api/v1/writing/drafts/{draft_id}/export?format=txt", headers=headers)
    assert res_txt.status_code == 200
    assert "text/plain" in res_txt.headers["content-type"]
    assert "EXPORT TEST" in res_txt.text

    # 3. Word DOCX Export
    res_docx = client.get(f"/api/v1/writing/drafts/{draft_id}/export?format=docx", headers=headers)
    assert res_docx.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in res_docx.headers["content-type"]
    assert len(res_docx.content) > 1000  # Valid docx binary

    # 4. HTML Export
    res_html = client.get(f"/api/v1/writing/drafts/{draft_id}/export?format=html", headers=headers)
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "<h1>Export Test Draft Article</h1>" in res_html.text

def test_version_history_and_restoration(client):
    headers = get_auth_headers(client)

    # 1. Create Draft
    d_res = client.post("/api/v1/writing/drafts", json={
        "title": "Version History Verification",
        "original_content": "Version 1 content."
    }, headers=headers)
    draft_id = d_res.json()["id"]

    # 2. Update to Version 2
    client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "revised_content": "Version 2 content with deeper analysis."
    }, headers=headers)

    # 3. Update to Version 3
    client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "revised_content": "Version 3 final publication content."
    }, headers=headers)

    # 4. Check versions list
    v_res = client.get(f"/api/v1/writing/drafts/{draft_id}/versions", headers=headers)
    assert v_res.status_code == 200
    versions = v_res.json()
    assert len(versions) >= 2

    # 5. Restore Version 1
    v1 = [v for v in versions if "Version 1" in v["content_snapshot"] or v["version_number"] == 1][0]
    r_res = client.post(f"/api/v1/writing/drafts/{draft_id}/restore/{v1['id']}", headers=headers)
    assert r_res.status_code == 200
    restore_data = r_res.json()
    assert "Version 1" in (restore_data.get("updated_content") or restore_data.get("content") or "")

    # 6. Verify current draft matches restored content
    current_draft = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers).json()
    assert "Version 1" in current_draft["revised_content"]


def test_all_14_selection_rewrite_operations(client):
    headers = get_auth_headers(client)

    operations = [
        "improve_clarity",
        "improve_readability",
        "fix_grammar",
        "improve_sentence_structure",
        "reduce_repetition",
        "improve_transitions",
        "simplify_language",
        "adjust_tone",
        "generate_headlines",
        "summarize_selection",
        "expand_content",
        "rewrite_selection",
        "improve_introduction",
        "improve_conclusion"
    ]

    base_text = "In order to evaluate the very unique performance [1], it is important to note that many tests were run."

    for op in operations:
        res = client.post("/api/v1/writing/rewrite-selection", json={
            "selected_text": base_text,
            "operation": op,
            "target_tone": "conversational" if op == "adjust_tone" else None
        }, headers=headers)
        assert res.status_code == 200, f"Failed for operation {op}: {res.text}"
        data = res.json()
        assert data["operation"] == op
        assert len(data["rewritten_text"]) > 0
        assert len(data["explanation"]) > 0
        # Critical Phase 7 requirement: preserve inline citation [1]
        assert "[1]" in data["rewritten_text"], f"Citation [1] was lost during {op}"


def test_editorial_style_profile_and_default_fallback(client):
    headers = get_auth_headers(client)

    # 1. Create a draft with jargon
    draft_res = client.post("/api/v1/writing/drafts", json={
        "title": "Corporate Synergy Analysis",
        "original_content": "This game-changer platform provides disruptive synergy across all departments. The end result is positive."
    }, headers=headers)
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # 2. Run style check with no custom profile created (should engage safe built-in default profile without 400)
    style_res = client.post(f"/api/v1/writing/drafts/{draft_id}/style-check", json={}, headers=headers)
    assert style_res.status_code == 200
    style_data = style_res.json()
    assert "style_score" in style_data
    assert style_data["style_score"] >= 0
    assert "suggestions" in style_data
    assert len(style_data["suggestions"]) > 0
    # Checks that avoided words like 'game-changer' or 'synergy' were flagged
    flagged_terms = [s.get("original_text", "").lower() for s in style_data["suggestions"]]
    assert any("synergy" in term or "game-changer" in term or "disruptive" in term for term in flagged_terms)


def test_suggestion_workflow_and_compare(client):
    headers = get_auth_headers(client)

    # 1. Create and analyze draft
    draft_res = client.post("/api/v1/writing/drafts", json={
        "title": "Editorial Workflow Draft",
        "original_content": "In order to optimize teh latency, extensive testing was conducted. Basically, results were very good."
    }, headers=headers)
    draft_id = draft_res.json()["id"]

    # 2. Run analysis
    an_res = client.post(f"/api/v1/writing/drafts/{draft_id}/analyze", headers=headers)
    assert an_res.status_code == 200
    analysis = an_res.json()
    assert len(analysis["issues"]) >= 1

    # 3. Retrieve suggestions
    sugg_res = client.get(f"/api/v1/writing/drafts/{draft_id}/suggestions", headers=headers)
    assert sugg_res.status_code == 200
    suggestions = sugg_res.json()
    assert len(suggestions) >= 1
    sugg_id = suggestions[0]["id"]

    # 4. Accept suggestion
    acc_res = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{sugg_id}/accept", headers=headers)
    assert acc_res.status_code == 200

    # 5. Check compare endpoint
    comp_res = client.get(f"/api/v1/writing/drafts/{draft_id}/compare", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["draft_id"] == draft_id
    assert comp_data["accepted_count"] >= 1


def test_multi_tenant_draft_isolation(client):
    # Org A User
    headers_a = get_auth_headers(client)

    # Org B User
    headers_b = get_auth_headers(client)

    # 1. Create Draft in Org A
    draft_res = client.post("/api/v1/writing/drafts", json={
        "title": "Org A Confidential Editorial",
        "original_content": "Confidential trade secrets and strategic roadmap."
    }, headers=headers_a)
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # 2. Org B User attempts to read Org A draft -> 404
    b_get = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers_b)
    assert b_get.status_code in (403, 404)

    # 3. Org B User attempts to update Org A draft -> 404
    b_put = client.put(f"/api/v1/writing/drafts/{draft_id}", json={
        "title": "Hacked Title"
    }, headers=headers_b)
    assert b_put.status_code in (403, 404)

    # 4. Org B User attempts to delete Org A draft -> 404
    b_del = client.delete(f"/api/v1/writing/drafts/{draft_id}", headers=headers_b)
    assert b_del.status_code in (403, 404)

