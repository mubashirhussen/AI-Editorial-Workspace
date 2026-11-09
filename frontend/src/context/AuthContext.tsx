import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User, Organization, OrgRole } from '../types/auth';
import { authService } from '../services/authService';

interface AuthContextType {
  user: User | null;
  activeOrg: Organization | null;
  organizations: Organization[];
  role: OrgRole | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  switchOrganization: (orgId: string) => Promise<void>;
  login: (payload: { email: string; password: string; remember_me?: boolean }) => Promise<void>;
  register: (payload: {
    email: string;
    password: string;
    confirm_password?: string;
    full_name: string;
    organization_name?: string;
    terms_accepted?: boolean;
  }) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message: string; dev_reset_token?: string }>;
  resetPassword: (token: string, new_password: string) => Promise<{ success: boolean; message: string }>;
  refreshUserProfile: () => Promise<void>;
  updateProfile: (payload: { full_name?: string; profile_image?: string }) => Promise<User>;
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
    const handleSessionExpired = () => {
      setUser(null);
      setActiveOrg(null);
      setOrganizations([]);
      setToken(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('active_org_id');
    };
    window.addEventListener('session-expired', handleSessionExpired);
    return () => window.removeEventListener('session-expired', handleSessionExpired);
  }, []);

  const loadUserAndOrgs = useCallback(async () => {
    const currentToken = localStorage.getItem('access_token');
    if (!currentToken) {
      setUser(null);
      setActiveOrg(null);
      setOrganizations([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const profile = await authService.getMe();
      setUser(profile.user);

      const orgs: Organization[] = profile.organizations.map((o) => ({
        id: o.id,
        name: o.name,
        slug: o.slug,
        role: o.role,
        created_at: o.joined_at,
      }));
      setOrganizations(orgs);

      const savedOrgId = localStorage.getItem('active_org_id');
      const matched = orgs.find((o) => o.id === savedOrgId) || orgs[0] || null;
      if (matched) {
        setActiveOrg(matched);
        localStorage.setItem('active_org_id', matched.id);
      }
    } catch (err: any) {
      console.warn('Session load warning:', err?.message || err);
      // If 401, clear stored invalid token
      if (err?.statusCode === 401 || err?.response?.status === 401) {
        localStorage.removeItem('access_token');
        setToken(null);
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUserAndOrgs();
  }, [token, loadUserAndOrgs]);

  const switchOrganization = async (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      setActiveOrg(org);
      localStorage.setItem('active_org_id', org.id);
      window.dispatchEvent(new Event('organization-changed'));
    }
  };

  const login = async (payload: { email: string; password: string; remember_me?: boolean }) => {
    const res = await authService.login(payload);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    if (res.organization) {
      localStorage.setItem('active_org_id', res.organization.id);
      setActiveOrg(res.organization);
    }
    await loadUserAndOrgs();
  };

  const register = async (payload: {
    email: string;
    password: string;
    confirm_password?: string;
    full_name: string;
    organization_name?: string;
    terms_accepted?: boolean;
  }) => {
    const res = await authService.register(payload);
    localStorage.setItem('access_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    if (res.organization) {
      localStorage.setItem('active_org_id', res.organization.id);
      setActiveOrg(res.organization);
    }
    await loadUserAndOrgs();
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setActiveOrg(null);
      setOrganizations([]);
      setToken(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('active_org_id');
    }
  };

  const forgotPassword = async (email: string) => {
    return authService.forgotPassword(email);
  };

  const resetPassword = async (tkn: string, new_password: string) => {
    return authService.resetPassword(tkn, new_password);
  };

  const refreshUserProfile = async () => {
    await loadUserAndOrgs();
  };

  const updateProfile = async (payload: { full_name?: string; profile_image?: string }) => {
    const updated = await authService.updateUserProfile(payload);
    setUser(updated);
    return updated;
  };

  const role = (activeOrg?.role as OrgRole) || 'OWNER';
  const isAuthenticated = Boolean(user && token);
  const isAdmin = user?.role === 'ADMIN';

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
        isAuthenticated,
        isAdmin,
        switchOrganization,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        refreshUserProfile,
        updateProfile,
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
