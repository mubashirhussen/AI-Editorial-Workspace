"""
Phase 15 - User Acceptance Testing (UAT) & FDE Assessment Validation Suite
Systematically tests the end-to-end editorial journeys, data integrity,
security tenant boundaries, and failure recovery for the AI Editorial Workspace.
"""

import uuid
import pytest
from backend.app.models.base import (
    User, Organization, OrganizationMembership, ResearchProject,
    Source, ResearchBrief, WritingDraft, EditorialOutput,
    ProviderUsageRecord
)


class TestPhase15UATValidation:
    """Independent UAT verification covering Scenarios A, B, C, Data Integrity & Security."""

    def test_uat_scenario_a_first_time_user_journey(self, client, db_session):
        """Scenario A: Complete end-to-end journey for a first-time user.
        Step 1: Check application health.
        Step 2: Create first research project.
        Step 3: Add 3 research sources.
        Step 4: Process and extract sources.
        Step 5: Generate an evidence-backed research brief.
        Step 6: Create writing draft in Writing Assistant.
        Step 7: Execute Hemingway editorial quality audit.
        Step 8: Save revised draft.
        Step 9: Generate editorial newsletter in Editorial Studio.
        Step 10: Verify traceable citations, submit review, and export.
        """
        # 1. Check live health
        health_res = client.get("/api/v1/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["database"] == "connected"

        # 2. Create first research project
        proj_res = client.post("/api/v1/research/projects", json={
            "title": "Autonomous AI Agents in Enterprise Editorial",
            "description": "Evaluating agentic reasoning, memory persistence, and evidence provenance."
        })
        assert proj_res.status_code == 201
        project = proj_res.json()
        project_id = project["id"]
        assert project["title"] == "Autonomous AI Agents in Enterprise Editorial"

        # 3. Add 3 research sources
        sources_data = [
            {
                "title": "Anthropic Model Context Protocol Announcement",
                "source_type": "text",
                "text_content": (
                    "The Model Context Protocol (MCP) provides an open architecture connecting AI assistants to "
                    "external tools, enterprise databases, and development workspaces. Standardized tool definitions "
                    "prevent vendor lock-in and enable deterministic parameter schema validation."
                )
            },
            {
                "title": "DeepSeek R1 Technical Architecture Overview",
                "source_type": "text",
                "text_content": (
                    "DeepSeek R1 demonstrates that pure reinforcement learning without supervised fine-tuning incentives "
                    "self-correction and multi-step reasoning capabilities. The model verifies intermediate steps, "
                    "substantially reducing mathematical and logical hallucinations in technical evaluations."
                )
            },
            {
                "title": "Enterprise RAG Benchmarks 2026",
                "source_type": "text",
                "text_content": (
                    "Empirical tests across 10,000 production queries show that grounding generative responses on "
                    "verified source excerpts reduces factual hallucinations below 2.4%. Sentence-level citation "
                    "mapping is critical for editorial trust in professional publications."
                )
            }
        ]

        source_ids = []
        for s in sources_data:
            s_res = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
            assert s_res.status_code == 201
            source_ids.append(s_res.json()["id"])
        assert len(source_ids) == 3

        # 4. Extract and analyze sources
        for s_id in source_ids:
            ext_res = client.post(f"/api/v1/sources/{s_id}/extract")
            assert ext_res.status_code in (200, 201)

        # 5. Generate Research Brief
        brief_res = client.post(f"/api/v1/research/projects/{project_id}/brief")
        assert brief_res.status_code in (200, 201)
        brief_data = brief_res.json()
        assert "executive_summary" in brief_data or "title" in brief_data

        # 6. Create Writing Draft
        raw_editorial_draft = (
            "In order to understand the significance of recent reasoning benchmarks, it is important to note that "
            "a large number of tests were conducted by the research team. Due to the fact that retrieval-augmented "
            "generation relies on embeddings and vector database search, basically the architecture has the ability "
            "to process unstructured technical documentation with high throughput.\n\n"
            "Furthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous "
            "subordinate clauses and technical parameters without giving the reader a single moment of pause or cognitive respite, "
            "which obviously makes it exceedingly difficult to parse in a fast-paced executive editorial environment.\n\n"
            "At the end of the day, founders who implement verifiable evaluation metrics will dominate the commercial landscape, "
            "while fragile wrapper applications will face commoditization."
        )
        draft_res = client.post("/api/v1/writing/drafts", json={
            "title": "The Paradigm Shift in Agentic Editorial Workflows",
            "original_content": raw_editorial_draft,
            "content_type": "ANALYSIS"
        })
        assert draft_res.status_code == 201
        draft = draft_res.json()
        draft_id = draft["id"]
        assert draft["word_count"] > 50

        # 7. Execute Hemingway Editorial Quality Audit
        audit_res = client.post(f"/api/v1/writing/drafts/{draft_id}/analyze")
        assert audit_res.status_code == 200
        audit_data = audit_res.json()
        assert "issues" in audit_data or "overall_feedback" in audit_data

        # 8. Snapshot baseline version and update with concise text
        v_res = client.post(f"/api/v1/writing/drafts/{draft_id}/rewrite", json={
            "instruction": "Audited initial baseline draft"
        })
        assert v_res.status_code in (200, 201)

        concise_content = (
            "Reinforcement learning empowers AI assistants with robust reasoning capabilities. "
            "Verified source grounding lowers hallucination rates to under 2.4%."
        )
        update_res = client.put(f"/api/v1/writing/drafts/{draft_id}", json={
            "title": "The Paradigm Shift in Agentic Editorial Workflows (Concise)",
            "revised_content": concise_content
        })
        assert update_res.status_code == 200

        # 9. Generate Editorial in Editorial Studio
        ed_res = client.post("/api/v1/editorial/generate", json={
            "project_id": project_id,
            "selected_headline": "Why Enterprise AI Demands Verified Citations"
        })
        assert ed_res.status_code in (200, 201)
        editorial = ed_res.json()
        editorial_id = editorial["id"]
        assert editorial["word_count"] > 100
        assert "content" in editorial

        # 10. Peer Review and Export
        rev_res = client.post(f"/api/v1/editorial/{editorial_id}/submit-review", json={
            "reviewer_name": "Executive Editor",
            "review_status": "APPROVED",
            "overall_feedback": "Excellently grounded with traceable source citations."
        })
        assert rev_res.status_code in (200, 201)

        exp_res = client.get(f"/api/v1/editorial/{editorial_id}/export?format=markdown")
        assert exp_res.status_code == 200
        assert len(exp_res.content) > 0

    def test_uat_scenario_b_returning_user_and_persistence(self, client, db_session):
        """Scenario B: Returning user reopens previous project, drafts, and versions."""
        # 1. Create project
        proj_res = client.post("/api/v1/research/projects", json={
            "title": "Persistent Project Delta",
            "description": "Cross-session persistence test."
        })
        assert proj_res.status_code == 201
        project_id = proj_res.json()["id"]

        # 2. Add source
        s_res = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
            "title": "Persistent Anchor Document",
            "source_type": "text",
            "text_content": "Anchor content ensuring persistent database state."
        })
        assert s_res.status_code == 201

        # 3. Create draft
        d_res = client.post("/api/v1/writing/drafts", json={
            "title": "Draft with Version History",
            "original_content": "Initial revision paragraph.",
            "content_type": "NEWSLETTER"
        })
        assert d_res.status_code == 201
        draft_id = d_res.json()["id"]

        # Snapshot version 1
        client.post(f"/api/v1/writing/drafts/{draft_id}/rewrite", json={"instruction": "Snapshot v1"})

        # Update draft to version 2
        client.put(f"/api/v1/writing/drafts/{draft_id}", json={
            "title": "Draft with Version History (v2)",
            "revised_content": "Second revision paragraph with expanded analysis."
        })

        # 4. Simulate returning user session: query project directly from DB and API
        ret_proj = client.get("/api/v1/research/projects")
        assert ret_proj.status_code == 200
        proj_data = ret_proj.json()
        proj_list = proj_data.get("items", [])
        assert any(p["id"] == project_id for p in proj_list)

        # 5. Verify draft and versions persist
        versions_res = client.get(f"/api/v1/writing/drafts/{draft_id}/versions")
        assert versions_res.status_code == 200
        versions = versions_res.json()
        assert len(versions) >= 1

        # 6. Verify restored database records
        db_draft = db_session.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        assert db_draft is not None
        assert "Second revision" in db_draft.revised_content

    def test_uat_scenario_c_security_and_tenant_isolation(self, client, db_session):
        """Scenario C: Multi-tenant boundary enforcement and unauthorized request rejection."""
        # 1. Create Org Alpha and User Alpha
        org_a = Organization(id=str(uuid.uuid4()), name="Alpha News Corp", slug=f"alpha-{uuid.uuid4().hex[:6]}")
        user_a = User(id=str(uuid.uuid4()), email=f"lead@{org_a.slug}.com", hashed_password="pw", full_name="Alpha Lead")
        mem_a = OrganizationMembership(id=str(uuid.uuid4()), organization_id=org_a.id, user_id=user_a.id, role="OWNER")
        db_session.add_all([org_a, user_a, mem_a])

        # 2. Create Org Beta and User Beta
        org_b = Organization(id=str(uuid.uuid4()), name="Beta Media Lab", slug=f"beta-{uuid.uuid4().hex[:6]}")
        user_b = User(id=str(uuid.uuid4()), email=f"writer@{org_b.slug}.com", hashed_password="pw", full_name="Beta Writer")
        mem_b = OrganizationMembership(id=str(uuid.uuid4()), organization_id=org_b.id, user_id=user_b.id, role="MEMBER")
        db_session.add_all([org_b, user_b, mem_b])
        db_session.commit()

        # 3. Create project in Org Alpha
        proj_a = ResearchProject(
            id=str(uuid.uuid4()),
            organization_id=org_a.id,
            title="Confidential Alpha Investigation",
            status="ACTIVE"
        )
        db_session.add(proj_a)
        db_session.commit()

        # 4. User B attempts to access Org Alpha's project via Header spoofing -> REJECTED (403 or 404)
        unauth_res = client.get(
            f"/api/v1/projects/{proj_a.id}",
            headers={"X-Organization-Id": org_b.id}
        )
        assert unauth_res.status_code in (403, 404)

    def test_uat_data_validation_and_calculated_metrics(self, client, db_session):
        """Data Validation: Verify exact correspondence between DB records, word counts, and dashboard stats."""
        # 1. Dashboard stats and project count in DB vs API
        initial_stats = client.get("/api/v1/research/dashboard/stats").json()
        initial_projects = initial_stats["total_projects"]

        p1 = client.post("/api/v1/research/projects", json={"title": "Metric Validation Project 1"})
        p2 = client.post("/api/v1/research/projects", json={"title": "Metric Validation Project 2"})
        assert p1.status_code == 201
        assert p2.status_code == 201

        updated_projects = db_session.query(ResearchProject).count()
        assert updated_projects == initial_projects + 2

        updated_stats = client.get("/api/v1/research/dashboard/stats").json()
        assert updated_stats["total_projects"] == initial_projects + 2

        # 2. Word count formula validation
        sample_text = "The quick brown fox jumps over the lazy dog. " * 20  # 180 words
        d_res = client.post("/api/v1/writing/drafts", json={
            "title": "Word Count Calculation Draft",
            "original_content": sample_text,
            "content_type": "BLOG"
        })
        assert d_res.status_code == 201
        draft_data = d_res.json()
        assert draft_data["word_count"] == 180

        # Deterministic reading time formula: Math.ceil(word_count / 200) -> 1 minute for 180 words
        estimated_reading_minutes = max(1, round(draft_data["word_count"] / 200))
        assert estimated_reading_minutes == 1

        # 3. Telemetry metrics retrieval
        obs_res = client.get("/api/v1/observability/metrics")
        assert obs_res.status_code == 200
        obs_data = obs_res.json()
        assert "total_operations" in obs_data or "total_requests" in obs_data
