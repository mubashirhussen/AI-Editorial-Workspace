import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Organization, OrgRole } from '../types/auth';
import { authService } from '../services/authService';

interface AuthContextType {
  user: User | null;
  activeOrg: Organization | null;
  organizations: Organization[];
  role: OrgRole | null;
  token: string | null;
  loading: boolean;
  switchOrganization: (orgId: string) => Promise<void>;
  login: (payload: { email: string; password: string }) => Promise<void>;
  register: (payload: { email: string; password: string; full_name: string; organization_name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
  canManageOrg: boolean;
  canInvite: boolean;
  canCreateProjects: boolean;
  canAddSources: boolean;
  canEditDrafts: boolean;
  canApprove: boolean;
  canReview: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));

  useEffect(() => {
    loadUserAndOrgs();
  }, [token]);

  const loadUserAndOrgs = async () => {
    try {
      setLoading(true);
      const profile = await authService.getMe();
      setUser(profile.user);
      
      const orgs: Organization[] = profile.organizations.map(o => ({
        id: o.id,
        name: o.name,
        slug: o.slug,
        role: o.role,
        created_at: o.joined_at
      }));
      setOrganizations(orgs);

      const savedOrgId = localStorage.getItem('active_org_id');
      const matched = orgs.find(o => o.id === savedOrgId) || orgs[0] || null;
      if (matched) {
        setActiveOrg(matched);
        localStorage.setItem('active_org_id', matched.id);
      }
    } catch (err) {
      // In single-user dev mode, backend automatically provisions default user
      console.warn('Authentication initialized in default workspace mode.');
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = async (orgId: string) => {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setActiveOrg(org);
      localStorage.setItem('active_org_id', org.id);
      // Reload project list by notifying consumers
      window.dispatchEvent(new Event('organization-changed'));
    }
  };

  const login = async (payload: { email: string; password: string }) => {
    const res = await authService.login(payload);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    if (res.organization) {
      localStorage.setItem('active_org_id', res.organization.id);
      setActiveOrg(res.organization);
    }
    await loadUserAndOrgs();
  };

  const register = async (payload: { email: string; password: string; full_name: string; organization_name?: string }) => {
    const res = await authService.register(payload);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    if (res.organization) {
      localStorage.setItem('active_org_id', res.organization.id);
      setActiveOrg(res.organization);
    }
    await loadUserAndOrgs();
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
    setActiveOrg(null);
    setOrganizations([]);
    setToken(null);
  };

  const refreshUserProfile = async () => {
    await loadUserAndOrgs();
  };

  const role = (activeOrg?.role as OrgRole) || 'OWNER';

  const canManageOrg = role === 'OWNER' || role === 'ADMIN';
  const canInvite = role === 'OWNER' || role === 'ADMIN';
  const canCreateProjects = role === 'OWNER' || role === 'ADMIN' || role === 'EDITOR';
  const canAddSources = role === 'OWNER' || role === 'ADMIN' || role === 'EDITOR';
  const canEditDrafts = role === 'OWNER' || role === 'ADMIN' || role === 'EDITOR';
  const canApprove = role === 'OWNER' || role === 'ADMIN' || role === 'REVIEWER';
  const canReview = role !== 'VIEWER';

  return (
    <AuthContext.Provider
      value={{
        user,
        activeOrg,
        organizations,
        role,
        token,
        loading,
        switchOrganization,
        login,
        register,
        logout,
        refreshUserProfile,
        canManageOrg,
        canInvite,
        canCreateProjects,
        canAddSources,
        canEditDrafts,
        canApprove,
        canReview,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

