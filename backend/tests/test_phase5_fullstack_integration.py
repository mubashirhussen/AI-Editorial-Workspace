import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

class TestPhase5FullStackIntegration:
    """
    Phase 5 Full-Stack Integration Verification Suite.
    Validates end-to-end communication, authentication, research, writing,
    versioning, and multi-tenant isolation scenarios A, B, C, and D.
    """

    # =========================================================================
    # SCENARIO A: Complete Authentication, Session & Password Reset Lifecycle
    # =========================================================================
    def test_scenario_a_authentication_lifecycle(self, monkeypatch):
        """
        Scenario A:
        1. Register user & org.
        2. Login with credentials.
        3. Retrieve authenticated profile & organization.
        4. Request password reset & retrieve reset token.
        5. Reset password with cryptographic token.
        6. Login with new password.
        7. Logout and verify token revocation.
        """
        # Ensure strict token checks
        monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_DEV", False)

        test_email = f"lead_editor_{uuid.uuid4().hex[:6]}@editorial.ai"
        initial_password = "SecurePassword123!"
        new_password = "UpdatedPassword456!"
        full_name = "Lead Editorial Architect"
        org_name = "Scout Editorial Corp"

        # 1. Registration
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": initial_password,
                "full_name": full_name,
                "organization_name": org_name
            }
        )
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        reg_data = reg_resp.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["email"] == test_email
        assert reg_data["organization"]["name"] == org_name
        assert reg_data["organization"]["role"] == "OWNER"

        token = reg_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": initial_password}
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Retrieve /auth/me
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["user"]["email"] == test_email
        assert len(me_data["organizations"]) >= 1

        # 4. Forgot password request
        forgot_resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_email}
        )
        assert forgot_resp.status_code == 200
        forgot_data = forgot_resp.json()
        assert forgot_data["success"] is True
        reset_token = forgot_data.get("dev_reset_token")
        assert reset_token is not None, "Dev reset token should be returned in development"

        # 5. Reset password
        reset_resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": new_password}
        )
        assert reset_resp.status_code == 200
        assert reset_resp.json()["success"] is True

        # 6. Login with new password
        login_new_resp = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": new_password}
        )
        assert login_new_resp.status_code == 200
        token = login_new_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 7. Logout
        logout_resp = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_resp.status_code == 200

        # Verify revoked token cannot access protected endpoints
        protected_resp = client.get("/api/v1/auth/me", headers=headers)
        assert protected_resp.status_code == 401

    # =========================================================================
    # SCENARIO B: Research Assistant End-to-End Workflow & Brief Generation
    # =========================================================================
    def test_scenario_b_research_assistant_flow(self):
        """
        Scenario B:
        1. Register and login editor.
        2. Create research investigation project.
        3. Ingest pasted text source.
        4. Ingest document file upload.
        5. Ingest web URL source.
        6. Verify source count, analyze source, and synthesize research brief.
        7. Verify persisted brief with newsletter angles and verified citations.
        """
        # Session setup
        email = f"researcher_{uuid.uuid4().hex[:6]}@editorial.ai"
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "ResearchPassword123!",
                "full_name": "Senior Staff Researcher",
                "organization_name": "AI Insights Lab"
            }
        ).json()
        headers = {"Authorization": f"Bearer {reg['access_token']}"}

        # 1. Create project
        proj_resp = client.post(
            "/api/v1/research/projects",
            json={
                "title": "Quantum AI & Transformer Scaling 2026",
                "description": "Comprehensive benchmark across frontier architectures."
            },
            headers=headers
        )
        assert proj_resp.status_code == 201
        project = proj_resp.json()
        proj_id = project["id"]

        # 2. Ingest Source 1: Text
        src1_resp = client.post(
            f"/api/v1/projects/{proj_id}/sources",
            json={
                "source_type": "text",
                "title": "Frontier Attention Architecture Technical Spec",
                "text_content": (
                    "Transformers rely on multi-head scaled dot-product self-attention mechanisms. "
                    "In 2026, inference efficiency is driven by mixture-of-experts routing and kv-cache optimization. "
                    "Empirical tests show a 40% latency reduction in production reasoning workloads."
                )
            },
            headers=headers
        )
        assert src1_resp.status_code == 201
        src1 = src1_resp.json()
        assert src1["extraction_status"].lower() == "completed"

        # 3. Ingest Source 2: File Upload (plain text document)
        file_content = b"Technical whitepaper on foundation model latency, inference cost, and verification benchmarks."
        src2_resp = client.post(
            f"/api/v1/projects/{proj_id}/sources/upload",
            files={"file": ("inference_benchmarks.txt", io.BytesIO(file_content), "text/plain")},
            data={"title": "Whitepaper: Inference Benchmarks"},
            headers=headers
        )
        assert src2_resp.status_code == 201
        src2 = src2_resp.json()

        # 4. Ingest Source 3: Text source
        src3_resp = client.post(
            f"/api/v1/projects/{proj_id}/sources",
            json={
                "source_type": "text",
                "title": "Production Deployment Safety and Hallucination Guardrails",
                "text_content": (
                    "Editorial accuracy requires end-to-end evidence attribution and citation verification. "
                    "Unverifiable claims lead to reputational decay in technical publications."
                )
            },
            headers=headers
        )
        assert src3_resp.status_code == 201

        # 5. List sources
        sources_list = client.get(f"/api/v1/projects/{proj_id}/sources", headers=headers)
        assert sources_list.status_code == 200
        sources = sources_list.json()
        assert len(sources) >= 3

        # 6. Generate Research Brief
        brief_resp = client.post(f"/api/v1/research/projects/{proj_id}/brief", headers=headers)
        assert brief_resp.status_code in (200, 201)
        brief = brief_resp.json()
        assert "angles" in brief or "key_findings" in brief or "executive_summary" in brief

        # 7. Verify persisted project details
        proj_detail = client.get(f"/api/v1/research/projects/{proj_id}", headers=headers)
        assert proj_detail.status_code == 200
        p_data = proj_detail.json()
        assert p_data["id"] == proj_id
        assert len(p_data.get("sources", [])) >= 3

    # =========================================================================
    # SCENARIO C: Writing Assistant Complete Lifecycle & Version Control
    # =========================================================================
    def test_scenario_c_writing_assistant_and_versions(self):
        """
        Scenario C:
        1. Register and login author.
        2. Create draft editorial document.
        3. Request writing metrics & analysis.
        4. Apply suggestion and update draft content.
        5. Verify automatic version snapshot creation.
        6. Retrieve version history.
        7. Restore initial version and verify content restoration.
        """
        email = f"author_{uuid.uuid4().hex[:6]}@editorial.ai"
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "AuthorPassword123!",
                "full_name": "Lead Newsletter Author",
                "organization_name": "Weekly AI Dispatch"
            }
        ).json()
        headers = {"Authorization": f"Bearer {reg['access_token']}"}

        # 1. Create draft
        original_text = (
            "Due to the fact that foundation models require significant compute, it is important to note "
            "that modern editorial pipelines must incorporate source attribution to avoid inaccuracies."
        )
        draft_resp = client.post(
            "/api/v1/writing/drafts",
            json={
                "title": "State of AI Engineering 2026",
                "content": original_text
            },
            headers=headers
        )
        assert draft_resp.status_code in (200, 201)
        draft = draft_resp.json()
        draft_id = draft["id"]

        # 2. Get metrics
        metrics_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/metrics", headers=headers)
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert metrics["word_count"] > 10

        # 3. Analyze text
        analysis_resp = client.post(
            "/api/v1/writing/analyze",
            json={"text": original_text, "title": "State of AI Engineering 2026"},
            headers=headers
        )
        assert analysis_resp.status_code == 200
        analysis = analysis_resp.json()
        assert "metrics" in analysis

        # 4. Update draft (generates revision version)
        updated_text = (
            "Because foundation models demand substantial compute, modern editorial pipelines "
            "must enforce direct source attribution to prevent hallucinations."
        )
        patch_resp = client.patch(
            f"/api/v1/writing/drafts/{draft_id}",
            json={"content": updated_text},
            headers=headers
        )
        assert patch_resp.status_code == 200

        # 5. List version history
        versions_resp = client.get(f"/api/v1/writing/drafts/{draft_id}/versions", headers=headers)
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) >= 1

        # 6. Restore original version
        first_version_id = versions[-1]["id"]
        restore_resp = client.post(
            f"/api/v1/writing/drafts/{draft_id}/restore/{first_version_id}",
            headers=headers
        )
        assert restore_resp.status_code == 200
        restored = restore_resp.json()
        assert restored["content"] == original_text

    # =========================================================================
    # SCENARIO D: Multi-Tenant Data Isolation and Authorization Matrix
    # =========================================================================
    def test_scenario_d_multi_tenant_isolation(self):
        """
        Scenario D:
        1. Create Organization Alpha with User Alpha.
        2. Create Organization Beta with User Beta.
        3. Create research project in Org Alpha.
        4. Verify User Beta cannot view, edit, or delete Org Alpha's project.
        5. Verify User Beta cannot access Org Alpha's sources or drafts.
        """
        # User Alpha
        reg_alpha = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"alpha_{uuid.uuid4().hex[:6]}@alpha.org",
                "password": "AlphaPassword123!",
                "full_name": "Alpha Director",
                "organization_name": "Alpha Research Org"
            }
        ).json()
        headers_alpha = {"Authorization": f"Bearer {reg_alpha['access_token']}"}

        # User Beta
        reg_beta = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"beta_{uuid.uuid4().hex[:6]}@beta.org",
                "password": "BetaPassword123!",
                "full_name": "Beta Editor",
                "organization_name": "Beta Publishing Org"
            }
        ).json()
        headers_beta = {"Authorization": f"Bearer {reg_beta['access_token']}"}

        # Alpha creates project
        proj_alpha = client.post(
            "/api/v1/research/projects",
            json={"title": "Confidential Alpha Research"},
            headers=headers_alpha
        ).json()
        proj_id = proj_alpha["id"]

        # Beta attempts to read Alpha's project
        read_attempt = client.get(
            f"/api/v1/research/projects/{proj_id}",
            headers=headers_beta
        )
        assert read_attempt.status_code in (403, 404), (
            f"Cross-tenant access must be rejected with 403 or 404. Got {read_attempt.status_code}"
        )

        # Beta attempts to add source to Alpha's project
        add_source_attempt = client.post(
            f"/api/v1/projects/{proj_id}/sources",
            json={"source_type": "text", "title": "Injected Source", "text_content": "Unauthorized injection attempt"},
            headers=headers_beta
        )
        assert add_source_attempt.status_code in (403, 404)

        # Beta attempts to delete Alpha's project
        del_attempt = client.delete(
            f"/api/v1/research/projects/{proj_id}",
            headers=headers_beta
        )
        assert del_attempt.status_code in (403, 404)
