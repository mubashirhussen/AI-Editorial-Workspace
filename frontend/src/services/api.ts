import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface ApiError extends Error {
  requestId?: string;
  statusCode?: number;
  errorCategory?: string;
  details?: any;
}

// In-flight GET request deduplication cache to prevent duplicate redundant calls
const pendingGetRequests = new Map<string, Promise<any>>();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const orgId = localStorage.getItem('active_org_id');
  if (orgId && config.headers) {
    config.headers['X-Organization-Id'] = orgId;
  }

  // Ensure multipart file uploads let the browser generate the boundary
  if (config.data instanceof FormData && config.headers) {
    delete config.headers['Content-Type'];
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<any>) => {
    let message = 'An unexpected network error occurred.';
    let requestId: string | undefined = undefined;
    let errorCategory: string | undefined = undefined;
    let details: any = undefined;

    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Extract Request ID from headers or error body
      requestId = (error.response.headers?.['x-request-id'] as string) || data?.request_id;
      errorCategory = data?.error_category || data?.error?.code;
      details = data?.error?.details || data?.detail;

      // Session expiration handling
      if (status === 401) {
        const hadToken = !!localStorage.getItem('access_token');
        if (hadToken) {
          localStorage.removeItem('access_token');
          window.dispatchEvent(
            new CustomEvent('session-expired', {
              detail: { message: 'Your session has expired. Please sign in again.' },
            })
          );
        }
      }

      if (data?.message) {
        message = data.message;
      } else if (data?.detail) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Pydantic validation error array
          message = data.detail.map((d: any) => `${d.loc?.join('.') || 'field'}: ${d.msg}`).join(', ');
        } else {
          message = JSON.stringify(data.detail);
        }
      } else if (status === 400) {
        message = 'Invalid request parameters (400).';
      } else if (status === 401) {
        message = 'Authentication required. Please sign in.';
      } else if (status === 403) {
        message = 'You do not have permission to perform this action (403).';
      } else if (status === 404) {
        message = 'Requested resource not found (404).';
      } else if (status === 422) {
        message = 'Validation error: please verify submitted data (422).';
      } else if (status === 429) {
        message = 'Rate limit exceeded: please slow down requests (429).';
      } else if (status === 503) {
        message = 'Service Unavailable: critical backend dependencies are not ready (503).';
      } else if (status >= 500) {
        message = 'Internal server error: backend service encountered an issue (500).';
      }
    } else if (error.code === 'ECONNABORTED') {
      message = 'Request timed out after 30 seconds. Please retry.';
    } else if (error.request) {
      message = 'Backend service is currently unreachable. Ensure server is running on port 8000.';
    }

    if (requestId && !message.includes(requestId)) {
      message = `${message} (Correlation ID: ${requestId})`;
    }

    console.error(`[API Error ${error.response?.status || 'Network'}]:`, message);

    const apiError = new Error(message) as ApiError;
    apiError.requestId = requestId;
    apiError.statusCode = error.response?.status;
    apiError.errorCategory = errorCategory;
    apiError.details = details;

    return Promise.reject(apiError);
  }
);
