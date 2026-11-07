"""
AI Reliability, Evaluation, Hallucination Detection & Observability Router.
Provides organization-isolated metrics, evaluation runners, prompt governance,
and token/cost tracking.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.core.database import get_db
from backend.app.models.base import User, Organization, ProviderUsageRecord
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.services.ai.pricing import calculate_estimated_cost
from backend.app.services.ai.prompt_registry import prompt_registry
from backend.app.services.ai.claim_verification_service import claim_verification_service
from backend.app.evaluation.runners.runner import EvaluationRunner

router = APIRouter(prefix="/observability", tags=["AI Reliability & Observability"])

@router.get("/ai-metrics")
def get_ai_metrics(
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated AI reliability, latency, token consumption,
    and estimated cost metrics strictly scoped to the active organization.
    """
    query = db.query(ProviderUsageRecord).filter(
        (ProviderUsageRecord.organization_id == org.id) | (ProviderUsageRecord.organization_id == None)
    )

    records = query.all()
    total_ops = len(records)
    successful = sum(1 for r in records if r.status == "success")
    fallbacks = sum(1 for r in records if r.status == "fallback")
    failed = sum(1 for r in records if r.status == "failed")

    total_prompt_tokens = sum(r.prompt_tokens for r in records)
    total_completion_tokens = sum(r.completion_tokens for r in records)
    total_tokens = sum(r.total_tokens for r in records)
    total_cost = sum(getattr(r, "estimated_cost_usd", 0.0) or 0.0 for r in records)

    durations = sorted([r.duration_ms for r in records if r.duration_ms > 0])
    avg_latency = round(sum(durations) / len(durations), 2) if durations else 0.0
    p95_idx = int(len(durations) * 0.95)
    p95_latency = round(durations[p95_idx], 2) if durations else 0.0

    # Operations breakdown
    ops_breakdown: Dict[str, int] = {}
    for r in records:
        ops_breakdown[r.operation] = ops_breakdown.get(r.operation, 0) + 1

    # Cost breakdown by provider
    provider_costs: Dict[str, float] = {}
    for r in records:
        prov = r.provider or "fallback"
        c = getattr(r, "estimated_cost_usd", 0.0) or 0.0
        provider_costs[prov] = round(provider_costs.get(prov, 0.0) + c, 4)

    success_rate = round((successful / total_ops) * 100, 2) if total_ops > 0 else 100.0

    return {
        "organization_id": org.id,
        "total_operations": total_ops,
        "successful_operations": successful,
        "fallback_operations": fallbacks,
        "failed_operations": failed,
        "success_rate_pct": success_rate,
        "tokens": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens
        },
        "estimated_cost_usd": round(total_cost, 4),
        "latency_ms": {
            "average": avg_latency,
            "p95": p95_latency
        },
        "operations_breakdown": ops_breakdown,
        "cost_by_provider": provider_costs
    }

@router.get("/operations")
def list_ai_operations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    operation: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Returns paginated, multi-tenant isolated audit records of AI model executions.
    """
    query = db.query(ProviderUsageRecord).filter(
        (ProviderUsageRecord.organization_id == org.id) | (ProviderUsageRecord.organization_id == None)
    )

    if operation:
        query = query.filter(ProviderUsageRecord.operation == operation)
    if status_filter:
        query = query.filter(ProviderUsageRecord.status == status_filter)

    total = query.count()
    records = query.order_by(desc(ProviderUsageRecord.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "operation": r.operation,
                "provider": r.provider,
                "model": r.model,
                "prompt_version": getattr(r, "prompt_version", "v1.0.0"),
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "duration_ms": r.duration_ms,
                "status": r.status,
                "estimated_cost_usd": getattr(r, "estimated_cost_usd", 0.0),
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }

@router.get("/prompts")
def list_versioned_prompts(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the version-controlled prompt registry catalog and security guardrails.
    """
    return prompt_registry.list_prompts()

@router.post("/evaluate")
async def run_evaluation_benchmark(
    suite: str = Query("all", pattern="^(all|research|writing|editorial|hallucination)$"),
    mode: str = Query("offline", pattern="^(offline|live)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Executes automated benchmark evaluation and returns precision, recall,
    citation accuracy, and hallucination detection metrics.
    """
    runner = EvaluationRunner(mode=mode)
    if suite == "research":
        res = await runner.run_research_suite()
    elif suite == "writing":
        res = runner.run_writing_suite()
    elif suite == "editorial":
        res = await runner.run_editorial_suite()
    elif suite == "hallucination":
        res = runner.run_hallucination_suite()
    else:
        res = await runner.run_all()

    return res

@router.post("/verify-claim")
def verify_claim_evidence(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates arbitrary claim text against reference sources and outputs
    5-state status: SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTED | NOT_VERIFIABLE.
    """
    content = payload.get("content", "")
    sources = payload.get("sources", [])
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    report = claim_verification_service.audit_draft(content, sources)
    return report.model_dump()
