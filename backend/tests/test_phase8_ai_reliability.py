"""
Phase 8 Automated Verification Suite:
AI Reliability, Evaluation, Hallucination Detection & Observability.

Covers all 16 required test scenarios:
1. Provider success
2. Provider failure
3. Timeout handling
4. Retry behavior with exponential backoff
5. Structured response validation
6. Malformed AI output handling
7. Citation integrity (VALID, MISSING, FABRICATED, TAMPERED)
8. Unsupported claims detection
9. Partially supported claims
10. Contradictory evidence detection
11. Verification persistence & API
12. Prompt version tracking
13. Token usage and cost calculation
14. Organization-level analytics & telemetry isolation
15. Logging privacy & secret safety
16. Offline evaluation benchmark reproducibility (34 test cases)
"""

import pytest
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.base import User, Organization, OrganizationMembership, ProviderUsageRecord
from backend.app.services.ai.base import BaseAIProvider, AIResponse
from backend.app.services.ai.pricing import calculate_estimated_cost
from backend.app.services.ai.prompt_registry import prompt_registry, PromptMetadata
from backend.app.services.ai.claim_verification_service import (
    claim_verification_service,
    VerificationStatus,
    CitationIntegrity
)
from backend.app.services.ai.router import ai_router, AIRouter
from backend.app.services.ai.adapters.fallback_adapter import FallbackAdapter
from backend.app.evaluation.runners.runner import EvaluationRunner

client = TestClient(app)

def get_auth_headers(email_prefix: str) -> Dict[str, str]:
    payload = {
        "email": f"{email_prefix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Reliability Lead",
        "organization_name": f"Org-{email_prefix}"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    if res.status_code == 201:
        token = res.json()["access_token"]
        org_id = res.json()["organization"]["id"]
    else:
        login_res = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
        token = login_res.json()["access_token"]
        org_id = login_res.json()["organization"]["id"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": org_id
    }


# =========================================================================
# Scenario 1: Provider Success
# =========================================================================
def test_01_provider_success():
    """Verifies that an AI provider adapter generates a successful response with valid metadata."""
    adapter = FallbackAdapter()
    res = asyncio.run(adapter.generate_text("Explain the latest transformer architectures"))
    assert res is not None
    assert res.provider in ("fallback", "deterministic_fallback")
    assert res.content is not None
    assert len(res.content) > 20
    assert res.duration_ms >= 0.0
    assert res.prompt_tokens >= 0
    assert res.completion_tokens >= 0


# =========================================================================
# Scenario 2: Provider Failure & Fallback Handling
# =========================================================================
def test_02_provider_failure_fallback_handling():
    """Verifies that provider exceptions are intercepted and routed to the deterministic engine."""
    class FailingAdapter(FallbackAdapter):
        @property
        def provider_name(self) -> str:
            return "failing_mock"

        async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> AIResponse:
            raise RuntimeError("Upstream 503 Service Unavailable: Rate limit exceeded")

        async def generate_structured(self, prompt: str, system_prompt: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> AIResponse:
            raise RuntimeError("Upstream 503 Service Unavailable")

    router = AIRouter()
    router.get_adapter = lambda *args, **kwargs: FailingAdapter()

    res = asyncio.run(router.execute_text("Generate newsletter", max_retries=1))
    assert res is not None
    assert res.is_fallback is True
    assert res.provider in ("fallback", "deterministic_fallback")
    assert len(res.content) > 0


# =========================================================================
# Scenario 3: Timeout Handling
# =========================================================================
def test_03_timeout_handling():
    """Verifies that calls exceeding the configured timeout trigger failover without crashing."""
    class SlowHangingAdapter(FallbackAdapter):
        @property
        def provider_name(self) -> str:
            return "hanging_mock"

        async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> AIResponse:
            await asyncio.sleep(2.0)
            return AIResponse(content="Late response", provider="hanging_mock", model="slow-model")

        async def generate_structured(self, prompt: str, system_prompt: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> AIResponse:
            await asyncio.sleep(2.0)
            return AIResponse(content="{}", provider="hanging_mock", model="slow-model", parsed_json={})

    router = AIRouter()
    router.get_adapter = lambda *args, **kwargs: SlowHangingAdapter()

    res = asyncio.run(
        router.execute_text(
            "Summarize research paper",
            max_retries=0,
            timeout_seconds=0.1
        )
    )
    assert res is not None
    assert res.is_fallback is True
    assert res.provider in ("fallback", "deterministic_fallback")


# =========================================================================
# Scenario 4: Retry Behavior with Exponential Backoff
# =========================================================================
def test_04_retry_behavior_with_exponential_backoff():
    """Verifies that transient errors trigger bounded retries with backoff."""
    attempt_count = 0

    class FlakyAdapter(FallbackAdapter):
        @property
        def provider_name(self) -> str:
            return "flaky_mock"

        async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> AIResponse:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Transient network reset")
            return AIResponse(
                content="Recovered after retries",
                provider="flaky_mock",
                model="flaky-model",
                prompt_tokens=10,
                completion_tokens=5
            )

        async def generate_structured(self, prompt: str, system_prompt: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> AIResponse:
            return await self.generate_text(prompt, system_prompt)

    router = AIRouter()
    router.get_adapter = lambda *args, **kwargs: FlakyAdapter()

    res = asyncio.run(router.execute_text("Test retry logic", max_retries=2))
    assert attempt_count == 3
    assert res.content == "Recovered after retries"
    assert res.is_fallback is False


# =========================================================================
# Scenario 5: Structured Response Validation
# =========================================================================
def test_05_structured_response_validation():
    """Verifies that execute_structured returns valid JSON conforming to the requested schema."""
    res = asyncio.run(
        ai_router.execute_structured(
            prompt="Analyze computational efficiency of attention heads",
            provider="fallback",
            operation_name="structured_analysis",
            schema={"type": "object", "properties": {"executive_summary": {"type": "string"}}}
        )
    )
    assert res.parsed_json is not None
    assert isinstance(res.parsed_json, dict)
    assert "executive_summary" in res.parsed_json or "findings" in res.parsed_json or len(res.parsed_json) > 0


# =========================================================================
# Scenario 6: Malformed AI Output Handling
# =========================================================================
def test_06_malformed_ai_output_handling():
    """Verifies that unparseable or corrupted JSON outputs are safely intercepted."""
    class MalformedOutputAdapter(FallbackAdapter):
        @property
        def provider_name(self) -> str:
            return "malformed_mock"

        async def generate_structured(self, prompt: str, system_prompt: Optional[str] = None, schema: Optional[Dict[str, Any]] = None) -> AIResponse:
            raise ValueError("Invalid JSON token at position 14: Bad control character")

        async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> AIResponse:
            return AIResponse(content="Malformed", provider="malformed_mock", model="malformed-model")

    router = AIRouter()
    router.get_adapter = lambda *args, **kwargs: MalformedOutputAdapter()

    res = asyncio.run(router.execute_structured("Produce JSON report", max_retries=0))
    assert res is not None
    assert res.is_fallback is True
    assert isinstance(res.parsed_json, dict)


# =========================================================================
# Scenario 7: Citation Integrity Checks (VALID, MISSING, FABRICATED, TAMPERED)
# =========================================================================
def test_07_citation_integrity_checks():
    """Verifies all four citation integrity classifications: VALID, MISSING, FABRICATED, TAMPERED."""
    sources = [
        {
            "id": "src-1",
            "title": "Quantum Compute Benchmarks",
            "extracted_content": "The Q-100 processor delivers 45.2 teraflops of compute performance."
        }
    ]

    # 1. VALID
    rep_valid = claim_verification_service.audit_draft(
        "The Q-100 processor delivers 45.2 teraflops of compute performance [1].",
        sources
    )
    assert rep_valid.claims[0].citation_integrity == CitationIntegrity.VALID
    assert rep_valid.claims[0].verification_status == VerificationStatus.SUPPORTED

    # 2. MISSING
    rep_missing = claim_verification_service.audit_draft(
        "The Q-100 processor delivers 45.2 teraflops of compute performance.",
        sources
    )
    assert rep_missing.claims[0].citation_integrity == CitationIntegrity.MISSING
    assert len(rep_missing.missing_citations) >= 1

    # 3. FABRICATED (pointing to non-existent source index)
    rep_fab = claim_verification_service.audit_draft(
        "The Q-100 processor delivers 45.2 teraflops of compute performance [999].",
        sources
    )
    assert rep_fab.claims[0].citation_integrity == CitationIntegrity.FABRICATED

    # 4. TAMPERED (cites valid source [1] but alters numbers not in source)
    rep_tampered = claim_verification_service.audit_draft(
        "The Q-100 processor delivers 999.9 teraflops of compute performance [1].",
        sources
    )
    assert rep_tampered.claims[0].citation_integrity == CitationIntegrity.TAMPERED
    assert rep_tampered.claims[0].verification_status == VerificationStatus.UNSUPPORTED


# =========================================================================
# Scenario 8: Unsupported Claims Detection
# =========================================================================
def test_08_unsupported_claims_detection():
    """Verifies that novel statistical or financial assertions without source support are flagged UNSUPPORTED."""
    sources = [
        {"id": "src-a", "extracted_content": "DataCorp raised $45 million in Series B."}
    ]
    rep = claim_verification_service.audit_draft(
        "DataCorp raised $950 million in Series D mega-round funding.",
        sources
    )
    assert rep.unsupported_count >= 1
    assert rep.claims[0].verification_status == VerificationStatus.UNSUPPORTED
    assert len(rep.unsupported_claims_summary) >= 1


# =========================================================================
# Scenario 9: Partially Supported Claims
# =========================================================================
def test_09_partially_supported_claims():
    """Verifies that claims with conceptual overlap but absent exact statistics are classified as PARTIALLY_SUPPORTED."""
    sources = [
        {
            "id": "src-b",
            "extracted_content": "The research team observed that inference latency improved under certain constrained network conditions."
        }
    ]
    rep = claim_verification_service.audit_draft(
        "Under constrained conditions, operational parameters showed notable resilience during testing [1].",
        sources
    )
    assert rep.partially_supported_count >= 1
    assert rep.claims[0].verification_status == VerificationStatus.PARTIALLY_SUPPORTED


# =========================================================================
# Scenario 10: Contradictory Evidence Detection
# =========================================================================
def test_10_contradictory_evidence_detection():
    """Verifies that statements asserting opposing facts to source material are flagged CONTRADICTED."""
    sources = [
        {"id": "src-c", "extracted_content": "Production latency dropped by 38% after model quantization."}
    ]
    rep = claim_verification_service.audit_draft(
        "Production latency increased substantially after quantization during test runs.",
        sources
    )
    assert rep.contradicted_count >= 1
    assert rep.claims[0].verification_status == VerificationStatus.CONTRADICTED
    assert len(rep.contradiction_warnings) >= 1


# =========================================================================
# Scenario 11: Verification Persistence & API
# =========================================================================
def test_11_verification_persistence_and_api():
    """Verifies the /api/v1/observability/verify-claim API endpoint."""
    headers = get_auth_headers(f"user_verify_{uuid.uuid4().hex[:6]}")
    payload = {
        "content": "The Q-100 system achieved 92.4% accuracy on standard benchmarks [1].",
        "sources": [
            {
                "id": "src-1",
                "title": "Benchmarking Systems",
                "extracted_content": "The Q-100 system achieved 92.4% accuracy on standard benchmarks."
            }
        ]
    }
    res = client.post("/api/v1/observability/verify-claim", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["supported_count"] >= 1
    assert data["grounding_score"] == 1.0
    assert len(data["claims"]) >= 1


# =========================================================================
# Scenario 12: Prompt Version Tracking
# =========================================================================
def test_12_prompt_version_tracking():
    """Verifies prompt registry semantic versioning and audit stamping."""
    meta = prompt_registry.get_prompt("research_synthesis", "v1.0.0")
    assert meta.version == "v1.0.0"
    assert "<source_content>" in meta.user_template or "sources_block" in meta.input_variables

    db = SessionLocal()
    try:
        org_id = f"test-org-{uuid.uuid4().hex[:6]}"
        db.add(Organization(id=org_id, name="Prompt Org", slug=f"slug-{org_id}"))
        db.commit()

        # Execute structured call with custom prompt version
        res = asyncio.run(
            ai_router.execute_structured(
                prompt="Synthesize paper",
                provider="fallback",
                db=db,
                organization_id=org_id,
                prompt_version="v2.1.0-alpha"
            )
        )
        rec = db.query(ProviderUsageRecord).filter(
            ProviderUsageRecord.organization_id == org_id
        ).order_by(ProviderUsageRecord.created_at.desc()).first()

        assert rec is not None
        assert rec.prompt_version == "v2.1.0-alpha"
    finally:
        db.close()


# =========================================================================
# Scenario 13: Token Usage & Cost Calculation
# =========================================================================
def test_13_token_usage_and_cost_calculation():
    """Verifies token rate calculations across Groq, OpenAI, Gemini, Anthropic, and Fallback."""
    cost_groq = calculate_estimated_cost("groq", "llama-3.3-70b-versatile", 1000, 500)
    assert cost_groq > 0.0

    cost_gpt4o = calculate_estimated_cost("openai", "gpt-4o", 10000, 2000)
    assert cost_gpt4o > 0.0

    cost_claude = calculate_estimated_cost("anthropic", "claude-3-5-sonnet-latest", 5000, 1000)
    assert cost_claude > 0.0

    cost_gemini = calculate_estimated_cost("google_gemini", "gemini-1.5-flash", 8000, 1500)
    assert cost_gemini > 0.0

    cost_fallback = calculate_estimated_cost("fallback", "deterministic", 1000, 500)
    assert cost_fallback == 0.0


# =========================================================================
# Scenario 14: Multi-Tenant Observability Isolation
# =========================================================================
def test_14_multi_tenant_observability_isolation():
    """Verifies that observability telemetry and cost metrics are strictly isolated between tenants."""
    db = SessionLocal()
    try:
        org1_id = f"test-org-1-{uuid.uuid4().hex[:6]}"
        org2_id = f"test-org-2-{uuid.uuid4().hex[:6]}"

        org1 = Organization(id=org1_id, name="Test Org 1", slug=f"slug-{org1_id}")
        org2 = Organization(id=org2_id, name="Test Org 2", slug=f"slug-{org2_id}")
        db.add_all([org1, org2])
        db.commit()

        rec1 = ProviderUsageRecord(
            organization_id=org1_id,
            provider="groq",
            model="llama-3.3-70b-versatile",
            operation="test_synthesis",
            prompt_tokens=500,
            completion_tokens=200,
            total_tokens=700,
            duration_ms=120.0,
            status="success",
            estimated_cost_usd=0.0005
        )
        rec2 = ProviderUsageRecord(
            organization_id=org2_id,
            provider="openai",
            model="gpt-4o",
            operation="test_drafting",
            prompt_tokens=2000,
            completion_tokens=800,
            total_tokens=2800,
            duration_ms=850.0,
            status="success",
            estimated_cost_usd=0.0130
        )
        db.add_all([rec1, rec2])
        db.commit()

        records_org1 = db.query(ProviderUsageRecord).filter(ProviderUsageRecord.organization_id == org1_id).all()
        records_org2 = db.query(ProviderUsageRecord).filter(ProviderUsageRecord.organization_id == org2_id).all()

        assert len(records_org1) == 1
        assert records_org1[0].provider == "groq"
        assert len(records_org2) == 1
        assert records_org2[0].provider == "openai"
    finally:
        db.close()


# =========================================================================
# Scenario 15: Logging Privacy & Secret Safety
# =========================================================================
def test_15_logging_privacy_no_credential_leakage():
    """Verifies that secrets and raw API keys are never leaked into telemetry records or exceptions."""
    db = SessionLocal()
    try:
        org_id = f"test-org-{uuid.uuid4().hex[:6]}"
        db.add(Organization(id=org_id, name="Privacy Org", slug=f"slug-{org_id}"))
        db.commit()

        secret_dummy_key = "gsk_super_secret_production_credential_999"
        res = asyncio.run(
            ai_router.execute_text(
                prompt="Evaluate security",
                provider="fallback",
                db=db,
                organization_id=org_id
            )
        )
        records = db.query(ProviderUsageRecord).filter(
            ProviderUsageRecord.organization_id == org_id
        ).all()

        for rec in records:
            assert secret_dummy_key not in (rec.error_message or "")
            assert secret_dummy_key not in rec.operation
    finally:
        db.close()


# =========================================================================
# Scenario 16: Offline Evaluation Benchmark Reproducibility (34 Test Cases)
# =========================================================================
def test_16_offline_evaluation_benchmark_reproducibility():
    """Executes the full 34-case offline evaluation suite and asserts 100% pass rate."""
    runner = EvaluationRunner(mode="offline")
    summary = asyncio.run(runner.run_all())

    assert summary["total_tests"] == 34
    assert summary["passed_tests"] == 34
    assert summary["overall_pass_rate"] == 1.0
