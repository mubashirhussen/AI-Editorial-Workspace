import { apiClient } from './api';
import {
  DocumentType,
  EditorialVersion,
  VersionComparisonResponse,
  RestoreVersionResponse
} from '../types/version';

export const versionService = {
  getVersions: async (
    documentType: DocumentType,
    documentId: string,
    limit: number = 50
  ): Promise<EditorialVersion[]> => {
    const res = await apiClient.get(`/documents/${documentType}/${documentId}/versions`, {
      params: { limit }
    });
    return res.data;
  },

  getVersion: async (
    documentType: DocumentType,
    documentId: string,
    versionId: string
  ): Promise<EditorialVersion> => {
    const res = await apiClient.get(`/documents/${documentType}/${documentId}/versions/${versionId}`);
    return res.data;
  },

  compareVersions: async (
    documentType: DocumentType,
    documentId: string,
    fromVersion: string | number,
    toVersion: string | number
  ): Promise<VersionComparisonResponse> => {
    const res = await apiClient.get(`/documents/${documentType}/${documentId}/compare`, {
      params: {
        from_version: String(fromVersion),
        to_version: String(toVersion)
      }
    });
    return res.data;
  },

  restoreVersion: async (
    documentType: DocumentType,
    documentId: string,
    versionId: string,
    note?: string
  ): Promise<RestoreVersionResponse> => {
    const res = await apiClient.post(
      `/documents/${documentType}/${documentId}/restore/${versionId}`,
      { confirm: true, note }
    );
    return res.data;
  }
};

