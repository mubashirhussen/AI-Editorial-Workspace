import React, { useEffect, useState } from 'react';
import { 
  Building2, 
  Users, 
  UserPlus, 
  ShieldCheck, 
  Trash2, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Copy,
  Plus,
  RefreshCw,
  Info
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';
import { Membership, Invitation, OrgRole } from '../types/auth';
import { Button } from '../components/common/Button';
import { LoadingState } from '../components/common/LoadingState';

export const OrganizationPage: React.FC = () => {
  const { activeOrg, role, canManageOrg, canInvite, refreshUserProfile } = useAuth();
  const [members, setMembers] = useState<Membership[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Invite modal state
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<OrgRole>('EDITOR');
  const [submittingInvite, setSubmittingInvite] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  useEffect(() => {
    if (activeOrg) {
      loadMembersAndInvitations();
    }
  }, [activeOrg]);

  const loadMembersAndInvitations = async () => {
    if (!activeOrg) return;
    try {
      setLoading(true);
      setError(null);
      const [membersData, invitationsData] = await Promise.all([
        authService.getMembers(activeOrg.id).catch(() => []),
        canInvite ? authService.getInvitations(activeOrg.id).catch(() => []) : Promise.resolve([])
      ]);
      setMembers(membersData);
      setInvitations(invitationsData);
    } catch (err: any) {
      setError(err?.message || 'Failed to load organization members.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: OrgRole) => {
    if (!activeOrg) return;
    try {
      await authService.updateMemberRole(activeOrg.id, userId, newRole);
      await loadMembersAndInvitations();
    } catch (err: any) {
      alert(err?.message || 'Failed to update member role.');
    }
  };

  const handleRemoveMember = async (userId: string, userName: string) => {
    if (!activeOrg) return;
    if (!window.confirm(`Are you sure you want to remove ${userName} from ${activeOrg.name}?`)) {
      return;
    }
    try {
      await authService.removeMember(activeOrg.id, userId);
      await loadMembersAndInvitations();
    } catch (err: any) {
      alert(err?.message || 'Failed to remove member.');
    }
  };

  const handleCreateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrg || !inviteEmail.trim()) return;
    try {
      setSubmittingInvite(true);
      await authService.createInvitation(activeOrg.id, {
        email: inviteEmail.trim(),
        role: inviteRole
      });
      setInviteEmail('');
      setShowInviteModal(false);
      await loadMembersAndInvitations();
    } catch (err: any) {
      alert(err?.message || 'Failed to send invitation.');
    } finally {
      setSubmittingInvite(false);
    }
  };

  const handleRevokeInvite = async (invitationId: string) => {
    if (!activeOrg) return;
    try {
      await authService.revokeInvitation(activeOrg.id, invitationId);
      await loadMembersAndInvitations();
    } catch (err: any) {
      alert(err?.message || 'Failed to revoke invitation.');
    }
  };

  const copyToClipboard = (token: string) => {
    const inviteLink = `${window.location.origin}/join/${token}`;
    navigator.clipboard.writeText(inviteLink);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  const getRoleBadgeStyle = (r: OrgRole) => {
    switch (r) {
      case 'OWNER':
        return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300';
      case 'ADMIN':
        return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300';
      case 'EDITOR':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300';
      case 'REVIEWER':
        return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300';
      case 'VIEWER':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-6">
      {/* Workspace Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
              {activeOrg?.name || 'Workspace Management'}
            </h1>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold border ${getRoleBadgeStyle(role as OrgRole)}`}>
              Your Role: {role || 'OWNER'}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage multi-tenant workspace members, role permissions, and access governance.
          </p>
        </div>

        {canInvite && (
          <Button
            onClick={() => setShowInviteModal(true)}
            variant="primary"
            size="sm"
            leftIcon={<UserPlus className="w-4 h-4" />}
          >
            Invite Member
          </Button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState message="Loading organization members and permissions..." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Members Table (Left 2 cols) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                    Workspace Members ({members.length})
                  </h2>
                </div>
                <button
                  onClick={loadMembersAndInvitations}
                  className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Refresh
                </button>
              </div>

              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {members.map((mem) => {
                  const isOwner = mem.role === 'OWNER';
                  return (
                    <div key={mem.id} className="p-4 flex items-center justify-between gap-4">
                      <div className="space-y-0.5 truncate">
                        <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                          {mem.user?.full_name || 'Team Member'}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate">
                          {mem.user?.email}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        {canManageOrg && !isOwner ? (
                          <select
                            value={mem.role}
                            onChange={(e) => handleRoleChange(mem.user_id, e.target.value as OrgRole)}
                            className="text-xs py-1 px-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                          >
                            <option value="ADMIN">ADMIN</option>
                            <option value="EDITOR">EDITOR</option>
                            <option value="REVIEWER">REVIEWER</option>
                            <option value="VIEWER">VIEWER</option>
                          </select>
                        ) : (
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-semibold border ${getRoleBadgeStyle(mem.role)}`}>
                            {mem.role}
                          </span>
                        )}

                        {canManageOrg && !isOwner && (
                          <button
                            onClick={() => handleRemoveMember(mem.user_id, mem.user?.full_name || 'User')}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                            title="Remove member"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Pending Invitations Section */}
            {canInvite && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs overflow-hidden">
                <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                      Pending Invitations ({invitations.length})
                    </h2>
                  </div>
                </div>

                {invitations.length === 0 ? (
                  <div className="p-8 text-center text-xs text-slate-400">
                    No pending invitations. Click "Invite Member" above to add team members.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {invitations.map((inv) => (
                      <div key={inv.id} className="p-4 flex items-center justify-between gap-4">
                        <div className="space-y-0.5">
                          <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                            {inv.email}
                          </div>
                          <div className="text-[10px] text-slate-400 flex items-center gap-2">
                            <span>Role: {inv.role}</span>
                            <span>•</span>
                            <span>Expires {new Date(inv.expires_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => copyToClipboard(inv.token)}
                            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/40"
                          >
                            {copiedToken === inv.token ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Copied Link
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" /> Copy Invite Link
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleRevokeInvite(inv.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 transition-colors"
                            title="Revoke invitation"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Role Permissions Matrix Card (Right 1 col) */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
              <div className="flex items-center gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Role Permission Matrix</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-2.5 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/60 dark:border-purple-900/40">
                  <span className="font-bold text-purple-700 dark:text-purple-300">OWNER</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                    Full workspace administration, role updates, member removal, and organization deletion.
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40">
                  <span className="font-bold text-blue-700 dark:text-blue-300">ADMIN</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                    Invite members, manage projects, edit drafts, and approve editorials. Cannot remove Owner.
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-900/40">
                  <span className="font-bold text-emerald-700 dark:text-emerald-300">EDITOR</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                    Create research projects, ingest sources, draft articles, and submit revisions. Cannot approve.
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40">
                  <span className="font-bold text-amber-700 dark:text-amber-300">REVIEWER</span>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                    Inspect drafts, execute AI pre-reviews, leave comments, and approve editorials.
                  </p>
                </div>

                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200/60 dark:border-slate-700">
                  <span className="font-bold text-slate-700 dark:text-slate-300">VIEWER</span>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Read-only access to projects, evidence briefs, and published editions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Invite New Team Member</h3>
              <button onClick={() => setShowInviteModal(false)} className="text-slate-400 hover:text-slate-600 text-xs">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateInvite} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Assigned Role
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as OrgRole)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                >
                  <option value="EDITOR">EDITOR (Create projects, add sources, edit drafts)</option>
                  <option value="REVIEWER">REVIEWER (Review drafts, leave comments, approve)</option>
                  <option value="ADMIN">ADMIN (Workspace management, invitations, approval)</option>
                  <option value="VIEWER">VIEWER (Read-only access)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowInviteModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={submittingInvite}
                >
                  {submittingInvite ? 'Sending...' : 'Generate Invitation'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

