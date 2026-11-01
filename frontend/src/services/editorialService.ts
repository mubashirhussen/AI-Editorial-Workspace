import { apiClient } from './api';
import { 
  EditorialOutput, 
  EditorialCreate, 
  EditorialUpdate, 
  EditorialExportResponse,
  HeadlineGenerateRequest,
  HeadlineGenerateResponse,
  EditorialReview,
  EditorialComment,
  EditorialDashboardStats
} from '../types';

export const editorialService = {
  async generateHeadlines(payload: HeadlineGenerateRequest): Promise<HeadlineGenerateResponse> {
    const res = await apiClient.post('/editorial/headlines', payload);
    return res.data;
  },

  async generateEditorial(payload: EditorialCreate): Promise<EditorialOutput> {
    const res = await apiClient.post('/editorial/generate', payload);
    return res.data;
  },

  async getEditorials(projectId?: string): Promise<EditorialOutput[]> {
    const res = await apiClient.get('/editorial', { params: projectId ? { project_id: projectId } : {} });
    return res.data;
  },

  async getEditorial(id: string): Promise<EditorialOutput> {
    const res = await apiClient.get(`/editorial/${id}`);
    return res.data;
  },

  async createEditorial(payload: any): Promise<EditorialOutput> {
    const res = await apiClient.post('/editorial', payload);
    return res.data;
  },

  async updateEditorial(id: string, payload: EditorialUpdate): Promise<EditorialOutput> {
    const res = await apiClient.put(`/editorial/${id}`, payload);
    return res.data;
  },

  async deleteEditorial(id: string): Promise<void> {
    await apiClient.delete(`/editorial/${id}`);
  },

  async exportEditorial(id: string, format: string = 'markdown'): Promise<EditorialExportResponse> {
    const res = await apiClient.get(`/editorial/${id}/export`, { params: { format } });
    return res.data;
  },

  async runAiReview(id: string): Promise<any> {
    const res = await apiClient.post(`/editorial/${id}/ai-review`);
    return res.data;
  },

  async submitForReview(id: string): Promise<any> {
    const res = await apiClient.post(`/editorial/${id}/submit-review`);
    return res.data;
  },

  async getReviews(id: string): Promise<EditorialReview[]> {
    const res = await apiClient.get(`/editorial/${id}/reviews`);
    return res.data;
  },

  async createReview(id: string, payload: any): Promise<EditorialReview> {
    const res = await apiClient.post(`/editorial/${id}/reviews`, payload);
    return res.data;
  },

  async addComment(reviewId: string, payload: any): Promise<EditorialComment> {
    const res = await apiClient.post(`/editorial/reviews/${reviewId}/comments`, payload);
    return res.data;
  },

  async updateComment(commentId: string, payload: any): Promise<EditorialComment> {
    const res = await apiClient.patch(`/editorial/comments/${commentId}`, payload);
    return res.data;
  },

  async requestChanges(id: string, payload: { reviewer_name: string; feedback: string }): Promise<any> {
    const res = await apiClient.post(`/editorial/${id}/request-changes`, payload);
    return res.data;
  },

  async approveEditorial(id: string, payload: { reviewer_name: string; approval_notes?: string }): Promise<any> {
    const res = await apiClient.post(`/editorial/${id}/approve`, payload);
    return res.data;
  },

  async finalizeEditorial(id: string, payload: { finalized_by: string; publication_notes?: string }): Promise<any> {
    const res = await apiClient.post(`/editorial/${id}/finalize`, payload);
    return res.data;
  },

  async updateRevision(id: string, payload: { revised_content: string; headline?: string }): Promise<any> {
    const res = await apiClient.put(`/editorial/${id}/revision`, payload);
    return res.data;
  },

  async getDashboardStats(): Promise<EditorialDashboardStats> {
    const res = await apiClient.get('/editorial/dashboard/stats');
    return res.data;
  },
};
