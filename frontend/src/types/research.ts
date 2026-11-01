export interface ClaimItem {
  claim: string;
  evidence: string;
  evidence_type: 'direct' | 'reported' | 'inferred';
  supporting_excerpt: string;
}

export interface SourceAnalysis {
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
  source_type: 'url' | 'text';
  extracted_content?: string;
  summary?: string;
  author?: string;
  published_at?: string;
  extraction_status: 'pending' | 'extracting' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  analysis?: SourceAnalysis;
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
  evidence_verification: Array<{
    claim: string;
    supporting_excerpt: string;
    source_title: string;
    source_url: string;
  }>;
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
  evidence: any[];
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
  title: string;
  text_content: string;
}

