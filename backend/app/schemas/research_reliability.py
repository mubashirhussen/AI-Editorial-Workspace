"""
Phase 39: AI Research Reliability, Source Intelligence & Citation Verification Schemas.
Pydantic schemas for source credibility, citation validation, claim-to-evidence mapping,
evidence quality, research quality reporting, and evidence-grounded section regeneration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class SourceCredibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    project_id: str
    credibility_tier: str = Field(..., description="PRIMARY_SOURCE, OFFICIAL_SOURCE, PEER_REVIEWED, INSTITUTIONAL, NEWS_REPORTING, SECONDARY_ANALYSIS, OPINION, COMMERCIAL, UNKNOWN")
    publisher_type: Optional[str] = None
    publisher_name: Optional[str] = None
    author_name: Optional[str] = None
    publication_date: Optional[str] = None
    retrieved_at: datetime
    freshness_status: str = Field(..., description="CURRENT, RECENT, AGED, HISTORICAL, UNKNOWN")
    freshness_criteria: Optional[str] = None
    accessibility_status: str = Field(..., description="ACCESSIBLE, RETRIABLE_ERROR, PERMANENT_ERROR, TIMEOUT, RESTRICTED")
    is_primary_source: bool
    methodological_transparency: str = Field(..., description="HIGH, STANDARD, LOW, NONE")
    criteria_breakdown: Dict[str, Any] = Field(default_factory=dict)
    criteria_breakdown_json: Optional[Dict[str, Any]] = None
    limitations: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "criteria_breakdown_json"):
            cb = getattr(data, "criteria_breakdown_json") or {}
            return {
                "id": data.id,
                "source_id": data.source_id,
                "project_id": data.project_id,
                "credibility_tier": data.credibility_tier,
                "publisher_type": data.publisher_type,
                "publisher_name": data.publisher_name,
                "author_name": data.author_name,
                "publication_date": data.publication_date,
                "retrieved_at": data.retrieved_at,
                "freshness_status": data.freshness_status,
                "freshness_criteria": data.freshness_criteria,
                "accessibility_status": data.accessibility_status,
                "is_primary_source": data.is_primary_source,
                "methodological_transparency": data.methodological_transparency,
                "criteria_breakdown": cb,
                "criteria_breakdown_json": cb,
                "limitations": data.limitations,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        elif isinstance(data, dict):
            cb = data.get("criteria_breakdown") or data.get("criteria_breakdown_json") or {}
            data["criteria_breakdown"] = cb
            data["criteria_breakdown_json"] = cb
            return data
        return data


class CitationValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    brief_id: Optional[str] = None
    source_id: Optional[str] = None
    claim_id: Optional[str] = None
    citation_text: str
    citation_url: Optional[str] = None
    citation_number: Optional[int] = None
    status: str = Field(..., description="VALID, INVALID, BROKEN, INACCESSIBLE, UNVERIFIED, NEEDS_REVIEW")
    validation_details: Dict[str, Any] = Field(default_factory=dict)
    validation_details_json: Optional[Dict[str, Any]] = None
    is_fabricated: bool
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "validation_details_json"):
            vd = getattr(data, "validation_details_json") or {}
            return {
                "id": data.id,
                "project_id": data.project_id,
                "brief_id": data.brief_id,
                "source_id": data.source_id,
                "claim_id": data.claim_id,
                "citation_text": data.citation_text,
                "citation_url": data.citation_url,
                "citation_number": data.citation_number,
                "status": data.status,
                "validation_details": vd,
                "validation_details_json": vd,
                "is_fabricated": data.is_fabricated,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        elif isinstance(data, dict):
            vd = data.get("validation_details") or data.get("validation_details_json") or {}
            data["validation_details"] = vd
            data["validation_details_json"] = vd
            return data
        return data


class ClaimVerificationItem(BaseModel):
    id: str
    claim_text: str
    claim_type: str = Field(..., description="FACTUAL, OPINION, RECOMMENDATION, PREDICTION, INTERPRETATION, HYPOTHESIS, CONCLUSION, EDITORIAL_FRAMING")
    verification_status: str = Field(..., description="SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNVERIFIED, NOT_APPLICABLE")
    claim_location: Optional[str] = None
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    citation_references: List[str] = Field(default_factory=list)
    confidence: float = 0.9
    explanation: str = ""


class ResearchQualityReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    brief_id: Optional[str] = None
    total_claims: int
    claims_requiring_evidence: int
    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    contradicted_claims: int
    unverified_claims: int
    not_applicable_claims: int
    evidence_coverage_score: float
    citation_health_score: float
    source_diversity_score: float
    overall_quality_grade: str
    source_quality_summary: Dict[str, Any] = Field(default_factory=dict)
    source_quality_summary_json: Optional[Dict[str, Any]] = None
    corroboration_summary: Dict[str, Any] = Field(default_factory=dict)
    corroboration_summary_json: Optional[Dict[str, Any]] = None
    contradictions_count: int
    limitations_summary: Optional[str] = None
    audit_findings: List[Dict[str, Any]] = Field(default_factory=list)
    audit_findings_json: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "source_quality_summary_json"):
            sq = getattr(data, "source_quality_summary_json") or {}
            cs = getattr(data, "corroboration_summary_json") or {}
            af = getattr(data, "audit_findings_json") or []
            return {
                "id": data.id,
                "project_id": data.project_id,
                "brief_id": data.brief_id,
                "total_claims": data.total_claims,
                "claims_requiring_evidence": data.claims_requiring_evidence,
                "supported_claims": data.supported_claims,
                "partially_supported_claims": data.partially_supported_claims,
                "unsupported_claims": data.unsupported_claims,
                "contradicted_claims": data.contradicted_claims,
                "unverified_claims": data.unverified_claims,
                "not_applicable_claims": data.not_applicable_claims,
                "evidence_coverage_score": data.evidence_coverage_score,
                "citation_health_score": data.citation_health_score,
                "source_diversity_score": data.source_diversity_score,
                "overall_quality_grade": data.overall_quality_grade,
                "source_quality_summary": sq,
                "source_quality_summary_json": sq,
                "corroboration_summary": cs,
                "corroboration_summary_json": cs,
                "contradictions_count": data.contradictions_count,
                "limitations_summary": data.limitations_summary,
                "audit_findings": af,
                "audit_findings_json": af,
                "created_at": data.created_at,
            }
        elif isinstance(data, dict):
            sq = data.get("source_quality_summary") or data.get("source_quality_summary_json") or {}
            cs = data.get("corroboration_summary") or data.get("corroboration_summary_json") or {}
            af = data.get("audit_findings") or data.get("audit_findings_json") or []
            data["source_quality_summary"] = sq
            data["source_quality_summary_json"] = sq
            data["corroboration_summary"] = cs
            data["corroboration_summary_json"] = cs
            data["audit_findings"] = af
            data["audit_findings_json"] = af
            return data
        return data


class SectionRegenerateRequest(BaseModel):
    section_key: str = Field(..., description="executive_summary, key_developments, strategic_implications, etc.")
    instructions: Optional[str] = Field(default=None, description="Optional editor steering instructions")
    required_evidence_ids: Optional[List[str]] = Field(default=None, description="Optional specific evidence passage IDs to incorporate")


class SectionRegenerateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revision_id: str
    project_id: str
    brief_id: str
    section_key: str
    original_text: str
    regenerated_text: str
    diff_summary: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    supporting_evidence_ids_json: Optional[List[str]] = None
    claims_verified: List[ClaimVerificationItem] = Field(default_factory=list)
    status: str
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def populate_fields(cls, data: Any) -> Any:
        if hasattr(data, "supporting_evidence_ids_json"):
            ev_ids = getattr(data, "supporting_evidence_ids_json") or []
            return {
                "revision_id": data.id,
                "project_id": data.project_id,
                "brief_id": data.brief_id,
                "section_key": data.section_key,
                "original_text": data.original_text,
                "regenerated_text": data.regenerated_text,
                "diff_summary": data.diff_summary or "",
                "supporting_evidence_ids": ev_ids,
                "supporting_evidence_ids_json": ev_ids,
                "claims_verified": [],
                "status": data.status,
                "created_at": data.created_at,
            }
        elif isinstance(data, dict):
            ev_ids = data.get("supporting_evidence_ids") or data.get("supporting_evidence_ids_json") or []
            data["supporting_evidence_ids"] = ev_ids
            data["supporting_evidence_ids_json"] = ev_ids
            return data
        return data


class SourceIngestRequest(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    text_content: Optional[str] = None
    source_type: str = "URL"
    freshness_requirement: str = Field(default="technology", description="breaking_news, technology, industry_update, scientific, historical")


class SourceIngestResponse(BaseModel):
    source_id: str
    project_id: str
    title: str
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    extraction_status: str
    content_hash: str
    is_duplicate: bool
    credibility: Optional[SourceCredibilityResponse] = None
    evidence_count: int = 0
