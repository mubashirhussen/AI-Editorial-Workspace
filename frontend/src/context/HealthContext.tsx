import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { checkHealth, HealthStatus } from '../services/healthService';
import { ApiError } from '../services/api';

export type ConnectionStatus = 'CONNECTED' | 'CONNECTING' | 'DEGRADED' | 'UNAVAILABLE' | 'AUTH_REQUIRED';

interface HealthContextType {
  status: ConnectionStatus;
  health: HealthStatus | null;
  lastChecked: Date | null;
  error: string | null;
  isBackendHealthy: boolean;
  isOffline: boolean;
  recheckHealth: () => Promise<void>;
}

const HealthContext = createContext<HealthContextType | undefined>(undefined);

export const HealthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<ConnectionStatus>('CONNECTING');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const backoffDelayRef = useRef<number>(3000); // starts at 3s, max 24s
  const isCheckingRef = useRef<boolean>(false);

  const performHealthCheck = useCallback(async (isManualTrigger = false) => {
    if (isCheckingRef.current) return;
    isCheckingRef.current = true;

    if (isManualTrigger) {
      setStatus('CONNECTING');
    }

    try {
      const data = await checkHealth();
      setHealth(data);
      setLastChecked(new Date());
      setError(null);
      backoffDelayRef.current = 3000; // reset backoff on success

      if (data.status === 'healthy' && data.database === 'connected') {
        setStatus('CONNECTED');
      } else {
        setStatus('DEGRADED');
      }
    } catch (err: any) {
      setLastChecked(new Date());
      const apiErr = err as ApiError;
      const errMsg = apiErr.message || 'Failed to connect to backend';
      setError(errMsg);

      if (apiErr.statusCode === 401 || apiErr.statusCode === 403) {
        setStatus('AUTH_REQUIRED');
      } else if (apiErr.statusCode && apiErr.statusCode >= 500) {
        setStatus('DEGRADED');
      } else {
        // Network error / connection refused
        setStatus('UNAVAILABLE');
      }

      // Schedule exponential backoff retry if not already scheduled
      if (!isManualTrigger) {
        backoffDelayRef.current = Math.min(24000, backoffDelayRef.current * 2);
      }
    } finally {
      isCheckingRef.current = false;
    }
  }, []);

  const recheckHealth = useCallback(async () => {
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
    backoffDelayRef.current = 3000;
    await performHealthCheck(true);
  }, [performHealthCheck]);

  // Periodic heartbeat with dynamic cadence (30s when healthy, exponential backoff when failing)
  useEffect(() => {
    performHealthCheck();

    const scheduleNext = () => {
      const delay = status === 'CONNECTED' ? 30000 : backoffDelayRef.current;
      retryTimeoutRef.current = setTimeout(async () => {
        await performHealthCheck();
        scheduleNext();
      }, delay);
    };

    scheduleNext();

    // Recheck immediately when window regains focus or network comes online
    const handleFocus = () => {
      performHealthCheck();
    };
    const handleOnline = () => {
      backoffDelayRef.current = 3000;
      performHealthCheck();
    };

    window.addEventListener('focus', handleFocus);
    window.addEventListener('online', handleOnline);

    return () => {
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('online', handleOnline);
    };
  }, [performHealthCheck, status]);

  const isBackendHealthy = status === 'CONNECTED';
  const isOffline = status === 'UNAVAILABLE';

  return (
    <HealthContext.Provider
      value={{
        status,
        health,
        lastChecked,
        error,
        isBackendHealthy,
        isOffline,
        recheckHealth,
      }}
    >
      {children}
    </HealthContext.Provider>
  );
};

export const useHealth = (): HealthContextType => {
  const context = useContext(HealthContext);
  if (!context) {
    throw new Error('useHealth must be used within a HealthProvider');
  }
  return context;
};

