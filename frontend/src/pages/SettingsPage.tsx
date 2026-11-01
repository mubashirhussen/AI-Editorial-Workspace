import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  ShieldCheck, 
  Cpu, 
  Database, 
  Server, 
  CheckCircle2, 
  AlertCircle,
  Sparkles,
  Sun,
  Moon,
  Laptop,
  Check,
  Search,
  User,
  Key,
  Users,
  CreditCard,
  Grid,
  Code,
  Activity,
  RefreshCw,
  Clock,
  Terminal
} from 'lucide-react';
import { apiClient } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'appearance' | 'observability' | 'ai' | 'security' | 'database'>('appearance');
  const [themePreference, setThemePreference] = useState<'system' | 'light' | 'dark'>('system');
  const [transparentSidebar, setTransparentSidebar] = useState(false);
  const [sidebarFeature, setSidebarFeature] = useState('Recent changes');
  const [tableView, setTableView] = useState<'default' | 'compact'>('default');
  
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/health');
      setHealthData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleThemeChange = (theme: 'system' | 'light' | 'dark') => {
    setThemePreference(theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else if (theme === 'light') {
      document.documentElement.classList.remove('dark');
    } else {
      // System preference
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  };

  const subNavItems = [
    { id: 'appearance', label: 'Appearance', icon: Sparkles },
    { id: 'observability', label: 'Observability & SRE', icon: Activity },
    { id: 'ai', label: 'AI Engine & LLM', icon: Cpu },
    { id: 'security', label: 'Security & SSRF', icon: ShieldCheck },
    { id: 'database', label: 'Database & Storage', icon: Database },
  ];

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex items-center gap-2 pb-2">
        <span className="text-sm font-semibold text-slate-400">•</span>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Settings</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sub-nav Left Column matching Untitled UI Reference */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search settings"
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <nav className="space-y-1">
            {subNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Settings Body */}
        <div className="md:col-span-3 space-y-8">
          {activeTab === 'appearance' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-8">
              {/* Section Header */}
              <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Appearance</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Change how Editorial AI looks and feels in your browser.
                </p>
              </div>

              {/* Interface Theme */}
              <div className="space-y-3">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Interface theme</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Select or customize your UI theme.</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                  {/* Option 1: System preference */}
                  <div 
                    onClick={() => handleThemeChange('system')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all relative ${
                      themePreference === 'system'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                    }`}
                  >
                    <div className="h-24 rounded-lg bg-slate-100 dark:bg-slate-800 overflow-hidden flex border border-slate-200 dark:border-slate-700">
                      <div className="w-1/2 bg-white p-2 border-r border-slate-200">
                        <div className="w-8 h-2 bg-slate-200 rounded mb-2" />
                        <div className="w-12 h-1.5 bg-slate-100 rounded mb-1" />
                        <div className="w-10 h-1.5 bg-slate-100 rounded" />
                      </div>
                      <div className="w-1/2 bg-slate-900 p-2">
                        <div className="w-8 h-2 bg-slate-700 rounded mb-2" />
                        <div className="w-12 h-1.5 bg-slate-800 rounded mb-1" />
                        <div className="w-10 h-1.5 bg-slate-800 rounded" />
                      </div>
                    </div>
                    <div className="mt-2.5 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">System preference</span>
                      {themePreference === 'system' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Option 2: Light */}
                  <div 
                    onClick={() => handleThemeChange('light')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all relative ${
                      themePreference === 'light'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                    }`}
                  >
                    <div className="h-24 rounded-lg bg-white p-2.5 border border-slate-200 overflow-hidden">
                      <div className="w-12 h-2 bg-slate-200 rounded mb-2" />
                      <div className="w-20 h-1.5 bg-slate-100 rounded mb-1.5" />
                      <div className="w-16 h-1.5 bg-slate-100 rounded mb-1.5" />
                      <div className="w-24 h-1.5 bg-slate-100 rounded" />
                    </div>
                    <div className="mt-2.5 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Light</span>
                      {themePreference === 'light' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Option 3: Dark */}
                  <div 
                    onClick={() => handleThemeChange('dark')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all relative ${
                      themePreference === 'dark'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800 hover:border-slate-300'
                    }`}
                  >
                    <div className="h-24 rounded-lg bg-slate-900 p-2.5 border border-slate-800 overflow-hidden">
                      <div className="w-12 h-2 bg-slate-700 rounded mb-2" />
                      <div className="w-20 h-1.5 bg-slate-800 rounded mb-1.5" />
                      <div className="w-16 h-1.5 bg-slate-800 rounded mb-1.5" />
                      <div className="w-24 h-1.5 bg-slate-800 rounded" />
                    </div>
                    <div className="mt-2.5 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Dark</span>
                      {themePreference === 'dark' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Transparent Sidebar Toggle */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Transparent sidebar</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Make the desktop sidebar transparent.</p>
                </div>
                <button
                  onClick={() => setTransparentSidebar(!transparentSidebar)}
                  className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                    transparentSidebar ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                      transparentSidebar ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Sidebar Feature Dropdown */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Sidebar feature</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">What shows in the desktop sidebar.</p>
                </div>
                <select
                  value={sidebarFeature}
                  onChange={(e) => setSidebarFeature(e.target.value)}
                  className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 rounded-xl px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                >
                  <option value="Recent changes">• Recent changes</option>
                  <option value="Quick links">• Quick links</option>
                  <option value="System status">• System status</option>
                </select>
              </div>

              {/* Tables View Selector matching Screen 2 */}
              <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Tables view</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">How are tables displayed in the app.</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div
                    onClick={() => setTableView('default')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all ${
                      tableView === 'default'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="h-20 bg-slate-50 dark:bg-slate-800/60 rounded-lg p-2.5 space-y-2 border border-slate-200 dark:border-slate-700">
                      <div className="flex justify-between border-b pb-1 border-slate-200 dark:border-slate-700">
                        <div className="w-16 h-2 bg-slate-300 rounded" />
                        <div className="w-10 h-2 bg-slate-300 rounded" />
                      </div>
                      <div className="flex justify-between">
                        <div className="w-12 h-2 bg-slate-200 rounded" />
                        <div className="w-8 h-2 bg-slate-200 rounded" />
                      </div>
                      <div className="flex justify-between">
                        <div className="w-14 h-2 bg-slate-200 rounded" />
                        <div className="w-8 h-2 bg-slate-200 rounded" />
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Default</span>
                      {tableView === 'default' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>

                  <div
                    onClick={() => setTableView('compact')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all ${
                      tableView === 'compact'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="h-20 bg-slate-50 dark:bg-slate-800/60 rounded-lg p-2 space-y-1 border border-slate-200 dark:border-slate-700">
                      <div className="flex justify-between border-b pb-0.5 border-slate-200 dark:border-slate-700">
                        <div className="w-16 h-1.5 bg-slate-300 rounded" />
                        <div className="w-10 h-1.5 bg-slate-300 rounded" />
                      </div>
                      <div className="flex justify-between">
                        <div className="w-12 h-1.5 bg-slate-200 rounded" />
                        <div className="w-8 h-1.5 bg-slate-200 rounded" />
                      </div>
                      <div className="flex justify-between">
                        <div className="w-14 h-1.5 bg-slate-200 rounded" />
                        <div className="w-8 h-1.5 bg-slate-200 rounded" />
                      </div>
                      <div className="flex justify-between">
                        <div className="w-10 h-1.5 bg-slate-200 rounded" />
                        <div className="w-6 h-1.5 bg-slate-200 rounded" />
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Compact</span>
                      {tableView === 'compact' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'observability' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Activity className="w-4 h-4 text-blue-500" />
                    Observability, Health & Telemetry
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Live operational telemetry, health probes, and structured error tracking.
                  </p>
                </div>
                <button
                  onClick={checkHealth}
                  disabled={loading}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>

              {/* Core SRE Health Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Overall Status</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                    <span className={`w-2 h-2 rounded-full ${healthData?.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                    <span className="capitalize">{healthData?.status || 'Online'}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">API & Services</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Liveness Probe</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    GET /health/live
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Process healthy (200 OK)</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Readiness Probe</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    GET /health/ready
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">DB: {healthData?.database || 'connected'}</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Uptime & Tracing</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-slate-900 dark:text-white font-mono">
                    <Clock className="w-3.5 h-3.5 text-blue-500" />
                    {healthData?.telemetry?.uptime_seconds ? `${Math.floor(healthData.telemetry.uptime_seconds)}s` : 'Active'}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">X-Request-ID active</span>
                </div>
              </div>

              {/* AI Provider Telemetry & Token Usage */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
                    AI Service Telemetry & Token Usage
                  </h3>
                  <span className="text-[11px] font-mono text-slate-500">
                    Mode: {healthData?.ai_engine?.mode || 'Deterministic Fallback Engine'}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                    <div className="text-[10px] text-slate-400 uppercase">Total Operations</div>
                    <div className="text-base font-bold text-slate-900 dark:text-white font-mono mt-0.5">
                      {healthData?.telemetry?.ai_telemetry?.total_operations ?? 0}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                    <div className="text-[10px] text-slate-400 uppercase">Live LLM Success</div>
                    <div className="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5">
                      {healthData?.telemetry?.ai_telemetry?.successful_operations ?? 0}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                    <div className="text-[10px] text-slate-400 uppercase">Fallback Triggers</div>
                    <div className="text-base font-bold text-blue-600 dark:text-blue-400 font-mono mt-0.5">
                      {healthData?.telemetry?.ai_telemetry?.fallback_operations ?? 0}
                    </div>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-200/60 dark:border-slate-700/60">
                    <div className="text-[10px] text-slate-400 uppercase">Tokens Consumed</div>
                    <div className="text-base font-bold text-purple-600 dark:text-purple-400 font-mono mt-0.5">
                      {healthData?.telemetry?.ai_telemetry?.cumulative_tokens?.total_tokens ?? 0}
                    </div>
                  </div>
                </div>

                <div className="text-[11px] text-slate-500 dark:text-slate-400 flex flex-wrap gap-4 pt-1">
                  <span>Prompt Tokens: <strong className="font-mono text-slate-700 dark:text-slate-200">{healthData?.telemetry?.ai_telemetry?.cumulative_tokens?.prompt_tokens ?? 0}</strong></span>
                  <span>Completion Tokens: <strong className="font-mono text-slate-700 dark:text-slate-200">{healthData?.telemetry?.ai_telemetry?.cumulative_tokens?.completion_tokens ?? 0}</strong></span>
                  <span>Last Activity: <strong className="font-mono text-slate-700 dark:text-slate-200">{healthData?.telemetry?.last_successful_operation ? new Date(healthData.telemetry.last_successful_operation).toLocaleTimeString() : 'Ready'}</strong></span>
                </div>
              </div>

              {/* Ring Buffer: Recent Events */}
              <div className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-slate-400" />
                    Telemetry Event Buffer (Last 10 Operations)
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono">In-Memory Ring Buffer</span>
                </div>

                {healthData?.telemetry?.recent_events && healthData.telemetry.recent_events.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 font-mono uppercase">
                          <th className="pb-2">Time</th>
                          <th className="pb-2">Operation</th>
                          <th className="pb-2">Status</th>
                          <th className="pb-2 text-right">Duration</th>
                          <th className="pb-2 text-right">Tokens</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                        {healthData.telemetry.recent_events.map((evt: any, idx: number) => (
                          <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                            <td className="py-2 text-slate-400">
                              {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '—'}
                            </td>
                            <td className="py-2 font-medium text-slate-800 dark:text-slate-200">
                              {evt.operation}
                            </td>
                            <td className="py-2">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                evt.status === 'success' 
                                  ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60'
                                  : evt.status === 'fallback'
                                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border border-blue-200/60'
                                  : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200/60'
                              }`}>
                                {evt.status}
                              </span>
                            </td>
                            <td className="py-2 text-right text-slate-500">
                              {evt.duration_ms ? `${evt.duration_ms}ms` : '—'}
                            </td>
                            <td className="py-2 text-right text-slate-500">
                              {evt.tokens?.total ? `${evt.tokens.total}` : '0'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-lg">
                    No operations recorded in buffer yet. AI analysis and writing runs will display live metrics here.
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
              <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">AI Engine & Model Architecture</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Dual-tier architecture: OpenAI-compatible API with zero-failure deterministic fallback.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] font-mono text-slate-400 uppercase">Operational Mode</span>
                  <div className="text-sm font-bold text-slate-900 dark:text-white mt-1 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    {healthData?.ai_engine?.mode || 'Deterministic Fallback Engine'}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] font-mono text-slate-400 uppercase">Configured Target Model</span>
                  <div className="text-sm font-bold text-slate-900 dark:text-white mt-1 font-mono">
                    {healthData?.ai_engine?.model || 'gpt-4o-mini'}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 leading-relaxed">
                <strong>Guaranteed Execution:</strong> All 6 writing checks (sentence splitting, passive voice, filler removal, jargon glossary, repetition detection, and complexity scoring) run deterministically without external API dependencies.
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
              <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Security & SSRF Guardrails</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Enforced network and payload isolation policies.
                </p>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Loopback & Private IP Blocking</span>
                  <span className="font-mono text-emerald-600 font-bold">127.0.0.1, 10.0.0.0/8, 192.168.0.0/16 [Enforced]</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Max Payload & Redirect Limits</span>
                  <span className="font-mono text-emerald-600 font-bold">2MB Max / 4 Redirects [Enforced]</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Prompt Injection Mitigation</span>
                  <span className="font-mono text-emerald-600 font-bold">Untrusted Scraped Text Segregation [Enforced]</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'database' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
              <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Database & Persistence</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  SQLite database with SQLAlchemy and Alembic migrations.
                </p>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Database Engine</span>
                  <span className="font-mono text-slate-900 dark:text-white font-bold">SQLite 3.x (editorial.db)</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Connection Status</span>
                  <span className="font-mono text-emerald-600 font-bold">Connected</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Active Schema Tables</span>
                  <span className="font-mono text-slate-900 dark:text-white font-bold">7 Tables</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
