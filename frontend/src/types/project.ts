export interface Project {
  id: string;
  title: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
  sources?: any[];
  briefs?: any[];
}

export interface ProjectCreate {
  title: string;
  description?: string;
}

export interface ProjectUpdate {
  title?: string;
  description?: string;
  status?: string;
}

export interface DashboardStats {
  total_projects: number;
  total_sources: number;
  total_drafts: number;
  total_editorial: number;
  recent_projects: Array<{
    id: string;
    title: string;
    status: string;
    sources_count: number;
    has_brief: boolean;
    updated_at: string;
  }>;
  recent_sources: Array<{
    id: string;
    project_id: string;
    title: string;
    url?: string;
    status: string;
    created_at: string;
  }>;
}

