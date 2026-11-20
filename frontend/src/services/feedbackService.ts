import { apiClient } from './api';

export type FeedbackCategory =
  | 'bug_report'
  | 'feature_request'
  | 'ux_improvement'
  | 'ai_output_quality'
  | 'research_accuracy'
  | 'citation_issue'
  | 'writing_quality'
  | 'editorial_workflow'
  | 'general';

export type FeedbackSeverity = 'low' | 'medium' | 'high' | 'critical';

export type FeedbackStatus = 'NEW' | 'TRIAGED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'REJECTED';

export interface FeedbackItem {
  id: string;
  organization_id?: string | null;
  user_id?: string | null;
  user_email?: string | null;
  title: string;
  description: string;
  category: FeedbackCategory;
  severity: FeedbackSeverity;
  module_reference?: string | null;
  status: FeedbackStatus;
  admin_notes?: string | null;
  assigned_to?: string | null;
  resolution_summary?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackCreateInput {
  title: string;
  description: string;
  category: FeedbackCategory;
  severity: FeedbackSeverity;
  module_reference?: string;
}

export interface FeedbackUpdateInput {
  status?: FeedbackStatus;
  admin_notes?: string;
  assigned_to?: string;
  resolution_summary?: string;
}

export interface FeedbackListResponse {
  total: number;
  items: FeedbackItem[];
}

export interface FeedbackSummaryResponse {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
}

export const feedbackService = {
  async submitFeedback(data: FeedbackCreateInput): Promise<FeedbackItem> {
    const res = await apiClient.post<FeedbackItem>('/feedback', data);
    return res.data;
  },

  async listFeedback(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    category?: string;
    severity?: string;
    module_reference?: string;
  }): Promise<FeedbackListResponse> {
    const res = await apiClient.get<FeedbackListResponse>('/feedback', { params });
    return res.data;
  },

  async getSummary(): Promise<FeedbackSummaryResponse> {
    const res = await apiClient.get<FeedbackSummaryResponse>('/feedback/summary');
    return res.data;
  },

  async getFeedback(id: string): Promise<FeedbackItem> {
    const res = await apiClient.get<FeedbackItem>(`/feedback/${id}`);
    return res.data;
  },

  async updateFeedback(id: string, data: FeedbackUpdateInput): Promise<FeedbackItem> {
    const res = await apiClient.patch<FeedbackItem>(`/feedback/${id}`, data);
    return res.data;
  },

  async deleteFeedback(id: string): Promise<void> {
    await apiClient.delete(`/feedback/${id}`);
  }
};
