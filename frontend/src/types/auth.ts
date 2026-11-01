export type OrgRole = 'OWNER' | 'ADMIN' | 'EDITOR' | 'REVIEWER' | 'VIEWER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  role?: OrgRole | string;
  created_at: string;
}

export interface Membership {
  id: string;
  organization_id: string;
  user_id: string;
  role: OrgRole;
  joined_at: string;
  user?: User;
}

export interface Invitation {
  id: string;
  organization_id: string;
  email: string;
  role: OrgRole;
  token: string;
  expires_at: string;
  created_at: string;
  is_expired?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization?: Organization;
}

export interface UserProfileResponse {
  user: User;
  organizations: Array<{
    id: string;
    name: string;
    slug: string;
    role: OrgRole | string;
    joined_at: string;
  }>;
}

