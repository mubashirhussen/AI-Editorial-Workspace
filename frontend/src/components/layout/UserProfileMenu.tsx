import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  User as UserIcon, 
  Settings, 
  Building, 
  LogOut, 
  Shield, 
  ChevronDown,
  Sparkles,
  KeyRound,
  ShieldCheck,
  HelpCircle,
  LogIn,
  UserPlus,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../common/Toast';

export const UserProfileMenu: React.FC = () => {
  const { user, role, activeOrg, logout, isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { success } = useToast();

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // If user is logged out, render Login and Sign Up buttons
  if (!isAuthenticated && !user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          to="/login"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          <LogIn className="w-3.5 h-3.5 text-slate-400" />
          <span>Login</span>
        </Link>
        <Link
          to="/register"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-xs"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>Sign Up</span>
        </Link>
      </div>
    );
  }

  const getInitials = (name?: string, email?: string): string => {
    if (name && name.trim()) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return parts[0].substring(0, 2).toUpperCase();
    }
    if (email) {
      return email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  const displayName = user?.full_name || 'User';
  const displayEmail = user?.email || '';
  const userRole = user?.role || role || 'USER';
  const initials = getInitials(user?.full_name, user?.email);

  const handleLogout = async () => {
    try {
      await logout();
      success('Logged out successfully');
      setIsOpen(false);
      navigate('/login');
    } catch (err) {
      console.error('Logout error', err);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Profile Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 pl-1.5 pr-2.5 py-1 rounded-xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/70 transition-all text-left shadow-2xs group focus:outline-none focus:ring-2 focus:ring-blue-500/20"
        aria-label="User Profile Menu"
        aria-expanded={isOpen}
      >
        {/* Avatar with Status Pulse */}
        <div className="relative shrink-0">
          {user?.profile_image ? (
            <img
              src={user.profile_image}
              alt={displayName}
              className="w-7 h-7 rounded-lg object-cover shadow-xs border border-slate-200 dark:border-slate-700"
            />
          ) : (
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 text-white font-bold text-xs flex items-center justify-center shadow-xs">
              {initials}
            </div>
          )}
          <span 
            className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" 
            title="Online & Verified"
          />
        </div>

        {/* User Details */}
        <div className="hidden sm:flex flex-col truncate max-w-[110px] md:max-w-[140px]">
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {displayName}
          </span>
          <span className="text-[10px] text-slate-400 dark:text-slate-500 truncate leading-tight font-mono">
            {userRole}
          </span>
        </div>

        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-blue-600' : ''}`} />
      </button>

      {/* Profile Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl z-50 p-2.5 animate-in fade-in zoom-in-95 duration-150">
          {/* Header Card */}
          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 mb-2">
            <div className="flex items-center gap-3">
              {user?.profile_image ? (
                <img
                  src={user.profile_image}
                  alt={displayName}
                  className="w-10 h-10 rounded-xl object-cover shadow-md border border-slate-200 dark:border-slate-700"
                />
              ) : (
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white font-bold text-sm flex items-center justify-center shadow-md">
                  {initials}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                    {displayName}
                  </span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold border ${
                    userRole === 'ADMIN'
                      ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
                      : 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
                  }`}>
                    {userRole}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                  {displayEmail}
                </div>
                <div className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 mt-1 font-medium">
                  <CheckCircle2 className="w-3 h-3" />
                  {activeOrg?.name || 'Personal Workspace'}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Items Matching Master Prompt */}
          <div className="space-y-0.5 text-xs">
            {/* 1. My Profile */}
            <button
              onClick={() => {
                navigate('/profile');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
            >
              <UserIcon className="w-4 h-4 text-blue-500" />
              <span>My Profile</span>
            </button>

            {/* 2. Account Settings */}
            <button
              onClick={() => {
                navigate('/settings');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
            >
              <Settings className="w-4 h-4 text-slate-400" />
              <span>Account Settings</span>
            </button>

            {/* 3. Change Password */}
            <button
              onClick={() => {
                navigate('/profile?tab=password');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
            >
              <KeyRound className="w-4 h-4 text-amber-500" />
              <span>Change Password</span>
            </button>

            {/* 4. Security & Sessions */}
            <button
              onClick={() => {
                navigate('/profile?tab=sessions');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
            >
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span>Security & Sessions</span>
            </button>

            {/* 5. Help / Support */}
            <button
              onClick={() => {
                navigate('/settings?tab=help');
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
            >
              <HelpCircle className="w-4 h-4 text-indigo-500" />
              <span>Help & Support</span>
            </button>
          </div>

          <div className="my-1.5 border-t border-slate-100 dark:border-slate-800" />

          {/* 6. Logout */}
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors text-xs text-left font-medium"
          >
            <LogOut className="w-4 h-4 text-rose-500" />
            <span>Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
};
