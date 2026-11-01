import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div className={`p-6 rounded-2xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 text-center space-y-3 max-w-md mx-auto ${className}`}>
      <div className="w-10 h-10 rounded-full bg-rose-100 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 mx-auto flex items-center justify-center">
        <AlertCircle className="w-5 h-5" />
      </div>
      <div>
        <h4 className="text-xs font-bold text-rose-900 dark:text-rose-200">{title}</h4>
        <p className="text-xs text-rose-700 dark:text-rose-300 mt-1 leading-relaxed">{message}</p>
      </div>
      {onRetry && (
        <div className="pt-2">
          <Button onClick={onRetry} variant="outline" size="sm" leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};

