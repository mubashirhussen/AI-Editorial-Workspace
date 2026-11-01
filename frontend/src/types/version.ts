export type DocumentType = 'WRITING_DRAFT' | 'RESEARCH_BRIEF' | 'EDITORIAL_OUTPUT';

export type ChangeType = 
  | 'INITIAL'
  | 'MANUAL_EDIT'
  | 'AI_REVISION'
  | 'SUGGESTION_ACCEPTED'
  | 'SUGGESTION_REJECTED'
  | 'RESTORE';

export interface EditorialVersion {
  id: string;
  organization_id?: string;
  document_type: DocumentType;
  document_id: string;
  version_number: number;
  title?: string;
  content_snapshot: string;
  change_summary: string;
  change_type: ChangeType;
  created_by?: string;
  author_name?: string;
  created_at: string;
  word_count: number;
  char_count: number;
}

export interface DiffChunk {
  type: 'addition' | 'deletion' | 'unchanged';
  text: string;
}

export interface WordDiffChunk {
  type: 'insert' | 'delete' | 'equal';
  text: string;
}

export interface VersionComparisonResponse {
  document_type: DocumentType;
  document_id: string;
  version_a: EditorialVersion;
  version_b: EditorialVersion;
  word_count_a: number;
  word_count_b: number;
  word_count_diff: number;
  char_count_a: number;
  char_count_b: number;
  char_count_diff: number;
  additions_count: number;
  deletions_count: number;
  unchanged_count: number;
  diff_chunks: DiffChunk[];
  word_diff_chunks: WordDiffChunk[];
}

export interface RestoreVersionRequest {
  confirm: boolean;
  note?: string;
}

export interface RestoreVersionResponse {
  success: boolean;
  message: string;
  document_type: DocumentType;
  document_id: string;
  restored_from_version: number;
  new_version: EditorialVersion;
  updated_content: string;
}
