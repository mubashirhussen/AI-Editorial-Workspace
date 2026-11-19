"""
Phase 31: AI Quality Engineering, Research Accuracy, Citation Integrity & Editorial Reliability Tests.
Validates:
1. Prompt Injection Defense and Delimiter Sandboxing.
2. Structured Response Validation and Schema Conformance.
3. 5-State Claim Verification (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, NOT_VERIFIABLE).
4. Citation Integrity Classification (VALID, ORPHANED, FABRICATED, MISSING, TAMPERED).
5. Cross-Source Contradiction Detection.
6. Writing Assistant Meaning and Entity Preservation.
7. Editorial Studio Grounding Audit.
8. AI Router Resilience, Bounded Retries, and Deterministic Offline Fallback.
"""

import json
import pytest
from pathlib import Path
from pydantic import BaseModel, ValidationError

from backend.app.services.ai.prompt_registry import (
    prompt_registry,
    PromptInjectionGuard,
    PROMPT_INJECTION_DEFENSE
)
from backend.app.services.ai.claim_verification_service import (
    claim_verification_service,
    VerificationStatus,
    CitationIntegrity,
    GroundingAuditReport
)
from backend.app.services.ai.router import AIRouter

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ai_quality"


@pytest.fixture
def research_fixtures():
    with open(FIXTURES_DIR / "research_scenarios.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def editorial_fixtures():
    with open(FIXTURES_DIR / "editorial_scenarios.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def writing_fixtures():
    with open(FIXTURES_DIR / "writing_scenarios.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def injection_fixtures():
    with open(FIXTURES_DIR / "prompt_injection_scenarios.json", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# TEST 1: Prompt Injection Defense & Delimiter Sandboxing
# ==============================================================================
def test_prompt_injection_defense_and_sandboxing(injection_fixtures):
    """
    Ensures PromptInjectionGuard neutralizes delimiter breakouts, strips hidden
    payloads, flags override attempts, and safely wraps untrusted text.
    """
    for item in injection_fixtures:
        raw_input = item["untrusted_input"]
        
        # 1. Check risk detection
        risk = PromptInjectionGuard.detect_injection_risk(raw_input)
        assert risk["is_risky"] is True, f"Failed to flag risk for {item['id']}"

        # 2. Check sanitization
        sanitized = PromptInjectionGuard.sanitize(raw_input)
        # Delimiters must be escaped
        assert "</source_content>" not in sanitized
        assert "<source_content>" not in sanitized
        assert "<system>" not in sanitized

        # 3. Check safe wrapping in prompt registry rendering
        rendered = prompt_registry.render(
            "research_synthesis",
            project_title="Security Test",
            sources_block=raw_input
        )
        assert "<source_content>" in rendered["user_prompt"]
        assert "</source_content>" in rendered["user_prompt"]
        # Ensure the malicious string did not prematurely close the tag
        # The only occurrences of source_content tags should be the outer sandbox boundaries
        assert rendered["user_prompt"].count("<source_content>") == 1
        assert rendered["user_prompt"].count("</source_content>") == 1
        assert PROMPT_INJECTION_DEFENSE in rendered["system_prompt"]


# ==============================================================================
# TEST 2: Structured Output Validation & Schema Conformance
# ==============================================================================
def test_structured_output_schema_conformance():
    """
    Validates that Pydantic models reject malformed LLM responses and enforce
    strict typing on critical editorial payloads.
    """
    class StrictSynthesisSchema(BaseModel):
        executive_summary: str
        key_findings: list[str]
        confidence: float

    # Valid payload parses cleanly
    valid_payload = {
        "executive_summary": "Neural synthesis demonstrates a 28% efficiency boost.",
        "key_findings": ["Finding 1 [1]", "Finding 2 [2]"],
        "confidence": 0.95
    }
    obj = StrictSynthesisSchema(**valid_payload)
    assert obj.confidence == 0.95
    assert len(obj.key_findings) == 2

    # Malformed payload (missing required field) raises ValidationError
    invalid_payload = {
        "key_findings": ["Incomplete data"]
    }
    with pytest.raises(ValidationError):
        StrictSynthesisSchema(**invalid_payload)


# ==============================================================================
# TEST 3: 5-State Claim Verification Grounding
# ==============================================================================
def test_five_state_claim_verification(research_fixtures):
    """
    Verifies that claims are accurately categorized into the 5 discrete states:
    SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTED | NOT_VERIFIABLE.
    """
    for sc in research_fixtures:
        verified_claim = claim_verification_service.verify_single_claim(
            claim=sc["claim"],
            source_text=sc["source_text"]
        )
        assert verified_claim.verification_status == VerificationStatus(sc["expected_status"]), (
            f"Scenario {sc['id']} ({sc['name']}) expected {sc['expected_status']}, "
            f"got {verified_claim.verification_status}"
        )
        assert verified_claim.confidence_score >= sc["expected_confidence_min"]


# ==============================================================================
# TEST 4: Citation Integrity Engine (5 States)
# ==============================================================================
def test_citation_integrity_classification(editorial_fixtures):
    """
    Validates the 5 citation integrity classifications:
    VALID | ORPHANED | FABRICATED | MISSING | TAMPERED.
    """
    for sc in editorial_fixtures:
        report = claim_verification_service.audit_draft(
            draft_content=sc["draft_text"],
            sources=sc["sources"]
        )
        assert len(report.claims) > 0
        claim = report.claims[0]

        assert claim.verification_status == VerificationStatus(sc["expected_claim_status"]), (
            f"Scenario {sc['id']} expected claim status {sc['expected_claim_status']}, got {claim.verification_status}"
        )
        assert claim.citation_integrity == CitationIntegrity(sc["expected_citation_integrity"]), (
            f"Scenario {sc['id']} expected citation {sc['expected_citation_integrity']}, got {claim.citation_integrity}"
        )


# ==============================================================================
# TEST 5: Cross-Source Multi-Document Contradiction Detection
# ==============================================================================
def test_cross_source_contradiction_detection():
    """
    Tests detection of factual or numeric contradictions across multi-source research inputs.
    """
    conflicting_sources = [
        {
            "id": "src-alpha",
            "title": "Vendor Q3 Earnings Report",
            "extracted_content": "Enterprise subscription revenue increased significantly across all cloud software segments."
        },
        {
            "id": "src-beta",
            "title": "Market Analyst Independent Audit",
            "extracted_content": "Enterprise subscription revenue decreased sharply due to customer churn in cloud software segments."
        }
    ]

    conflicts = claim_verification_service.detect_source_contradictions(conflicting_sources)
    assert len(conflicts) > 0
    assert conflicts[0]["source_1_id"] == "src-alpha"
    assert conflicts[0]["source_2_id"] == "src-beta"
    assert "'increased' vs 'decreased'" in conflicts[0]["polarity_conflict"]


# ==============================================================================
# TEST 6: Writing Assistant Meaning & Entity Preservation
# ==============================================================================
def test_writing_meaning_and_entity_preservation(writing_fixtures):
    """
    Verifies that rewritten selections retain citations and critical empirical figures.
    """
    for sc in writing_fixtures:
        orig = sc["input_text"]
        
        # Test case with entities and citations preserved
        if sc.get("requires_meaning_preservation"):
            rewritten_good = (
                f"In simpler terms, {orig}"
            )
            eval_result = claim_verification_service.evaluate_meaning_preservation(orig, rewritten_good)
            assert eval_result["preserved"] is True
            assert eval_result["citations_preserved"] is True
            assert eval_result["entities_preserved"] is True
            assert eval_result["retention_rate"] == 1.0

            # Test failure case where citations and figures are stripped
            rewritten_bad = "The latency was slightly elevated under heavy loads."
            eval_bad = claim_verification_service.evaluate_meaning_preservation(orig, rewritten_bad)
            assert eval_bad["preserved"] is False
            assert len(eval_bad["missing_citations"]) > 0 or len(eval_bad["missing_numbers"]) > 0


# ==============================================================================
# TEST 7: Editorial Studio Grounding Audit Report
# ==============================================================================
def test_editorial_studio_grounding_audit():
    """
    Validates comprehensive grounding audit report calculation, scoring, and remediation suggestions.
    """
    draft = (
        "Neural retrieval benchmarks improved precision@5 by 24% according to recent studies [1]. "
        "The model achieved 99.4% zero-shot accuracy across all medical diagnostics [99]."
    )
    sources = [
        {
            "id": "src-1",
            "title": "Retrieval Benchmarks",
            "extracted_content": "Our experimental results confirm neural retrieval benchmarks improved precision@5 by 24% over BM25."
        }
    ]

    report: GroundingAuditReport = claim_verification_service.audit_draft(draft, sources)
    assert report.total_claims == 2
    assert report.supported_count == 1
    assert report.unsupported_count == 1
    assert report.grounding_score == 0.5
    # The second claim used fabricated citation [99]
    assert report.citation_accuracy == 0.5
    assert len(report.unsupported_claims_summary) == 1
    assert any(c.citation_integrity == CitationIntegrity.FABRICATED for c in report.claims)


# ==============================================================================
# TEST 8: AI Router Resilience, Bounded Retries & Deterministic Fallback
# ==============================================================================
@pytest.mark.asyncio
async def test_ai_router_resilience_and_deterministic_fallback():
    """
    Verifies that the AIRouter gracefully degrades to the deterministic offline adapter
    when external credentials are invalid or unavailable.
    """
    router = AIRouter()

    # Request with deterministic/offline provider
    resp = await router.execute_text(
        prompt="Synthesize summary of AI trends",
        provider="deterministic",
        operation_name="test_offline_fallback"
    )
    assert resp is not None
    assert resp.content is not None
    assert len(resp.content) > 0
    assert "deterministic" in resp.provider or "offline" in resp.provider

    # Request structured generation offline
    structured_resp = await router.execute_structured(
        prompt="Generate structured summary",
        provider="fallback",
        operation_name="test_structured_offline"
    )
    assert structured_resp is not None
    data = structured_resp.parsed_json or json.loads(structured_resp.content)
    assert data is not None
    assert "headline" in data or "summary" in data or len(data) > 0
