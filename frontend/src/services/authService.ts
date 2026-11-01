import { apiClient } from './api';
import {
  AuthResponse,
  UserProfileResponse,
  Organization,
  Membership,
  Invitation,
  OrgRole
} from '../types/auth';

export const authService = {
  async register(payload: { email: string; password: string; full_name: string; organization_name?: string }): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/register', payload);
    return res.data;
  },

  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const res = await apiClient.post<AuthResponse>('/auth/login', payload);
    return res.data;
  },

  async getMe(): Promise<UserProfileResponse> {
    const res = await apiClient.get<UserProfileResponse>('/auth/me');
    return res.data;
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('active_org_id');
    }
  },

  async getOrganizations(): Promise<Organization[]> {
    const res = await apiClient.get<Organization[]>('/organizations');
    return res.data;
  },

  async createOrganization(payload: { name: string; slug?: string }): Promise<Organization> {
    const res = await apiClient.post<Organization>('/organizations', payload);
    return res.data;
  },

  async getOrganizationDetails(orgId: string): Promise<Organization> {
    const res = await apiClient.get<Organization>(`/organizations/${orgId}`);
    return res.data;
  },

  async updateOrganization(orgId: string, payload: { name?: string; slug?: string }): Promise<Organization> {
    const res = await apiClient.put<Organization>(`/organizations/${orgId}`, payload);
    return res.data;
  },

  async getMembers(orgId: string): Promise<Membership[]> {
    const res = await apiClient.get<Membership[]>(`/organizations/${orgId}/members`);
    return res.data;
  },

  async updateMemberRole(orgId: string, userId: string, role: OrgRole): Promise<Membership> {
    const res = await apiClient.put<Membership>(`/organizations/${orgId}/members/${userId}/role`, { role });
    return res.data;
  },

  async removeMember(orgId: string, userId: string): Promise<void> {
    await apiClient.delete(`/organizations/${orgId}/members/${userId}`);
  },

  async getInvitations(orgId: string): Promise<Invitation[]> {
    const res = await apiClient.get<Invitation[]>(`/organizations/${orgId}/invitations`);
    return res.data;
  },

  async createInvitation(orgId: string, payload: { email: string; role: OrgRole }): Promise<Invitation> {
    const res = await apiClient.post<Invitation>(`/organizations/${orgId}/invitations`, payload);
    return res.data;
  },

  async revokeInvitation(orgId: string, invitationId: string): Promise<void> {
    await apiClient.delete(`/organizations/${orgId}/invitations/${invitationId}`);
  },

  async acceptInvitation(token: string): Promise<Membership> {
    const res = await apiClient.post<Membership>(`/organizations/invitations/${token}/accept`);
    return res.data;
  }
};

