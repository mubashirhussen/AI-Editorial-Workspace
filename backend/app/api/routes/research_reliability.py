"""
Phase 39: AI Research Reliability, Source Intelligence & Citation Verification Router.
Endpoints for source credibility, citation validation, claim-to-evidence mapping,
evidence quality evaluation, research quality reporting, and evidence-grounded section regeneration.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import (
    ResearchProject,
    Source,
    ResearchBrief,
    ResearchRevision,
    SourceCredibilityAssessment,
    CitationValidation,
    ResearchQualityReport,
    User,
    Organization,
)
from backend.app.schemas.research_reliability import (
    SourceCredibilityResponse,
    CitationValidationResponse,
    ClaimVerificationItem,
    ResearchQualityReportResponse,
    SectionRegenerateRequest,
    SectionRegenerateResponse,
    SourceIngestRequest,
    SourceIngestResponse,
)
from backend.app.services.research_reliability_service import research_reliability_service
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.api.v1.endpoints.projects import check_project_tenant_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research-reliability", tags=["research-reliability"])


def _get_project_with_access(
    project_id: str,
    db: Session,
    current_user: User,
    active_org: Organization
) -> ResearchProject:
    """Verifies project existence and strictly enforces multi-tenant organization access."""
    project = db.query(ResearchProject).filter(
        ResearchProject.id == project_id,
        ResearchProject.deleted_at.is_(None)
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research project '{project_id}' not found.")
    if project.organization_id and project.organization_id != active_org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research project '{project_id}' not found.")
    check_project_tenant_access(db, project, current_user)
    return project


# ---------------------------------------------------------------------------
# 1. Source Ingestion & Credibility Assessment
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/sources/ingest", response_model=SourceIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_research_source(
    project_id: str,
    payload: SourceIngestRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Ingests research source with SSRF defense, URL canonicalization,
    content deduplication, sentence evidence extraction, and explainable credibility assessment.
    """
    project = _get_project_with_access(project_id, db, current_user, org)
    try:
        source, cred, is_dup = await research_reliability_service.ingest_source(
            db=db,
            project_id=project.id,
            request=payload
        )
        return SourceIngestResponse(
            source_id=source.id,
            project_id=source.project_id,
            title=source.title,
            url=source.url,
            canonical_url=source.url,
            extraction_status=source.extraction_status,
            content_hash=source.content_hash,
            is_duplicate=is_dup,
            credibility=SourceCredibilityResponse.model_validate(cred) if cred else None,
            evidence_count=len(source.raw_content.split("\n\n")) if source.raw_content else 0
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Source ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Source ingestion error: {str(e)}")


@router.get("/sources/{source_id}/credibility", response_model=SourceCredibilityResponse)
def get_source_credibility(
    source_id: str,
    freshness_req: str = Query("technology", description="breaking_news, technology, scientific, historical"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Retrieves or computes credibility and freshness assessment for a source."""
    source = db.query(Source).filter(Source.id == source_id, Source.deleted_at.is_(None)).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source '{source_id}' not found.")
    _get_project_with_access(source.project_id, db, current_user, org)

    cred = research_reliability_service.assess_source_credibility(db, source, freshness_req)
    return cred


@router.post("/sources/{source_id}/verify", response_model=SourceCredibilityResponse)
def verify_source(
    source_id: str,
    freshness_req: str = Query("technology"),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Re-runs credibility, accessibility, and freshness evaluation on a source."""
    source = db.query(Source).filter(Source.id == source_id, Source.deleted_at.is_(None)).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source '{source_id}' not found.")
    _get_project_with_access(source.project_id, db, current_user, org)

    cred = research_reliability_service.assess_source_credibility(db, source, freshness_req)
    return cred


# ---------------------------------------------------------------------------
# 2. Claim Extraction & Six-Tier Verification
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/claims", response_model=List[ClaimVerificationItem])
@router.post("/projects/{project_id}/verify-claims", response_model=List[ClaimVerificationItem])
def verify_project_claims(
    project_id: str,
    brief_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Performs six-tier claim verification across research brief statements:
    SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNVERIFIED, NOT_APPLICABLE.
    """
    project = _get_project_with_access(project_id, db, current_user, org)
    return research_reliability_service.extract_and_verify_claims(
        db=db,
        project_id=project.id,
        brief_id=brief_id
    )


# ---------------------------------------------------------------------------
# 3. Citation Validation & Anti-Fabrication
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/citations", response_model=List[CitationValidationResponse])
def get_project_citations(
    project_id: str,
    brief_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Lists validated citations for the project's research brief."""
    project = _get_project_with_access(project_id, db, current_user, org)
    existing = db.query(CitationValidation).filter(CitationValidation.project_id == project.id).all()
    if not existing:
        existing = research_reliability_service.validate_citations(db, project.id, brief_id)
    return existing


@router.post("/projects/{project_id}/validate-citations", response_model=List[CitationValidationResponse])
def validate_project_citations(
    project_id: str,
    brief_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Executes comprehensive citation audit:
    validates referential integrity against stored source records, detects fabricated citations,
    and checks URL accessibility status.
    """
    project = _get_project_with_access(project_id, db, current_user, org)
    return research_reliability_service.validate_citations(db, project.id, brief_id)


# ---------------------------------------------------------------------------
# 4. Corroboration & Contradiction Analysis
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/corroboration")
def get_corroboration_and_contradictions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Evaluates cross-publisher corroboration tiers and retrieves conflicting evidence assertions."""
    project = _get_project_with_access(project_id, db, current_user, org)
    return research_reliability_service.analyze_corroboration_and_contradictions(db, project.id)


# ---------------------------------------------------------------------------
# 5. Research Quality Report
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/quality-report", response_model=ResearchQualityReportResponse)
def get_research_quality_report(
    project_id: str,
    brief_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Synthesizes and returns the authoritative Research Quality Report with evidence coverage,
    citation health, source diversity, overall quality grade, and documented limitations.
    """
    project = _get_project_with_access(project_id, db, current_user, org)
    report = research_reliability_service.generate_quality_report(db, project.id, brief_id)
    return report


# ---------------------------------------------------------------------------
# 6. Evidence-Grounded Section Regeneration
# ---------------------------------------------------------------------------

@router.post("/projects/{project_id}/briefs/{brief_id}/regenerate-section", response_model=SectionRegenerateResponse)
def regenerate_brief_section(
    project_id: str,
    brief_id: str,
    payload: SectionRegenerateRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """
    Regenerates a brief section strictly constrained to verified evidence passages.
    Preserves original revision history and provides unified diff summary.
    """
    project = _get_project_with_access(project_id, db, current_user, org)
    try:
        revision, verified_claims = research_reliability_service.regenerate_section(
            db=db,
            project_id=project.id,
            brief_id=brief_id,
            section_key=payload.section_key,
            instructions=payload.instructions,
            required_evidence_ids=payload.required_evidence_ids
        )
        resp = SectionRegenerateResponse.model_validate(revision)
        resp.claims_verified = verified_claims
        return resp
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/revisions/{revision_id}/accept")
def accept_section_revision(
    revision_id: str,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_active_organization),
    db: Session = Depends(get_db)
):
    """Accepts regenerated revision, updating the research brief in place while preserving version history."""
    rev = db.query(ResearchRevision).filter(ResearchRevision.id == revision_id).first()
    if not rev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Revision '{revision_id}' not found.")
    _get_project_with_access(rev.project_id, db, current_user, org)

    brief = db.query(ResearchBrief).filter(ResearchBrief.id == rev.brief_id).first()
    if not brief:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found.")

    if rev.section_key == "executive_summary":
        brief.executive_summary = rev.regenerated_text
    elif rev.section_key == "strategic_implications":
        brief.strategic_implications = {"analysis": rev.regenerated_text}
    elif rev.section_key == "key_developments":
        brief.key_developments = [{"summary": rev.regenerated_text}]

    rev.status = "ACCEPTED"
    brief.version = (brief.version or 1) + 1
    brief.is_user_edited = True
    db.commit()

    return {
        "status": "ACCEPTED",
        "brief_id": brief.id,
        "section_key": rev.section_key,
        "new_version": brief.version
    }
