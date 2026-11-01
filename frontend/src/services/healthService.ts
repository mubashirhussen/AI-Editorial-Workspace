import { apiClient } from './api';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unavailable';
  database: string;
  application: string;
  version: string;
  ai_engine?: {
    configured: boolean;
    available: boolean;
    model: string;
    mode: string;
  };
  telemetry?: {
    uptime_seconds: number;
    last_successful_operation?: string | null;
    ai_telemetry: {
      total_operations: number;
      successful_operations: number;
      fallback_operations: number;
      failed_operations: number;
      cumulative_tokens: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
      };
    };
    recent_events: Array<{
      timestamp: string;
      operation: string;
      duration_ms: number;
      status: string;
      error_category?: string | null;
      tokens?: {
        prompt: number;
        completion: number;
        total: number;
      } | null;
    }>;
  };
}

export const checkHealth = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/health');
  return response.data;
};

export const checkLiveness = async (): Promise<{ status: string }> => {
  const response = await apiClient.get<{ status: string }>('/health/live');
  return response.data;
};

export const checkReadiness = async (): Promise<{ status: string; database: string }> => {
  const response = await apiClient.get<{ status: string; database: string }>('/health/ready');
  return response.data;
};


