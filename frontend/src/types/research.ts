export interface ClaimItem {
  claim: string;
  evidence: string;
  evidence_type: 'direct' | 'reported' | 'inferred';
  supporting_excerpt: string;
  source_id?: string;
}

export interface SourceAnalysis {
  source_id?: string;
  source_title: string;
  source_url?: string;
  summary: string;
  key_developments: string[];
  important_claims: ClaimItem[];
  facts: string[];
  analysis: string[];
  speculation: string[];
  technical_implications: string[];
  business_implications: string[];
  limitations: string[];
}

export interface Source {
  id: string;
  project_id: string;
  title: string;
  url?: string;
  original_url?: string;
  source_type: 'url' | 'text' | 'pdf' | 'document' | 'image' | string;
  domain?: string;
  word_count?: number;
  char_count?: number;
  content_hash?: string;
  extracted_content?: string;
  raw_content?: string;
  summary?: string;
  author?: string;
  published_at?: string;
  extraction_status: 'pending' | 'extracting' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  analysis?: SourceAnalysis;
}

export interface VerifiedEvidenceItem {
  evidence_id?: string;
  source_id: string;
  source_title: string;
  source_url?: string;
  claim: string;
  supporting_excerpt: string;
  evidence_classification?: string;
  status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'CONTRADICTED' | 'NOT_VERIFIABLE';
  confidence: number;
  grounded: boolean;
  section_reference?: string;
  reasoning?: string;
  corroboration?: Array<{
    source_id: string;
    source_title: string;
    matched_keywords: string[];
  }>;
}

export interface NewsletterAngle {
  id: string;
  headline: string;
  target_audience: string;
  angle_pitch: string;
  key_points: string[];
  why_now: string;
}

export interface ResearchBriefContent {
  executive_summary: string;
  what_happened: string;
  why_it_matters: string;
  who_should_care: {
    founders: string;
    developers: string;
    business_operators: string;
    ai_researchers: string;
  };
  evidence_verification: VerifiedEvidenceItem[];
  facts_vs_analysis: {
    facts: string[];
    analysis: string[];
    speculation: string[];
  };
  opportunities_and_risks: {
    opportunities: string[];
    risks: string[];
  };
  newsletter_angles: NewsletterAngle[];
  recommended_story: {
    headline: string;
    angle_pitch: string;
    reason: string;
  };
  follow_up_questions: string[];
}

export interface ResearchBrief {
  id: string;
  project_id: string;
  executive_summary: string;
  brief_content: ResearchBriefContent;
  evidence: VerifiedEvidenceItem[];
  newsletter_angles: NewsletterAngle[];
  recommended_angle: {
    headline: string;
    angle_pitch: string;
    reason: string;
  };
  created_at: string;
  updated_at: string;
}

export interface AddSourceUrlPayload {
  url: string;
  title?: string;
}

export interface AddSourceTextPayload {
  title?: string;
  text_content: string;
}
