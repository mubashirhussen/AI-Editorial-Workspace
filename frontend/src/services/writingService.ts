import { apiClient } from './api';
import { 
  WritingDraft, 
  DraftCreate, 
  DraftUpdate, 
  WritingAnalysisRequest, 
  WritingAnalysisResponse, 
  WritingMetrics,
  WritingIssue,
  SuggestionActionResponse,
  AcceptAllResponse,
  DraftComparisonResponse
} from '../types';

export const writingService = {
  async createDraft(payload: DraftCreate): Promise<WritingDraft> {
    const res = await apiClient.post('/writing/drafts', payload);
    return res.data;
  },

  async getDrafts(skip: number = 0, limit: number = 50): Promise<WritingDraft[]> {
    const res = await apiClient.get('/writing/drafts', { params: { skip, limit } });
    return res.data;
  },

  async getDraft(id: string): Promise<WritingDraft> {
    const res = await apiClient.get(`/writing/drafts/${id}`);
    return res.data;
  },

  async updateDraft(id: string, payload: DraftUpdate): Promise<WritingDraft> {
    const res = await apiClient.put(`/writing/drafts/${id}`, payload);
    return res.data;
  },

  async deleteDraft(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.delete(`/writing/drafts/${id}`);
    return res.data;
  },

  async analyzeWriting(payload: WritingAnalysisRequest): Promise<WritingAnalysisResponse> {
    const res = await apiClient.post('/writing/analyze', payload);
    return res.data;
  },

  async runDraftAnalysis(draftId: string): Promise<WritingAnalysisResponse> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/analyze`);
    return res.data;
  },

  async getDraftAnalysis(draftId: string): Promise<WritingAnalysisResponse> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/analysis`);
    return res.data;
  },

  async getDraftMetrics(draftId: string): Promise<WritingMetrics> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/metrics`);
    return res.data;
  },

  async getSuggestions(draftId: string): Promise<WritingIssue[]> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/suggestions`);
    return res.data;
  },

  async acceptSuggestion(draftId: string, suggestionId: string): Promise<SuggestionActionResponse> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/suggestions/${suggestionId}/accept`);
    return res.data;
  },

  async rejectSuggestion(draftId: string, suggestionId: string): Promise<SuggestionActionResponse> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/suggestions/${suggestionId}/reject`);
    return res.data;
  },

  async acceptAll(draftId: string): Promise<AcceptAllResponse> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/accept-all`);
    return res.data;
  },

  async compareDraft(draftId: string): Promise<DraftComparisonResponse> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/compare`);
    return res.data;
  },

  async rewriteDraft(draftId: string, payload?: { prompt?: string; mode?: string }): Promise<any> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/rewrite`, payload || {});
    return res.data;
  },

  async getDraftVersions(draftId: string): Promise<any[]> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/versions`);
    return res.data;
  },

  async restoreDraftVersion(draftId: string, versionId: string): Promise<any> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/restore/${versionId}`);
    return res.data;
  },

  async checkStyle(draftId: string, rules?: any): Promise<any> {
    const res = await apiClient.post(`/writing/drafts/${draftId}/style-check`, rules || {});
    return res.data;
  },

  async exportDraft(draftId: string, format: string = 'markdown'): Promise<{ blob: Blob; filename: string }> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    const disposition = res.headers['content-disposition'];
    let filename = `draft_${draftId}.${format === 'markdown' ? 'md' : format}`;
    if (disposition) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) filename = match[1];
    }
    return { blob: res.data, filename };
  },

  async rewriteSelection(payload: {
    selected_text: string;
    operation: string;
    draft_id?: string;
    target_tone?: string;
    custom_instructions?: string;
  }): Promise<any> {
    const res = await apiClient.post('/writing/rewrite-selection', payload);
    return res.data;
  },

  async getGroundingAudit(draftId: string): Promise<any> {
    const res = await apiClient.get(`/writing/drafts/${draftId}/grounding-audit`);
    return res.data;
  },

  async generateDraft(payload: {
    topic?: string;
    project_id?: string;
    brief_id?: string;
    content_type?: string;
    target_audience?: string;
    tone?: string;
    desired_length?: number;
    editorial_instructions?: string;
  }): Promise<any> {
    const res = await apiClient.post('/writing/drafts/generate', payload);
    return res.data;
  }
};
