import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LoadingState } from '../common/LoadingState';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center p-8 bg-slate-50 dark:bg-slate-950">
        <LoadingState message="Verifying authentication and workspace permissions..." />
      </div>
    );
  }

  // Redirect to login if user is neither authenticated via token nor running default dev user
  if (!user && !token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
