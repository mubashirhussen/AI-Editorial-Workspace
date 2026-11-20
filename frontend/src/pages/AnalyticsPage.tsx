import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Users, 
  Layers, 
  FolderKanban, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Clock, 
  MessageSquare, 
  ShieldCheck, 
  RefreshCw, 
  ArrowRight,
  TrendingUp,
  Activity,
  Sliders,
  Filter
} from 'lucide-react';
import { 
  analyticsService, 
  AnalyticsOverview, 
  WorkflowMetric, 
  FunnelsResponse, 
  FeatureMetric, 
  TrendDataPoint,
  AnalyticsHealth,
  AnalyticsPrivacyPreference 
} from '../services/analyticsService';

export const AnalyticsPage: React.FC = () => {
  const [days, setDays] = useState<number>(30);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowMetric[]>([]);
  const [funnels, setFunnels] = useState<FunnelsResponse | null>(null);
  const [features, setFeatures] = useState<FeatureMetric[]>([]);
  const [trends, setTrends] = useState<TrendDataPoint[]>([]);
  const [health, setHealth] = useState<AnalyticsHealth | null>(null);
  const [privacyPref, setPrivacyPref] = useState<AnalyticsPrivacyPreference | null>(null);
  const [activeFunnelTab, setActiveFunnelTab] = useState<'research' | 'writing' | 'editorial'>('research');

  const fetchAnalyticsData = async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      const [ovData, wfData, fnData, ftData, trData, hlData, prData] = await Promise.all([
        analyticsService.getOverview(days),
        analyticsService.getWorkflows(days),
        analyticsService.getFunnels(days),
        analyticsService.getFeatures(days),
        analyticsService.getTrends(days <= 7 ? 7 : 14),
        analyticsService.getHealth(),
        analyticsService.getPrivacyPreference().catch(() => null),
      ]);

      setOverview(ovData);
      setWorkflows(wfData.workflows || []);
      setFunnels(fnData);
      setFeatures(ftData.features || []);
      setTrends(trData.data_points || []);
      setHealth(hlData);
      if (prData) setPrivacyPref(prData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load product analytics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [days]);

  const handleToggleOptOut = async () => {
    if (!privacyPref) return;
    try {
      const updated = await analyticsService.updatePrivacyPreference({
        analytics_opt_out: !privacyPref.analytics_opt_out,
        do_not_track: privacyPref.do_not_track
      });
      setPrivacyPref(updated);
    } catch (err: any) {
      alert('Could not update privacy preference: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[70vh] flex-col items-center justify-center gap-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-sm font-medium text-slate-400">Aggregating privacy-conscious product intelligence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
            <h3 className="font-bold text-lg text-rose-200">Unable to load Analytics</h3>
          </div>
          <p className="text-sm text-rose-300/80">{error}</p>
          <div>
            <button
              onClick={() => fetchAnalyticsData()}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl transition-all"
            >
              Retry Loading
            </button>
          </div>
        </div>
      </div>
    );
  }

  const currentFunnel = activeFunnelTab === 'research' 
    ? funnels?.research_funnel 
    : activeFunnelTab === 'writing' 
      ? funnels?.writing_funnel 
      : funnels?.editorial_funnel;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-600/10 text-blue-400 border border-blue-500/20">
              <BarChart3 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Product Analytics & Journeys</h1>
              <p className="text-xs text-slate-400">Evidence-based feature adoption, user funnels, and workflow completion intelligence</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs font-medium text-slate-300">
            <button
              onClick={() => setDays(7)}
              className={`px-3 py-1.5 rounded-lg transition-all ${days === 7 ? 'bg-blue-600 text-white shadow-xs' : 'hover:text-white'}`}
            >
              7 Days
            </button>
            <button
              onClick={() => setDays(30)}
              className={`px-3 py-1.5 rounded-lg transition-all ${days === 30 ? 'bg-blue-600 text-white shadow-xs' : 'hover:text-white'}`}
            >
              30 Days
            </button>
            <button
              onClick={() => setDays(90)}
              className={`px-3 py-1.5 rounded-lg transition-all ${days === 90 ? 'bg-blue-600 text-white shadow-xs' : 'hover:text-white'}`}
            >
              90 Days
            </button>
          </div>

          <button
            onClick={() => fetchAnalyticsData(true)}
            disabled={refreshing}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-all disabled:opacity-50"
            title="Refresh analytics data"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Privacy Notice Banner */}
      <div className="px-4 py-3 rounded-xl bg-blue-950/40 border border-blue-800/40 flex items-center justify-between text-xs text-blue-300">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            <strong>First-Party Privacy Shield Active:</strong> Analytics strictly strips raw documents, prompts, credentials, and PII. User IDs are non-reversibly pseudorandomized.
          </span>
        </div>
        {privacyPref && (
          <div className="flex items-center gap-2">
            <span className="text-slate-400 text-[11px]">Tracking Opt-Out:</span>
            <button
              onClick={handleToggleOptOut}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase transition-all ${
                privacyPref.analytics_opt_out 
                  ? 'bg-rose-600 text-white' 
                  : 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-600/50'
              }`}
            >
              {privacyPref.analytics_opt_out ? 'Opted Out' : 'Active (Opt Out)'}
            </button>
          </div>
        )}
      </div>

      {/* Section 1: Executive KPI Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Users */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Active Users (Pseudonymous)</span>
            <Users className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.active_users ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">unique hash</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">{overview?.active_sessions ?? 0} active sessions</p>
        </div>

        {/* Projects Created */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Projects Created</span>
            <FolderKanban className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.projects_created ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">investigations</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">{overview?.feature_usage_count ?? 0} total events logged</p>
        </div>

        {/* Workflow Completion Rate */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Workflow Completion</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.workflow_completion_rate ?? 0}%</span>
            <span className="text-[11px] text-slate-500 font-mono">rate</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">{overview?.completed_workflows ?? 0} completed workflows</p>
        </div>

        {/* AI Reliability */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">AI Reliability Rate</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.ai_success_rate ?? 100}%</span>
            <span className="text-[11px] text-slate-500 font-mono">success</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">{overview?.successful_ai_operations ?? 0} ops / {overview?.failed_ai_operations ?? 0} failed</p>
        </div>
      </div>

      {/* Section 2: Workflow Conversion Funnels */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              User Journey Conversion Funnels
            </h2>
            <p className="text-xs text-slate-400">Tracking user drop-off and conversion rates across the 3 core pipelines</p>
          </div>

          <div className="flex items-center bg-slate-800/80 p-1 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setActiveFunnelTab('research')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeFunnelTab === 'research' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Research Funnel
            </button>
            <button
              onClick={() => setActiveFunnelTab('writing')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeFunnelTab === 'writing' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Writing Funnel
            </button>
            <button
              onClick={() => setActiveFunnelTab('editorial')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeFunnelTab === 'editorial' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Editorial Funnel
            </button>
          </div>
        </div>

        {currentFunnel && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800/60">
              <span className="font-semibold text-slate-300">{currentFunnel.workflow_name}</span>
              <span>Overall End-to-End Conversion: <strong className="text-emerald-400 font-mono">{currentFunnel.overall_conversion_rate}%</strong></span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {currentFunnel.steps.map((step, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">Step {idx + 1}</span>
                      <span className="text-xs font-bold text-blue-400 font-mono">{step.conversion_rate}%</span>
                    </div>
                    <div className="mt-2 font-semibold text-sm text-white">{step.step_name}</div>
                    <div className="mt-1 text-2xl font-bold text-slate-200">{step.count}</div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-700/40 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Drop-off:</span>
                    <span className={step.drop_off_count > 0 ? "text-amber-400 font-mono" : "text-slate-500 font-mono"}>
                      -{step.drop_off_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Section 3: Feature Adoption & Reliability Matrix */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Feature Adoption & Operational Reliability
          </h2>
          <p className="text-xs text-slate-400">Module-level execution frequency, success rates, and average latency</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-700/60">
              <tr>
                <th className="py-3 px-4">Feature Module</th>
                <th className="py-3 px-4 text-center">Invocations</th>
                <th className="py-3 px-4 text-center">Successes</th>
                <th className="py-3 px-4 text-center">Failures</th>
                <th className="py-3 px-4 text-center">Success Rate</th>
                <th className="py-3 px-4 text-right">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {features.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500">
                    No feature telemetry recorded in the selected time range.
                  </td>
                </tr>
              ) : (
                features.map((feat, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-white flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                      {feat.feature_name}
                    </td>
                    <td className="py-3 px-4 text-center text-slate-300 font-mono">{feat.usage_count}</td>
                    <td className="py-3 px-4 text-center text-emerald-400 font-mono">{feat.success_count}</td>
                    <td className="py-3 px-4 text-center font-mono">
                      <span className={feat.failure_count > 0 ? "text-rose-400 font-bold" : "text-slate-500"}>
                        {feat.failure_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                        feat.success_rate >= 95 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {feat.success_rate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400 font-mono">
                      {feat.avg_duration_ms > 0 ? `${feat.avg_duration_ms}ms` : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 4: Daily Trends & Subsystem Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Activity Timeline */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Recent Usage Trends
          </h2>
          <div className="space-y-3">
            {trends.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No trend datapoints available.</p>
            ) : (
              trends.map((item, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/40 flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-300 font-medium">{item.date}</span>
                  <div className="flex items-center gap-4 text-slate-400">
                    <span>Projects: <strong className="text-white font-mono">{item.projects}</strong></span>
                    <span>Workflows: <strong className="text-emerald-400 font-mono">{item.workflows_completed}</strong></span>
                    <span>AI Ops: <strong className="text-amber-400 font-mono">{item.ai_operations}</strong></span>
                    <span>Events: <strong className="text-blue-400 font-mono">{item.events_count}</strong></span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Subsystem Health & Governance */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sliders className="w-5 h-5 text-emerald-400" />
              Subsystem Governance
            </h2>
            <p className="text-xs text-slate-400 mt-1">Telemetry telemetry lifecycle and privacy auditing</p>
          </div>

          <div className="space-y-3 py-2 text-xs">
            <div className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-slate-400">Subsystem Status:</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[11px] font-bold">
                {health?.status ?? 'HEALTHY'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-slate-400">Total Durable Events:</span>
              <span className="text-white font-mono font-bold">{health?.total_events ?? 0}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-slate-400">Events (Last 24h):</span>
              <span className="text-blue-400 font-mono font-bold">{health?.events_last_24h ?? 0}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-slate-400">Sanitized Sensitive Payloads:</span>
              <span className="text-amber-400 font-mono font-bold">{health?.privacy_filtered_count ?? 0}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-slate-800">
              <span className="text-slate-400">Deduplicated Actions:</span>
              <span className="text-indigo-400 font-mono font-bold">{health?.deduplicated_events_count ?? 0}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-400">Data Retention Horizon:</span>
              <span className="text-slate-300 font-mono">{health?.storage_retention_days ?? 90} days</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-[11px] text-slate-400">
            Analytics data is retained for 90 days before automated non-destructive rotation. Core business entities are never purged.
          </div>
        </div>
      </div>
    </div>
  );
};
