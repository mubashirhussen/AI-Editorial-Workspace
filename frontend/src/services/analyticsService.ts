/**
 * Phase 37: Product Analytics & User Journey Intelligence Client Service
 * Provides typed API access to analytics overview, workflow funnels,
 * feature adoption, daily trends, subsystem health, and privacy controls.
 */

import { apiClient } from './api';

export interface AnalyticsOverview {
  time_range: string;
  active_users: number;
  active_sessions: number;
  projects_created: number;
  completed_workflows: number;
  workflow_completion_rate: number;
  feature_usage_count: number;
  successful_ai_operations: number;
  failed_ai_operations: number;
  ai_success_rate: number;
  avg_workflow_duration_ms: number;
  feedback_volume: number;
}

export interface WorkflowMetric {
  workflow_type: string;
  started: number;
  completed: number;
  failed: number;
  abandoned: number;
  completion_rate: number;
  median_duration_ms: number;
  bottleneck_step: string | null;
}

export interface FunnelStep {
  step_name: string;
  count: number;
  conversion_rate: number;
  drop_off_count: number;
}

export interface FunnelSummary {
  workflow_name: string;
  total_started: number;
  total_completed: number;
  overall_conversion_rate: number;
  steps: FunnelStep[];
}

export interface FunnelsResponse {
  research_funnel: FunnelSummary;
  writing_funnel: FunnelSummary;
  editorial_funnel: FunnelSummary;
}

export interface FeatureMetric {
  feature_name: string;
  usage_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  avg_duration_ms: number;
}

export interface TrendDataPoint {
  date: string;
  projects: number;
  workflows_completed: number;
  ai_operations: number;
  events_count: number;
}

export interface AnalyticsHealth {
  status: string;
  total_events: number;
  events_last_24h: number;
  privacy_filtered_count: number;
  deduplicated_events_count: number;
  opt_out_users_count: number;
  storage_retention_days: number;
}

export interface AnalyticsPrivacyPreference {
  user_id: string;
  organization_id?: string;
  analytics_opt_out: boolean;
  do_not_track: boolean;
  updated_at: string;
}

export interface AnalyticsEventPayload {
  event_name: string;
  event_version?: number;
  project_reference?: string;
  workflow_type?: string;
  workflow_reference?: string;
  session_reference?: string;
  source?: string;
  status?: string;
  duration_ms?: number;
  properties?: Record<string, any>;
}

export const analyticsService = {
  /**
   * Fetches high-level executive product metrics.
   */
  async getOverview(days = 30): Promise<AnalyticsOverview> {
    const res = await apiClient.get<AnalyticsOverview>(`/analytics/overview?days=${days}`);
    return res.data;
  },

  /**
   * Fetches workflow completion intelligence and bottlenecks.
   */
  async getWorkflows(days = 30): Promise<{ time_range: string; workflows: WorkflowMetric[] }> {
    const res = await apiClient.get<{ time_range: string; workflows: WorkflowMetric[] }>(`/analytics/workflows?days=${days}`);
    return res.data;
  },

  /**
   * Fetches step-by-step conversion funnels for research, writing, and editorial.
   */
  async getFunnels(days = 30): Promise<FunnelsResponse> {
    const res = await apiClient.get<FunnelsResponse>(`/analytics/funnels?days=${days}`);
    return res.data;
  },

  /**
   * Fetches feature adoption and module reliability metrics.
   */
  async getFeatures(days = 30): Promise<{ features: FeatureMetric[] }> {
    const res = await apiClient.get<{ features: FeatureMetric[] }>(`/analytics/features?days=${days}`);
    return res.data;
  },

  /**
   * Fetches daily usage trend data points.
   */
  async getTrends(days = 7): Promise<{ period: string; data_points: TrendDataPoint[] }> {
    const res = await apiClient.get<{ period: string; data_points: TrendDataPoint[] }>(`/analytics/trends?days=${days}`);
    return res.data;
  },

  /**
   * Fetches analytics subsystem health and privacy metrics.
   */
  async getHealth(): Promise<AnalyticsHealth> {
    const res = await apiClient.get<AnalyticsHealth>('/analytics/health');
    return res.data;
  },

  /**
   * Tracks a privacy-safe client-side event. Never throws errors to callers.
   */
  async trackEvent(payload: AnalyticsEventPayload): Promise<void> {
    try {
      await apiClient.post('/analytics/events', payload);
    } catch (err) {
      // Non-blocking: analytics failures must never crash or interrupt client UI
      console.warn('Analytics event tracking ignored or failed gracefully:', err);
    }
  },

  /**
   * Gets user privacy preference.
   */
  async getPrivacyPreference(): Promise<AnalyticsPrivacyPreference> {
    const res = await apiClient.get<AnalyticsPrivacyPreference>('/analytics/privacy-preference');
    return res.data;
  },

  /**
   * Updates user privacy preference (e.g. opt-out).
   */
  async updatePrivacyPreference(pref: { analytics_opt_out: boolean; do_not_track: boolean }): Promise<AnalyticsPrivacyPreference> {
    const res = await apiClient.put<AnalyticsPrivacyPreference>('/analytics/privacy-preference', pref);
    return res.data;
  }
};
