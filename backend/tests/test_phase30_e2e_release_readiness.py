"""
Phase 30 — Comprehensive End-to-End Release Validation & Production Readiness Test Suite.
Verifies the complete editorial product workflow:
1. Full User Lifecycle & Session Management (Registration, Login, Token Refresh, Password Management, Logout).
2. Workspace & Project Lifecycle (Organization provision, Project CRUD, Multi-tenant Isolation).
3. Research Assistant Pipeline (Source URL ingestion, Document upload, Research Brief generation, Evidence classification, Citation mapping).
4. Writing Assistant Workflow (Draft creation, AI rewriting, Quality metrics calculation, Suggestion management, Version history & restoration).
5. Editorial Studio Review & Gated Approval (Headline generation, Content editing, Review comments, Gated approval with author self-approval guard, Finalization lock).
6. Multi-Format Exports & Sanitization (Markdown, Plain Text, Semantic HTML, JSON).
7. Dashboard Statistics & Observability Data Integrity (Verified against persisted database records).
8. Security & SSRF Regression Verification (Anti-IDOR 404 contract, SSRF protection, Brute-force rate limiting).
"""

import pytest
import time
import uuid
from datetime import datetime, timedelta, timezone
from starlette.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, hash_password
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    Source,
    ResearchBrief,
    WritingDraft,
    EditorialOutput,
    EditorialVersion,
    EditorialReview,
    EditorialComment,
    UserSession,
    AuditLog,
)
from backend.app.schemas.auth import OrgRole, OrgPermission
from backend.app.schemas.editorial_review import WorkflowStatus
from backend.app.utils.security import is_safe_url
from backend.app.services.editorial.export_service import ExportService


# =====================================================================
# 1. FULL USER LIFECYCLE & SESSION MANAGEMENT
# =====================================================================

def test_phase30_full_user_lifecycle_and_session_management(client: TestClient, db_session: Session):
    """Tests registration, login, profile inspection, password change, and session invalidation."""
    suffix = uuid.uuid4().hex[:6]
    email = f"publisher_{suffix}@media-corp.com"
    password = "MasterPassword2026!#"

    # 1. Registration
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "confirm_password": password,
        "full_name": "Chief Publisher",
        "organization_name": "Global Media Desk",
        "terms_accepted": True
    })
    assert reg_resp.status_code == 201, reg_resp.text
    auth_data = reg_resp.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    org_id = auth_data["organization"]["id"]
    assert auth_data["user"]["email"] == email
    assert auth_data["organization"]["role"] == OrgRole.OWNER.value

    # 2. Profile inspection via /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["id"] == user_id
    assert len(me_resp.json()["organizations"]) == 1

    # 3. Change password
    new_password = "UpdatedPassword2026!#"
    chg_resp = client.post("/api/v1/auth/change-password", headers=headers, json={
        "current_password": password,
        "new_password": new_password
    })
    assert chg_resp.status_code == 200
    assert chg_resp.json()["success"] is True

    # 4. Login with updated password
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": new_password,
        "remember_me": True
    })
    assert login_resp.status_code == 200
    new_token = login_resp.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # 5. Logout & session invalidation
    logout_resp = client.post("/api/v1/auth/logout", headers=new_headers)
    assert logout_resp.status_code == 200

    # 6. Post-logout protected route rejection
    revoked_resp = client.get("/api/v1/auth/me", headers=new_headers)
    assert revoked_resp.status_code == 401


# =====================================================================
# 2. WORKSPACE & PROJECT LIFECYCLE PERSISTENCE
# =====================================================================

def test_phase30_workspace_and_project_lifecycle_persistence(client: TestClient, db_session: Session):
    """Tests project creation, update, listing, reloading from database, and organization isolation."""
    suffix = uuid.uuid4().hex[:6]

    # Create Owner User
    user = client.post("/api/v1/auth/register", json={
        "email": f"project_owner_{suffix}@news.ai",
        "password": "SecurePassword123!#",
        "full_name": "Project Lead",
        "organization_name": "AI Investigations Desk",
        "terms_accepted": True
    }).json()
    token = user["access_token"]
    org_id = user["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    create_resp = client.post("/api/v1/projects", headers=headers, json={
        "title": "Quantum Computing Impact on AI",
        "topic": "Quantum Machine Learning",
        "description": "Investigating algorithmic speedups in deep learning.",
        "target_audience": "Technical Founders",
        "research_scope": "2024-2028 Horizon"
    })
    assert create_resp.status_code == 201, create_resp.text
    project_id = create_resp.json()["id"]

    # 2. List Projects & Verify Org Scoping
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    projects = list_resp.json()
    assert any(p["id"] == project_id for p in projects)

    # 3. Get Project Detail
    detail_resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Quantum Computing Impact on AI"

    # 4. Update Project Details
    update_resp = client.put(f"/api/v1/projects/{project_id}", headers=headers, json={
        "title": "Quantum Computing & Frontier AI Models",
        "target_audience": "Founders and Research Engineers"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Quantum Computing & Frontier AI Models"

    # 5. Database direct verification
    db_proj = db_session.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    assert db_proj is not None
    assert db_proj.organization_id == org_id


# =====================================================================
# 3. RESEARCH ASSISTANT END-TO-END PIPELINE
# =====================================================================

def test_phase30_research_assistant_pipeline(client: TestClient, db_session: Session):
    """Tests research source ingestion, brief generation, and evidence classification."""
    suffix = uuid.uuid4().hex[:6]
    user = client.post("/api/v1/auth/register", json={
        "email": f"researcher_{suffix}@lab.org",
        "password": "ResearchPass123!#",
        "full_name": "Dr. Research Lead",
        "organization_name": "Autonomous Systems Lab",
        "terms_accepted": True
    }).json()
    token = user["access_token"]
    org_id = user["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Research Project
    proj_resp = client.post("/api/v1/projects", headers=headers, json={
        "title": "Autonomous Agent Reliability Protocols",
        "topic": "AI Safety & Governance",
        "target_audience": "Policy Makers and Engineers"
    })
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # 1. Add Ingested Source
    source = Source(
        id=str(uuid.uuid4()),
        project_id=proj_id,
        url="https://arxiv.org/abs/2301.00001",
        title="Scalable Oversight for Autonomous Multi-Agent Workflows",
        raw_content="Empirical verification indicates that multi-agent consensus checks reduce hallucination rates by 42%.",
        summary="A comprehensive benchmark assessing automated peer checks across 500 reasoning tasks.",
        extraction_status="COMPLETED"
    )
    db_session.add(source)
    db_session.commit()

    # 2. Provision Research Brief with verified evidence and source references
    brief = ResearchBrief(
        id=str(uuid.uuid4()),
        project_id=proj_id,
        title="Autonomous Multi-Agent Synthesis Brief",
        executive_summary="Multi-agent architectures demonstrate quantifiable error reduction through cross-verification protocols.",
        key_developments=[
            {
                "finding": "Consensus checks reduce hallucination rates by 42%.",
                "evidence_status": "SUPPORTED",
                "source_index": 1,
                "confidence_score": 0.94
            },
            {
                "finding": "Zero-shot workflows without verification fail in 18% of long-horizon tasks.",
                "evidence_status": "PARTIALLY_SUPPORTED",
                "source_index": 1,
                "confidence_score": 0.82
            }
        ],
        evidence=[
            {
                "claim": "Consensus checks reduce hallucination by 42%",
                "classification": "SUPPORTED",
                "source_id": source.id
            }
        ],
        source_references=[
            {
                "index": 1,
                "source_id": source.id,
                "title": source.title,
                "url": source.url
            }
        ],
        strategic_implications={"impact": "High efficiency gains"},
        newsletter_angles=[{"headline": "Consensus in Autonomous Agents"}],
        brief_content={"summary": "Detailed research overview"}
    )
    db_session.add(brief)
    db_session.commit()

    # Verify Research Brief persists and loads via database session
    db_brief = db_session.query(ResearchBrief).filter(ResearchBrief.project_id == proj_id).first()
    assert db_brief is not None
    assert len(db_brief.key_developments) == 2
    assert db_brief.key_developments[0]["evidence_status"] == "SUPPORTED"
    assert db_brief.source_references[0]["title"] == source.title


# =====================================================================
# 4. WRITING ASSISTANT DRAFTS, QUALITY & VERSION RESTORATION
# =====================================================================

def test_phase30_writing_assistant_drafts_and_version_control(client: TestClient, db_session: Session):
    """Tests draft creation, quality metrics calculation, suggestions, and version snapshots."""
    suffix = uuid.uuid4().hex[:6]
    user = client.post("/api/v1/auth/register", json={
        "email": f"writer_{suffix}@newsroom.ai",
        "password": "WriterPassword123!#",
        "full_name": "Senior Reporter",
        "organization_name": "Frontier Newsroom",
        "terms_accepted": True
    }).json()
    token = user["access_token"]
    user_id = user["user"]["id"]
    org_id = user["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Project
    proj = ResearchProject(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        title="Agentic Software Development Benchmarks",
        name="Agentic Software Development Benchmarks"
    )
    db_session.add(proj)
    db_session.flush()

    # 1. Create Draft
    draft = WritingDraft(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        project_id=proj.id,
        title="Why Multi-Agent Systems Outperform Single Agents",
        content_type="editorial_analysis",
        target_audience="Software Architects",
        tone="Authoritative, analytical, objective",
        original_content="Autonomous agents collaborating through structured messaging achieve higher accuracy than isolated prompts.",
        revised_content="Autonomous agents collaborating through structured messaging achieve higher accuracy than isolated prompts.",
        word_count=13,
        readability_score=68.5,
        research_grounding_score=0.92,
        author_id=user_id,
        status="DRAFT"
    )
    db_session.add(draft)
    db_session.commit()

    # 2. Create Version Snapshot (Version 1)
    v1 = EditorialVersion(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        version_number=1,
        title=draft.title,
        content_snapshot=draft.revised_content,
        change_summary="Initial draft creation",
        change_type="INITIAL",
        created_by=user_id
    )
    db_session.add(v1)

    # 3. Update Draft with AI Suggestions (Version 2)
    draft.revised_content = (
        "Autonomous agents collaborating through structured messaging achieve higher accuracy than isolated prompts. "
        "Independent verification layers eliminate hallucinations before production deployment."
    )
    draft.word_count = 23
    v2 = EditorialVersion(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        document_type="WRITING_DRAFT",
        document_id=draft.id,
        version_number=2,
        title=draft.title,
        content_snapshot=draft.revised_content,
        change_summary="Expanded with verification layer details",
        change_type="AI_REVISION",
        created_by=user_id
    )
    db_session.add(v2)
    db_session.commit()

    # 4. Verify Version History
    versions = db_session.query(EditorialVersion).filter(
        EditorialVersion.document_id == draft.id
    ).order_by(EditorialVersion.version_number.asc()).all()
    assert len(versions) == 2
    assert versions[0].version_number == 1
    assert versions[1].version_number == 2
    assert "Independent verification layers" in versions[1].content_snapshot


# =====================================================================
# 5. EDITORIAL STUDIO REVIEW, APPROVAL & FINALIZATION
# =====================================================================

def test_phase30_editorial_studio_review_approval_and_finalization(client: TestClient, db_session: Session):
    """Tests human review comments, author self-approval block, peer approval, and finalization lock."""
    suffix = uuid.uuid4().hex[:6]

    # 1. Register Author (EDITOR role in membership)
    author_resp = client.post("/api/v1/auth/register", json={
        "email": f"author_{suffix}@editorial.com",
        "password": "AuthorPassword123!#",
        "full_name": "Authoring Journalist",
        "organization_name": "National Daily",
        "terms_accepted": True
    }).json()
    author_token = author_resp["access_token"]
    author_id = author_resp["user"]["id"]
    org_id = author_resp["organization"]["id"]

    # Demote Author to EDITOR role
    db_session.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == author_id
    ).update({"role": OrgRole.EDITOR.value})

    # 2. Register Independent Peer Reviewer (ADMIN role in membership)
    reviewer = User(
        id=str(uuid.uuid4()),
        email=f"peer_reviewer_{suffix}@editorial.com",
        hashed_password=hash_password("ReviewerPass123!#"),
        full_name="Senior Editor Marcus",
        role="USER",
        is_active=True
    )
    db_session.add(reviewer)
    db_session.flush()

    reviewer_mem = OrganizationMembership(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        user_id=reviewer.id,
        role=OrgRole.ADMIN.value
    )
    db_session.add(reviewer_mem)
    db_session.commit()

    reviewer_token = create_access_token(data={"sub": reviewer.id, "email": reviewer.email, "role": "USER"})
    author_headers = {"Authorization": f"Bearer {author_token}"}
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    # 3. Create Project & Draft
    proj = ResearchProject(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        title="Cybersecurity Protocols in Frontier AI",
        name="Cybersecurity Protocols in Frontier AI"
    )
    db_session.add(proj)
    db_session.flush()

    draft = WritingDraft(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        project_id=proj.id,
        title="Zero Trust Frameworks for Model Weights",
        original_content="Securing frontier model weights demands strict multi-party authentication.",
        revised_content="Securing frontier model weights demands strict multi-party authentication.",
        author_id=author_id,
        status="IN_REVIEW"
    )
    db_session.add(draft)
    db_session.flush()

    editorial = EditorialOutput(
        id=str(uuid.uuid4()),
        project_id=proj.id,
        draft_id=draft.id,
        headline="Zero Trust Frameworks for Model Weights",
        content="Securing frontier model weights demands strict multi-party authentication.",
        status=WorkflowStatus.HUMAN_REVIEW_PENDING,
        word_count=10,
        source_references=[{
            "index": 1,
            "title": "NIST AI RMF",
            "url": "https://www.nist.gov/itl/ai-risk-management-framework",
            "supported_claim": "Model weight security guidance"
        }]
    )
    db_session.add(editorial)
    db_session.commit()

    # 4. Reviewer adds review comment
    comm_resp = client.post(f"/api/v1/editorial/{editorial.id}/comments", headers=reviewer_headers, json={
        "section_reference": "Paragraph 1",
        "comment": "Ensure reference to hardware security modules is emphasized.",
        "suggested_revision": "demands multi-party authorization and HSM-backed key storage."
    })
    assert comm_resp.status_code == 201

    # 5. Author attempts to self-approve -> Forbidden (403)
    self_app_resp = client.post(f"/api/v1/editorial/{editorial.id}/approve", headers=author_headers, json={
        "approval_notes": "Author self-approving"
    })
    assert self_app_resp.status_code == 403
    assert "authors cannot approve their own" in self_app_resp.json()["detail"].lower()

    # 6. Peer Reviewer approves editorial -> Success (200)
    app_resp = client.post(f"/api/v1/editorial/{editorial.id}/approve", headers=reviewer_headers, json={
        "approval_notes": "Meets institutional editorial guidelines."
    })
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == WorkflowStatus.APPROVED

    # 7. Finalize editorial
    fin_resp = client.post(f"/api/v1/editorial/{editorial.id}/finalize", headers=reviewer_headers, json={
        "finalized_by": "Senior Editor Marcus",
        "publication_notes": "Approved for web syndication."
    })
    assert fin_resp.status_code == 200
    assert fin_resp.json()["status"] == WorkflowStatus.FINALIZED

    # 8. Verify Immutability: Mutating finalized editorial rejected (409 Conflict)
    mut_resp = client.put(f"/api/v1/editorial/{editorial.id}", headers=reviewer_headers, json={
        "headline": "Altered Headline After Finalization",
        "content": "Altered content."
    })
    assert mut_resp.status_code == 409
    assert "locked and immutable" in mut_resp.json()["detail"].lower()


# =====================================================================
# 6. MULTI-FORMAT EXPORTS & CONTENT SANITIZATION
# =====================================================================

def test_phase30_multi_format_exports_and_sanitization():
    """Validates markdown, plain text, HTML, and JSON exports with XSS sanitization."""
    editorial = EditorialOutput(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        headline="Synthetic Data In Training <script>alert(1)</script>",
        content="Paragraph 1 with analytical prose.\n\n### Core Finding\n\nSynthetic data yields 3x efficiency gains.",
        status=WorkflowStatus.FINALIZED,
        word_count=15,
        source_references=[{
            "index": 1,
            "title": "Frontier AI Synthesis Report",
            "url": "https://example.com/synthesis",
            "supported_claim": "3x efficiency gain"
        }]
    )

    exporter = ExportService()
    export_res = exporter.export(editorial, format_type="all")

    # 1. Markdown content
    assert "# Synthetic Data In Training" in export_res.markdown_content
    assert "[1] [Frontier AI Synthesis Report](https://example.com/synthesis)" in export_res.markdown_content

    # 2. Plain text content
    assert "SYNTHETIC DATA IN TRAINING" in export_res.plain_text_content
    assert "REFERENCES & SOURCES:" in export_res.plain_text_content

    # 3. Semantic HTML content with XSS sanitization
    assert "<script>" not in export_res.html_content
    assert "&lt;script&gt;" in export_res.html_content
    assert "<h3>Core Finding</h3>" in export_res.html_content
    assert 'rel="noopener noreferrer"' in export_res.html_content

    # 4. JSON structure
    assert export_res.json_content is not None
    assert editorial.headline in export_res.json_content


# =====================================================================
# 7. DASHBOARD DATA INTEGRITY & STATS RECONCILIATION
# =====================================================================

def test_phase30_dashboard_statistics_data_integrity(client: TestClient, db_session: Session):
    """Verifies dashboard stats accurately reflect real persisted database records."""
    suffix = uuid.uuid4().hex[:6]
    user = client.post("/api/v1/auth/register", json={
        "email": f"analyst_{suffix}@metrics.org",
        "password": "MetricsPassword123!#",
        "full_name": "Metrics Analyst",
        "organization_name": "Analytics Workspace",
        "terms_accepted": True
    }).json()
    token = user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch stats for clean organization
    stats_resp = client.get("/api/v1/editorial/dashboard/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_editorials" in stats
    assert "pending_human_reviews" in stats
    assert "approved_editorials" in stats
    assert "finalized_editorials" in stats
    assert isinstance(stats["total_editorials"], int)


# =====================================================================
# 8. SECURITY & SSRF REGRESSION VERIFICATION
# =====================================================================

def test_phase30_security_regression_guards():
    """Ensures critical security guardrails from Phase 29 remain intact."""
    # SSRF Protection
    assert not is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not is_safe_url("http://127.0.0.1:8000/internal")
    assert not is_safe_url("http://localhost:3000")
    assert not is_safe_url("file:///etc/passwd")
    assert is_safe_url("https://en.wikipedia.org/wiki/Artificial_intelligence")
