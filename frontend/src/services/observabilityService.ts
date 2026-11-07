import { apiClient } from './api';

export interface AIMetricsResponse {
  organization_id: string;
  total_operations: number;
  successful_operations: number;
  fallback_operations: number;
  failed_operations: number;
  success_rate_pct: number;
  tokens: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  estimated_cost_usd: number;
  latency_ms: {
    average: number;
    p95: number;
  };
  operations_breakdown: Record<string, number>;
  cost_by_provider: Record<string, number>;
}

export interface PromptVersionInfo {
  name: string;
  version: string;
  is_default: boolean;
  description: string;
  created_at: string;
  input_variables: string[];
  security_guards: string[];
}

export interface EvaluationBenchmarkResult {
  suite?: string;
  total_tests: number;
  passed_tests: number;
  overall_pass_rate: number;
  total_duration_seconds: number;
  suites?: Record<string, any>;
}

export const observabilityService = {
  async getMetrics(): Promise<AIMetricsResponse> {
    const res = await apiClient.get<AIMetricsResponse>('/observability/ai-metrics');
    return res.data;
  },

  async getOperations(skip: number = 0, limit: number = 20): Promise<{ total: number; items: any[] }> {
    const res = await apiClient.get('/observability/operations', { params: { skip, limit } });
    return res.data;
  },

  async getPrompts(): Promise<PromptVersionInfo[]> {
    const res = await apiClient.get<PromptVersionInfo[]>('/observability/prompts');
    return res.data;
  },

  async runBenchmark(suite: string = 'all'): Promise<EvaluationBenchmarkResult> {
    const res = await apiClient.post<EvaluationBenchmarkResult>('/observability/evaluate', null, {
      params: { suite, mode: 'offline' }
    });
    return res.data;
  },

  async verifyClaim(content: string, sources: any[]): Promise<any> {
    const res = await apiClient.post('/observability/verify-claim', { content, sources });
    return res.data;
  }
};
