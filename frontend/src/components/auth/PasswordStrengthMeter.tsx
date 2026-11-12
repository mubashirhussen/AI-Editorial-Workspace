import React from 'react';
import { Check, X } from 'lucide-react';

interface PasswordStrengthMeterProps {
  password: string;
  email?: string;
  fullName?: string;
}

export const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  email = '',
  fullName = '',
}) => {
  const requirements = [
    { label: 'At least 12 characters', met: password.length >= 12 },
    { label: 'Uppercase letter (A-Z)', met: /[A-Z]/.test(password) },
    { label: 'Lowercase letter (a-z)', met: /[a-z]/.test(password) },
    { label: 'Numeric digit (0-9)', met: /\d/.test(password) },
    { label: 'Special symbol (!@#$%^&*)', met: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]/.test(password) },
  ];

  const metCount = requirements.filter((r) => r.met).length;

  // Compute score: 0 to 4
  let score = 0;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/`~]/.test(password)) score += 1;

  // Personal info check
  const cleanPwd = password.toLowerCase();
  const emailPrefix = email.split('@')[0]?.toLowerCase();
  const containsEmail = emailPrefix && emailPrefix.length >= 3 && cleanPwd.includes(emailPrefix);
  const containsName = fullName
    .toLowerCase()
    .split(/\s+/)
    .some((part) => part.length >= 3 && cleanPwd.includes(part));

  if (containsEmail || containsName) {
    score = Math.min(score, 1);
  }

  const getStrengthInfo = () => {
    if (!password) return { label: '', color: 'bg-slate-200 dark:bg-slate-700', text: 'text-slate-400', width: 'w-0' };
    if (score <= 1) return { label: 'Weak', color: 'bg-rose-500', text: 'text-rose-500', width: 'w-1/4' };
    if (score === 2) return { label: 'Fair', color: 'bg-amber-500', text: 'text-amber-500', width: 'w-2/4' };
    if (score === 3) return { label: 'Good', color: 'bg-blue-500', text: 'text-blue-500', width: 'w-3/4' };
    return { label: 'Strong', color: 'bg-emerald-500', text: 'text-emerald-500', width: 'w-full' };
  };

  const strength = getStrengthInfo();

  if (!password) return null;

  return (
    <div className="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-2.5 transition-all text-xs">
      {/* Strength Bar */}
      <div>
        <div className="flex items-center justify-between text-xs font-semibold mb-1">
          <span className="text-slate-600 dark:text-slate-300">Password Strength:</span>
          <span className={`${strength.text} font-bold`}>{strength.label}</span>
        </div>
        <div className="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div className={`h-full ${strength.color} ${strength.width} transition-all duration-300 rounded-full`} />
        </div>
      </div>

      {/* Warnings */}
      {containsEmail && (
        <div className="text-[11px] text-rose-500 font-medium">
          Password should not contain your email address.
        </div>
      )}
      {containsName && (
        <div className="text-[11px] text-rose-500 font-medium">
          Password should not contain your name.
        </div>
      )}

      {/* Checklist */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
        {requirements.map((req, idx) => (
          <div key={idx} className="flex items-center gap-1.5 text-[11px]">
            {req.met ? (
              <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            ) : (
              <X className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500 shrink-0" />
            )}
            <span className={req.met ? 'text-slate-700 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500'}>
              {req.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

