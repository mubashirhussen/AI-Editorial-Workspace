import { apiClient } from './api';
import { 
  Project, 
  Source, 
  ResearchBrief, 
  AddSourceUrlPayload, 
  AddSourceTextPayload 
} from '../types';

export const researchService = {
  async addSource(projectId: string, payload: {
    source_type: 'url' | 'text';
    url?: string;
    title?: string;
    text_content?: string;
  }): Promise<Source> {
    const res = await apiClient.post(`/research/projects/${projectId}/sources`, payload);
    return res.data;
  },

  async addSourceUrl(projectId: string, payload: AddSourceUrlPayload): Promise<Source> {
    return this.addSource(projectId, {
      source_type: 'url',
      url: payload.url,
      title: payload.title,
    });
  },

  async addSourceText(projectId: string, payload: AddSourceTextPayload): Promise<Source> {
    return this.addSource(projectId, {
      source_type: 'text',
      title: payload.title,
      text_content: payload.text_content,
    });
  },

  async updateSource(sourceId: string, payload: { title?: string; text_content?: string }): Promise<Source> {
    const res = await apiClient.put(`/sources/${sourceId}`, payload);
    return res.data;
  },

  async deleteSource(sourceId: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.delete(`/sources/${sourceId}`);
    return res.data;
  },

  async extractSource(sourceId: string): Promise<Source> {
    const res = await apiClient.post(`/sources/${sourceId}/extract`);
    return res.data;
  },

  async analyzeSource(sourceId: string): Promise<any> {
    const res = await apiClient.post(`/sources/${sourceId}/analyze`);
    return res.data;
  },

  async uploadSourceFile(projectId: string, file: File, title?: string): Promise<Source> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }
    const res = await apiClient.post(`/research/projects/${projectId}/sources/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async reuploadSourceFile(sourceId: string, file: File): Promise<Source> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post(`/sources/${sourceId}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async generateBrief(projectId: string): Promise<ResearchBrief> {
    const res = await apiClient.post(`/research/projects/${projectId}/generate-brief`);
    return res.data;
  },

  async getBrief(projectId: string): Promise<ResearchBrief> {
    const res = await apiClient.get(`/research/projects/${projectId}/brief`);
    return res.data;
  },
};
