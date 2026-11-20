import axios from 'axios';

const API_BASE = '/api/v1/research-reliability';

export interface SourceCredibility {
  id: string;
  source_id: string;
  project_id: string;
  credibility_tier: string;
  publisher_type?: string;
  publisher_name?: string;
  author_name?: string;
  publication_date?: string;
  retrieved_at: string;
  freshness_status: string;
  freshness_criteria?: string;
  accessibility_status: string;
  is_primary_source: boolean;
  methodological_transparency: string;
  criteria_breakdown: Record<string, any>;
  limitations?: string;
  created_at: string;
  updated_at: string;
}

export interface CitationValidationItem {
  id: string;
  project_id: string;
  brief_id?: string;
  source_id?: string;
  claim_id?: string;
  citation_text: string;
  citation_url?: string;
  citation_number?: number;
  status: 'VALID' | 'INVALID' | 'BROKEN' | 'INACCESSIBLE' | 'UNVERIFIED' | 'NEEDS_REVIEW';
  validation_details: Record<string, any>;
  is_fabricated: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClaimVerification {
  id: string;
  claim_text: string;
  claim_type: string;
  verification_status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'CONTRADICTED' | 'UNVERIFIED' | 'NOT_APPLICABLE';
  claim_location?: string;
  supporting_evidence: Array<{
    evidence_id?: string;
    source_id?: string;
    source_title?: string;
    excerpt: string;
    fact_type?: string;
    confidence?: number;
  }>;
  conflicting_evidence: Array<Record<string, any>>;
  citation_references: string[];
  confidence: number;
  explanation: string;
}

export interface ResearchQualityReport {
  id: string;
  project_id: string;
  brief_id?: string;
  total_claims: number;
  claims_requiring_evidence: number;
  supported_claims: number;
  partially_supported_claims: number;
  unsupported_claims: number;
  contradicted_claims: number;
  unverified_claims: number;
  not_applicable_claims: number;
  evidence_coverage_score: number;
  citation_health_score: number;
  source_diversity_score: number;
  overall_quality_grade: string;
  source_quality_summary: Record<string, any>;
  corroboration_summary: Record<string, any>;
  contradictions_count: number;
  limitations_summary?: string;
  audit_findings: Array<{
    severity: string;
    finding: string;
    remediation: string;
  }>;
  created_at: string;
}

export interface SectionRegenerateResult {
  revision_id: string;
  project_id: string;
  brief_id: string;
  section_key: string;
  original_text: string;
  regenerated_text: string;
  diff_summary: string;
  supporting_evidence_ids: string[];
  claims_verified: ClaimVerification[];
  status: string;
  created_at: string;
}

export interface IngestSourceResult {
  source_id: string;
  project_id: string;
  title: string;
  url?: string;
  canonical_url?: string;
  extraction_status: string;
  content_hash: string;
  is_duplicate: boolean;
  credibility?: SourceCredibility;
  evidence_count: number;
}

export const researchReliabilityService = {
  async ingestSource(
    projectId: string,
    payload: {
      url?: string;
      title?: string;
      text_content?: string;
      source_type?: string;
      freshness_requirement?: string;
    }
  ): Promise<IngestSourceResult> {
    const res = await axios.post<IngestSourceResult>(
      `${API_BASE}/projects/${projectId}/sources/ingest`,
      payload
    );
    return res.data;
  },

  async getSourceCredibility(
    sourceId: string,
    freshnessReq: string = 'technology'
  ): Promise<SourceCredibility> {
    const res = await axios.get<SourceCredibility>(
      `${API_BASE}/sources/${sourceId}/credibility?freshness_req=${freshnessReq}`
    );
    return res.data;
  },

  async verifySource(
    sourceId: string,
    freshnessReq: string = 'technology'
  ): Promise<SourceCredibility> {
    const res = await axios.post<SourceCredibility>(
      `${API_BASE}/sources/${sourceId}/verify?freshness_req=${freshnessReq}`
    );
    return res.data;
  },

  async verifyProjectClaims(
    projectId: string,
    briefId?: string
  ): Promise<ClaimVerification[]> {
    const url = briefId
      ? `${API_BASE}/projects/${projectId}/claims?brief_id=${briefId}`
      : `${API_BASE}/projects/${projectId}/claims`;
    const res = await axios.get<ClaimVerification[]>(url);
    return res.data;
  },

  async getProjectCitations(
    projectId: string,
    briefId?: string
  ): Promise<CitationValidationItem[]> {
    const url = briefId
      ? `${API_BASE}/projects/${projectId}/citations?brief_id=${briefId}`
      : `${API_BASE}/projects/${projectId}/citations`;
    const res = await axios.get<CitationValidationItem[]>(url);
    return res.data;
  },

  async validateProjectCitations(
    projectId: string,
    briefId?: string
  ): Promise<CitationValidationItem[]> {
    const url = briefId
      ? `${API_BASE}/projects/${projectId}/validate-citations?brief_id=${briefId}`
      : `${API_BASE}/projects/${projectId}/validate-citations`;
    const res = await axios.post<CitationValidationItem[]>(url);
    return res.data;
  },

  async getCorroboration(projectId: string): Promise<Record<string, any>> {
    const res = await axios.get<Record<string, any>>(
      `${API_BASE}/projects/${projectId}/corroboration`
    );
    return res.data;
  },

  async getQualityReport(
    projectId: string,
    briefId?: string
  ): Promise<ResearchQualityReport> {
    const url = briefId
      ? `${API_BASE}/projects/${projectId}/quality-report?brief_id=${briefId}`
      : `${API_BASE}/projects/${projectId}/quality-report`;
    const res = await axios.get<ResearchQualityReport>(url);
    return res.data;
  },

  async regenerateSection(
    projectId: string,
    briefId: string,
    payload: {
      section_key: string;
      instructions?: string;
      required_evidence_ids?: string[];
    }
  ): Promise<SectionRegenerateResult> {
    const res = await axios.post<SectionRegenerateResult>(
      `${API_BASE}/projects/${projectId}/briefs/${briefId}/regenerate-section`,
      payload
    );
    return res.data;
  },

  async acceptRevision(
    revisionId: string
  ): Promise<{ status: string; brief_id: string; section_key: string; new_version: number }> {
    const res = await axios.post(
      `${API_BASE}/revisions/${revisionId}/accept`
    );
    return res.data;
  },
};
