import { apiClient } from './api';
import {
  StyleProfile,
  StyleProfileCreate,
  StyleCheckResponse
} from '../types/style';

export const styleService = {
  getProfiles: async (): Promise<StyleProfile[]> => {
    const res = await apiClient.get('/styles');
    return res.data;
  },

  getProfile: async (id: string): Promise<StyleProfile> => {
    const res = await apiClient.get(`/styles/${id}`);
    return res.data;
  },

  createProfile: async (data: StyleProfileCreate): Promise<StyleProfile> => {
    const res = await apiClient.post('/styles', data);
    return res.data;
  },

  updateProfile: async (id: string, data: Partial<StyleProfileCreate>): Promise<StyleProfile> => {
    const res = await apiClient.put(`/styles/${id}`, data);
    return res.data;
  },

  deleteProfile: async (id: string): Promise<void> => {
    await apiClient.delete(`/styles/${id}`);
  },

  checkDraftStyle: async (
    draftId: string,
    payload?: { style_profile_id?: string; content?: string }
  ): Promise<StyleCheckResponse> => {
    const res = await apiClient.post(`/writing/drafts/${draftId}/style-check`, payload || {});
    return res.data;
  }
};

