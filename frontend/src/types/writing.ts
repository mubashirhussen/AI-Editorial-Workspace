export interface WritingIssue {
  id: string;
  category: 'long_sentence' | 'passive_voice' | 'filler' | 'jargon' | 'repetition' | 'complexity';
  severity: 'low' | 'medium' | 'high';
  original_text: string;
  explanation: string;
  suggested_rewrite: string;
  reason?: string;
  confidence: number;
  status: 'pending' | 'accepted' | 'rejected';
}

export interface WritingMetrics {
  word_count: number;
  character_count: number;
  sentence_count: number;
  paragraph_count: number;
  average_sentence_length: number;
  reading_time_minutes: number;
  readability_score?: number;
  readability_grade?: string;
  readability_note?: string;
}

export interface WritingAnalysisRequest {
  text: string;
  title?: string;
  draft_id?: string;
  project_id?: string;
}

export interface WritingAnalysisResponse {
  draft_id?: string;
  overall_feedback: string;
  issues: WritingIssue[];
  metrics: WritingMetrics;
}

export interface WritingDraft {
  id: string;
  project_id?: string;
  brief_id?: string;
  title: string;
  original_content: string;
  revised_content: string;
  final_content?: string;
  content_type?: string;
  target_audience?: string;
  tone?: string;
  desired_length?: number;
  word_count?: number;
  readability_score?: number;
  research_grounding_score?: number;
  unsupported_claims_count?: number;
  style_profile_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
  suggestions?: WritingIssue[];
}

export interface DraftCreate {
  title?: string;
  original_content?: string;
  content?: string;
  project_id?: string;
  brief_id?: string;
  content_type?: string;
  target_audience?: string;
  tone?: string;
  desired_length?: number;
  style_profile_id?: string;
}

export interface DraftUpdate {
  title?: string;
  content?: string;
  revised_content?: string;
  final_content?: string;
  status?: string;
  content_type?: string;
  target_audience?: string;
  tone?: string;
  desired_length?: number;
  style_profile_id?: string;
}

export interface SuggestionActionResponse {
  success: boolean;
  draft_id: string;
  suggestion_id: string;
  status: 'accepted' | 'rejected';
  revised_content: string;
  metrics?: WritingMetrics;
}

export interface AcceptAllResponse {
  success: boolean;
  draft_id: string;
  applied_count: number;
  revised_content: string;
  metrics?: WritingMetrics;
}

export interface DraftComparisonResponse {
  draft_id: string;
  title: string;
  original_content: string;
  revised_content: string;
  diff_summary: {
    characters_added: number;
    characters_removed: number;
    word_count_delta: number;
    readability_delta: number;
  };
  suggestions_applied: {
    accepted: number;
    rejected: number;
    pending: number;
  };
  metrics: WritingMetrics;
}

