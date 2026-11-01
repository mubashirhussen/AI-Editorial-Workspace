import React from 'react';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helperText?: string;
  error?: string;
  showCount?: boolean;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  helperText,
  error,
  showCount = false,
  className = '',
  id,
  value,
  maxLength,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const currentLength = typeof value === 'string' ? value.length : 0;

  return (
    <div className="space-y-1.5 w-full">
      <div className="flex items-center justify-between">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
            {label}
          </label>
        )}
        {showCount && maxLength && (
          <span className="text-[11px] text-slate-400 font-mono">
            {currentLength}/{maxLength}
          </span>
        )}
      </div>
      <textarea
        id={inputId}
        value={value}
        maxLength={maxLength}
        className={`w-full bg-white dark:bg-slate-900 border rounded-xl p-3 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 transition-all resize-y ${
          error
            ? 'border-rose-300 focus:ring-rose-500/20 focus:border-rose-500'
            : 'border-slate-200 dark:border-slate-800 focus:ring-blue-500/20 focus:border-blue-500'
        } ${className}`}
        {...props}
      />
      {error ? (
        <p className="text-[11px] text-rose-600 dark:text-rose-400 font-medium">{error}</p>
      ) : helperText ? (
        <p className="text-[11px] text-slate-400">{helperText}</p>
      ) : null}
    </div>
  );
};

