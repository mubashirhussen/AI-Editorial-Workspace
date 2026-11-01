from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# Enums as Literals
EntityType = Literal[
    "COMPANY",
    "PERSON",
    "AI_MODEL",
    "PRODUCT",
    "TECHNOLOGY",
    "INVESTOR",
    "FUNDING_ORG",
    "INDUSTRY",
    "MARKET"
]

EvidenceClassification = Literal[
    "DIRECTLY_STATED",
    "REPORTED_BY_SOURCE",
    "INFERENCE",
    "UNVERIFIED"
]

RelationshipType = Literal[
    "ANNOUNCED",
    "DEVELOPED",
    "INVESTED_IN",
    "COMPETES_WITH",
    "USES",
    "REPORTED_BY",
    "SUPPORTS",
    "CONTRADICTS"
]

TrendCategory = Literal[
    "EMERGING_TECHNOLOGY",
    "REPEATED_ANNOUNCEMENT",
    "MARKET_DEVELOPMENT",
    "DEVELOPER_ADOPTION",
    "FUNDING_PATTERN",
    "PRODUCT_LAUNCH"
]

class EntityItem(BaseModel):
    id: Optional[str] = None
    name: str
    normalized_name: str
    entity_type: EntityType
    source_id: Optional[str] = None
    source_title: Optional[str] = None
    supporting_excerpt: Optional[str] = None
    confidence: float = 0.9
    extraction_method: str = "heuristic_nlp"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ClaimItemModel(BaseModel):
    id: Optional[str] = None
    source_id: str
    source_title: Optional[str] = None
    claim_text: str
    supporting_excerpt: str
    evidence_classification: EvidenceClassification
    entity_references: List[str] = Field(default_factory=list)
    confidence: float = 0.9
    publication_date: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RelationshipItem(BaseModel):
    id: Optional[str] = None
    source_entity_name: str
    target_entity_name: str
    relationship_type: RelationshipType
    source_id: Optional[str] = None
    source_title: Optional[str] = None
    supporting_evidence: str
    confidence: float = 0.85
    explanation: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ContradictionItem(BaseModel):
    id: Optional[str] = None
    claim_a_id: Optional[str] = None
    claim_b_id: Optional[str] = None
    source_a_id: Optional[str] = None
    source_b_id: Optional[str] = None
    source_a_title: Optional[str] = None
    source_b_title: Optional[str] = None
    claim_a_text: str
    claim_b_text: str
    disagreement_nature: str
    possible_explanations: str
    unresolved_questions: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TrendItem(BaseModel):
    id: Optional[str] = None
    theme: str
    category: TrendCategory
    supporting_source_ids: List[str] = Field(default_factory=list)
    supporting_source_titles: List[str] = Field(default_factory=list)
    evidence_summary: str
    is_prediction: bool = False
    confidence: float = 0.85
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # COMPANY, PRODUCT, PERSON, TECHNOLOGY, CLAIM, SOURCE, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: RelationshipType
    evidence: str
    confidence: float
    source_id: Optional[str] = None

class KnowledgeGraphResponse(BaseModel):
    project_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict[str, int] = Field(default_factory=dict)

class IntelligenceAnalysisResponse(BaseModel):
    project_id: str
    status: str = "completed"
    entities_count: int
    claims_count: int
    relationships_count: int
    contradictions_count: int
    trends_count: int
    summary: str
    created_at: datetime

