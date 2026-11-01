"""
Phase 23 - Human-in-the-Loop Editorial Review & Workflow Test Suite
Verifies:
1. Valid workflow lifecycle transitions (DRAFT -> HUMAN_REVIEW_PENDING -> APPROVED -> FINALIZED)
2. Enforced finalization restrictions (unapproved content cannot be finalized)
3. Immutability of finalized content (cannot revise or re-approve once FINALIZED)
4. Meaningful feedback enforcement on change requests (Pydantic min length)
5. Review and Comment lifecycle (create comment, resolve comment)
6. Automated AI Pre-Review quality evaluation without premature approval
7. Version-aware revision management and original content preservation
8. Real database-backed dashboard statistics
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.schemas.editorial_review import WorkflowStatus

def _create_project_with_sources_and_editorial(client, project_title="Autonomous Agent Workspaces"):
    proj_resp = client.post("/api/v1/projects", json={
        "title": project_title,
        "description": "Evaluation of agentic developer tooling"
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    for i in range(1, 4):
        src_resp = client.post(f"/api/v1/projects/{project_id}/sources", json={
            "title": f"Agentic IDE Disclosures #{i}",
            "url": f"https://example.com/agentic-ide-{i}",
            "text_content": (
                f"Engineering team #{i} reported a 40% reduction in turnaround time for bugfixes. "
                "Autonomous multi-file editing is verified across isolated containers."
            )
        })
        assert src_resp.status_code == 201

    # Brief generation
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief")
    assert brief_resp.status_code == 200

    # Generate editorial
    gen_resp = client.post("/api/v1/editorial/generate", json={
        "project_id": project_id,
        "headline": f"The Strategic Shift in {project_title}",
        "min_words": 300,
        "max_words": 500
    })
    assert gen_resp.status_code == 201
    editorial_data = gen_resp.json()
    return project_id, editorial_data["id"]

def test_phase23_workflow_lifecycle_complete_journey(client):
    """
    Tests complete lifecycle:
    1. Create Project, Sources, Brief & Generate Editorial
    2. Run AI Pre-Review (AI checks pass, status moves to HUMAN_REVIEW_PENDING)
    3. Request Changes with constructive feedback (CHANGES_REQUESTED)
    4. Submit Revision (preserves original content, increments version, back to HUMAN_REVIEW_PENDING)
    5. Human Approval (APPROVED)
    6. Finalization (FINALIZED and locked)
    """
    project_id, editorial_id = _create_project_with_sources_and_editorial(client, "Agentic Workspaces Journey")

    # Check initial status
    ed_init = client.get(f"/api/v1/editorial/{editorial_id}")
    assert ed_init.status_code == 200
    assert ed_init.json()["status"].lower() in ["draft_created", "draft"]

    # 1. Automated AI Pre-Review
    ai_rev_resp = client.post(f"/api/v1/editorial/{editorial_id}/ai-review")
    assert ai_rev_resp.status_code == 200
    ai_review = ai_rev_resp.json()
    assert "word_count_compliance" in ai_review
    assert "readability_grade" in ai_review
    assert "writing_issues_count" in ai_review
    assert ai_review["ai_verdict"] in ["READY_FOR_HUMAN_REVIEW", "FLAGGED_WITH_WARNINGS"]

    # Verify status transitioned to HUMAN_REVIEW_PENDING, NOT APPROVED!
    ed_check = client.get(f"/api/v1/editorial/{editorial_id}")
    assert ed_check.status_code == 200
    assert ed_check.json()["status"] == WorkflowStatus.HUMAN_REVIEW_PENDING

    # 2. Human Reviewer Requests Changes
    # Edge case: Empty / too short feedback must fail validation (HTTP 422)
    short_resp = client.post(f"/api/v1/editorial/{editorial_id}/request-changes", json={
        "reviewer_name": "Senior Editor",
        "feedback": "Bad"  # under 10 chars
    })
    assert short_resp.status_code == 422

    # Valid change request
    chg_resp = client.post(f"/api/v1/editorial/{editorial_id}/request-changes", json={
        "reviewer_name": "Senior Editor",
        "feedback": "Please elaborate on unit economics for startup founders in the strategic analysis section."
    })
    assert chg_resp.status_code == 200
    assert chg_resp.json()["status"] == WorkflowStatus.CHANGES_REQUESTED

    # 3. Author Submits Revision
    rev_text = ed_check.json()["content"] + "\n\n### Extended Unit Economics\nFor startup founders, self-hosted distillation cuts token operational expenses by 80%."
    rev_resp = client.put(f"/api/v1/editorial/{editorial_id}/revision", json={
        "revised_content": rev_text,
        "headline": "The Strategic Shift in Agentic Workspaces (Updated)"
    })
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["version"] == 2
    assert rev_data["status"] == WorkflowStatus.HUMAN_REVIEW_PENDING
    assert rev_data["diff_summary"]["added_lines"] > 0

    # 4. Human Approval
    app_resp = client.post(f"/api/v1/editorial/{editorial_id}/approve", json={
        "reviewer_name": "Managing Editor",
        "approval_notes": "Unit economics analysis verified. Ready for publication."
    })
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == WorkflowStatus.APPROVED

    # 5. Finalization
    fin_resp = client.post(f"/api/v1/editorial/{editorial_id}/finalize", json={
        "finalized_by": "Publisher",
        "publication_notes": "Signed off for morning newsletter dispatch."
    })
    assert fin_resp.status_code == 200
    assert fin_resp.json()["status"] == WorkflowStatus.FINALIZED

    # 6. Immutability Check: Attempting to edit or approve finalized content must fail!
    fail_rev = client.put(f"/api/v1/editorial/{editorial_id}/revision", json={
        "revised_content": "Unauthorized tampering post-finalization that definitely exceeds fifty characters in total length."
    })
    assert fail_rev.status_code == 400
    assert "Cannot edit a finalized editorial" in fail_rev.json()["detail"]

    fail_app = client.post(f"/api/v1/editorial/{editorial_id}/approve", json={
        "reviewer_name": "Rogue Editor"
    })
    assert fail_app.status_code == 400

def test_phase23_unapproved_finalization_rejected(client):
    """Verifies invariant: an unapproved editorial cannot jump directly to FINALIZED."""
    _, editorial_id = _create_project_with_sources_and_editorial(client, "Security Invariant Project")

    # Attempt to finalize directly from DRAFT_CREATED
    resp = client.post(f"/api/v1/editorial/{editorial_id}/finalize", json={
        "finalized_by": "Attacker"
    })
    assert resp.status_code == 400
    assert "must be 'APPROVED' first" in resp.json()["detail"]

def test_phase23_review_comments_and_resolution(client):
    """Verifies adding reviews, attaching line comments, and resolving them."""
    _, editorial_id = _create_project_with_sources_and_editorial(client, "Comments Project")

    # Create a review with an embedded comment
    rev_resp = client.post(f"/api/v1/editorial/{editorial_id}/reviews", json={
        "reviewer_name": "Fact Checker",
        "review_status": "HUMAN_REVIEW_PENDING",
        "overall_feedback": "Reviewing source attributions.",
        "comments": [
            {
                "section_reference": "Strategic Analysis",
                "original_text": "token operational expenses by 80%",
                "comment": "Ensure the 80% figure is cited directly.",
                "suggested_revision": "token operational expenses by up to 80% [1]"
            }
        ]
    })
    assert rev_resp.status_code == 200
    review_data = rev_resp.json()
    assert len(review_data["comments"]) == 1
    comment_id = review_data["comments"][0]["id"]
    assert review_data["comments"][0]["resolution_status"] == "open"

    # Resolve comment
    patch_resp = client.patch(f"/api/v1/editorial/comments/{comment_id}", json={
        "resolution_status": "resolved"
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["resolution_status"] == "resolved"

    # Fetch reviews history
    hist_resp = client.get(f"/api/v1/editorial/{editorial_id}/reviews")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1
    assert hist_resp.json()[0]["comments"][0]["resolution_status"] == "resolved"

def test_phase23_dashboard_statistics(client):
    """Validates database-backed dashboard metrics."""
    resp = client.get("/api/v1/editorial/dashboard/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "pending_human_reviews" in stats
    assert "approved_editorials" in stats
    assert "changes_requested" in stats
    assert "finalized_editorials" in stats
    assert "total_editorials" in stats
    assert isinstance(stats["recent_activity"], list)
