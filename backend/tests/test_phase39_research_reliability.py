"""
Phase 39: AI Research Reliability, Source Intelligence, Citation Verification & Evidence Quality Tests.
Validates:
- Explainable source credibility assessment & freshness calculation
- Source ingestion, SSRF protection, and canonical deduplication
- Sentence-level evidence extraction & paragraph/sentence location indexing
- Six-tier epistemic claim verification (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNVERIFIED, NOT_APPLICABLE)
- Citation validation & anti-fabrication enforcement (flagging hallucinated references)
- Cross-publisher corroboration & contradiction preservation
- Comprehensive Research Quality Report generation & scorecards
- Evidence-grounded section regeneration with diff tracking & revision acceptance
- Multi-tenant organization isolation
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    Source,
    ResearchBrief,
    ResearchEvidence,
    ResearchClaim,
    ResearchContradiction,
    SourceCredibilityAssessment,
    CitationValidation,
    ResearchQualityReport,
    ResearchRevision,
)
from backend.app.core.security import hash_password, create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_research_tenants(db_session):
    """Creates two isolated organizations for research reliability testing."""
    uid = uuid.uuid4().hex[:8]

    # Tenant Alpha
    org_a = Organization(id=f"org-rr-a-{uid}", name="Alpha Research Org", slug=f"alpha-rr-{uid}")
    user_a = User(
        id=f"user-rr-a-{uid}",
        email=f"alpha.researcher.{uid}@example.com",
        hashed_password=hash_password("ResearchReliability123!"),
        full_name="Alpha Principal Researcher",
        is_active=True
    )
    mem_a = OrganizationMembership(
        id=f"mem-rr-a-{uid}",
        organization_id=org_a.id,
        user_id=user_a.id,
        role="OWNER"
    )

    # Tenant Beta
    org_b = Organization(id=f"org-rr-b-{uid}", name="Beta Research Org", slug=f"beta-rr-{uid}")
    user_b = User(
        id=f"user-rr-b-{uid}",
        email=f"beta.researcher.{uid}@example.com",
        hashed_password=hash_password("ResearchReliability123!"),
        full_name="Beta Principal Researcher",
        is_active=True
    )
    mem_b = OrganizationMembership(
        id=f"mem-rr-b-{uid}",
        organization_id=org_b.id,
        user_id=user_b.id,
        role="MEMBER"
    )

    # Project Alpha
    proj_a = ResearchProject(
        id=f"proj-rr-a-{uid}",
        organization_id=org_a.id,
        title="Reasoning LLMs Architecture Benchmark",
        description="Comprehensive evaluation of test-time compute scaling laws.",
        status="active"
    )

    db_session.add_all([org_a, user_a, mem_a, org_b, user_b, mem_b, proj_a])
    db_session.commit()

    token_a = create_access_token(data={"sub": user_a.id, "email": user_a.email})
    token_b = create_access_token(data={"sub": user_b.id, "email": user_b.email})

    return {
        "org_a": org_a,
        "user_a": user_a,
        "token_a": token_a,
        "proj_a": proj_a,
        "org_b": org_b,
        "user_b": user_b,
        "token_b": token_b,
    }


def seed_research_data_for_project(db_session, project_id):
    """Seeds authentic sources, evidence passages, brief, and contradictions for testing."""
    s1 = Source(
        id=f"src-1-{uuid.uuid4().hex[:6]}",
        project_id=project_id,
        title="DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
        url="https://arxiv.org/abs/2501.12948",
        original_url="https://arxiv.org/abs/2501.12948?utm_source=twitter",
        source_type="URL",
        extracted_content=(
            "DeepSeek-R1 achieves state-of-the-art reasoning performance across mathematical benchmarks. "
            "The model demonstrates that pure reinforcement learning without supervised fine-tuning can incentivize chain-of-thought behaviors. "
            "Training was completed using 2,048 H800 GPUs over a period of 55 days. "
            "Benchmark evaluations show a Pass@1 accuracy of 79.8% on AIME 2024 and 97.3% on MATH-500."
        ),
        author="DeepSeek-AI Research Team",
        published_at=(datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%d"),
        extraction_status="COMPLETED"
    )

    s2 = Source(
        id=f"src-2-{uuid.uuid4().hex[:6]}",
        project_id=project_id,
        title="OpenAI o1 System Card and Reasoning Evaluations",
        url="https://openai.com/research/o1-system-card",
        source_type="URL",
        extracted_content=(
            "OpenAI o1 utilizes reinforcement learning to spend more time thinking before answering. "
            "On competitive programming benchmarks including Codeforces, OpenAI o1 reached the 89th percentile. "
            "OpenAI safety evaluations indicate a 84% reduction in jailbreak susceptibility compared to GPT-4o."
        ),
        author="OpenAI Safety Team",
        published_at="2024-09-12",
        extraction_status="COMPLETED"
    )

    brief = ResearchBrief(
        id=f"brief-1-{uuid.uuid4().hex[:6]}",
        project_id=project_id,
        title="Reasoning Models Breakthrough Brief",
        executive_summary="DeepSeek-R1 achieves state-of-the-art reasoning performance across mathematical benchmarks. In our opinion, this represents a fascinating turning point for open weights. Benchmark evaluations show a Pass@1 accuracy of 79.8% on AIME 2024.",
        key_developments=[
            {"summary": "Training was completed using 2,048 H800 GPUs over a period of 55 days."},
            {"summary": "OpenAI o1 reached the 89th percentile on Codeforces competitive programming benchmarks."},
            {"summary": "The model achieved 99.9% accuracy on quantum cryptography benchmarks without evidence."} # Intentional unsupported claim
        ],
        strategic_implications={"impact": "Compute costs will shift from pre-training to test-time inference scaling."},
        newsletter_angles=["Open weights reasoning vs closed frontier models"],
        source_references=[
            {"source_id": s1.id, "title": s1.title, "url": s1.url},
            {"source_id": s2.id, "title": s2.title, "url": s2.url},
            {"source_id": "non-existent-source-id", "title": "Fabricated Citation Tech Report", "url": "https://fake-citation-ai.org/paper.pdf"} # Intentional fabricated citation
        ]
    )

    contra = ResearchContradiction(
        id=f"contra-1-{uuid.uuid4().hex[:6]}",
        project_id=project_id,
        claim_a_text="Training cost was under 6 million dollars.",
        claim_b_text="Training cost exceeded 50 million dollars according to industry estimates.",
        disagreement_nature="Discrepancy in estimated cluster amortized hardware expenditure.",
        possible_explanations="Hardware depreciation vs raw energy operational expenditure.",
        unresolved_questions="What was the actual electricity cost per GPU cluster hour?"
    )

    db_session.add_all([s1, s2, brief, contra])
    db_session.commit()
    db_session.refresh(s1)
    db_session.refresh(s2)
    db_session.refresh(brief)

    # Extract sentence evidence for both sources
    from backend.app.services.research_reliability_service import research_reliability_service
    research_reliability_service.extract_evidence_passages(db_session, s1)
    research_reliability_service.extract_evidence_passages(db_session, s2)

    return {"s1": s1, "s2": s2, "brief": brief, "contra": contra}


def test_source_credibility_assessment_and_explainable_criteria(client, test_research_tenants, db_session):
    """Test 1: Assesses source credibility, publisher authority, freshness, and explainable criteria."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    s1 = data["s1"]

    res = client.get(f"/api/v1/research-reliability/sources/{s1.id}/credibility", headers=headers)
    assert res.status_code == 200
    cred = res.json()

    assert cred["source_id"] == s1.id
    assert cred["credibility_tier"] == "PEER_REVIEWED"
    assert cred["publisher_name"] == "ArXiv"
    assert cred["is_primary_source"] is True
    assert cred["methodological_transparency"] == "HIGH"
    assert cred["freshness_status"] in ("CURRENT", "RECENT")
    assert "criteria_breakdown" in cred
    assert cred["criteria_breakdown"]["publisher_identified"] is True
    assert "limitations" in cred


def test_source_ingestion_ssrf_and_deduplication(client, test_research_tenants, db_session):
    """Test 2: Verifies SSRF defense on internal addresses and canonical URL deduplication."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Block SSRF to localhost and internal metadata IP
    ssrf_payload = {
        "url": "http://127.0.0.1:8000/internal-secrets",
        "title": "Localhost exploit",
        "source_type": "URL"
    }
    res_ssrf = client.post(f"/api/v1/research-reliability/projects/{proj.id}/sources/ingest", json=ssrf_payload, headers=headers)
    assert res_ssrf.status_code == 201
    assert res_ssrf.json()["extraction_status"].lower() == "failed"

    # 2. Ingest valid text source
    text_payload = {
        "title": "Constitutional AI Specification",
        "text_content": "Constitutional AI trains models using a set of explicit behavioral principles. Principles guide self-critique and revision steps.",
        "source_type": "TEXT"
    }
    res_ingest = client.post(f"/api/v1/research-reliability/projects/{proj.id}/sources/ingest", json=text_payload, headers=headers)
    assert res_ingest.status_code == 201
    ingest_data = res_ingest.json()
    assert ingest_data["is_duplicate"] is False
    assert len(ingest_data["content_hash"]) > 10

    # 3. Duplicate ingestion of identical content -> marked is_duplicate = True
    res_dup = client.post(f"/api/v1/research-reliability/projects/{proj.id}/sources/ingest", json=text_payload, headers=headers)
    assert res_dup.status_code == 201
    dup_data = res_dup.json()
    assert dup_data["is_duplicate"] is True
    assert dup_data["source_id"] == ingest_data["source_id"]


def test_sentence_level_evidence_extraction(client, test_research_tenants, db_session):
    """Test 3: Sentence-level evidence extraction produces atomic excerpts with fact type classification."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    s1 = data["s1"]

    ev_rows = db_session.query(ResearchEvidence).filter(ResearchEvidence.source_id == s1.id).all()
    assert len(ev_rows) >= 3
    for ev in ev_rows:
        assert len(ev.excerpt) >= 40
        assert ev.fact_type in ("DIRECT_FACT", "REPORTED_FACT", "INFERENCE")
        assert ev.confidence >= 0.85
        assert ev.verified is True


def test_six_tier_claim_verification(client, test_research_tenants, db_session):
    """Test 4: Classifies claims into SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, NOT_APPLICABLE."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    brief = data["brief"]

    res = client.get(f"/api/v1/research-reliability/projects/{proj.id}/claims?brief_id={brief.id}", headers=headers)
    assert res.status_code == 200
    claims = res.json()
    assert len(claims) >= 3

    statuses = [c["verification_status"] for c in claims]
    types = [c["claim_type"] for c in claims]

    # Must contain SUPPORTED (DeepSeek-R1 mathematical benchmark statement)
    assert "SUPPORTED" in statuses
    # Must contain NOT_APPLICABLE (Opinion statement "In our opinion, this represents...")
    assert "NOT_APPLICABLE" in statuses
    assert any(t in ("OPINION", "PREDICTION", "RECOMMENDATION") for t in types)
    # Must contain UNSUPPORTED (Quantum cryptography statement)
    assert "UNSUPPORTED" in statuses

    # Verify supporting evidence passages attached to SUPPORTED claim
    supported_claim = next(c for c in claims if c["verification_status"] == "SUPPORTED")
    assert len(supported_claim["supporting_evidence"]) >= 1
    assert "DeepSeek" in supported_claim["supporting_evidence"][0]["excerpt"]


def test_citation_validation_and_antifabrication(client, test_research_tenants, db_session):
    """Test 5: Validates authentic citations and detects fabricated references citing non-existent sources."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    brief = data["brief"]

    res = client.post(f"/api/v1/research-reliability/projects/{proj.id}/validate-citations?brief_id={brief.id}", headers=headers)
    assert res.status_code == 200
    citations = res.json()
    assert len(citations) == 3

    # 1. Authentic citations to ArXiv and OpenAI
    valid_citations = [c for c in citations if c["status"] == "VALID"]
    assert len(valid_citations) >= 2
    for vc in valid_citations:
        assert vc["is_fabricated"] is False
        assert vc["validation_details"]["source_record_found"] is True

    # 2. Fabricated citation
    fabricated = [c for c in citations if c["is_fabricated"] is True]
    assert len(fabricated) == 1
    assert fabricated[0]["status"] == "INVALID"
    assert "Fabricated Citation" in fabricated[0]["citation_text"]
    assert fabricated[0]["validation_details"]["source_record_found"] is False


def test_corroboration_and_contradiction_analysis(client, test_research_tenants, db_session):
    """Test 6: Evaluates multi-publisher corroboration and cross-source discrepancies."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    seed_research_data_for_project(db_session, proj.id)

    res = client.get(f"/api/v1/research-reliability/projects/{proj.id}/corroboration", headers=headers)
    assert res.status_code == 200
    corrob = res.json()

    assert corrob["unique_domains_count"] >= 2
    assert corrob["corroboration_tier"] in ("STRONG_INDEPENDENT_CORROBORATION", "MODERATE_CROSS_PUBLISHER")
    assert corrob["contradictions_count"] >= 1
    assert len(corrob["contradictions"]) >= 1
    assert "Training cost" in corrob["contradictions"][0]["claim_a"]


def test_research_quality_report_generation(client, test_research_tenants, db_session):
    """Test 7: Generates comprehensive Research Quality Report with evidence coverage and grade."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    brief = data["brief"]

    res = client.get(f"/api/v1/research-reliability/projects/{proj.id}/quality-report?brief_id={brief.id}", headers=headers)
    assert res.status_code == 200
    rep = res.json()

    assert rep["project_id"] == proj.id
    assert rep["total_claims"] >= 4
    assert rep["supported_claims"] >= 1
    assert rep["unsupported_claims"] >= 1
    assert rep["evidence_coverage_score"] > 0.0
    assert rep["overall_quality_grade"] in ("A", "B", "C", "D")
    assert "source_quality_summary" in rep
    assert "corroboration_summary" in rep
    assert len(rep["audit_findings"]) >= 1


def test_evidence_grounded_section_regeneration(client, test_research_tenants, db_session):
    """Test 8: Regenerates section constrained strictly to verified evidence, diffs, and accepts revision."""
    token = test_research_tenants["token_a"]
    proj = test_research_tenants["proj_a"]
    headers = {"Authorization": f"Bearer {token}"}

    data = seed_research_data_for_project(db_session, proj.id)
    brief = data["brief"]

    # 1. Regenerate executive summary
    payload = {
        "section_key": "executive_summary",
        "instructions": "Incorporate training GPU hardware and duration empirical figures."
    }
    res_regen = client.post(
        f"/api/v1/research-reliability/projects/{proj.id}/briefs/{brief.id}/regenerate-section",
        json=payload,
        headers=headers
    )
    assert res_regen.status_code == 200
    regen_data = res_regen.json()

    assert regen_data["section_key"] == "executive_summary"
    assert len(regen_data["diff_summary"]) > 10
    assert len(regen_data["supporting_evidence_ids"]) >= 1
    assert regen_data["status"] == "PENDING"
    revision_id = regen_data["revision_id"]

    # 2. Accept section revision
    res_accept = client.post(f"/api/v1/research-reliability/revisions/{revision_id}/accept", headers=headers)
    assert res_accept.status_code == 200
    accept_data = res_accept.json()
    assert accept_data["status"] == "ACCEPTED"
    assert accept_data["new_version"] >= 2

    # Verify brief updated in DB
    db_session.refresh(brief)
    assert "Grounded Evidence Revision" in brief.executive_summary
    assert brief.version >= 2


def test_tenant_isolation_on_research_reliability(client, test_research_tenants, db_session):
    """Test 9: Strict multi-tenant isolation prevents cross-tenant access to research reliability."""
    token_b = test_research_tenants["token_b"]
    proj_a = test_research_tenants["proj_a"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    seed_research_data_for_project(db_session, proj_a.id)

    # Org B attempts to query Org A's quality report -> 404
    res_b = client.get(f"/api/v1/research-reliability/projects/{proj_a.id}/quality-report", headers=headers_b)
    assert res_b.status_code == 404

    # Org B attempts to validate Org A's citations -> 404
    res_cit_b = client.post(f"/api/v1/research-reliability/projects/{proj_a.id}/validate-citations", headers=headers_b)
    assert res_cit_b.status_code == 404
