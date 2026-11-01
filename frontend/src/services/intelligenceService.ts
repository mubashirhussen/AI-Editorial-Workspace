import { apiClient } from './api';
import {
  EntityItem,
  IntelClaimItem,
  RelationshipItem,
  ContradictionItem,
  TrendItem,
  KnowledgeGraphResponse,
  IntelligenceAnalysisResponse
} from '../types/intelligence';

export const intelligenceService = {
  analyzeProject: async (projectId: string): Promise<IntelligenceAnalysisResponse> => {
    const res = await apiClient.post(`/projects/${projectId}/intelligence/analyze`);
    return res.data;
  },

  getEntities: async (
    projectId: string,
    params?: { entity_type?: string; source_id?: string }
  ): Promise<EntityItem[]> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/entities`, { params });
    return res.data;
  },

  getClaims: async (
    projectId: string,
    params?: { evidence_classification?: string; source_id?: string }
  ): Promise<IntelClaimItem[]> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/claims`, { params });
    return res.data;
  },

  getRelationships: async (
    projectId: string,
    params?: { relationship_type?: string }
  ): Promise<RelationshipItem[]> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/relationships`, { params });
    return res.data;
  },

  getContradictions: async (projectId: string): Promise<ContradictionItem[]> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/contradictions`);
    return res.data;
  },

  getTrends: async (projectId: string): Promise<TrendItem[]> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/trends`);
    return res.data;
  },

  getKnowledgeGraph: async (projectId: string): Promise<KnowledgeGraphResponse> => {
    const res = await apiClient.get(`/projects/${projectId}/intelligence/graph`);
    return res.data;
  }
};
