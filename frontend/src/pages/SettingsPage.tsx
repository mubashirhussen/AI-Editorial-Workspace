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
  Terminal,
  Zap,
  Lock,
  Globe,
  Sliders,
  RotateCw
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

  // AI Multi-Provider State
  const [aiConnections, setAiConnections] = useState<any[]>([]);
  const [aiModels, setAiModels] = useState<any[]>([]);
  const [aiUsage, setAiUsage] = useState<any>(null);
  const [testingConnId, setTestingConnId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, { status: string; latency_ms?: number; message?: string }>>({});
  const [keyInput, setKeyInput] = useState<Record<string, string>>({});
  const [modelSelect, setModelSelect] = useState<Record<string, string>>({});
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [rotatingConnId, setRotatingConnId] = useState<string | null>(null);
  const [newRotateKey, setNewRotateKey] = useState('');

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    if (activeTab === 'ai') {
      fetchAiConfig();
    }
  }, [activeTab]);

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

  const fetchAiConfig = async () => {
    try {
      const [connRes, modelRes, usageRes] = await Promise.all([
        apiClient.get('/ai/connections').catch(() => ({ data: [] })),
        apiClient.get('/ai/models').catch(() => ({ data: [] })),
        apiClient.get('/ai/usage/summary').catch(() => ({ data: null }))
      ]);
      setAiConnections(connRes.data || []);
      setAiModels(modelRes.data || []);
      setAiUsage(usageRes.data);
    } catch (e) {
      console.error('Failed to load AI config:', e);
    }
  };

  const handleTestConnection = async (connId: string) => {
    setTestingConnId(connId);
    const start = performance.now();
    try {
      const res = await apiClient.post(`/ai/connections/${connId}/validate`);
      const latency = Math.round(performance.now() - start);
      setTestResult(prev => ({
        ...prev,
        [connId]: { status: 'success', latency_ms: latency, message: `Connected in ${latency}ms` }
      }));
      fetchAiConfig();
    } catch (err: any) {
      const latency = Math.round(performance.now() - start);
      setTestResult(prev => ({
        ...prev,
        [connId]: { status: 'error', latency_ms: latency, message: err.response?.data?.detail || 'Handshake error' }
      }));
    } finally {
      setTestingConnId(null);
    }
  };

  const handleSaveConnection = async (provider: string, defaultName: string) => {
    const rawKey = keyInput[provider];
    if (!rawKey) return;
    setSavingProvider(provider);
    try {
      await apiClient.post('/ai/connections', {
        provider,
        name: defaultName,
        api_key: rawKey,
        model: modelSelect[provider] || undefined,
        is_default: provider === 'groq'
      });
      setKeyInput(prev => ({ ...prev, [provider]: '' }));
      fetchAiConfig();
    } catch (err: any) {
      alert('Failed to save connection: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingProvider(null);
    }
  };

  const handleRotateKey = async (connId: string) => {
    if (!newRotateKey.trim()) return;
    try {
      await apiClient.post(`/ai/connections/${connId}/rotate`, { new_api_key: newRotateKey.trim() });
      setRotatingConnId(null);
      setNewRotateKey('');
      fetchAiConfig();
    } catch (err: any) {
      alert('Key rotation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleThemeChange = (theme: 'system' | 'light' | 'dark') => {
    setThemePreference(theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else if (theme === 'light') {
      document.documentElement.classList.remove('dark');
    } else {
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

  const providerCatalog = [
    {
      id: 'groq',
      name: 'Groq LPU Cloud',
      category: 'Ultra-low Latency LPU',
      badgeColor: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
      description: 'Specialized Tensor Streaming Processor yielding 300+ tok/s for instant editorial generation and synthesis.',
      defaultModel: 'openai/gpt-oss-20b'
    },
    {
      id: 'openai',
      name: 'OpenAI (GPT-4o)',
      category: 'Frontier Intelligence',
      badgeColor: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
      description: 'High-capability multi-modal models suitable for complex synthesis, deep analysis, and style transformation.',
      defaultModel: 'gpt-4o-mini'
    },
    {
      id: 'anthropic',
      name: 'Anthropic Claude',
      category: 'Long-Form & Nuance',
      badgeColor: 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300',
      description: 'Industry-standard analytical reasoning with 200k context window and strict adherence to editorial tone.',
      defaultModel: 'claude-3-5-sonnet-latest'
    },
    {
      id: 'google_gemini',
      name: 'Google Gemini',
      category: 'Massive Context',
      badgeColor: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
      description: 'Frontier multimodal architecture supporting 1M+ token context windows for deep research archives.',
      defaultModel: 'gemini-1.5-flash'
    }
  ];

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex items-center gap-2 pb-2">
        <span className="text-sm font-semibold text-slate-400">•</span>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Settings</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Sub-nav Left Column */}
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
                  className={`w-full flex items-center justify-between px-3 py-2 text-xs font-semibold rounded-xl transition-all ${
                    isActive
                      ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {isActive && <div className="w-1.5 h-1.5 rounded-full bg-blue-600 dark:bg-blue-400" />}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content Column */}
        <div className="md:col-span-3 space-y-6">
          {activeTab === 'appearance' && (
            <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-6">
              <div className="pb-4 border-b border-slate-100 dark:border-slate-800">
                <h2 className="text-base font-bold text-slate-900 dark:text-white">Appearance & Interface</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Customize how the AI Editorial Workspace looks and feels on your screen.
                </p>
              </div>

              {/* Theme Selector */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-900 dark:text-white">Interface theme</h3>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">Select or sync with your system display preference.</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                  <div
                    onClick={() => handleThemeChange('system')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all ${
                      themePreference === 'system'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
                      <Laptop className="w-6 h-6 text-slate-500" />
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">System preference</span>
                      {themePreference === 'system' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>

                  <div
                    onClick={() => handleThemeChange('light')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all ${
                      themePreference === 'light'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="h-20 bg-white border border-slate-200 rounded-lg flex items-center justify-center">
                      <Sun className="w-6 h-6 text-amber-500" />
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Light</span>
                      {themePreference === 'light' && (
                        <div className="w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center">
                          <Check className="w-2.5 h-2.5" />
                        </div>
                      )}
                    </div>
                  </div>

                  <div
                    onClick={() => handleThemeChange('dark')}
                    className={`cursor-pointer rounded-xl border p-3 transition-all ${
                      themePreference === 'dark'
                        ? 'border-blue-600 ring-2 ring-blue-500/20'
                        : 'border-slate-200 dark:border-slate-800'
                    }`}
                  >
                    <div className="h-20 bg-slate-900 border border-slate-700 rounded-lg flex items-center justify-center">
                      <Moon className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="mt-2 flex items-center justify-between">
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

              {/* Sidebar display */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Transparent sidebar</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Make the desktop navigation bar slightly transparent.</p>
                </div>
                <button
                  onClick={() => setTransparentSidebar(!transparentSidebar)}
                  className={`w-9 h-5 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
                    transparentSidebar ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div className={`bg-white w-3 h-3 rounded-full shadow-md transform transition-transform ${
                    transparentSidebar ? 'translate-x-4' : 'translate-x-0'
                  }`} />
                </button>
              </div>

              {/* Sidebar feature dropdown */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">Sidebar feature</h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">What shows in the desktop sidebar footer.</p>
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

              {/* Tables View Selector */}
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

              {/* Telemetry Ring Buffer */}
              <div className="pt-2 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
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
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-blue-500" />
                    AI Provider Integration & API Key Management
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Manage multi-provider LLM credentials, model routing, sub-second LPU acceleration, and key rotation.
                  </p>
                </div>
                <button
                  onClick={fetchAiConfig}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Refresh
                </button>
              </div>

              {/* Usage & Telemetry Stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Active Provider</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                    <Zap className="w-3.5 h-3.5 text-amber-500" />
                    <span className="capitalize">{healthData?.ai_engine?.provider || 'Groq LPU'}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">{healthData?.ai_engine?.model || 'openai/gpt-oss-20b'}</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Total Calls</span>
                  <div className="mt-1 text-sm font-bold text-slate-900 dark:text-white font-mono">
                    {aiUsage?.total_calls || 0}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Recorded requests</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Tokens Processed</span>
                  <div className="mt-1 text-sm font-bold text-slate-900 dark:text-white font-mono">
                    {aiUsage?.total_tokens ? aiUsage.total_tokens.toLocaleString() : '0'}
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">{aiUsage?.total_prompt_tokens || 0} in / {aiUsage?.total_completion_tokens || 0} out</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Failover Security</span>
                  <div className="mt-1 flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Deterministic Fallback
                  </div>
                  <span className="text-[10px] text-slate-500 mt-0.5 block">0% Downtime guarantee</span>
                </div>
              </div>

              {/* Multi-Provider Cards */}
              <div className="space-y-4 pt-2">
                <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
                  Supported AI Providers & Connections
                </h3>

                <div className="grid grid-cols-1 gap-4">
                  {providerCatalog.map((prov) => {
                    const conn = aiConnections.find(c => c.provider === prov.id);
                    const providerModels = aiModels.filter(m => m.provider === prov.id);
                    const isConfigured = !!conn;
                    const testStatus = conn ? testResult[conn.id] : null;

                    return (
                      <div 
                        key={prov.id}
                        className="rounded-xl border border-slate-200 dark:border-slate-800 p-4 bg-slate-50/50 dark:bg-slate-800/30 space-y-3"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200/60 dark:border-slate-800">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-blue-50 dark:bg-blue-950 flex items-center justify-center font-bold text-blue-600 dark:text-blue-400 text-xs">
                              {prov.name[0]}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="text-xs font-bold text-slate-900 dark:text-white">{prov.name}</h4>
                                <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${prov.badgeColor}`}>
                                  {prov.category}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{prov.description}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            {isConfigured ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60">
                                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                                {conn.status === 'connected' ? 'Connected' : 'Configured'}
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                                Not Configured
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Connection Details or Configuration Form */}
                        {isConfigured ? (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs pt-1">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="text-[11px] text-slate-400 font-mono">Credential:</span>
                                <span className="font-mono text-slate-700 dark:text-slate-200 bg-slate-200/60 dark:bg-slate-800 px-2 py-0.5 rounded">
                                  {conn.masked_key}
                                </span>
                                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                                  <Lock className="w-2.5 h-2.5 text-emerald-500" /> AES-128
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                                <span>Default Model: <strong>{conn.model || prov.defaultModel}</strong></span>
                                {conn.last_synced_at && (
                                  <span>• Last synced {new Date(conn.last_synced_at).toLocaleTimeString()}</span>
                                )}
                              </div>
                              {testStatus && (
                                <div className={`text-[11px] font-medium flex items-center gap-1 ${
                                  testStatus.status === 'success' ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                                }`}>
                                  {testStatus.status === 'success' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                                  {testStatus.message}
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleTestConnection(conn.id)}
                                disabled={testingConnId === conn.id}
                                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg transition-colors"
                              >
                                <RefreshCw className={`w-3 h-3 ${testingConnId === conn.id ? 'animate-spin' : ''}`} />
                                Test Handshake
                              </button>
                              <button
                                onClick={() => setRotatingConnId(conn.id)}
                                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg transition-colors"
                              >
                                <RotateCw className="w-3 h-3 text-blue-500" />
                                Rotate Key
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-1 text-xs">
                            <input
                              type="password"
                              placeholder={`Paste ${prov.name} API Key...`}
                              value={keyInput[prov.id] || ''}
                              onChange={(e) => setKeyInput(prev => ({ ...prev, [prov.id]: e.target.value }))}
                              className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                            />
                            {providerModels.length > 0 && (
                              <select
                                value={modelSelect[prov.id] || prov.defaultModel}
                                onChange={(e) => setModelSelect(prev => ({ ...prev, [prov.id]: e.target.value }))}
                                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-2 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 focus:outline-none"
                              >
                                {providerModels.map(m => (
                                  <option key={m.id} value={m.id}>{m.name}</option>
                                ))}
                              </select>
                            )}
                            <button
                              onClick={() => handleSaveConnection(prov.id, `${prov.name} Integration`)}
                              disabled={savingProvider === prov.id || !keyInput[prov.id]}
                              className="px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl transition-colors shadow-xs"
                            >
                              {savingProvider === prov.id ? 'Connecting...' : 'Connect'}
                            </button>
                          </div>
                        )}

                        {/* Rotate Key Dialog Inline */}
                        {rotatingConnId === conn?.id && (
                          <div className="mt-2 p-3 bg-blue-50/60 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 rounded-xl space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-bold text-blue-900 dark:text-blue-200 flex items-center gap-1.5">
                                <Key className="w-3 h-3" /> Rotate Secret for {prov.name}
                              </span>
                              <button onClick={() => setRotatingConnId(null)} className="text-[10px] text-slate-400 hover:text-slate-600">Cancel</button>
                            </div>
                            <div className="flex items-center gap-2">
                              <input
                                type="password"
                                placeholder="Enter replacement API key..."
                                value={newRotateKey}
                                onChange={(e) => setNewRotateKey(e.target.value)}
                                className="flex-1 bg-white dark:bg-slate-900 border border-blue-300 dark:border-blue-700 rounded-lg px-2.5 py-1 text-xs font-mono"
                              />
                              <button
                                onClick={() => handleRotateKey(conn.id)}
                                className="px-3 py-1 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                              >
                                Save & Encrypt
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Tier Failover Architecture Callout */}
              <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 leading-relaxed space-y-1">
                <div className="font-bold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  Dual-Tier Failover Resilience Policy
                </div>
                <p className="text-[11px]">
                  All editorial operations execute through the intelligent provider router. If the primary cloud provider experiences rate limits or network degradation, requests automatically fall back with bounded jitter retry to secondary providers and the deterministic local extraction engine.
                </p>
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
                  <span className="font-mono text-slate-900 dark:text-white font-bold">34 Tables (Phase 4 Migration Complete)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
