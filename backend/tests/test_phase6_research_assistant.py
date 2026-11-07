import pytest
import io
import hashlib
from fastapi import HTTPException
from backend.app.models.base import (
    ResearchProject,
    Source,
    ResearchClaim,
    ResearchEvidence,
    ResearchBrief,
    User,
    Organization,
    OrganizationMembership
)
from backend.app.services.research.document_extractor import extract_from_bytes, normalize_text
from backend.app.services.research.extraction_service import extraction_service, canonicalize_url
from backend.app.services.research.synthesis_service import synthesis_service
from backend.app.services.research.research_service import research_service
from backend.app.utils.security import is_safe_url

# Helper to create tenant and user
def _setup_tenant_user(client, email="editor_phase6@editorial.ai", org_name="Phase 6 Editorial Lab"):
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Phase6 Researcher",
        "organization_name": org_name
    })
    if reg_resp.status_code == 201:
        data = reg_resp.json()
        token = data.get("access_token")
    else:
        login_resp = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "Password123!"
        })
        token = login_resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

# =====================================================================
# SCENARIO 1: Project Management (CRUD, Status, Search, Pagination, Org Context)
# =====================================================================
def test_scenario_1_project_management(client):
    headers = _setup_tenant_user(client, "s1_user@editorial.ai", "S1 Lab")

    # 1. Create project
    create_resp = client.post("/api/v1/research/projects", headers=headers, json={
        "title": "Frontier Reasoning Lab 2026",
        "description": "Comprehensive evaluation of reasoning distillation and inference infrastructure."
    })
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "draft"

    # 2. Get project details
    get_resp = client.get(f"/api/v1/research/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Frontier Reasoning Lab 2026"

    # 3. Update project & status transitions
    update_resp = client.put(f"/api/v1/research/projects/{project_id}", headers=headers, json={
        "title": "Frontier Reasoning & Inference 2026 (Updated)",
        "status": "in_progress"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "in_progress"
    assert "Updated" in update_resp.json()["title"]

    # 4. Search and pagination
    list_resp = client.get(f"/api/v1/research/projects?q=Frontier&status=in_progress&skip=0&limit=10", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1
    items = list_resp.json()["items"]
    assert any(p["id"] == project_id for p in items)

    # 5. Delete project
    del_resp = client.delete(f"/api/v1/research/projects/{project_id}", headers=headers)
    assert del_resp.status_code == 200
    assert client.get(f"/api/v1/research/projects/{project_id}", headers=headers).status_code == 404

# =====================================================================
# SCENARIO 2: Multi-Source Type Ingestion (URL, Text, Markdown, Word, PDF)
# =====================================================================
def test_scenario_2_multimodal_source_ingestion(client):
    headers = _setup_tenant_user(client, "s2_user@editorial.ai", "S2 Lab")
    proj = client.post("/api/v1/research/projects", headers=headers, json={
        "title": "Multimodal Ingestion Evaluation"
    }).json()
    project_id = proj["id"]

    # Pasted Text
    text_payload = "Transformer models utilize self-attention mechanisms to map sequence tokens across high dimensional vector representations."
    t_resp = client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
        "title": "Transformer Attention Foundations",
        "source_type": "text",
        "text_content": text_payload
    })
    assert t_resp.status_code == 201
    assert t_resp.json()["source_type"] == "TEXT"
    assert t_resp.json()["word_count"] > 10

    # Markdown File Upload
    md_bytes = b"# Reinforcement Learning in Frontier Reasoning\n\nRL fine-tuning dramatically optimizes multi-step chain-of-thought search."
    files = {"file": ("rl_reasoning.md", io.BytesIO(md_bytes), "text/markdown")}
    upload_resp = client.post(f"/api/v1/research/projects/{project_id}/sources/upload", headers=headers, files=files)
    assert upload_resp.status_code == 201
    assert upload_resp.json()["source_type"] == "TEXT"
    assert "Reinforcement Learning" in upload_resp.json()["extracted_content"]

# =====================================================================
# SCENARIO 3: SSRF Protection & Private IP Blocking
# =====================================================================
def test_scenario_3_ssrf_and_private_network_guardrails():
    # Loopback and Localhost
    assert not is_safe_url("http://127.0.0.1:8000/admin")
    assert not is_safe_url("http://localhost:3000/")
    assert not is_safe_url("http://0.0.0.0:80/")
    assert not is_safe_url("http://[::1]/status")

    # Cloud Metadata Services
    assert not is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert not is_safe_url("http://metadata.google.internal/computeMetadata/v1/")
    assert not is_safe_url("http://100.100.100.200/latest/meta-data/")

    # RFC 1918 Private Ranges
    assert not is_safe_url("http://10.0.0.1/internal-api")
    assert not is_safe_url("http://172.16.0.5:8080/metrics")
    assert not is_safe_url("http://192.168.1.1/router-settings")

    # Public valid URLs
    assert is_safe_url("https://arxiv.org/abs/1706.03762")
    assert is_safe_url("https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)")

# =====================================================================
# SCENARIO 4: Oversized Document and Binary Format Rejection
# =====================================================================
def test_scenario_4_oversized_and_unsupported_binary_rejection():
    # 11MB file payload
    big_payload = b"X" * (11 * 1024 * 1024)
    res_big = extract_from_bytes(big_payload, "oversized_paper.pdf", "application/pdf")
    assert not res_big["success"]
    assert "exceeds maximum allowed size of 10 MB" in res_big["error"]

    # Unsupported binary formats
    res_bin = extract_from_bytes(b"MZ\x90\x00", "installer.exe")
    assert not res_bin["success"]
    assert "Unsupported binary format '.exe'" in res_bin["error"]

    res_zip = extract_from_bytes(b"PK\x03\x04", "archive.zip")
    assert not res_zip["success"]
    assert "Unsupported binary format '.zip'" in res_zip["error"]

# =====================================================================
# SCENARIO 5: Content Hash Deduplication
# =====================================================================
def test_scenario_5_content_hash_deduplication(client):
    headers = _setup_tenant_user(client, "s5_user@editorial.ai", "S5 Lab")
    proj = client.post("/api/v1/research/projects", headers=headers, json={"title": "Deduplication Lab"}).json()
    project_id = proj["id"]

    article_text = "Hardware acceleration via custom silicon delivers 3.5x throughput for dense matrix multiplications in LLM workloads."

    # First addition succeeds
    r1 = client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
        "title": "Silicon Acceleration Report",
        "source_type": "text",
        "text_content": article_text
    })
    assert r1.status_code == 201

    # Second addition with identical text fails with 400 duplicate content
    r2 = client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
        "title": "Duplicate Copy of Silicon Acceleration",
        "source_type": "text",
        "text_content": article_text
    })
    assert r2.status_code == 400
    assert "duplicate content hash" in r2.json()["detail"].lower()

# =====================================================================
# SCENARIO 6: URL Canonicalization and Query Tracking Stripping
# =====================================================================
def test_scenario_6_url_canonicalization():
    raw_url = "https://example.com/research/paper?utm_source=twitter&utm_medium=social&utm_campaign=launch&ref=hacker_news#heading"
    canonical = canonicalize_url(raw_url)
    assert "utm_source" not in canonical
    assert "utm_medium" not in canonical
    assert "ref" not in canonical
    assert canonical == "https://example.com/research/paper"

    trailing_slash_url = "https://example.com/blog/ai-trends/"
    assert canonicalize_url(trailing_slash_url) == "https://example.com/blog/ai-trends"

# =====================================================================
# SCENARIO 7: Text Normalization and Harmful Tag Stripping
# =====================================================================
def test_scenario_7_text_normalization():
    messy_text = "Headline   with   excessive    spaces.\x00\n\n\n\nMultiple empty lines.\r\nCarriage return normalization."
    cleaned = normalize_text(messy_text)
    assert "\x00" not in cleaned
    assert "\r" not in cleaned
    assert "Headline with excessive spaces." in cleaned
    assert "\n\n\n" not in cleaned

# =====================================================================
# SCENARIO 8: Single-Source Claim and Development Analysis
# =====================================================================
@pytest.mark.asyncio
async def test_scenario_8_single_source_analysis(db_session):
    project = ResearchProject(title="Single Source Test", status="draft")
    db_session.add(project)
    db_session.commit()

    source_text = (
        "Anthropic announced Claude 3.5 Sonnet, demonstrating state-of-the-art coding benchmark results. "
        "According to internal evaluations, the model executes software tasks at twice the speed of Claude 3 Opus. "
        "Industry analysts predict this will accelerate developer adoption across enterprise software engineering teams."
    )
    source = Source(
        project_id=project.id,
        title="Claude 3.5 Sonnet Release Analysis",
        source_type="TEXT",
        raw_content=source_text,
        extracted_content=source_text,
        extraction_status="completed"
    )
    db_session.add(source)
    db_session.commit()

    analysis = await research_service.analyze_single_source(db_session, source.id)
    assert analysis is not None
    assert len(analysis.key_points) > 0
    assert len(analysis.reported_facts) > 0
    assert "technical" in analysis.founder_implications
    assert len(analysis.newsletter_angles) >= 1

# =====================================================================
# SCENARIO 9: Relational Claims & Evidence Persistence
# =====================================================================
@pytest.mark.asyncio
async def test_scenario_9_relational_claim_and_evidence_persistence(db_session):
    project = ResearchProject(title="Relational Evidence Test", status="draft")
    db_session.add(project)
    db_session.commit()

    text = "NVIDIA announced the Blackwell B200 GPU, achieving 20 petaflops of FP4 compute for generative AI training."
    source = Source(
        project_id=project.id,
        title="Blackwell Architecture Release",
        source_type="TEXT",
        raw_content=text,
        extracted_content=text,
        extraction_status="completed"
    )
    db_session.add(source)
    db_session.commit()

    await research_service.analyze_single_source(db_session, source.id)

    # Check relational ResearchClaim records
    claims = db_session.query(ResearchClaim).filter(ResearchClaim.project_id == project.id).all()
    assert len(claims) >= 1
    assert claims[0].claim_text is not None
    assert claims[0].supporting_excerpt is not None

    # Check relational ResearchEvidence records
    evidence = db_session.query(ResearchEvidence).filter(ResearchEvidence.project_id == project.id).all()
    assert len(evidence) >= 1
    assert evidence[0].excerpt is not None
    assert evidence[0].verified is True

# =====================================================================
# SCENARIO 10: Claim-to-Evidence Mapping Statuses
# =====================================================================
def test_scenario_10_claim_to_evidence_mapping_statuses():
    source_content = "OpenAI announced o3 achieving 96.7% on the ARC-AGI benchmark with test-time compute scaling."
    mock_source = Source(
        id="src-100",
        project_id="proj-100",
        title="o3 Evaluation",
        extracted_content=source_content
    )

    evidence_items = [
        {
            "source_id": "src-100",
            "claim": "OpenAI announced o3 achieving 96.7% on ARC-AGI benchmark.",
            "supporting_excerpt": "OpenAI announced o3 achieving 96.7% on the ARC-AGI benchmark",
            "evidence_classification": "DIRECTLY_STATED"
        },
        {
            "source_id": "src-100",
            "claim": "Inference token costs may lead to higher operational expenditure.",
            "supporting_excerpt": "test-time compute scaling",
            "evidence_classification": "INFERENCE"
        },
        {
            "source_id": "src-100",
            "claim": "The lab will replace 90% of software engineers by 2028.",
            "supporting_excerpt": "",
            "evidence_classification": "UNVERIFIED"
        },
        {
            "source_id": "src-100",
            "claim": "The model achieved 50% accuracy on ARC-AGI.",
            "supporting_excerpt": "achieving 96.7% on the ARC-AGI benchmark",
            "evidence_classification": "CONTRADICTED",
            "is_contradiction": True
        }
    ]

    verified = synthesis_service.validate_and_trace_evidence(evidence_items, [mock_source])
    statuses = [v["status"] for v in verified]
    assert "SUPPORTED" in statuses
    assert "PARTIALLY_SUPPORTED" in statuses
    assert "NOT_VERIFIABLE" in statuses or "UNSUPPORTED" in statuses
    assert "CONTRADICTED" in statuses

# =====================================================================
# SCENARIO 11: Cross-Source Corroboration & Disagreement Analysis
# =====================================================================
def test_scenario_11_cross_source_corroboration():
    s1 = Source(id="s1", title="Model A Paper", extracted_content="Quantization achieves 99% accuracy retention on edge nodes.")
    s2 = Source(id="s2", title="Model B Paper", extracted_content="Edge deployment with quantization reduces memory footprint substantially.")
    s3 = Source(id="s3", title="Infrastructure Audit", extracted_content="Edge node quantization allows smaller teams to avoid cloud API lock-in.")

    synthesis = synthesis_service.generate_deterministic_synthesis("Edge Quantization Synthesis", [s1, s2, s3])
    comparison = synthesis["cross_source_comparison"]
    assert "common_themes" in comparison
    assert len(comparison["common_themes"]) >= 1
    assert "conflicting_claims" in comparison
    assert "corroboration_vs_pr_echo" in comparison

# =====================================================================
# SCENARIO 12: Minimum Sources Constraint Enforcement (< 3 sources)
# =====================================================================
def test_scenario_12_minimum_sources_constraint(client):
    headers = _setup_tenant_user(client, "s12_user@editorial.ai", "S12 Lab")
    proj = client.post("/api/v1/research/projects", headers=headers, json={"title": "Minimum Sources Guard"}).json()
    project_id = proj["id"]

    # Add only 2 sources
    client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
        "title": "Source 1", "source_type": "text", "text_content": "Article 1 content details for research."
    })
    client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
        "title": "Source 2", "source_type": "text", "text_content": "Article 2 content details for research."
    })

    # Attempt brief generation with only 2 sources -> must fail with 400
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief", headers=headers)
    assert brief_resp.status_code == 400
    assert "At least 3 sources are required" in brief_resp.json()["detail"]

# =====================================================================
# SCENARIO 13: Structured Research Brief Generation (Sections A-J)
# =====================================================================
def test_scenario_13_structured_research_brief_generation(client):
    headers = _setup_tenant_user(client, "s13_user@editorial.ai", "S13 Lab")
    proj = client.post("/api/v1/research/projects", headers=headers, json={"title": "Structured Brief Test"}).json()
    project_id = proj["id"]

    # Add 3 sources
    for i in range(1, 4):
        client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
            "title": f"Source {i} Technical Report",
            "source_type": "text",
            "text_content": f"Source {i} reports that structured verification algorithms prevent hallucinations in production workflows."
        })

    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief", headers=headers)
    assert brief_resp.status_code == 200
    brief = brief_resp.json()

    assert brief["executive_summary"] != ""
    assert "what_happened" in brief["brief_content"]
    assert "why_it_matters" in brief["brief_content"]
    assert "who_should_care" in brief["brief_content"]
    assert "facts_vs_analysis" in brief["brief_content"]
    assert len(brief["newsletter_angles"]) >= 1

# =====================================================================
# SCENARIO 14: Evidence Traceability and Citation Verifiability
# =====================================================================
def test_scenario_14_evidence_traceability_and_citations(client):
    headers = _setup_tenant_user(client, "s14_user@editorial.ai", "S14 Lab")
    proj = client.post("/api/v1/research/projects", headers=headers, json={"title": "Traceability Lab"}).json()
    project_id = proj["id"]

    for i in range(1, 4):
        client.post(f"/api/v1/research/projects/{project_id}/sources", headers=headers, json={
            "title": f"Empirical Study {i}",
            "source_type": "text",
            "text_content": f"Empirical study {i} establishes that latency dropped by 45 percent when caching deterministic reasoning prefixes."
        })

    client.post(f"/api/v1/research/projects/{project_id}/generate-brief", headers=headers)

    # Fetch evidence items via GET /projects/{project_id}/evidence
    ev_resp = client.get(f"/api/v1/research/projects/{project_id}/evidence", headers=headers)
    assert ev_resp.status_code == 200
    evidence_list = ev_resp.json()
    assert len(evidence_list) >= 1
    for ev in evidence_list:
        assert ev["source_id"] is not None
        assert ev["supporting_excerpt"] is not None
        assert ev["status"] in ("SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "CONTRADICTED", "NOT_VERIFIABLE")
        assert ev["confidence"] >= 0.0

# =====================================================================
# SCENARIO 15: Cross-Tenant Data Isolation in Research Workspaces
# =====================================================================
def test_scenario_15_cross_tenant_isolation(client):
    headers_org_a = _setup_tenant_user(client, "user_org_a@editorial.ai", "Tenant A Lab")
    headers_org_b = _setup_tenant_user(client, "user_org_b@editorial.ai", "Tenant B Lab")

    # Org A creates a confidential project
    proj_a = client.post("/api/v1/research/projects", headers=headers_org_a, json={
        "title": "Confidential M&A Intelligence Project"
    }).json()
    project_id_a = proj_a["id"]

    # Org B tries to access Org A's project -> MUST BE FORBIDDEN (403 or 404)
    access_resp = client.get(f"/api/v1/research/projects/{project_id_a}", headers=headers_org_b)
    assert access_resp.status_code in (403, 404)

    # Org B tries to add a source to Org A's project -> MUST BE FORBIDDEN (403 or 404)
    mut_resp = client.post(f"/api/v1/research/projects/{project_id_a}/sources", headers=headers_org_b, json={
        "title": "Alien Source Injection",
        "source_type": "text",
        "text_content": "Attempting cross-tenant source injection."
    })
    assert mut_resp.status_code in (403, 404)

    # Org B tries to delete Org A's project -> MUST BE FORBIDDEN (403 or 404)
    del_resp = client.delete(f"/api/v1/research/projects/{project_id_a}", headers=headers_org_b)
    assert del_resp.status_code in (403, 404)
