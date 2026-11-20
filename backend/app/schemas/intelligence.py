"""
Phase 38: Product Intelligence Schemas
Pydantic schemas for data quality validation, evidence-backed insights,
recommendation lifecycles, workflow optimization, and impact measurement.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class DataQualityReport(BaseModel):
    status: str = Field(..., description="HEALTHY, WARNING, or INSUFFICIENT_DATA")
    score: float = Field(..., ge=0.0, le=100.0, description="Computed data completeness score")
    sample_size: int = Field(..., ge=0, description="Number of validated event records analyzed")
    is_sufficient: bool = Field(..., description="Whether sample size exceeds threshold for statistically reliable analysis")
    checks: Dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic breakdown")


class IntelligenceInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    severity: str
    title: str
    description: str
    detected_pattern: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    evidence_json: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metrics_json: Optional[Dict[str, Any]] = None
    confidence_score: float
    status: str
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "evidence_json"):
            ev = getattr(data, "evidence_json") or {}
            mt = getattr(data, "metrics_json") or {}
            return {
                "id": data.id,
                "category": data.category,
                "severity": data.severity,
                "title": data.title,
                "description": data.description,
                "detected_pattern": data.detected_pattern,
                "evidence": ev,
                "evidence_json": ev,
                "metrics": mt,
                "metrics_json": mt,
                "confidence_score": data.confidence_score,
                "status": data.status,
                "created_at": data.created_at,
            }
        elif isinstance(data, dict):
            ev = data.get("evidence") or data.get("evidence_json") or {}
            mt = data.get("metrics") or data.get("metrics_json") or {}
            data["evidence"] = ev
            data["evidence_json"] = ev
            data["metrics"] = mt
            data["metrics_json"] = mt
            return data
        return data


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    insight_id: Optional[str] = None
    category: str
    priority: str
    severity: str
    title: str
    description: str
    proposed_action: str
    expected_benefit: str
    estimated_effort: str
    risk_level: str
    confidence_score: float
    status: str
    assigned_to: Optional[str] = None
    implementation_notes: Optional[str] = None
    is_automated: bool
    created_at: datetime
    updated_at: datetime


class RecommendationStatusUpdateRequest(BaseModel):
    status: Optional[str] = Field(default=None, description="Target lifecycle state: ACCEPTED, REJECTED, DEFERRED, IN_PROGRESS, IMPLEMENTED, VERIFIED")
    notes: Optional[str] = Field(default=None, description="Optional justification or implementation notes")
    assigned_to: Optional[str] = Field(default=None, description="Optional team member assignment")


class RecommendationFeedbackCreate(BaseModel):
    feedback_type: str = Field(..., description="helpful, irrelevant, inaccurate_evidence, implemented, difficult")
    rating: int = Field(default=5, ge=1, le=5, description="1 to 5 star rating")
    comment: Optional[str] = Field(default=None, description="Detailed user feedback")


class RecommendationFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recommendation_id: str
    feedback_type: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class OptimizationActionRequest(BaseModel):
    action_type: str = Field(..., description="Controlled low-risk action identifier")
    action_payload: Dict[str, Any] = Field(default_factory=dict)


class OptimizationActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recommendation_id: Optional[str] = None
    action_type: str
    status: str
    executed_by: Optional[str] = None
    audit_trail: List[Any] = Field(default_factory=list)
    audit_trail_json: Optional[List[Any]] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "audit_trail_json"):
            at = getattr(data, "audit_trail_json") or []
            return {
                "id": data.id,
                "recommendation_id": data.recommendation_id,
                "action_type": data.action_type,
                "status": data.status,
                "executed_by": data.executed_by,
                "audit_trail": at,
                "audit_trail_json": at,
                "created_at": data.created_at,
            }
        elif isinstance(data, dict):
            at = data.get("audit_trail") or data.get("audit_trail_json") or []
            data["audit_trail"] = at
            data["audit_trail_json"] = at
            return data
        return data


class ImpactEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recommendation_id: str
    baseline_metrics: Dict[str, Any] = Field(default_factory=dict)
    baseline_metrics_json: Optional[Dict[str, Any]] = None
    current_metrics: Dict[str, Any] = Field(default_factory=dict)
    current_metrics_json: Optional[Dict[str, Any]] = None
    metric_delta: Dict[str, Any] = Field(default_factory=dict)
    metric_delta_json: Optional[Dict[str, Any]] = None
    evaluation_status: str
    notes: Optional[str] = None
    evaluated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "baseline_metrics_json"):
            bm = getattr(data, "baseline_metrics_json") or {}
            cm = getattr(data, "current_metrics_json") or {}
            md = getattr(data, "metric_delta_json") or {}
            return {
                "id": data.id,
                "recommendation_id": data.recommendation_id,
                "baseline_metrics": bm,
                "baseline_metrics_json": bm,
                "current_metrics": cm,
                "current_metrics_json": cm,
                "metric_delta": md,
                "metric_delta_json": md,
                "evaluation_status": data.evaluation_status,
                "notes": data.notes,
                "evaluated_at": data.evaluated_at,
            }
        elif isinstance(data, dict):
            bm = data.get("baseline_metrics") or data.get("baseline_metrics_json") or {}
            cm = data.get("current_metrics") or data.get("current_metrics_json") or {}
            md = data.get("metric_delta") or data.get("metric_delta_json") or {}
            data["baseline_metrics"] = bm
            data["baseline_metrics_json"] = bm
            data["current_metrics"] = cm
            data["current_metrics_json"] = cm
            data["metric_delta"] = md
            data["metric_delta_json"] = md
            return data
        return data


class IntelligenceOverviewResponse(BaseModel):
    data_quality: DataQualityReport
    active_insights_count: int
    high_priority_recommendations_count: int
    implemented_improvements_count: int
    pending_recommendations_count: int
    insights: List[IntelligenceInsightResponse]
    recommendations: List[RecommendationResponse]
