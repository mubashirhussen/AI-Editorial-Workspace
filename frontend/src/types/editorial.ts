export interface SourceReference {
  index: number;
  source_id?: string;
  title: string;
  url?: string;
  citation_text?: string;
  supported_claim?: string;
  supporting_excerpt?: string;
  evidence_classification?: string;
}

export interface HeadlineOption {
  headline: string;
  editorial_angle: string;
  explanation: string;
}

export interface HeadlineGenerateRequest {
  project_id: string;
  research_brief_id?: string;
  audience?: string;
  editorial_angle?: string;
  tone?: string;
}

export interface HeadlineGenerateResponse {
  project_id: string;
  headlines: HeadlineOption[];
  recommended_headline?: string;
}

export interface EditorialOutput {
  id: string;
  project_id: string;
  draft_id?: string;
  headline: string;
  content: string;
  original_content?: string;
  version?: number;
  word_count: number;
  source_references: SourceReference[];
  ai_review_results?: any;
  status: string;
  created_at: string;
  updated_at: string;
  reviews?: EditorialReview[];
}

export interface EditorialComment {
  id: string;
  review_id: string;
  section_reference?: string;
  original_text?: string;
  comment: string;
  suggested_revision?: string;
  resolution_status: 'open' | 'resolved' | 'rejected';
  created_at: string;
}

export interface EditorialReview {
  id: string;
  editorial_id: string;
  reviewer_name: string;
  review_status: string;
  overall_feedback?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
  comments: EditorialComment[];
}

export interface EditorialDashboardStats {
  pending_human_reviews: number;
  approved_editorials: number;
  changes_requested: number;
  finalized_editorials: number;
  total_editorials: number;
  recent_activity: Array<{
    review_id: string;
    editorial_id: string;
    reviewer_name: string;
    review_status: string;
    overall_feedback?: string;
    created_at?: string;
  }>;
}

export interface EditorialCreate {
  project_id: string;
  research_brief_id?: string;
  selected_headline?: string;
  angle_headline?: string;
  audience?: string;
  editorial_angle?: string;
  tone?: string;
  min_words?: number;
  max_words?: number;
  key_takeaway?: string;
}

export interface EditorialUpdate {
  headline?: string;
  content?: string;
  status?: string;
}

export interface EditorialExportResponse {
  editorial_id: string;
  headline: string;
  markdown_content: string;
  plain_text_content: string;
  html_content?: string;
  format?: string;
  word_count: number;
  exported_at: string;
}
