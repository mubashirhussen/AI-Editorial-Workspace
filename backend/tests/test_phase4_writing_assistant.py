import pytest

def test_all_six_writing_checks(client):
    """
    Validates all six deterministic checks:
    1. Long sentences (>25 words)
    2. Passive voice
    3. Filler words
    4. Technical jargon
    5. Repetition
    6. Complexity (long paragraph & low readability)
    """
    long_sentence = (
        "Furthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous subordinate clauses "
        "and technical parameters without providing the busy executive reader with a single moment of pause or cognitive respite, "
        "which obviously makes it exceedingly difficult to parse in a fast-paced editorial environment."
    )
    
    dense_paragraph = (
        "In order to comprehend the new architecture, it is important to note that tests were conducted by the research team. "
        "Due to the fact that retrieval-augmented generation relies on embeddings and vector database search, basically the system "
        "has the ability to process technical documentation with high throughput. Actually, fine-tuning an agentic workflow requires "
        "specialized model inference infrastructure. "
        "At the end of the day, enterprise deployment demands rigorous verification. Deployment requires continuous evaluation. "
        "Deployment also necessitates strict security guardrails. Deployment guarantees reliable uptime across all critical production clusters."
    )

    full_draft = f"{dense_paragraph}\n\n{long_sentence}"

    resp = client.post("/api/v1/writing/analyze", json={
        "text": full_draft,
        "title": "Comprehensive 6-Check Suite"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "issues" in data
    assert "metrics" in data

    categories = {issue["category"] for issue in data["issues"]}

    # Verify all 6 checks triggered
    assert "long_sentence" in categories, "Long sentence check failed"
    assert "passive_voice" in categories, "Passive voice check failed"
    assert "filler" in categories, "Filler words check failed"
    assert "jargon" in categories, "Technical jargon check failed"
    assert "repetition" in categories, "Repetition check failed"
    assert "complexity" in categories, "Complexity check failed"

    # Verify Metrics
    metrics = data["metrics"]
    assert metrics["word_count"] > 100
    assert metrics["sentence_count"] >= 5
    assert metrics["paragraph_count"] >= 2
    assert metrics["average_sentence_length"] > 15
    assert metrics["reading_time_minutes"] > 0
    assert metrics["readability_score"] is not None
    assert "diagnostic" in metrics["readability_note"].lower()

def test_suggestion_workflow_and_original_preservation(client):
    """
    Tests suggestion creation, individual accept, reject, accept-all,
    immutable original preservation, and comparison diffs.
    """
    original_text = (
        "In order to optimize operations, the benchmark was published by Anthropic. "
        "Basically, vector database systems allow rapid retrieval."
    )

    # 1. Analyze and create draft
    analyze_resp = client.post("/api/v1/writing/analyze", json={
        "text": original_text,
        "title": "Workflow & Preservation Test"
    })
    assert analyze_resp.status_code == 200
    draft_id = analyze_resp.json()["draft_id"]
    issues = analyze_resp.json()["issues"]
    assert len(issues) >= 2

    # Identify individual issues
    filler_issue = next(i for i in issues if i["category"] == "filler" and "in order to" in i["original_text"].lower())
    passive_issue = next(i for i in issues if i["category"] == "passive_voice")

    # 2. Accept filler issue ("In order to" -> "to")
    accept_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{filler_issue['id']}/accept")
    assert accept_resp.status_code == 200
    revised_1 = accept_resp.json()["revised_content"]
    assert "In order to" not in revised_1
    assert "to optimize operations" in revised_1.lower()

    # Verify original draft in database remains 100% identical to original input
    draft_state_1 = client.get(f"/api/v1/writing/drafts/{draft_id}").json()
    assert draft_state_1["original_content"] == original_text
    assert draft_state_1["revised_content"] == revised_1

    # 3. Reject passive issue
    reject_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{passive_issue['id']}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
    assert reject_resp.json()["revised_content"] == revised_1 # Unchanged on reject

    # 4. Accept All Remaining Suggestions
    accept_all_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/accept-all")
    assert accept_all_resp.status_code == 200
    final_revised = accept_all_resp.json()["revised_content"]

    # Original must still be untouched!
    draft_final = client.get(f"/api/v1/writing/drafts/{draft_id}").json()
    assert draft_final["original_content"] == original_text
    assert draft_final["revised_content"] == final_revised

    # 5. Check Comparison Endpoint
    compare_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert compare_resp.status_code == 200
    comp_data = compare_resp.json()
    assert comp_data["draft_id"] == draft_id
    assert comp_data["original_content"] == original_text
    assert comp_data["revised_content"] == final_revised
    assert comp_data["accepted_count"] >= 1
    assert comp_data["rejected_count"] >= 1

def test_safe_replacement_with_citations_and_ambiguity(client):
    """
    Tests that sentence replacements preserve inline citations [1], [2]
    and safely reject ambiguous multi-match targets without corrupting text.
    """
    from backend.app.utils.text_processing import replace_text_safely

    doc_with_citations = (
        "Enterprise adoption accelerated this quarter [1]. "
        "In order to scale inference pipelines, engineers deployed quantization [2]."
    )

    # Replace filler
    new_doc, success, err = replace_text_safely(doc_with_citations, "In order to", "To")
    assert success is True
    assert err is None
    # Citations must be strictly preserved
    assert "[1]" in new_doc
    assert "[2]" in new_doc
    assert "To scale inference pipelines" in new_doc

    # Ambiguous empty target
    _, fail_empty, err_empty = replace_text_safely(doc_with_citations, "", "Replace")
    assert fail_empty is False
    assert err_empty is not None

    # Missing target
    _, fail_missing, err_missing = replace_text_safely(doc_with_citations, "Nonexistent phrase 123", "Replace")
    assert fail_missing is False
    assert "could not be uniquely matched" in err_missing

def test_phase4_new_endpoints(client):
    """
    Directly tests all Phase 4 specific endpoints:
    - POST /api/v1/writing/drafts/{draft_id}/analyze
    - GET  /api/v1/writing/drafts/{draft_id}/analysis
    - GET  /api/v1/writing/drafts/{draft_id}/metrics
    - GET  /api/v1/writing/drafts/{draft_id}/suggestions
    - POST /api/v1/writing/suggestions/{suggestion_id}/accept
    - POST /api/v1/writing/suggestions/{suggestion_id}/reject
    - POST /api/v1/writing/drafts/{draft_id}/accept-all
    - GET  /api/v1/writing/drafts/{draft_id}/compare
    """
    raw_content = "In order to comprehend model evaluation, it is important to note that tests were conducted by the research team."
    draft_resp = client.post("/api/v1/writing/drafts", json={
        "title": "Phase 4 Specific Endpoints Draft",
        "original_content": raw_content
    })
    assert draft_resp.status_code == 201
    draft_id = draft_resp.json()["id"]

    # Analyze via POST /drafts/{draft_id}/analyze
    analyze_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis_data = analyze_resp.json()
    assert len(analysis_data["issues"]) >= 2

    # GET /drafts/{draft_id}/analysis
    get_analysis_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/analysis")
    assert get_analysis_resp.status_code == 200

    # GET /drafts/{draft_id}/metrics
    get_metrics_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/metrics")
    assert get_metrics_resp.status_code == 200
    assert get_metrics_resp.json()["word_count"] > 10

    # GET /drafts/{draft_id}/suggestions
    suggs_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/suggestions")
    assert suggs_resp.status_code == 200
    suggs = suggs_resp.json()
    assert len(suggs) >= 2

    sugg_1 = suggs[0]["id"]
    sugg_2 = suggs[1]["id"]

    # POST /suggestions/{suggestion_id}/accept (direct route)
    acc_resp = client.post(f"/api/v1/writing/suggestions/{sugg_1}/accept")
    assert acc_resp.status_code == 200
    assert acc_resp.json()["success"] is True

    # POST /suggestions/{suggestion_id}/reject (direct route)
    rej_resp = client.post(f"/api/v1/writing/suggestions/{sugg_2}/reject")
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"].lower() == "rejected"

    # POST /drafts/{draft_id}/accept-all
    accept_all_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/accept-all")
    assert accept_all_resp.status_code == 200

    # GET /drafts/{draft_id}/compare
    compare_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert compare_resp.status_code == 200
    comp_data = compare_resp.json()
    assert comp_data["original_content"] == raw_content
    assert comp_data["draft_id"] == draft_id

