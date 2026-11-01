import { apiClient } from './api';
import { Project, ProjectCreate, ProjectUpdate, DashboardStats } from '../types';

export const projectService = {
  async getProjects(skip: number = 0, limit: number = 50): Promise<{ total: number; items: Project[] }> {
    const res = await apiClient.get('/research/projects', { params: { skip, limit } });
    if (Array.isArray(res.data)) {
      return { total: res.data.length, items: res.data };
    }
    return res.data;
  },

  async getProject(id: string): Promise<Project> {
    const res = await apiClient.get(`/research/projects/${id}`);
    return res.data;
  },

  async createProject(payload: ProjectCreate): Promise<Project> {
    const res = await apiClient.post('/research/projects', payload);
    return res.data;
  },

  async updateProject(id: string, payload: ProjectUpdate): Promise<Project> {
    const res = await apiClient.put(`/research/projects/${id}`, payload);
    return res.data;
  },

  async deleteProject(id: string): Promise<{ success: boolean; message: string }> {
    const res = await apiClient.delete(`/research/projects/${id}`);
    return res.data;
  },

  async getStats(): Promise<DashboardStats> {
    const res = await apiClient.get('/research/dashboard/stats');
    return res.data;
  },
};
