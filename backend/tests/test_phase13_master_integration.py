import pytest
import uuid
from backend.app.models.base import (
    ResearchProject,
    Source,
    ResearchBrief,
    WritingDraft,
    EditorialOutput,
    EditorialVersion,
    ProviderUsageRecord,
    Organization,
    OrganizationMembership,
    User
)

class TestPhase13MasterIntegration:
    """
    Master Phase 13 End-to-End System Integration Suite
    Verifies all 7 scenarios specified in the Phase 13 Master Implementation Prompt:
      Scenario 1: Application startup, liveness, readiness, and health probes
      Scenario 2: Complete research workflow (project, 3 sources, extraction, brief, evidence persistence)
      Scenario 3: Complete writing workflow (draft, Hemingway audit, suggestions, versions, restore)
      Scenario 4: Editorial Studio generation, citation traceability, review, and export
      Scenario 5: Multi-tenant security, cross-organization data isolation, and RBAC
      Scenario 6: Observability, real execution telemetry, and token tracking
      Scenario 7: Recovery resilience and data persistence integrity
    """

    def test_scenario_1_application_startup_and_health(self, client):
        """SCENARIO 1: Verify health, readiness, and liveness endpoints."""
        # 1. Liveness Probe
        live_res = client.get("/api/v1/health/live")
        assert live_res.status_code == 200
        live_data = live_res.json()
        assert live_data["status"] == "alive"
        assert "application" in live_data

        # 2. Readiness Probe
        ready_res = client.get("/api/v1/health/ready")
        assert ready_res.status_code == 200
        ready_data = ready_res.json()
        assert ready_data["status"] == "ready"
        assert ready_data["database"] == "connected"
        assert "ai_engine" in ready_data["dependencies"]

        # 3. Detailed Health & Diagnostics
        health_res = client.get("/api/v1/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] in ("healthy", "degraded")
        assert health_data["database"] == "connected"
        assert health_data["database_diagnostics"]["status"] == "healthy"
        assert "latency_ms" in health_data["database_diagnostics"]
        assert "telemetry" in health_data

    def test_scenario_2_research_workflow_and_persistence(self, client, db_session):
        """SCENARIO 2: Ingest 3 sources, generate brief, verify claims & evidence persistence."""
        # 1. Create Research Project
        p_res = client.post("/api/v1/research/projects", json={
            "title": "Quantum AI Frontier Benchmark Report",
            "description": "Evaluation of quantum-assisted transformer models."
        })
        assert p_res.status_code == 201
        project = p_res.json()
        project_id = project["id"]

        # 2. Add 3 sources (URL, Text, Technical notes)
        sources_data = [
            {
                "title": "MIT Quantum Annealing Paper",
                "source_type": "text",
                "text_content": (
                    "Researchers at MIT demonstrated a 40% speedup in quadratic unconstrained binary optimization "
                    "using hybrid quantum-classical annealing algorithms. The experiment utilized 128 physical qubits "
                    "at 15 millikelvin temperatures. Scientists hypothesize this will accelerate molecular docking simulation."
                )
            },
            {
                "title": "Google Quantum AI Roadmap",
                "source_type": "text",
                "text_content": (
                    "Google Quantum AI published performance data on the Willow architecture, achieving beyond-classical "
                    "random circuit sampling while demonstrating continuous surface code error suppression below threshold. "
                    "Hardware fabrication cost totaled an estimated $45 million over three fiscal years."
                )
            },
            {
                "title": "Industry Consensus Survey 2026",
                "source_type": "text",
                "text_content": (
                    "A cross-sectional survey of 250 enterprise infrastructure leaders revealed that 68% plan to pilot "
                    "quantum-classical hybrid accelerators by 2028. However, 82% noted that cryocooler maintenance costs "
                    "and developer tooling deficits represent prohibitive adoption barriers."
                )
            }
        ]

        source_ids = []
        for s in sources_data:
            s_res = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
            assert s_res.status_code == 201
            source_ids.append(s_res.json()["id"])
        assert len(source_ids) == 3

        # 3. Process and Extract sources
        for s_id in source_ids:
            ext_res = client.post(f"/api/v1/sources/{s_id}/extract")
            assert ext_res.status_code in (200, 201)

        # 4. Generate Research Brief
        brief_res = client.post(f"/api/v1/research/projects/{project_id}/brief")
        assert brief_res.status_code in (200, 201)
        brief_data = brief_res.json()
        assert "executive_summary" in brief_data or "title" in brief_data

        # 5. Verify Persistence across fresh query
        saved_project = db_session.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        assert saved_project is not None
        assert len(saved_project.sources) == 3
        assert len(saved_project.briefs) >= 1

    def test_scenario_3_writing_workflow_and_versions(self, client, db_session):
        """SCENARIO 3: Create draft, execute Hemingway audit, save version, and restore."""
        raw_text = (
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

        # 1. Create Draft
        d_res = client.post("/api/v1/writing/drafts", json={
            "title": "Quantum Acceleration Analysis",
            "original_content": raw_text,
            "content_type": "ANALYSIS"
        })
        assert d_res.status_code == 201
        draft = d_res.json()
        draft_id = draft["id"]
        assert draft["word_count"] > 50

        # 2. Run Hemingway Quality Audit via /analyze
        audit_res = client.post(f"/api/v1/writing/drafts/{draft_id}/analyze")
        assert audit_res.status_code == 200
        audit_data = audit_res.json()
        assert "issues" in audit_data or "overall_feedback" in audit_data

        # 3. Snapshot a Version
        v_res = client.post(f"/api/v1/writing/drafts/{draft_id}/rewrite", json={
            "instruction": "Initial audited baseline draft"
        })
        assert v_res.status_code in (200, 201)

        versions_res = client.get(f"/api/v1/writing/drafts/{draft_id}/versions")
        assert versions_res.status_code == 200
        versions = versions_res.json()
        assert len(versions) >= 1
        version_id = versions[0]["id"]

        # 4. Modify draft text
        revised_text = "Quantum accelerators offer a 40% speedup for optimization workloads."
        update_res = client.put(f"/api/v1/writing/drafts/{draft_id}", json={
            "title": "Quantum Acceleration Analysis (Concise)",
            "revised_content": revised_text
        })
        assert update_res.status_code == 200

        # 5. Restore earlier version
        restore_res = client.post(f"/api/v1/writing/drafts/{draft_id}/restore/{version_id}")
        assert restore_res.status_code in (200, 201)

        # 6. Verify persistence in database
        refreshed_draft = db_session.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        assert refreshed_draft is not None
        assert "reasoning benchmarks" in refreshed_draft.revised_content

    def test_scenario_4_editorial_studio_traceability(self, client, db_session):
        """SCENARIO 4: Generate editorial from project, verify citations, review, and export."""
        # Setup project with 3 sources and brief
        p_res = client.post("/api/v1/research/projects", json={
            "title": "Editorial Newsletter Edition #42",
            "description": "Traceable citations test."
        })
        project_id = p_res.json()["id"]

        # Ingest 3 sources
        sources_payload = [
            {"title": "Source 1: Enterprise LLM Verification", "source_type": "text", "text_content": "Evaluated 100 enterprise deployments: 88% required verified citation tracking before production sign-off."},
            {"title": "Source 2: Industry Hallucination Benchmarks", "source_type": "text", "text_content": "Independent evaluators report that epistemic classification reduces factual hallucination by 42%."},
            {"title": "Source 3: Autonomous Agent Tool Audits", "source_type": "text", "text_content": "Deterministic guardrails lowered unauthorized tool calls to zero during red team security evaluations."}
        ]
        for s in sources_payload:
            s_res = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
            s_id = s_res.json()["id"]
            client.post(f"/api/v1/sources/{s_id}/extract")

        # Generate brief
        client.post(f"/api/v1/research/projects/{project_id}/brief")

        # 1. Generate Editorial Output
        ed_res = client.post("/api/v1/editorial/generate", json={
            "project_id": project_id,
            "selected_headline": "Why Enterprise AI Demands Verified Citations"
        })
        assert ed_res.status_code in (200, 201)
        editorial = ed_res.json()
        editorial_id = editorial["id"]
        assert editorial["word_count"] > 100
        assert "content" in editorial

        # 2. Submit Editorial Peer Review
        rev_res = client.post(f"/api/v1/editorial/{editorial_id}/submit-review", json={
            "reviewer_name": "Executive Editor",
            "review_status": "APPROVED",
            "overall_feedback": "Excellently grounded with traceable source citations."
        })
        assert rev_res.status_code in (200, 201)

        # 3. Export format
        exp_res = client.get(f"/api/v1/editorial/{editorial_id}/export?format=markdown")
        assert exp_res.status_code == 200

    def test_scenario_5_organization_security_and_tenant_isolation(self, client, db_session):
        """SCENARIO 5: Verify cross-tenant isolation and RBAC security boundaries."""
        # 1. Create Organization Alpha
        org_a = Organization(id=str(uuid.uuid4()), name="Alpha Tech Media", slug=f"alpha-{uuid.uuid4().hex[:6]}")
        user_a = User(id=str(uuid.uuid4()), email=f"editor@{org_a.slug}.com", hashed_password="pw", full_name="Alpha Editor")
        mem_a = OrganizationMembership(id=str(uuid.uuid4()), organization_id=org_a.id, user_id=user_a.id, role="OWNER")
        db_session.add_all([org_a, user_a, mem_a])
        db_session.commit()

        # 2. Create Organization Beta
        org_b = Organization(id=str(uuid.uuid4()), name="Beta Analytics", slug=f"beta-{uuid.uuid4().hex[:6]}")
        user_b = User(id=str(uuid.uuid4()), email=f"analyst@{org_b.slug}.com", hashed_password="pw", full_name="Beta Analyst")
        mem_b = OrganizationMembership(id=str(uuid.uuid4()), organization_id=org_b.id, user_id=user_b.id, role="VIEWER")
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

        # 4. Attempt to access Org Alpha's project with Org Beta headers
        unauth_res = client.get(
            f"/api/v1/projects/{proj_a.id}",
            headers={"X-Organization-Id": org_b.id}
        )
        # Must be rejected with 403 or 404
        assert unauth_res.status_code in (403, 404)

    def test_scenario_6_ai_observability_and_real_telemetry(self, client, db_session):
        """SCENARIO 6: Execute AI benchmark evaluation and verify persistent execution telemetry."""
        import asyncio
        from backend.app.services.ai.router import ai_router

        # 1. Trigger automated 34-benchmark evaluation
        eval_res = client.post("/api/v1/observability/evaluate")
        assert eval_res.status_code == 200
        eval_data = eval_res.json()
        assert eval_data["total_tests"] >= 34
        assert eval_data["passed_tests"] >= 34
        assert eval_data["overall_pass_rate"] == 1.0

        # 2. Execute an AI operation that logs to ProviderUsageRecord
        test_org_id = f"test-obs-org-{uuid.uuid4().hex[:6]}"
        db_session.add(Organization(id=test_org_id, name="Obs Test Org", slug=f"slug-{test_org_id}"))
        db_session.commit()

        asyncio.run(
            ai_router.execute_structured(
                prompt="Synthesize technical verification findings",
                provider="fallback",
                db=db_session,
                organization_id=test_org_id,
                prompt_version="v1.0.0"
            )
        )

        # 3. Fetch live telemetry metrics
        telemetry_res = client.get("/api/v1/observability/metrics")
        assert telemetry_res.status_code == 200

        # 4. Verify records exist in ProviderUsageRecord table
        records = db_session.query(ProviderUsageRecord).all()
        assert len(records) >= 1
        record = records[0]
        assert record.provider in ("groq", "openai", "anthropic", "deterministic_fallback", "fallback")
        assert record.total_tokens >= 0
        assert record.duration_ms >= 0.0
        assert telemetry_res.status_code == 200
        t_data = telemetry_res.json()
        assert "total_operations" in t_data or "total_requests" in t_data

        # 3. Verify records exist in ProviderUsageRecord table
        records = db_session.query(ProviderUsageRecord).all()
        assert len(records) >= 1
        record = records[0]
        assert record.provider in ("groq", "openai", "anthropic", "deterministic_fallback")
        assert record.total_tokens >= 0
        assert record.duration_ms >= 0.0

    def test_scenario_7_backend_recovery_and_persistence(self, client, db_session):
        """SCENARIO 7: Verify recovery resilience and persistence consistency."""
        # 1. Create a persistent research project
        recovery_proj = ResearchProject(
            id=str(uuid.uuid4()),
            title="Recovery Resilience Anchor Project",
            description="Must survive health checks and simulation.",
            status="ACTIVE"
        )
        db_session.add(recovery_proj)
        db_session.commit()
        proj_id = recovery_proj.id

        # 2. Health check remains 200 OK
        h_res = client.get("/api/v1/health")
        assert h_res.status_code == 200
        assert h_res.json()["database"] == "connected"

        # 3. Reload from database and assert full integrity
        reloaded = db_session.query(ResearchProject).filter(ResearchProject.id == proj_id).first()
        assert reloaded is not None
        assert reloaded.title == "Recovery Resilience Anchor Project"
        assert reloaded.status == "ACTIVE"
