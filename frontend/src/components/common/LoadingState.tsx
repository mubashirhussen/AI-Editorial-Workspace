import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
  subMessage?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading workspace data...',
  subMessage,
  className = '',
}) => {
  return (
    <div className={`py-16 flex flex-col items-center justify-center text-center space-y-3 ${className}`}>
      <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center">
        <Loader2 className="w-5 h-5 animate-spin" />
      </div>
      <div>
        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">{message}</p>
        {subMessage && (
          <p className="text-[11px] text-slate-400 mt-0.5">{subMessage}</p>
        )}
      </div>
    </div>
  );
};

