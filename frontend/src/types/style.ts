export interface StyleProfile {
  id: string;
  organization_id?: string | null;
  name: string;
  publication_name: string;
  tone: string;
  target_audience: string;
  max_sentence_length: number;
  preferred_sentence_length: number;
  max_paragraph_length: number;
  target_flesch_score: number;
  preferred_terminology: Record<string, string>;
  words_to_avoid: string[];
  headline_style: string;
  formatting_preferences: Record<string, any>;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface StyleProfileCreate {
  name: string;
  publication_name?: string;
  tone?: string;
  target_audience?: string;
  max_sentence_length?: number;
  preferred_sentence_length?: number;
  max_paragraph_length?: number;
  target_flesch_score?: number;
  preferred_terminology?: Record<string, string>;
  words_to_avoid?: string[];
  headline_style?: string;
  formatting_preferences?: Record<string, any>;
  is_default?: boolean;
}

export interface StyleSuggestionItem {
  id?: string;
  original_text: string;
  suggested_rewrite: string;
  explanation: string;
  category: string;
  style_rule: string;
  severity: string;
  confidence: number;
  status: string;
}

export interface StyleCheckResponse {
  draft_id?: string;
  style_profile_id: string;
  style_profile_name: string;
  style_score: number;
  metrics: {
    sentence_length_score: number;
    terminology_score: number;
    tone_score: number;
    readability_score: number;
    actual_flesch_reading_ease?: number;
    target_flesch_reading_ease?: number;
  };
  qualitative_feedback: string;
  tone_detected: string;
  terminology_deviations_count: number;
  avoided_words_count: number;
  suggestions: StyleSuggestionItem[];
}

