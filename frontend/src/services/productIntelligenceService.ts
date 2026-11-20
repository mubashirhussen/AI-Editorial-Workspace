/**
 * Phase 38: Product Intelligence, Recommendations & Workflow Optimization Client Service
 * Provides typed API access to data quality diagnostics, evidence-backed insights,
 * recommendation lifecycle actions, automated optimizations, and impact measurement.
 */

import { apiClient } from './api';

export interface DataQualityReport {
  status: 'HEALTHY' | 'WARNING' | 'INSUFFICIENT_DATA';
  score: number;
  sample_size: number;
  is_sufficient: boolean;
  checks: Record<string, string>;
}

export interface IntelligenceInsight {
  id: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  detected_pattern: string;
  evidence: Record<string, any>;
  metrics: Record<string, any>;
  confidence_score: number;
  status: string;
  created_at: string;
}

export interface IntelligenceRecommendation {
  id: string;
  insight_id?: string;
  category: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  proposed_action: string;
  expected_benefit: string;
  estimated_effort: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence_score: number;
  status: 'DETECTED' | 'READY' | 'ACCEPTED' | 'IN_PROGRESS' | 'IMPLEMENTED' | 'VERIFIED' | 'REJECTED' | 'DEFERRED';
  assigned_to?: string;
  implementation_notes?: string;
  is_automated: boolean;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceOverview {
  data_quality: DataQualityReport;
  active_insights_count: number;
  high_priority_recommendations_count: number;
  implemented_improvements_count: number;
  pending_recommendations_count: number;
  insights: IntelligenceInsight[];
  recommendations: IntelligenceRecommendation[];
}

export interface ImpactEvaluation {
  id: string;
  recommendation_id: string;
  baseline_metrics: Record<string, any>;
  current_metrics: Record<string, any>;
  metric_delta: Record<string, any>;
  evaluation_status: 'IMPROVED' | 'NO_SIGNIFICANT_CHANGE' | 'REGRESSED' | 'INSUFFICIENT_DATA' | 'NOT_EVALUATED';
  notes?: string;
  evaluated_at: string;
}

export const productIntelligenceService = {
  /**
   * Triggers an active intelligence analysis run over historical analytics data.
   */
  async runAnalysis(days = 30): Promise<{ status: string; insights_generated: number; recommendations_generated: number; data_quality: DataQualityReport }> {
    const res = await apiClient.post(`/intelligence/analyze?days=${days}`);
    return res.data;
  },

  /**
   * Fetches high-level intelligence overview.
   */
  async getOverview(): Promise<IntelligenceOverview> {
    const res = await apiClient.get<IntelligenceOverview>('/intelligence/overview');
    return res.data;
  },

  /**
   * Fetches data quality status.
   */
  async getStatus(days = 30): Promise<DataQualityReport> {
    const res = await apiClient.get<DataQualityReport>(`/intelligence/status?days=${days}`);
    return res.data;
  },

  /**
   * Fetches insights feed with optional category filter.
   */
  async getInsights(category?: string): Promise<IntelligenceInsight[]> {
    const url = category ? `/intelligence/insights?category=${encodeURIComponent(category)}` : '/intelligence/insights';
    const res = await apiClient.get<IntelligenceInsight[]>(url);
    return res.data;
  },

  /**
   * Fetches recommendations list with optional filters.
   */
  async getRecommendations(status?: string, priority?: string): Promise<IntelligenceRecommendation[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await apiClient.get<IntelligenceRecommendation[]>(`/intelligence/recommendations${qs}`);
    return res.data;
  },

  /**
   * Accepts a recommendation.
   */
  async acceptRecommendation(id: string, notes?: string): Promise<IntelligenceRecommendation> {
    const res = await apiClient.post<IntelligenceRecommendation>(`/intelligence/recommendations/${id}/accept`, { notes });
    return res.data;
  },

  /**
   * Rejects a recommendation.
   */
  async rejectRecommendation(id: string, notes?: string): Promise<IntelligenceRecommendation> {
    const res = await apiClient.post<IntelligenceRecommendation>(`/intelligence/recommendations/${id}/reject`, { notes });
    return res.data;
  },

  /**
   * Defers a recommendation.
   */
  async deferRecommendation(id: string, notes?: string): Promise<IntelligenceRecommendation> {
    const res = await apiClient.post<IntelligenceRecommendation>(`/intelligence/recommendations/${id}/defer`, { notes });
    return res.data;
  },

  /**
   * Marks a recommendation as implemented.
   */
  async implementRecommendation(id: string, notes?: string): Promise<IntelligenceRecommendation> {
    const res = await apiClient.post<IntelligenceRecommendation>(`/intelligence/recommendations/${id}/implement`, { notes });
    return res.data;
  },

  /**
   * Formally verifies a recommendation after impact demonstration.
   */
  async verifyRecommendation(id: string, notes?: string): Promise<IntelligenceRecommendation> {
    const res = await apiClient.post<IntelligenceRecommendation>(`/intelligence/recommendations/${id}/verify`, { notes });
    return res.data;
  },

  /**
   * Submits user feedback on recommendation quality.
   */
  async submitFeedback(id: string, feedback: { feedback_type: string; rating: number; comment?: string }): Promise<void> {
    await apiClient.post(`/intelligence/recommendations/${id}/feedback`, feedback);
  },

  /**
   * Executes a safe, low-risk automated workflow optimization.
   */
  async executeOptimization(action_type: string, recommendation_id?: string, payload: Record<string, any> = {}): Promise<any> {
    const url = recommendation_id ? `/intelligence/optimize?recommendation_id=${recommendation_id}` : '/intelligence/optimize';
    const res = await apiClient.post(url, { action_type, action_payload: payload });
    return res.data;
  },

  /**
   * Evaluates post-implementation impact.
   */
  async getImpact(recommendation_id: string): Promise<ImpactEvaluation> {
    const res = await apiClient.get<ImpactEvaluation>(`/intelligence/impact/${recommendation_id}`);
    return res.data;
  },

  /**
   * Fetches curated workflow optimizations.
   */
  async getWorkflowOptimizations(): Promise<Record<string, IntelligenceRecommendation[]>> {
    const res = await apiClient.get<Record<string, IntelligenceRecommendation[]>>('/intelligence/workflow-optimization');
    return res.data;
  }
};
