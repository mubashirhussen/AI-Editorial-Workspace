export type OrgRole = 'OWNER' | 'ADMIN' | 'EDITOR' | 'REVIEWER' | 'VIEWER';
export type SystemRole = 'ADMIN' | 'USER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role?: SystemRole | string;
  is_active: boolean;
  is_verified?: boolean;
  profile_image?: string | null;
  last_login_at?: string | null;
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

export interface UserSession {
  id: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  last_activity_at?: string;
  expires_at: string;
  is_current: boolean;
}

export interface PasswordStrengthResponse {
  is_valid: boolean;
  score: number;
  strength_label: 'Weak' | 'Fair' | 'Good' | 'Strong';
  error_message: string;
  requirements: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    digit: boolean;
    special: boolean;
  };
}
