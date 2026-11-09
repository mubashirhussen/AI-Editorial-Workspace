import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  User as UserIcon, 
  Mail, 
  Shield, 
  KeyRound, 
  Calendar, 
  CheckCircle2, 
  AlertCircle, 
  ShieldCheck, 
  Smartphone, 
  Laptop, 
  Trash2, 
  Users, 
  Edit3, 
  Save, 
  X,
  Lock,
  Eye,
  EyeOff,
  RefreshCw,
  Search
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import { useToast } from '../components/common/Toast';
import { Button } from '../components/common/Button';
import { PasswordStrengthMeter } from '../components/auth/PasswordStrengthMeter';
import { UserSession, User as UserType } from '../types/auth';

export const ProfilePage: React.FC = () => {
  const { user, isAdmin, updateProfile, refreshUserProfile } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overview';

  const { success, error: toastError } = useToast();

  // Profile Edit State
  const [isEditing, setIsEditing] = useState(false);
  const [editFullName, setEditFullName] = useState(user?.full_name || '');
  const [editProfileImage, setEditProfileImage] = useState(user?.profile_image || '');
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Change Password State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Sessions State
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Admin Management State
  const [adminUsers, setAdminUsers] = useState<UserType[]>([]);
  const [adminTotal, setAdminTotal] = useState(0);
  const [adminSearch, setAdminSearch] = useState('');
  const [isLoadingAdminUsers, setIsLoadingAdminUsers] = useState(false);

  useEffect(() => {
    if (user) {
      setEditFullName(user.full_name || '');
      setEditProfileImage(user.profile_image || '');
    }
  }, [user]);

  // Load sessions when switching to sessions tab
  useEffect(() => {
    if (activeTab === 'sessions') {
      loadSessions();
    }
    if (activeTab === 'admin' && isAdmin) {
      loadAdminUsers();
    }
  }, [activeTab, isAdmin]);

  const loadSessions = async () => {
    try {
      setIsLoadingSessions(true);
      const data = await authService.getUserSessions();
      setSessions(data);
    } catch (err: any) {
      toastError(err.message || 'Failed to load sessions.');
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await authService.revokeSession(sessionId);
      success('Session revoked successfully.');
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (err: any) {
      toastError(err.message || 'Failed to revoke session.');
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editFullName.trim() || editFullName.trim().length < 2) {
      toastError('Full name must be at least 2 characters long.');
      return;
    }
    try {
      setIsSavingProfile(true);
      await updateProfile({
        full_name: editFullName.trim(),
        profile_image: editProfileImage.trim() || undefined,
      });
      success('Profile updated successfully!');
      setIsEditing(false);
    } catch (err: any) {
      toastError(err.message || 'Failed to update profile.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);

    if (!currentPassword) {
      setPasswordError('Please enter your current password.');
      return;
    }
    if (newPassword.length < 12) {
      setPasswordError('New password must be at least 12 characters long.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }
    if (newPassword === currentPassword) {
      setPasswordError('New password cannot be the same as your current password.');
      return;
    }

    try {
      setIsChangingPassword(true);
      const res = await authService.changePassword(currentPassword, newPassword);
      success(res.message || 'Password changed successfully!');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err: any) {
      setPasswordError(err.message || 'Failed to change password.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const loadAdminUsers = async () => {
    try {
      setIsLoadingAdminUsers(true);
      const data = await authService.adminListUsers(0, 50, adminSearch || undefined);
      setAdminUsers(data.items || []);
      setAdminTotal(data.total || 0);
    } catch (err: any) {
      toastError(err.message || 'Failed to load users.');
    } finally {
      setIsLoadingAdminAdmin(false);
    }
  };

  const setIsLoadingAdminAdmin = (val: boolean) => setIsLoadingAdminUsers(val);

  const handleAdminToggleStatus = async (targetUser: UserType) => {
    if (targetUser.id === user?.id) {
      toastError('Administrators cannot deactivate their own active account.');
      return;
    }
    try {
      const updated = await authService.adminUpdateUserStatus(targetUser.id, !targetUser.is_active);
      setAdminUsers((prev) => prev.map((u) => (u.id === targetUser.id ? { ...u, is_active: updated.is_active } : u)));
      success(`User ${updated.full_name} is now ${updated.is_active ? 'Active' : 'Deactivated'}.`);
    } catch (err: any) {
      toastError(err.message || 'Failed to update user status.');
    }
  };

  const handleAdminChangeRole = async (targetUser: UserType, newRole: string) => {
    try {
      const updated = await authService.adminUpdateUserRole(targetUser.id, newRole);
      setAdminUsers((prev) => prev.map((u) => (u.id === targetUser.id ? { ...u, role: updated.role } : u)));
      success(`User ${updated.full_name} role updated to ${updated.role}.`);
    } catch (err: any) {
      toastError(err.message || 'Failed to update user role.');
    }
  };

  const getInitials = (name?: string, email?: string): string => {
    if (name && name.trim()) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
      return parts[0].substring(0, 2).toUpperCase();
    }
    return email ? email.substring(0, 2).toUpperCase() : 'U';
  };

  const initials = getInitials(user?.full_name, user?.email);
  const accountCreatedDate = user?.created_at ? new Date(user.created_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }) : 'Recently';

  const lastLoginDate = user?.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Current Session';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-200">
      {/* Top Header Card */}
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          {user?.profile_image ? (
            <img
              src={user.profile_image}
              alt={user.full_name}
              className="w-20 h-20 rounded-2xl object-cover border-2 border-white dark:border-slate-800 shadow-md"
            />
          ) : (
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white font-extrabold text-2xl flex items-center justify-center shadow-md">
              {initials}
            </div>
          )}
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
                {user?.full_name || 'User Profile'}
              </h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                user?.role === 'ADMIN'
                  ? 'bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800'
                  : 'bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800'
              }`}>
                {user?.role || 'USER'}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
              <Mail className="w-3.5 h-3.5" />
              <span>{user?.email}</span>
            </p>
            <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400 dark:text-slate-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Joined {accountCreatedDate}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                <CheckCircle2 className="w-3 h-3" />
                {user?.is_active ? 'Active Account' : 'Deactivated'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        {!isEditing && activeTab === 'overview' && (
          <Button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 py-2 px-4 rounded-xl text-xs font-semibold"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit Profile</span>
          </Button>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold overflow-x-auto pb-1">
        <button
          onClick={() => setSearchParams({ tab: 'overview' })}
          className={`px-4 py-2.5 rounded-xl transition-colors flex items-center gap-2 ${
            activeTab === 'overview'
              ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold border border-blue-200 dark:border-blue-800'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <UserIcon className="w-4 h-4" />
          <span>My Profile</span>
        </button>

        <button
          onClick={() => setSearchParams({ tab: 'password' })}
          className={`px-4 py-2.5 rounded-xl transition-colors flex items-center gap-2 ${
            activeTab === 'password'
              ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold border border-blue-200 dark:border-blue-800'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <KeyRound className="w-4 h-4" />
          <span>Change Password</span>
        </button>

        <button
          onClick={() => setSearchParams({ tab: 'sessions' })}
          className={`px-4 py-2.5 rounded-xl transition-colors flex items-center gap-2 ${
            activeTab === 'sessions'
              ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold border border-blue-200 dark:border-blue-800'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Security & Sessions</span>
        </button>

        {isAdmin && (
          <button
            onClick={() => setSearchParams({ tab: 'admin' })}
            className={`px-4 py-2.5 rounded-xl transition-colors flex items-center gap-2 ${
              activeTab === 'admin'
                ? 'bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 font-bold border border-purple-200 dark:border-purple-800'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Admin Users ({adminTotal || '•'})</span>
          </button>
        )}
      </div>

      {/* TAB 1: OVERVIEW & EDIT PROFILE */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <UserIcon className="w-4 h-4 text-blue-600" />
              <span>Personal Details</span>
            </h2>

            {isEditing ? (
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Full Name <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={editFullName}
                    onChange={(e) => setEditFullName(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Profile Image URL
                  </label>
                  <input
                    type="url"
                    value={editProfileImage}
                    onChange={(e) => setEditProfileImage(e.target.value)}
                    placeholder="https://example.com/avatar.jpg"
                    className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button
                    type="submit"
                    disabled={isSavingProfile}
                    className="flex items-center gap-2 py-2 px-4 rounded-xl text-xs font-bold"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{isSavingProfile ? 'Saving...' : 'Save Changes'}</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setIsEditing(false);
                      setEditFullName(user?.full_name || '');
                    }}
                    className="py-2 px-4 rounded-xl text-xs"
                  >
                    <X className="w-3.5 h-3.5 mr-1" />
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block text-[10px] font-semibold uppercase">Full Name</span>
                  <span className="font-semibold text-slate-900 dark:text-white mt-1 block">
                    {user?.full_name}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block text-[10px] font-semibold uppercase">Email Address (Read-Only)</span>
                  <span className="font-semibold text-slate-900 dark:text-white mt-1 block font-mono">
                    {user?.email}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block text-[10px] font-semibold uppercase">Assigned System Role</span>
                  <span className="font-semibold text-slate-900 dark:text-white mt-1 block">
                    {user?.role || 'USER'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-slate-400 block text-[10px] font-semibold uppercase">Last Active Login</span>
                  <span className="font-semibold text-slate-900 dark:text-white mt-1 block">
                    {lastLoginDate}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Security Badge Card */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span>Account Security</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                <span className="text-slate-600 dark:text-slate-300">Password Hashing</span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">Argon2id</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                <span className="text-slate-600 dark:text-slate-300">Email Verification</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold">Verified</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                <span className="text-slate-600 dark:text-slate-300">Session Security</span>
                <span className="text-blue-600 dark:text-blue-400 font-bold">Encrypted JWT</span>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={() => setSearchParams({ tab: 'password' })}
              className="w-full py-2 text-xs font-semibold rounded-xl"
            >
              Update Password
            </Button>
          </div>
        </div>
      )}

      {/* TAB 2: CHANGE PASSWORD */}
      {activeTab === 'password' && (
        <div className="max-w-xl mx-auto bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-amber-500" />
              <span>Change Password</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Your new password must be at least 12 characters and contain uppercase, lowercase, numbers, and symbols.
            </p>
          </div>

          {passwordError && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 flex items-start gap-2.5 text-rose-700 dark:text-rose-300 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{passwordError}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Current Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showCurrentPassword ? 'text' : 'password'}
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                New Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <PasswordStrengthMeter password={newPassword} email={user?.email} fullName={user?.full_name} />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Confirm New Password <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  required
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
              {confirmNewPassword && newPassword !== confirmNewPassword && (
                <p className="text-[11px] text-rose-500 font-medium mt-1">Passwords do not match.</p>
              )}
            </div>

            <Button
              type="submit"
              disabled={isChangingPassword}
              className="w-full py-2.5 text-xs font-bold rounded-xl mt-4"
            >
              {isChangingPassword ? 'Updating Password...' : 'Save New Password'}
            </Button>
          </form>
        </div>
      )}

      {/* TAB 3: SECURITY & SESSIONS */}
      {activeTab === 'sessions' && (
        <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Active Login Sessions</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Manage all active browser sessions authenticated to your account.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={loadSessions}
              className="py-1.5 px-3 text-xs rounded-xl flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </Button>
          </div>

          {isLoadingSessions ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading active sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">No active sessions found.</div>
          ) : (
            <div className="space-y-3">
              {sessions.map((sess) => (
                <div
                  key={sess.id}
                  className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex items-center justify-between gap-4 text-xs"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="p-2.5 rounded-xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400">
                      <Laptop className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 dark:text-white">
                          {sess.ip_address || '127.0.0.1'}
                        </span>
                        {sess.is_current && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                            Current Device
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-md mt-0.5 font-mono">
                        {sess.user_agent || 'Web Browser'}
                      </p>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                        Created {new Date(sess.created_at).toLocaleString()} • Expires {new Date(sess.expires_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {!sess.is_current && (
                    <button
                      onClick={() => handleRevokeSession(sess.id)}
                      className="p-2 rounded-xl text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                      title="Revoke session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: ADMIN USER MANAGEMENT (Admin only) */}
      {activeTab === 'admin' && isAdmin && (
        <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-600" />
                <span>User Administration ({adminTotal} Total)</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Manage account activation states and assign system administrative roles.
              </p>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-64">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={adminSearch}
                  onChange={(e) => setAdminSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadAdminUsers()}
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>
              <Button onClick={loadAdminUsers} className="py-1.5 px-3 text-xs rounded-xl">
                Search
              </Button>
            </div>
          </div>

          {isLoadingAdminUsers ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading user catalog...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                    <th className="py-3 px-4">User</th>
                    <th className="py-3 px-4">Role</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Joined Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {adminUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900 dark:text-white">{u.full_name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">{u.email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <select
                          value={u.role || 'USER'}
                          onChange={(e) => handleAdminChangeRole(u, e.target.value)}
                          disabled={u.id === user?.id}
                          className="px-2 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-semibold"
                        >
                          <option value="USER">USER</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          u.is_active
                            ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                            : 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300'
                        }`}>
                          {u.is_active ? 'Active' : 'Deactivated'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 font-mono">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleAdminToggleStatus(u)}
                          disabled={u.id === user?.id}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                            u.is_active
                              ? 'text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40'
                              : 'text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40'
                          } ${u.id === user?.id ? 'opacity-40 cursor-not-allowed' : ''}`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
