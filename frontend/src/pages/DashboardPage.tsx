import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FolderKanban, 
  Search, 
  PenTool, 
  Newspaper, 
  ArrowUpRight, 
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  Activity,
  Plus,
  ExternalLink,
  ChevronRight,
  Layers,
  BarChart3,
  AlertTriangle,
  FileCheck,
  Lock,
  UserCheck
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { projectService } from '../services/projectService';
import { editorialService } from '../services/editorialService';
import { DashboardStats, EditorialDashboardStats } from '../types';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { LoadingState } from '../components/common/LoadingState';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [workflowStats, setWorkflowStats] = useState<EditorialDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const [data, wfData] = await Promise.all([
        projectService.getStats(),
        editorialService.getDashboardStats().catch(() => null)
      ]);
      setStats(data);
      if (wfData) setWorkflowStats(wfData);
    } catch (err) {
      console.error('Failed to load dashboard stats', err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = [
    { name: 'Projects', count: stats?.total_projects || 0 },
    { name: 'Sources', count: stats?.total_sources || 0 },
    { name: 'Drafts', count: stats?.total_drafts || 0 },
    { name: 'Editorials', count: stats?.total_editorial || 0 },
  ];

  const hasAnyData = (stats?.total_projects || 0) > 0 || (stats?.total_sources || 0) > 0;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header Bar matching Reference UI */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">Dashboard</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time overview of active investigations, source attributions, and newsletter editions.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <Button
            onClick={() => navigate('/research')}
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Research
          </Button>
          <Button
            onClick={() => navigate('/writing')}
            variant="outline"
            size="sm"
            leftIcon={<PenTool className="w-3.5 h-3.5" />}
          >
            Audit Draft
          </Button>
          <Button
            onClick={() => navigate('/editorial')}
            variant="outline"
            size="sm"
            leftIcon={<Newspaper className="w-3.5 h-3.5" />}
          >
            Editorial Studio
          </Button>
        </div>
      </div>

      {loading ? (
        <LoadingState message="Loading workspace metrics from SQLite..." />
      ) : !hasAnyData ? (
        <EmptyState
          icon={<FolderKanban className="w-6 h-6 text-blue-600" />}
          title="Welcome to your AI Editorial Workspace"
          description="You haven't initialized any research projects yet. Start by ingesting 3 or more industry articles to verify claims and synthesize evidence."
          actionLabel="Initialize First Project"
          onAction={() => navigate('/research')}
        />
      ) : (
        <>
          {/* 4 Metric Cards Grid - Real Backend Data */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Total Research Projects */}
            <div 
              onClick={() => navigate('/projects')}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <FolderKanban className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                  <TrendingUp className="w-3 h-3" />
                  Active
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Projects</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats?.total_projects ?? 0}
                </div>
              </div>
            </div>

            {/* Card 2: Sources Verified */}
            <div 
              onClick={() => navigate('/research')}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <Search className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                  <ShieldCheck className="w-3 h-3" />
                  Verified
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Sources Ingested</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats?.total_sources ?? 0}
                </div>
              </div>
            </div>

            {/* Card 3: Drafts Analyzed */}
            <div 
              onClick={() => navigate('/writing')}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-full bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <PenTool className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                  6 Checks
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Drafts Analyzed</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats?.total_drafts ?? 0}
                </div>
              </div>
            </div>

            {/* Card 4: Published Editions */}
            <div 
              onClick={() => navigate('/editorial')}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  <Newspaper className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-semibold text-purple-600 dark:text-purple-400 flex items-center gap-0.5">
                  Export Ready
                </span>
              </div>
              <div className="mt-4">
                <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Editorial Outputs</div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats?.total_editorial ?? 0}
                </div>
              </div>
            </div>
          </div>

          {/* Phase 23: Human-in-the-Loop Editorial Lifecycle Workflow Metrics */}
          <div className="bg-slate-50/70 dark:bg-slate-900/50 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Editorial Lifecycle & Review Status
                </h2>
              </div>
              <button
                onClick={() => navigate('/editorial')}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline font-medium flex items-center gap-1"
              >
                Go to Review Studio <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div 
                onClick={() => navigate('/editorial')}
                className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-amber-200/70 dark:border-amber-900/50 cursor-pointer hover:shadow-xs transition-all"
              >
                <div className="flex items-center justify-between text-amber-600 dark:text-amber-400">
                  <span className="text-[11px] font-semibold">Pending Review</span>
                  <Clock className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {workflowStats?.pending_human_reviews ?? 0}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Awaiting human sign-off</div>
              </div>

              <div 
                onClick={() => navigate('/editorial')}
                className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-rose-200/70 dark:border-rose-900/50 cursor-pointer hover:shadow-xs transition-all"
              >
                <div className="flex items-center justify-between text-rose-600 dark:text-rose-400">
                  <span className="text-[11px] font-semibold">Changes Needed</span>
                  <AlertTriangle className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {workflowStats?.changes_requested ?? 0}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Revisions in progress</div>
              </div>

              <div 
                onClick={() => navigate('/editorial')}
                className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-emerald-200/70 dark:border-emerald-900/50 cursor-pointer hover:shadow-xs transition-all"
              >
                <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400">
                  <span className="text-[11px] font-semibold">Approved</span>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {workflowStats?.approved_editorials ?? 0}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Ready for finalization</div>
              </div>

              <div 
                onClick={() => navigate('/editorial')}
                className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-blue-200/70 dark:border-blue-900/50 cursor-pointer hover:shadow-xs transition-all"
              >
                <div className="flex items-center justify-between text-blue-600 dark:text-blue-400">
                  <span className="text-[11px] font-semibold">Finalized & Locked</span>
                  <Lock className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {workflowStats?.finalized_editorials ?? 0}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Immutable publication</div>
              </div>
            </div>
          </div>

          {/* Main Content Grid: Recent Activity (Left) + Recharts Analytics & Quick Stats (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Recent Projects & Sources (2 Cols) */}
            <div className="lg:col-span-2 space-y-6">
              {/* Recent Research Projects Card */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">Recent Research Projects</h2>
                  <button 
                    onClick={() => navigate('/projects')}
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                  >
                    View all <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {!stats?.recent_projects || stats.recent_projects.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">No active research projects logged.</div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800/80 mt-1">
                    {stats.recent_projects.map((proj) => (
                      <div 
                        key={proj.id}
                        onClick={() => navigate(`/research/${proj.id}`)}
                        className="py-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 px-2 rounded-xl cursor-pointer transition-colors"
                      >
                        <div className="space-y-0.5 truncate pr-3">
                          <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">{proj.title}</div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-2">
                            <span>{proj.sources_count} sources</span>
                            <span>•</span>
                            <span className={proj.has_brief ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-amber-600'}>
                              {proj.has_brief ? 'Brief Synthesized' : 'Needs Ingestion'}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 font-mono text-slate-600 dark:text-slate-300">
                          {proj.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Ingested Source Feed Card */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">Recent Ingested Sources</h2>
                  <button 
                    onClick={() => navigate('/research')}
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                  >
                    Open Research <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {!stats?.recent_sources || stats.recent_sources.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">No sources ingested yet.</div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800/80 mt-1">
                    {stats.recent_sources.map((s) => (
                      <div key={s.id} className="py-3 flex items-center justify-between gap-3 px-2">
                        <div className="truncate">
                          <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">{s.title}</div>
                          {s.url && (
                            <a href={s.url} target="_blank" rel="noreferrer" className="text-[11px] text-blue-500 hover:underline truncate block">
                              {s.url}
                            </a>
                          )}
                        </div>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300">
                          {s.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Phase 23: Editorial Review Activity Log */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <h2 className="text-sm font-bold text-slate-900 dark:text-white">Recent Editorial Review Activity</h2>
                  </div>
                  <button 
                    onClick={() => navigate('/editorial')}
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                  >
                    Editorial Studio <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                {!workflowStats?.recent_activity || workflowStats.recent_activity.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">
                    No editorial reviews recorded yet. Submit an editorial draft to initiate human verification.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800/80 mt-1">
                    {workflowStats.recent_activity.map((act) => (
                      <div key={act.review_id} className="py-3 flex items-start justify-between gap-3 px-2">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                              {act.reviewer_name}
                            </span>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                              act.review_status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300' :
                              act.review_status === 'CHANGES_REQUESTED' ? 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/50 dark:text-rose-300' :
                              'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/50 dark:text-amber-300'
                            }`}>
                              {act.review_status}
                            </span>
                          </div>
                          {act.overall_feedback && (
                            <p className="text-[11px] text-slate-500 dark:text-slate-400 italic line-clamp-1">
                              "{act.overall_feedback}"
                            </p>
                          )}
                        </div>
                        {act.created_at && (
                          <span className="text-[10px] text-slate-400 whitespace-nowrap">
                            {new Date(act.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Recharts Analytics & Quality Card (1 Col) */}
            <div className="space-y-6">
              {/* Recharts Analytics Card */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-2">
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white">Workspace Volume</h2>
                  <BarChart3 className="w-4 h-4 text-slate-400" />
                </div>
                
                <div className="h-44 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.15} />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <YAxis allowDecimals={false} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#0f172a', 
                          border: 'none', 
                          borderRadius: '8px', 
                          fontSize: '11px',
                          color: '#fff' 
                        }} 
                      />
                      <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Editorial Quality & Health Card */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">System Integrity</h2>
                
                <div className="space-y-3 pt-1 text-xs">
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                    <span className="text-slate-700 dark:text-slate-300">Dual-Engine Mode</span>
                    <span className="font-semibold text-emerald-600">Deterministic Fallback Active</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                    <span className="text-slate-700 dark:text-slate-300">SSRF Defense</span>
                    <span className="font-semibold text-emerald-600">Private IP Filter Enforced</span>
                  </div>
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800">
                    <span className="text-slate-700 dark:text-slate-300">Database Engine</span>
                    <span className="font-semibold text-slate-900 dark:text-white">SQLite 3.x (Connected)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
