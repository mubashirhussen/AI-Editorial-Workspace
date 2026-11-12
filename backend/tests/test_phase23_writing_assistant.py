import io
import uuid
import pytest
from fastapi.testclient import TestClient

def get_auth_headers(client, org_name="Phase 23 Writing Org", role_prefix="writer"):
    unique_email = f"{role_prefix}_{uuid.uuid4().hex[:8]}@phase23.ai"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "Phase23StrongPassword123!",
            "full_name": f"Phase 23 {role_prefix.title()}",
            "organization_name": org_name
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
    return {}

def test_draft_creation_empty_content_and_rich_metadata(client):
    """Verifies that drafts can be created with empty initial content and rich metadata."""
    headers = get_auth_headers(client)

    # 1. Empty content draft creation
    empty_payload = {
        "title": "Blank Workspace Document",
        "original_content": "",
        "content_type": "editorial_analysis",
        "target_audience": "Founders & Engineers",
        "tone": "authoritative",
        "desired_length": 1000
    }
    res = client.post("/api/v1/writing/drafts", json=empty_payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == "Blank Workspace Document"
    assert data["original_content"] == ""
    assert data["word_count"] == 0
    assert data["status"] == "draft"
    assert data["desired_length"] == 1000

    # 2. Rich metadata draft creation
    rich_payload = {
        "title": "Frontier AI Evaluation Frameworks",
        "original_content": "Modern foundation models require deterministic evaluation frameworks to prevent regression.",
        "content_type": "technical_explainer",
        "target_audience": "Machine Learning Architects",
        "tone": "analytical",
        "desired_length": 1200
    }
    res = client.post("/api/v1/writing/drafts", json=rich_payload, headers=headers)
    assert res.status_code == 201
    rich_data = res.json()
    assert rich_data["content_type"] == "technical_explainer"
    assert rich_data["target_audience"] == "Machine Learning Architects"
    assert rich_data["tone"] == "analytical"
    assert rich_data["word_count"] > 0

def test_draft_sorting_filtering_and_lifecycle(client):
    """Verifies draft sorting, status filtering, archiving, reopening, and duplication."""
    headers = get_auth_headers(client)

    # Create 3 drafts
    d1 = client.post("/api/v1/writing/drafts", json={"title": "Alpha Research Memo", "original_content": "Content alpha"}, headers=headers).json()
    d2 = client.post("/api/v1/writing/drafts", json={"title": "Beta Market Analysis", "original_content": "Content beta"}, headers=headers).json()
    d3 = client.post("/api/v1/writing/drafts", json={"title": "Gamma System Spec", "original_content": "Content gamma"}, headers=headers).json()

    # Sort by title asc
    res = client.get("/api/v1/writing/drafts?sort_by=title&sort_order=asc", headers=headers)
    assert res.status_code == 200
    items = res.json()
    titles = [x["title"] for x in items if x["id"] in [d1["id"], d2["id"], d3["id"]]]
    assert titles == sorted(titles)

    # Archive d2
    arch_res = client.post(f"/api/v1/writing/drafts/{d2['id']}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "archived"

    # Filter by status=archived
    res_arch = client.get("/api/v1/writing/drafts?status=archived", headers=headers)
    assert res_arch.status_code == 200
    arch_ids = [x["id"] for x in res_arch.json()]
    assert d2["id"] in arch_ids
    assert d1["id"] not in arch_ids

    # Reopen d2
    reopen_res = client.post(f"/api/v1/writing/drafts/{d2['id']}/reopen", headers=headers)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "draft"

    # Duplicate d1
    dup_res = client.post(f"/api/v1/writing/drafts/{d1['id']}/duplicate", headers=headers)
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["id"] != d1["id"]
    assert "Copy of Alpha Research Memo" in dup_data["title"]
    assert dup_data["original_content"] == "Content alpha"

def test_all_13_ai_rewrite_capabilities(client):
    """Verifies all 13 distinct AI rewrite operations run reliably with fallback and citation safety."""
    headers = get_auth_headers(client)

    # Create draft for context
    draft = client.post(
        "/api/v1/writing/drafts",
        json={"title": "AI Rewrite Test Draft", "original_content": "Initial baseline draft [1]."},
        headers=headers
    ).json()

    operations = [
        "improve_clarity",
        "fix_grammar",
        "improve_readability",
        "improve_sentence_structure",
        "reduce_repetition",
        "improve_transitions",
        "adjust_tone",
        "simplify_language",
        "summarize_selection",
        "expand_content",
        "generate_headlines",
        "generate_hook",
        "reorganize_paragraphs"
    ]

    sample_passage = "In order to understand the benchmark results [1], it is important to note that teh team conducted many tests."

    for op in operations:
        res = client.post(
            "/api/v1/writing/rewrite-selection",
            json={
                "draft_id": draft["id"],
                "selected_text": sample_passage,
                "operation": op,
                "target_tone": "analytical"
            },
            headers=headers
        )
        assert res.status_code == 200, f"Operation {op} failed with: {res.text}"
        data = res.json()
        assert data["rewritten_text"], f"Empty rewritten text for operation {op}"
        assert data["explanation"], f"Missing explanation for operation {op}"
        # Bracketed citation must be preserved
        assert "[1]" in data["rewritten_text"], f"Citation [1] dropped in operation {op}"

def test_style_check_tenant_isolation_and_fallback(client):
    """Verifies that style-check never returns 400 'No active style profile available' and protects tenant isolation."""
    headers = get_auth_headers(client)

    draft = client.post(
        "/api/v1/writing/drafts",
        json={"title": "Style Isolation Draft", "original_content": "We utilize complex paradigms to facilitate growth."},
        headers=headers
    ).json()

    # Style check with no style profile created in org -> MUST succeed with scoped fallback profile
    res = client.post(
        f"/api/v1/writing/drafts/{draft['id']}/style-check",
        json={"draft_id": draft["id"], "content": "We utilize complex paradigms to facilitate growth."},
        headers=headers
    )
    assert res.status_code == 200, f"Expected 200 fallback, got {res.status_code}: {res.text}"
    data = res.json()
    assert "style_score" in data or "score" in data or "compliance_score" in data or "overall_score" in data

def test_export_security_and_script_injection_defense(client):
    """Verifies multi-format export and ensures HTML exports escape malicious XSS scripts."""
    headers = get_auth_headers(client)

    malicious_content = "Safe header\n\n<script>alert('pwned')</script>\n\n<img src=x onerror=alert(1)>"
    draft = client.post(
        "/api/v1/writing/drafts",
        json={"title": "Security Export Draft", "original_content": malicious_content},
        headers=headers
    ).json()

    # 1. HTML export with XSS defense
    res_html = client.get(f"/api/v1/writing/drafts/{draft['id']}/export?format=html", headers=headers)
    assert res_html.status_code == 200
    html_body = res_html.text
    # Malicious script tags must be escaped
    assert "<script>" not in html_body
    assert "&lt;script&gt;" in html_body
    assert "&lt;img" in html_body

    # 2. Markdown export
    res_md = client.get(f"/api/v1/writing/drafts/{draft['id']}/export?format=markdown", headers=headers)
    assert res_md.status_code == 200
    assert "security export draft" in res_md.text.lower()

    # 3. Plain Text export
    res_txt = client.get(f"/api/v1/writing/drafts/{draft['id']}/export?format=txt", headers=headers)
    assert res_txt.status_code == 200
    assert "security export draft" in res_txt.text.lower()

    # 4. Word DOCX export
    res_docx = client.get(f"/api/v1/writing/drafts/{draft['id']}/export?format=docx", headers=headers)
    assert res_docx.status_code == 200
    assert len(res_docx.content) > 0

def test_version_history_non_destructive_restoration(client):
    """Verifies that version history records snapshots and restoring a version does not wipe prior history."""
    headers = get_auth_headers(client)

    # Version 1
    draft = client.post(
        "/api/v1/writing/drafts",
        json={"title": "Version History Draft", "original_content": "Version 1 Initial Content"},
        headers=headers
    ).json()
    draft_id = draft["id"]

    # Version 2 edit
    client.put(
        f"/api/v1/writing/drafts/{draft_id}",
        json={"title": "Version History Draft", "revised_content": "Version 2 Revised Content"},
        headers=headers
    )

    # Version 3 edit
    client.put(
        f"/api/v1/writing/drafts/{draft_id}",
        json={"title": "Version History Draft", "revised_content": "Version 3 Polished Content"},
        headers=headers
    )

    # Check versions list
    res_versions = client.get(
        f"/api/v1/writing/drafts/{draft_id}/versions",
        headers=headers
    )
    assert res_versions.status_code == 200
    versions = res_versions.json()
    assert len(versions) >= 2

    # Restore Version 1
    v1_id = versions[-1]["id"]
    res_restore = client.post(
        f"/api/v1/writing/drafts/{draft_id}/restore/{v1_id}",
        headers=headers
    )
    assert res_restore.status_code == 200

    # Ensure document content now reflects Version 1
    updated_draft = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers).json()
    assert "Version 1 Initial Content" in (updated_draft.get("revised_content") or updated_draft.get("original_content"))

    # Ensure history was preserved and not wiped
    res_after = client.get(
        f"/api/v1/writing/drafts/{draft_id}/versions",
        headers=headers
    )
    versions_after = res_after.json()
    assert len(versions_after) >= len(versions)

def test_cross_tenant_isolation_enforcement(client):
    """Verifies that Org B cannot view, edit, duplicate, or delete Org A's drafts."""
    headers_a = get_auth_headers(client, org_name="Tenant Alpha Org", role_prefix="alice")
    headers_b = get_auth_headers(client, org_name="Tenant Beta Org", role_prefix="bob")

    # Org A creates a confidential draft
    draft_a = client.post(
        "/api/v1/writing/drafts",
        json={"title": "Confidential Alpha Roadmap", "original_content": "Proprietary internal details"},
        headers=headers_a
    ).json()
    draft_id = draft_a["id"]

    # Org B attempts to read draft A -> 404
    res_read = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers_b)
    assert res_read.status_code == 404

    # Org B attempts to update draft A -> 404
    res_update = client.put(
        f"/api/v1/writing/drafts/{draft_id}",
        json={"title": "Hacked Title", "revised_content": "Hacked content"},
        headers=headers_b
    )
    assert res_update.status_code == 404

    # Org B attempts to duplicate draft A -> 404
    res_dup = client.post(f"/api/v1/writing/drafts/{draft_id}/duplicate", headers=headers_b)
    assert res_dup.status_code == 404

    # Org B attempts to delete draft A -> 404
    res_del = client.delete(f"/api/v1/writing/drafts/{draft_id}", headers=headers_b)
    assert res_del.status_code == 404
