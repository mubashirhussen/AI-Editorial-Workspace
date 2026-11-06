import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Sparkles, 
  Mail, 
  Lock, 
  User, 
  Building2, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  ShieldCheck,
  Feather,
  KeyRound,
  ArrowLeft
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/common/Toast';
import { Button } from '../components/common/Button';

type AuthMode = 'login' | 'register' | 'forgot' | 'reset';

export const AuthPage: React.FC = () => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const { login, register, forgotPassword, resetPassword } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { success, error: toastError } = useToast();

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const validateEmail = (val: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setStatusMessage(null);

    if (!email.trim() || !validateEmail(email.trim())) {
      setFormError('Please enter a valid email address.');
      return;
    }

    if (mode === 'login') {
      if (!password.trim()) {
        setFormError('Please enter your password.');
        return;
      }
      try {
        setIsLoading(true);
        await login({ email: email.trim(), password });
        success('Signed in successfully!');
        navigate(from, { replace: true });
      } catch (err: any) {
        setFormError(err.message || 'Authentication failed. Please verify credentials.');
      } finally {
        setIsLoading(false);
      }
      return;
    }

    if (mode === 'register') {
      if (!fullName.trim()) {
        setFormError('Please enter your full name.');
        return;
      }
      if (password.length < 8) {
        setFormError('Password must be at least 8 characters long.');
        return;
      }
      try {
        setIsLoading(true);
        await register({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          organization_name: orgName.trim() || undefined,
        });
        success('Account and organization created successfully!');
        navigate(from, { replace: true });
      } catch (err: any) {
        setFormError(err.message || 'Registration failed. Email may already be in use.');
      } finally {
        setIsLoading(false);
      }
      return;
    }

    if (mode === 'forgot') {
      try {
        setIsLoading(true);
        const res = await forgotPassword(email.trim());
        setStatusMessage(res.message);
        if (res.dev_reset_token) {
          setResetToken(res.dev_reset_token);
        }
        setMode('reset');
        success('Password reset instructions dispatched.');
      } catch (err: any) {
        setFormError(err.message || 'Unable to process password reset request.');
      } finally {
        setIsLoading(false);
      }
      return;
    }

    if (mode === 'reset') {
      if (!resetToken.trim()) {
        setFormError('Please enter the reset token.');
        return;
      }
      if (newPassword.length < 8) {
        setFormError('New password must be at least 8 characters long.');
        return;
      }
      try {
        setIsLoading(true);
        const res = await resetPassword(resetToken.trim(), newPassword);
        success(res.message || 'Password reset successfully!');
        setMode('login');
        setPassword('');
        setStatusMessage('Your password has been reset. Please sign in with your new password.');
      } catch (err: any) {
        setFormError(err.message || 'Invalid or expired reset token.');
      } finally {
        setIsLoading(false);
      }
      return;
    }
  };

  const getTitle = () => {
    switch (mode) {
      case 'register':
        return 'Create your Workspace';
      case 'forgot':
        return 'Reset your Password';
      case 'reset':
        return 'Set New Password';
      default:
        return 'Sign in to Editorial AI';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 transition-colors">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        {/* Workspace Brand Badge */}
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 shadow-lg shadow-blue-500/20 text-white mb-4">
          <Feather className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
          {getTitle()}
        </h2>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
          Professional AI-Powered Editorial Workspace with Source Traceability
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white dark:bg-slate-900 py-8 px-6 sm:px-10 shadow-xl border border-slate-200/80 dark:border-slate-800 rounded-3xl">
          {statusMessage && (
            <div className="mb-5 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 flex items-start gap-2.5 text-xs text-emerald-800 dark:text-emerald-300">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
              <span>{statusMessage}</span>
            </div>
          )}

          {formError && (
            <div className="mb-5 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 flex items-start gap-2.5 text-xs text-rose-700 dark:text-rose-300 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Organization / Publication Name (Optional)
                  </label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="This Week in AI"
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </>
            )}

            {mode !== 'reset' && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="editor@editorial.ai"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            )}

            {(mode === 'login' || mode === 'register') && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Password
                  </label>
                  {mode === 'login' && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode('forgot');
                        setFormError(null);
                        setStatusMessage(null);
                      }}
                      className="text-[11px] text-blue-600 dark:text-blue-400 hover:underline font-medium"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>
              </div>
            )}

            {mode === 'reset' && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Reset Token
                  </label>
                  <div className="relative">
                    <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={resetToken}
                      onChange={(e) => setResetToken(e.target.value)}
                      placeholder="Paste your 32-character reset token"
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="password"
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                    />
                  </div>
                </div>
              </>
            )}

            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full mt-2"
              isLoading={isLoading}
            >
              <span>
                {mode === 'register'
                  ? 'Create Account & Organization'
                  : mode === 'forgot'
                  ? 'Send Reset Token'
                  : mode === 'reset'
                  ? 'Reset Password & Sign In'
                  : 'Sign In to Workspace'}
              </span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
          </form>

          {/* Switch Mode Toggles */}
          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 text-center space-y-2">
            {mode === 'forgot' || mode === 'reset' ? (
              <button
                onClick={() => {
                  setMode('login');
                  setFormError(null);
                  setStatusMessage(null);
                }}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-semibold flex items-center justify-center gap-1 mx-auto"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Sign In</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  setMode(mode === 'login' ? 'register' : 'login');
                  setFormError(null);
                  setStatusMessage(null);
                }}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline font-semibold"
              >
                {mode === 'register'
                  ? 'Already have an account? Sign in here'
                  : "Don't have an account? Create a new workspace"}
              </button>
            )}
          </div>
        </div>

        {/* Security Assurance Banner */}
        <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-slate-500 dark:text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Argon2id Encrypted • Multi-Tenant RBAC Isolation</span>
        </div>
      </div>
    </div>
  );
};
