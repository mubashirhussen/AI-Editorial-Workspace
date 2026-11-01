export type EntityType = 
  | 'COMPANY'
  | 'PERSON'
  | 'AI_MODEL'
  | 'PRODUCT'
  | 'TECHNOLOGY'
  | 'INVESTOR'
  | 'FUNDING_ORG'
  | 'INDUSTRY'
  | 'MARKET';

export type EvidenceClassification = 
  | 'DIRECTLY_STATED'
  | 'REPORTED_BY_SOURCE'
  | 'INFERENCE'
  | 'UNVERIFIED';

export type RelationshipType = 
  | 'ANNOUNCED'
  | 'DEVELOPED'
  | 'INVESTED_IN'
  | 'COMPETES_WITH'
  | 'USES'
  | 'REPORTED_BY'
  | 'SUPPORTS'
  | 'CONTRADICTS';

export type TrendCategory = 
  | 'EMERGING_TECHNOLOGY'
  | 'REPEATED_ANNOUNCEMENT'
  | 'MARKET_DEVELOPMENT'
  | 'DEVELOPER_ADOPTION'
  | 'FUNDING_PATTERN'
  | 'PRODUCT_LAUNCH';

export interface EntityItem {
  id?: string;
  name: string;
  normalized_name: string;
  entity_type: EntityType;
  source_id?: string;
  source_title?: string;
  supporting_excerpt?: string;
  confidence: number;
  extraction_method: string;
  created_at?: string;
}

export interface IntelClaimItem {
  id?: string;
  source_id: string;
  source_title?: string;
  claim_text: string;
  supporting_excerpt: string;
  evidence_classification: EvidenceClassification;
  entity_references: string[];
  confidence: number;
  publication_date?: string;
  created_at?: string;
}

export interface RelationshipItem {
  id?: string;
  source_entity_name: string;
  target_entity_name: string;
  relationship_type: RelationshipType;
  source_id?: string;
  source_title?: string;
  supporting_evidence: string;
  confidence: number;
  explanation: string;
  created_at?: string;
}

export interface ContradictionItem {
  id?: string;
  claim_a_id?: string;
  claim_b_id?: string;
  source_a_id?: string;
  source_b_id?: string;
  source_a_title?: string;
  source_b_title?: string;
  claim_a_text: string;
  claim_b_text: string;
  disagreement_nature: string;
  possible_explanations: string;
  unresolved_questions: string;
  created_at?: string;
}

export interface TrendItem {
  id?: string;
  theme: string;
  category: TrendCategory;
  supporting_source_ids: string[];
  supporting_source_titles: string[];
  evidence_summary: string;
  is_prediction: boolean;
  confidence: number;
  created_at?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: RelationshipType;
  evidence: string;
  confidence: number;
  source_id?: string;
}

export interface KnowledgeGraphResponse {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: Record<string, number>;
}

export interface IntelligenceAnalysisResponse {
  project_id: string;
  status: string;
  entities_count: number;
  claims_count: number;
  relationships_count: number;
  contradictions_count: number;
  trends_count: number;
  summary: string;
  created_at: string;
}
