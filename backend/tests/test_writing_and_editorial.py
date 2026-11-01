import pytest

def test_writing_analysis_and_metrics(client):
    sample_text = (
        "In order to understand the new model, it is important to note that a large number of tests were conducted by the engineering team. "
        "Due to the fact that retrieval-augmented generation relies on embeddings and vector database search, basically the system has the ability to process documents rapidly. "
        "Furthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous clauses and conceptual pivots without providing the reader with a moment of pause or cognitive respite, which obviously makes it exceedingly difficult to parse in a high-speed editorial environment."
    )

    resp = client.post("/api/v1/writing/analyze", json={
        "text": sample_text,
        "title": "Editorial Test Draft"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert data["metrics"]["word_count"] > 30
    assert data["metrics"]["readability_score"] is not None

    # Verify at least 3 categories detected (filler, jargon, long_sentence, passive_voice)
    categories = {issue["category"] for issue in data["issues"]}
    assert "filler" in categories
    assert "jargon" in categories
    assert "long_sentence" in categories

def test_suggestion_accept_and_reject(client):
    original_text = "In order to streamline operations, the report was published by OpenAI."
    
    # 1. Analyze and create draft
    analyze_resp = client.post("/api/v1/writing/analyze", json={
        "text": original_text,
        "title": "Accept/Reject Test"
    })
    draft_id = analyze_resp.json()["draft_id"]
    issues = analyze_resp.json()["issues"]
    assert len(issues) >= 1

    filler_issue = next((i for i in issues if i["category"] == "filler"), None)
    assert filler_issue is not None

    # 2. Accept filler suggestion
    accept_resp = client.post(f"/api/v1/writing/drafts/{draft_id}/suggestions/{filler_issue['id']}/accept")
    assert accept_resp.status_code == 200
    revised = accept_resp.json()["revised_content"]
    assert "In order to" not in revised
    assert "to streamline operations" in revised.lower()

    # 3. Verify original draft is untouched!
    get_draft_resp = client.get(f"/api/v1/writing/drafts/{draft_id}")
    assert get_draft_resp.status_code == 200
    draft_data = get_draft_resp.json()
    assert draft_data["original_content"] == original_text
    assert draft_data["revised_content"] != original_text

    # 4. Compare draft
    comp_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/compare")
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["accepted_count"] >= 1

def test_editorial_generation_and_export(client):
    # Create project and 3 sources
    p_resp = client.post("/api/v1/research/projects", json={"title": "AI Hardware Superclusters"})
    p_id = p_resp.json()["id"]

    for i in range(3):
        client.post(f"/api/v1/research/projects/{p_id}/sources", json={
            "title": f"Source #{i+1}",
            "source_type": "text",
            "text_content": f"Hardware cluster {i+1} operates with 10,000 GPUs delivering peak FP8 throughput and 99.9% uptime according to independent auditors."
        })

    client.post(f"/api/v1/research/projects/{p_id}/generate-brief")

    # Generate editorial
    gen_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": p_id
    })
    assert gen_resp.status_code == 201
    editorial_data = gen_resp.json()
    assert editorial_data["headline"] is not None
    assert editorial_data["word_count"] > 100
    editorial_id = editorial_data["id"]

    # Export editorial
    export_resp = client.get(f"/api/v1/editorial/{editorial_id}/export")
    assert export_resp.status_code == 200
    export_data = export_resp.json()
    assert "markdown_content" in export_data
    assert "plain_text_content" in export_data
    assert "# " in export_data["markdown_content"]

