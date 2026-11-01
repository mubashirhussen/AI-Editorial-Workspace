import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.base import (
    ResearchProject,
    Source,
    ResearchEntity,
    ResearchClaim,
    ResearchRelationship,
    ResearchContradiction,
    ResearchTrend,
    User,
    Organization
)
from backend.app.schemas.research_intelligence import (
    EntityItem,
    ClaimItemModel,
    RelationshipItem,
    ContradictionItem,
    TrendItem,
    KnowledgeGraphResponse,
    IntelligenceAnalysisResponse,
    EntityType,
    EvidenceClassification,
    RelationshipType
)
from backend.app.services.research_intelligence.synthesis_engine import intelligence_engine
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.api.v1.endpoints.projects import check_project_tenant_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/intelligence", tags=["research-intelligence"])

def _get_project_with_access(
    project_id: str,
    db: Session,
    current_user: User,
    active_org: Organization
) -> ResearchProject:
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research project not found")
    if project.organization_id and project.organization_id != active_org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research project not found")
    check_project_tenant_access(db, project, current_user)
    return project

@router.post("/analyze", response_model=IntelligenceAnalysisResponse)
def run_intelligence_analysis(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Executes cross-source research intelligence discovery:
    extracts entities, evidentiary claims, relationships, contradictions, and corroborated trends.
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    try:
        result = intelligence_engine.analyze_project(db, project.id)
        return result
    except Exception as e:
        logger.error(f"Intelligence analysis failed for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligence analysis failed: {str(e)}"
        )

@router.get("/entities", response_model=List[EntityItem])
def get_project_entities(
    project_id: str,
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves all extracted entities with source-traceable excerpts.
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    query = db.query(ResearchEntity).filter(ResearchEntity.project_id == project.id)

    if entity_type:
        query = query.filter(ResearchEntity.entity_type == entity_type)
    if source_id:
        query = query.filter(ResearchEntity.source_id == source_id)

    entities = query.order_by(ResearchEntity.confidence.desc(), ResearchEntity.name).all()

    # Enrich with source title
    source_map = {s.id: s.title for s in db.query(Source).filter(Source.project_id == project.id).all()}
    results = []
    for ent in entities:
        item = EntityItem.model_validate(ent)
        item.source_title = source_map.get(ent.source_id)
        results.append(item)

    return results

@router.get("/claims", response_model=List[ClaimItemModel])
def get_project_claims(
    project_id: str,
    evidence_classification: Optional[EvidenceClassification] = Query(None, description="Filter by classification"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves claims with epistemic classification (DIRECTLY_STATED, REPORTED_BY_SOURCE, INFERENCE, UNVERIFIED).
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    query = db.query(ResearchClaim).filter(ResearchClaim.project_id == project.id)

    if evidence_classification:
        query = query.filter(ResearchClaim.evidence_classification == evidence_classification)
    if source_id:
        query = query.filter(ResearchClaim.source_id == source_id)

    claims = query.order_by(ResearchClaim.created_at.desc()).all()

    source_map = {s.id: s.title for s in db.query(Source).filter(Source.project_id == project.id).all()}
    results = []
    for c in claims:
        item = ClaimItemModel.model_validate(c)
        item.source_title = source_map.get(c.source_id)
        results.append(item)

    return results

@router.get("/relationships", response_model=List[RelationshipItem])
def get_project_relationships(
    project_id: str,
    relationship_type: Optional[RelationshipType] = Query(None, description="Filter by relationship type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves validated semantic entity relationships backed by specific sentence evidence.
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    query = db.query(ResearchRelationship).filter(ResearchRelationship.project_id == project.id)

    if relationship_type:
        query = query.filter(ResearchRelationship.relationship_type == relationship_type)

    relationships = query.order_by(ResearchRelationship.created_at.desc()).all()

    source_map = {s.id: s.title for s in db.query(Source).filter(Source.project_id == project.id).all()}
    results = []
    for r in relationships:
        item = RelationshipItem.model_validate(r)
        item.source_title = source_map.get(r.source_id)
        results.append(item)

    return results

@router.get("/contradictions", response_model=List[ContradictionItem])
def get_project_contradictions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves cross-source discrepancies and conflicting assertions.
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    contradictions = db.query(ResearchContradiction).filter(
        ResearchContradiction.project_id == project.id
    ).order_by(ResearchContradiction.created_at.desc()).all()

    source_map = {s.id: s.title for s in db.query(Source).filter(Source.project_id == project.id).all()}
    results = []
    for cd in contradictions:
        item = ContradictionItem.model_validate(cd)
        item.source_a_title = source_map.get(cd.source_a_id)
        item.source_b_title = source_map.get(cd.source_b_id)
        results.append(item)

    return results

@router.get("/trends", response_model=List[TrendItem])
def get_project_trends(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Retrieves recurring cross-source patterns meeting corroboration threshold (>= 2 sources).
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    trends = db.query(ResearchTrend).filter(
        ResearchTrend.project_id == project.id
    ).order_by(ResearchTrend.confidence.desc()).all()

    source_map = {s.id: s.title for s in db.query(Source).filter(Source.project_id == project.id).all()}
    results = []
    for td in trends:
        item = TrendItem.model_validate(td)
        item.supporting_source_titles = [
            source_map.get(sid, sid) for sid in td.supporting_source_ids or []
        ]
        results.append(item)

    return results

@router.get("/graph", response_model=KnowledgeGraphResponse)
def get_project_knowledge_graph(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    """
    Returns graph visualization payload (nodes and edges) for the knowledge graph.
    """
    project = _get_project_with_access(project_id, db, current_user, active_org)
    return intelligence_engine.build_knowledge_graph(db, project.id)
