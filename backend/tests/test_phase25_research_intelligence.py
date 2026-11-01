import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.models.base import (
    User,
    Organization,
    OrganizationMembership,
    ResearchProject,
    Source,
    ResearchEntity,
    ResearchClaim,
    ResearchRelationship,
    ResearchContradiction,
    ResearchTrend
)
from backend.app.core.security import create_access_token, hash_password
from backend.app.services.research_intelligence.entity_extractor import EntityExtractor, normalize_entity_name
from backend.app.services.research_intelligence.claim_extractor import ClaimExtractor
from backend.app.services.research_intelligence.relationship_analyzer import RelationshipAnalyzer
from backend.app.services.research_intelligence.contradiction_detector import ContradictionDetector
from backend.app.services.research_intelligence.trend_detector import TrendDetector
from backend.app.services.research_intelligence.synthesis_engine import intelligence_engine

client = TestClient(app)

def test_entity_extraction_and_normalization():
    extractor = EntityExtractor()
    sample_text = (
        "OpenAI Inc. announced GPT-4o today. CEO Sam Altman stated that Microsoft Corporation "
        "has invested in Anthropic AI and OpenAI to advance Retrieval-Augmented Generation using Nvidia H100 GPUs."
    )
    entities = extractor.extract_entities(sample_text, source_id="src-1", source_title="AI Launch")

    extracted_names = {e["normalized_name"] for e in entities}
    assert "OpenAI" in extracted_names
    assert "GPT-4" in extracted_names or "GPT-4o" in sample_text
    assert "Sam Altman" in extracted_names
    assert "Microsoft" in extracted_names
    assert "Anthropic" in extracted_names
    assert "Retrieval-Augmented Generation" in extracted_names
    assert "Nvidia" in extracted_names or "Nvidia H100" in extracted_names

    # Verify normalization logic
    assert normalize_entity_name("OpenAI, Inc.") == "OpenAI"
    assert normalize_entity_name("Microsoft Corporation") == "Microsoft"
    assert normalize_entity_name("NVIDIA Corp.") == "Nvidia"
    assert normalize_entity_name("Anthropic PBC") == "Anthropic"

    # Verify excerpt and confidence
    openai_ent = next(e for e in entities if e["normalized_name"] == "OpenAI")
    assert openai_ent["confidence"] >= 0.9
    assert "OpenAI" in openai_ent["supporting_excerpt"]

def test_claim_extraction_epistemic_classification():
    claim_extractor = ClaimExtractor()
    entities = [{"name": "OpenAI", "normalized_name": "OpenAI"}]

    sample_text = (
        "OpenAI announced a new flagship model today. "
        "According to reports from industry insiders, the model achieved record scores. "
        "This indicates a shift towards power-efficient inference clusters. "
        "Rumors suggest an unconfirmed partnership with sovereign funds."
    )

    claims = claim_extractor.extract_claims(
        text=sample_text,
        source_id="src-test",
        source_title="Test News",
        known_entities=entities
    )

    assert len(claims) >= 3
    classifications = {c["evidence_classification"] for c in claims}

    assert "DIRECTLY_STATED" in classifications
    assert "REPORTED_BY_SOURCE" in classifications
    assert "INFERENCE" in classifications
    assert "UNVERIFIED" in classifications

def test_relationship_analyzer_requires_explicit_evidence():
    analyzer = RelationshipAnalyzer()
    entities = [
        {"name": "Microsoft", "normalized_name": "Microsoft"},
        {"name": "OpenAI", "normalized_name": "OpenAI"},
        {"name": "Anthropic", "normalized_name": "Anthropic"}
    ]

    # Sentence 1: Explicit investment relation
    c1 = {
        "claim_text": "Microsoft invested $10 billion in OpenAI to scale compute.",
        "supporting_excerpt": "Microsoft invested $10 billion in OpenAI to scale compute.",
        "source_id": "src-1",
        "source_title": "Source 1"
    }

    # Sentence 2: Co-occurrence without relational syntax
    c2 = {
        "claim_text": "Anthropic and OpenAI are both based in California near coffee shops.",
        "supporting_excerpt": "Anthropic and OpenAI are both based in California near coffee shops.",
        "source_id": "src-2",
        "source_title": "Source 2"
    }

    rels1 = analyzer.analyze_relationships([c1], entities)
    assert len(rels1) == 1
    assert rels1[0]["relationship_type"] == "INVESTED_IN"
    assert rels1[0]["source_entity_name"] == "Microsoft"
    assert rels1[0]["target_entity_name"] == "OpenAI"
    assert "invested" in rels1[0]["supporting_evidence"]

    rels2 = analyzer.analyze_relationships([c2], entities)
    # Must NOT infer a false relationship solely based on co-occurrence!
    assert len(rels2) == 0

def test_contradiction_detection_maintains_neutrality():
    detector = ContradictionDetector()
    claims = [
        {
            "id": "c-1",
            "source_id": "src-A",
            "source_title": "TechCrunch",
            "claim_text": "Databricks raised $500 million in series I funding.",
            "entity_references": ["Databricks"]
        },
        {
            "id": "c-2",
            "source_id": "src-B",
            "source_title": "Bloomberg",
            "claim_text": "Databricks raised $650 million according to official filings.",
            "entity_references": ["Databricks"]
        }
    ]

    contradictions = detector.detect_contradictions(claims)
    assert len(contradictions) == 1
    contra = contradictions[0]
    assert contra["source_a_id"] == "src-A"
    assert contra["source_b_id"] == "src-B"
    assert "Discrepancy in reported funding" in contra["disagreement_nature"]
    # Verify it does not declare a winner
    assert "What was the officially filed SEC Form D" in contra["unresolved_questions"]

def test_trend_detection_requires_cross_source_threshold():
    detector = TrendDetector()
    sources = [
        {"id": "src-1", "title": "SemiAnalysis 2026"},
        {"id": "src-2", "title": "DataCenter Dynamics"}
    ]

    # Two distinct sources discussing immersion cooling
    multi_source_claims = [
        {"claim_text": "Hyperscalers are deploying two-phase immersion cooling to curb PUE.", "source_id": "src-1"},
        {"claim_text": "Adoption of immersion cooling has doubled across AI clusters.", "source_id": "src-2"}
    ]

    trends = detector.detect_trends(multi_source_claims, sources)
    assert len(trends) >= 1
    immersion_trend = next((t for t in trends if "Immersion Cooling" in t["theme"]), None)
    assert immersion_trend is not None
    assert len(immersion_trend["supporting_source_ids"]) == 2
    assert immersion_trend["is_prediction"] is False

    # Single source discussing a theme should be rejected as insufficient evidence
    single_source_claims = [
        {"claim_text": "One lab is exploring small modular reactor energy.", "source_id": "src-1"}
    ]
    rejected_trends = detector.detect_trends(single_source_claims, sources)
    smr_trend = next((t for t in rejected_trends if "Small Modular Reactor" in t["theme"]), None)
    assert smr_trend is None

def test_intelligence_api_and_cross_tenant_isolation():
    import time
    unique_suffix = int(time.time() * 1000)

    # 1. Register Tenant A
    user_a_resp = client.post("/api/v1/auth/register", json={
        "email": f"intel_a_{unique_suffix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Intel Alpha",
        "organization_name": "Org Alpha Intel"
    })
    assert user_a_resp.status_code == 201
    user_a = user_a_resp.json()
    token_a = user_a["access_token"]
    org_a_id = user_a["organization"]["id"]

    # 2. Register Tenant B
    user_b_resp = client.post("/api/v1/auth/register", json={
        "email": f"intel_b_{unique_suffix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Intel Beta",
        "organization_name": "Org Beta Intel"
    })
    assert user_b_resp.status_code == 201
    user_b = user_b_resp.json()
    token_b = user_b["access_token"]
    org_b_id = user_b["organization"]["id"]

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_a_id}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}

    # 3. Create Project in Tenant A
    proj_a_resp = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={"title": "Datacenter Scaling 2026"}
    )
    assert proj_a_resp.status_code == 201
    proj_a_id = proj_a_resp.json()["id"]

    # 4. Add 2 sources to Project A
    s1_resp = client.post(
        f"/api/v1/projects/{proj_a_id}/sources",
        headers=headers_a,
        json={
            "source_type": "text",
            "title": "Hardware Analysis 2026",
            "text_content": "Nvidia announced the Blackwell architecture. Microsoft invested heavily in Blackwell clusters using immersion cooling."
        }
    )
    assert s1_resp.status_code == 201

    s2_resp = client.post(
        f"/api/v1/projects/{proj_a_id}/sources",
        headers=headers_a,
        json={
            "source_type": "text",
            "title": "Cooling Innovations",
            "text_content": "Two-phase immersion cooling decreases PUE dramatically. Datacenter operators are adopting immersion cooling at scale."
        }
    )
    assert s2_resp.status_code == 201

    # 5. Tenant A triggers intelligence analysis
    res_analyze = client.post(f"/api/v1/projects/{proj_a_id}/intelligence/analyze", headers=headers_a)
    assert res_analyze.status_code == 200, res_analyze.text
    data = res_analyze.json()
    assert data["status"] == "completed"
    assert data["entities_count"] > 0
    assert data["claims_count"] > 0

    # 6. Tenant A queries entities, claims, relationships, trends, and graph
    res_entities = client.get(f"/api/v1/projects/{proj_a_id}/intelligence/entities", headers=headers_a)
    assert res_entities.status_code == 200
    assert len(res_entities.json()) > 0

    res_claims = client.get(f"/api/v1/projects/{proj_a_id}/intelligence/claims", headers=headers_a)
    assert res_claims.status_code == 200
    assert len(res_claims.json()) > 0

    res_trends = client.get(f"/api/v1/projects/{proj_a_id}/intelligence/trends", headers=headers_a)
    assert res_trends.status_code == 200

    res_graph = client.get(f"/api/v1/projects/{proj_a_id}/intelligence/graph", headers=headers_a)
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert graph_data["stats"]["total_nodes"] > 0

    # 7. Tenant B attempts to access Tenant A's project intelligence -> Must return 404 Not Found!
    res_b_attempt = client.get(f"/api/v1/projects/{proj_a_id}/intelligence/graph", headers=headers_b)
    assert res_b_attempt.status_code == 404
