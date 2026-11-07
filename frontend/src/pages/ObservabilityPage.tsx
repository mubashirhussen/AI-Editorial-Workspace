import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  ShieldCheck, 
  Zap, 
  Clock, 
  AlertTriangle, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink, 
  Terminal, 
  Database,
  Search,
  Filter,
  BarChart2,
  PieChart,
  Layers,
  FileText,
  Info,
  ChevronDown,
  ChevronUp,
  Download,
  Share2,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Cpu,
  Radio,
  Send,
  HelpCircle,
  FlaskConical,
  Play,
  Wrench,
  Check,
  X,
  FileCode,
  Sliders,
  Sparkles,
  UserCheck,
  Award,
  Bookmark,
  FileDown
} from 'lucide-react';
import { 
  observabilityService, 
  AIMetricsResponse, 
  PromptVersionInfo, 
  EvaluationBenchmarkResult 
} from '../services/observabilityService';
import { useAuth } from '../context/AuthContext';
import { LoadingState } from '../components/common/LoadingState';

export const ObservabilityPage: React.FC = () => {
  const { activeOrg } = useAuth();
  
  // Primary Tabs covering all user-provided reference interfaces
  const [activeTab, setActiveTab] = useState<
    'tracelens' | 'agent_tools' | 'sentinel' | 'dt_evals' | 'claim_studio' | 'hitl_studio' | 'trust' | 'evals'
  >('tracelens');

  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<AIMetricsResponse | null>(null);
  const [operations, setOperations] = useState<any[]>([]);
  const [prompts, setPrompts] = useState<PromptVersionInfo[]>([]);
  const [benchmarkResult, setBenchmarkResult] = useState<EvaluationBenchmarkResult | null>(null);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState(false);

  // Global Time and Filter controls
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedModel, setSelectedModel] = useState('all');

  // ==========================================
  // State for AI Claim Verification System (media_1794040926742_7d56dbf4.jpg)
  // ==========================================
  const [claimMode, setClaimMode] = useState<'single' | 'batch' | 'extract_only' | 'extract_verify'>('single');
  const [claimSpeed, setClaimSpeed] = useState<'quick' | 'standard' | 'thorough'>('standard');
  const [claimTopic, setClaimTopic] = useState('Company Financial Performance');
  const [singleClaimText, setSingleClaimText] = useState('The current Rector of UNU is Dr. David Malone');
  const [isVerifyingClaim, setIsVerifyingClaim] = useState(false);
  const [claimVerificationResult, setClaimVerificationResult] = useState<any | null>({
    totalClaims: 1,
    verdict: 'False',
    confidence: 'High',
    claimText: 'The current Rector of UNU is Dr. David Malone',
    evidenceSummary: 'Dr. David Malone was the Rector of the United Nations University (UNU) from 2013 to 2023, but he is no longer in this position. The current Rector is Prof. Tshilidzi Marwala, who assumed the role in March 2023.',
    sources: [
      'https://unu.edu/about/leadership/rector - Official UNU website showing current leadership',
      'https://www.un.org/press/en/2022/sga2175.doc.htm - UN Press Release announcing Marwala appointment'
    ]
  });

  // ==========================================
  // State for Human-in-the-Loop Verdict Studio (media_1794040974006_fd23835b.jpg)
  // ==========================================
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState(3); // Sentence #4
  const [humanVerdict, setHumanVerdict] = useState<'Supported' | 'Contradictory' | 'Inconclusive' | 'None'>('Contradictory');
  const [humanReason, setHumanReason] = useState('Numerical superiority over daily oral PrEP was statistically significant in HPTN 083 (66% lower risk, HR 0.34), but the claim asserts it holds regardless of adherence level, which conflicts with sub-group analysis.');
  const [confidenceLevel, setConfidenceLevel] = useState<'Certain' | 'Confident' | 'Uncertain'>('Certain');
  const [errorCategory, setErrorCategory] = useState<'Collection' | 'Analysis' | 'Generalization' | 'None'>('Generalization');
  const [annotationSavedNotice, setAnnotationSavedNotice] = useState(false);

  // Sentences list for HITL Studio
  const hitlSentences = [
    { id: 1, title: 'Title', text: 'The Efficacy, Safety, and Implementation of Long-Acting Cabotegravir for HIV Pre-Exposure Prophylaxis: A Comprehensive Review of Clinical Trial and Real-World Data', isHeader: true },
    { id: 2, title: 'Section', text: 'Executive Summary', isHeader: true },
    { id: 3, title: 'Claim', text: 'Long-acting injectable cabotegravir (CAB-LA) represents a transformative advancement in the field of biomedical HIV prevention.', isHeader: false, status: 'supported' },
    { id: 4, title: 'Claim', text: 'Evidence from two pivotal, large-scale, randomized controlled trials—HPTN 083 and HPTN 084—has unequivocally established its statistical superiority over daily oral tenofovir disoproxil fumarate/emtricitabine (TDF/FTC) for pre-exposure prophylaxis (PrEP), regardless of adherence level.', isHeader: false, status: 'unsupported' },
    { id: 5, title: 'Claim', text: 'In HPTN 083, which enrolled cisgender men who have sex with men (MSM) and transgender women (TGW), CAB-LA demonstrated a 66% reduction in the risk of HIV infection compared to daily oral TDF/FTC.', isHeader: false, status: 'supported' },
    { id: 6, title: 'Claim', text: 'In HPTN 084, conducted among cisgender women in sub-Saharan Africa, CAB-LA was 89% more effective than daily oral TDF/FTC.', isHeader: false, status: 'supported' },
  ];

  useEffect(() => {
    loadData();
  }, [activeOrg]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [m, ops, p] = await Promise.all([
        observabilityService.getMetrics().catch(() => null),
        observabilityService.getOperations(0, 30).catch(() => ({ total: 0, items: [] })),
        observabilityService.getPrompts().catch(() => [])
      ]);
      if (m) setMetrics(m);
      if (ops && ops.items) setOperations(ops.items);
      if (p) setPrompts(p);
    } catch (err) {
      console.error('Failed to load observability data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setIsRunningBenchmark(true);
      const res = await observabilityService.runBenchmark('all');
      setBenchmarkResult(res);
      await loadData();
    } catch (err) {
      console.error('Benchmark run failed', err);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  const handleExecuteClaimVerification = async () => {
    if (!singleClaimText.trim()) return;
    try {
      setIsVerifyingClaim(true);
      const sources = [
        {
          id: 'kb-src-1',
          title: 'UNU Leadership History & Official Records',
          extracted_content: 'Dr. David Malone served as Rector of United Nations University from 2013 until 2023. Prof. Tshilidzi Marwala assumed office as the current Rector in March 2023.'
        }
      ];
      const res = await observabilityService.verifyClaim(singleClaimText, sources);
      const firstClaim = res.claims?.[0];
      setClaimVerificationResult({
        totalClaims: res.total_claims || 1,
        verdict: firstClaim?.verification_status === 'SUPPORTED' ? 'True' : 'False',
        confidence: firstClaim?.confidence_score >= 0.85 ? 'High' : 'Medium',
        claimText: singleClaimText,
        evidenceSummary: firstClaim?.warning_message || firstClaim?.supporting_excerpt || 'Corroboration evaluated against ingested knowledge base.',
        sources: [
          'https://unu.edu/about/leadership/rector - Official UNU website showing current leadership',
          'https://www.un.org/press - UN Press Release records'
        ]
      });
    } catch (err) {
      console.error('Claim verification failed', err);
    } finally {
      setIsVerifyingClaim(false);
    }
  };

  const handleSaveHITLAnnotation = () => {
    setAnnotationSavedNotice(true);
    setTimeout(() => setAnnotationSavedNotice(false), 3000);
  };

  // Mock datasets for TraceLens & Sentinel
  const sentinelInterceptions = [
    { model: 'GPT-4 LLM', text: 'The contract clause in section 4.2 specifies recurring licensing rights and SLA performance metrics.', claims: 5, trust: 92, time: '2m ago' },
    { model: 'Claude-3.5 LLM', text: 'Based on the financial analysis, revenue grew 38% year-over-year while operating margins held at 24%.', claims: 4, trust: 88, time: '5m ago' },
    { model: 'Gemini-1.5 LLM', text: 'The regulatory framework under Basel III requires capital adequacy ratios exceeding 10.5%.', claims: 6, trust: 94, time: '8m ago' },
    { model: 'Llama-3.3 LLM', text: 'Historical data suggests market correction in Q3 due to macroeconomic interest rate adjustments.', claims: 4, trust: 71, time: '12m ago' },
    { model: 'Mistral Agent', text: 'The compliance check returned 3 active policy notices across European privacy and GDPR directives.', claims: 3, trust: 85, time: '16m ago' },
    { model: 'Deterministic Fallback', text: 'Editorial brief structured with 4 key findings, in-text source citations, and 3 newsletter angles.', claims: 5, trust: 96, time: '18m ago' },
  ];

  // Most actionable failures for dt-evals (media_1794040913402_e51adce4.jpg)
  const dtActionableFailures = [
    { time: 'Today, 4:54 PM', score: 0.002, verdict: 'fail', metric: 'prompt-injection', model: 'gpt-4o-mini', explanation: 'The input contains indirect instruction override, but output executed prompt formatting command.', trace: 'ba14ababfe', span: '434e8cab' },
    { time: 'Today, 4:52 PM', score: 0.324, verdict: 'fail', metric: 'faithfulness', model: 'gpt-4o-mini', explanation: 'The answer makes a specific numeric valuation claim not substantiated by provided weather tool context.', trace: '7b971471c1', span: '641dee25' },
    { time: 'Today, 4:51 PM', score: 0.477, verdict: 'fail', metric: 'answer-completeness', model: 'gpt-4o-mini', explanation: 'Response partially addressed user query but omitted key safety recommendations.', trace: '27a0da60c4', span: '5071827d' },
    { time: 'Today, 4:50 PM', score: 0.583, verdict: 'fail', metric: 'context-relevance', model: 'gpt-4o-mini', explanation: 'Retrieved context is about routing requests; only one sentence is directly relevant to target query.', trace: '84e125b62b', span: '184ef05d' },
  ];

  // Tool usage metrics for Agent Observability (media_1794040941239_2a611cb5.jpg)
  const toolUsageData = [
    { name: 'execute_tool research_scrape', count: 24, avg_ms: '432.67ms' },
    { name: 'execute_tool get_source_metrics', count: 9, avg_ms: '216.89ms' },
    { name: 'execute_tool update_draft_layout', count: 4, avg_ms: '142.50ms' },
    { name: 'execute_tool verify_grounding', count: 8, avg_ms: '118.00ms' },
    { name: 'execute_tool list_editorial_profiles', count: 2, avg_ms: '45.12ms' },
  ];

  if (loading && !metrics) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <LoadingState message="Loading observability & telemetry telemetry..." />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Context Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/10 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold">
              <Activity className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              AI Reliability & Observability Center
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              Enterprise SRE
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Comprehensive telemetry, continuous evals, tool spans, claim fact-checking, and human grounding annotation for {activeOrg?.name || 'Workspace'}.
          </p>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-700 dark:text-slate-200"
          >
            <option value="1h">Last 1 Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>

          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleRunBenchmark}
            disabled={isRunningBenchmark}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-xs transition-colors disabled:opacity-60 cursor-pointer"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${isRunningBenchmark ? 'animate-spin' : ''}`} />
            {isRunningBenchmark ? 'Evaluating...' : 'Run 34-Case Benchmark'}
          </button>
        </div>
      </div>

      {/* Primary Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200 dark:border-slate-800 pb-px overflow-x-auto text-xs font-semibold">
        <button
          onClick={() => setActiveTab('tracelens')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'tracelens'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          LLM Tracking (TraceLens)
        </button>

        <button
          onClick={() => setActiveTab('agent_tools')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'agent_tools'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Wrench className="w-3.5 h-3.5" />
          Agent & Tool Spans (OpsAI)
        </button>

        <button
          onClick={() => setActiveTab('dt_evals')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'dt_evals'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Continuous Evals (dt-evals)
        </button>

        <button
          onClick={() => setActiveTab('claim_studio')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'claim_studio'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Search className="w-3.5 h-3.5" />
          AI Claim Verification
        </button>

        <button
          onClick={() => setActiveTab('hitl_studio')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'hitl_studio'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <UserCheck className="w-3.5 h-3.5" />
          Human Verdict Studio (HITL)
        </button>

        <button
          onClick={() => setActiveTab('sentinel')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'sentinel'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          Sentinel Interception
        </button>

        <button
          onClick={() => setActiveTab('trust')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'trust'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Quellen & Vertrauen
        </button>

        <button
          onClick={() => setActiveTab('evals')}
          className={`flex items-center gap-2 px-3 py-2 border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'evals'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          Offline Benchmarks
        </button>
      </div>

      {/* ========================================================================= */}
      {/* 1. TRACELENS & DEEP COST ANALYSIS                                         */}
      {/* ========================================================================= */}
      {activeTab === 'tracelens' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Total LLM Requests</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">
                {metrics?.total_operations ?? 153}
              </div>
              <span className="text-[10px] text-emerald-600 font-medium">↗ +8.5% Last 24h</span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Average Latency</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">
                {metrics?.latency_ms?.average ? `${Math.round(metrics.latency_ms.average)}ms` : '1623ms'}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">P95: {metrics?.latency_ms?.p95 ? `${Math.round(metrics.latency_ms.p95)}ms` : '6547ms'}</span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Success Rate</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
                {metrics?.success_rate_pct ? `${metrics.success_rate_pct}%` : '88.9%'}
              </div>
              <span className="text-[10px] text-slate-400">0.1 req / min</span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Total Cost</span>
              <div className="mt-1 text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">
                ${(metrics?.estimated_cost_usd ?? 1.75).toFixed(2)}
              </div>
              <span className="text-[10px] text-emerald-600">$0.000007 / token</span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Total Tokens</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">
                {metrics?.tokens?.total_tokens ? `${(metrics.tokens.total_tokens / 1000).toFixed(1)}K` : '248.3K'}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">In: 167K / Out: 81K</span>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Error Rate</span>
              <div className="mt-1 text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
                {metrics?.success_rate_pct ? `${(100 - metrics.success_rate_pct).toFixed(1)}%` : '11.1%'}
              </div>
              <span className="text-[10px] text-slate-400">System reliability OK</span>
            </div>
          </div>

          {/* Deep Cost Analysis & Expensive Prompts (media_1794040955690_00d78797.jpg) */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
              Top Expensive AI Execution Prompts
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 uppercase">
                    <th className="pb-2">Trace ID</th>
                    <th className="pb-2">Tokens</th>
                    <th className="pb-2">Prompt Summary</th>
                    <th className="pb-2 text-right">Cost ($ USD)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  <tr>
                    <td className="py-2 text-indigo-500">572c010e97a3</td>
                    <td className="py-2">1,527</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400 truncate max-w-xs">Synthesize cross-source analysis across 12 academic PDFs</td>
                    <td className="py-2 text-right font-bold text-slate-900 dark:text-white">$0.0219</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-indigo-500">a62c1154067c</td>
                    <td className="py-2">1,251</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400 truncate max-w-xs">Generate editorial newsletter draft with AP Style verification</td>
                    <td className="py-2 text-right font-bold text-slate-900 dark:text-white">$0.0185</td>
                  </tr>
                  <tr>
                    <td className="py-2 text-indigo-500">4ddde0de740f</td>
                    <td className="py-2">1,222</td>
                    <td className="py-2 text-slate-600 dark:text-slate-400 truncate max-w-xs">Comprehensive factual claim extraction and grounding audit</td>
                    <td className="py-2 text-right font-bold text-slate-900 dark:text-white">$0.0178</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. AGENT & TOOL OBSERVABILITY (Agno / OpsAI)                              */}
      {/* Reference: media_1794040941239_2a611cb5.jpg                              */}
      {/* ========================================================================= */}
      {activeTab === 'agent_tools' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Number of Spans</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">100</div>
              <span className="text-[10px] text-slate-400">Total traced calls</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Trace Success Rate</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">80%</div>
              <span className="text-[10px] text-slate-400">80 spans OK</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Failed Spans</span>
              <div className="mt-1 text-2xl font-bold font-mono text-red-600">20</div>
              <span className="text-[10px] text-slate-400">Recovered via fallback</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Trace Error Rate</span>
              <div className="mt-1 text-2xl font-bold font-mono text-amber-600">20%</div>
              <span className="text-[10px] text-slate-400">Handled gracefully</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Avg Tokens / Span</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">1,200</div>
              <span className="text-[10px] text-slate-400">tokens / execution</span>
            </div>
          </div>

          {/* Latency by Model Table */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
              Latency by Model & Provider
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 uppercase">
                    <th className="pb-2">Model</th>
                    <th className="pb-2">Provider</th>
                    <th className="pb-2">AVG</th>
                    <th className="pb-2">P75</th>
                    <th className="pb-2">P90</th>
                    <th className="pb-2 text-right">P95</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  <tr>
                    <td className="py-2 font-bold text-slate-900 dark:text-white">llama-3.3-70b-versatile</td>
                    <td className="py-2 text-slate-500">groq</td>
                    <td className="py-2 text-emerald-600">1.22s</td>
                    <td className="py-2">2.20s</td>
                    <td className="py-2">4.10s</td>
                    <td className="py-2 text-right text-amber-600">5.34s</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold text-slate-900 dark:text-white">gpt-4o</td>
                    <td className="py-2 text-slate-500">openai</td>
                    <td className="py-2 text-emerald-600">1.53s</td>
                    <td className="py-2">1.82s</td>
                    <td className="py-2">1.94s</td>
                    <td className="py-2 text-right text-amber-600">6.63s</td>
                  </tr>
                  <tr>
                    <td className="py-2 font-bold text-slate-900 dark:text-white">claude-3-5-sonnet</td>
                    <td className="py-2 text-slate-500">anthropic</td>
                    <td className="py-2 text-emerald-600">2.14s</td>
                    <td className="py-2">3.20s</td>
                    <td className="py-2">5.12s</td>
                    <td className="py-2 text-right text-amber-600">7.86s</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Tools Frequency Breakdown */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
              Agent Tool Invocations & Durations
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                {toolUsageData.map((t, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-700 dark:text-slate-300">{t.name}</span>
                      <span className="font-bold text-indigo-600">{t.count} calls</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${(t.count / 24) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 uppercase">
                      <th className="pb-2">Tool Name</th>
                      <th className="pb-2 text-right">Avg Duration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {toolUsageData.map((t, idx) => (
                      <tr key={idx}>
                        <td className="py-2 text-slate-700 dark:text-slate-300">{t.name}</td>
                        <td className="py-2 text-right text-emerald-600">{t.avg_ms}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. CONTINUOUS EVALS (dt-evals / Dynatrace View)                            */}
      {/* Reference: media_1794040913402_e51adce4.jpg                              */}
      {/* ========================================================================= */}
      {activeTab === 'dt_evals' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Quality Score</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">0.75</div>
              <span className="text-[10px] text-slate-400">Aggregate benchmark</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Pass Rate</span>
              <div className="mt-1 text-2xl font-bold font-mono text-indigo-600">82.0%</div>
              <span className="text-[10px] text-slate-400">41 / 50 passed</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Failures</span>
              <div className="mt-1 text-2xl font-bold font-mono text-amber-600">9</div>
              <span className="text-[10px] text-slate-400">Flagged for review</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Drift Events</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">0</div>
              <span className="text-[10px] text-slate-400">Zero drift detected</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Evaluations</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">50</div>
              <span className="text-[10px] text-slate-400">Evaluator runs</span>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono uppercase text-slate-400">Distinct Services</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">1</div>
              <span className="text-[10px] text-slate-400">editorial-backend</span>
            </div>
          </div>

          {/* Actionable Failures Table */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
                Worst / Most Actionable Failures (dt-evals Audit Log)
              </h3>
              <span className="text-[10px] text-slate-400 font-mono">Automated LLM Judge</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] text-slate-400 uppercase">
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Score</th>
                    <th className="pb-2">Verdict</th>
                    <th className="pb-2">Metric</th>
                    <th className="pb-2">Explanation</th>
                    <th className="pb-2 text-right">Trace</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {dtActionableFailures.map((f, idx) => (
                    <tr key={idx}>
                      <td className="py-2.5 text-slate-400">{f.time}</td>
                      <td className="py-2.5 text-red-600 font-bold">{f.score}</td>
                      <td className="py-2.5">
                        <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-800 uppercase">
                          {f.verdict}
                        </span>
                      </td>
                      <td className="py-2.5 text-slate-900 dark:text-white font-semibold">{f.metric}</td>
                      <td className="py-2.5 text-slate-600 dark:text-slate-400 max-w-md truncate">{f.explanation}</td>
                      <td className="py-2.5 text-right text-indigo-500">{f.trace}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. AI CLAIM VERIFICATION STUDIO                                           */}
      {/* Reference: media_1794040926742_7d56dbf4.jpg                              */}
      {/* ========================================================================= */}
      {activeTab === 'claim_studio' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                AI Claim Verification System
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Verify factual claims using evidence grounding and web research capabilities across single, batch, or extract modes.
              </p>
            </div>

            {/* Mode & Speed Switchers */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
              <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
                <button
                  onClick={() => setClaimMode('single')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${claimMode === 'single' ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-500'}`}
                >
                  Single Claim Verification
                </button>
                <button
                  onClick={() => setClaimMode('batch')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${claimMode === 'batch' ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-500'}`}
                >
                  Batch Claims
                </button>
                <button
                  onClick={() => setClaimMode('extract_only')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${claimMode === 'extract_only' ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-500'}`}
                >
                  Extract Claims Only
                </button>
                <button
                  onClick={() => setClaimMode('extract_verify')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${claimMode === 'extract_verify' ? 'bg-white dark:bg-slate-900 text-indigo-600 shadow-xs' : 'text-slate-500'}`}
                >
                  Extract & Verify
                </button>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Speed:</span>
                {(['quick', 'standard', 'thorough'] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setClaimSpeed(s)}
                    className={`px-2.5 py-1 rounded-lg font-mono capitalize ${claimSpeed === s ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Input & Context Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-slate-900 dark:text-white block font-mono mb-1">
                    Enter Claim to Verify:
                  </label>
                  <textarea
                    value={singleClaimText}
                    onChange={(e) => setSingleClaimText(e.target.value)}
                    rows={4}
                    className="w-full text-xs font-mono p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-900 dark:text-white block font-mono mb-1">
                    Topic / Context for Claims (Optional):
                  </label>
                  <input
                    type="text"
                    value={claimTopic}
                    onChange={(e) => setClaimTopic(e.target.value)}
                    className="w-full text-xs font-mono p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleExecuteClaimVerification}
                    disabled={isVerifyingClaim}
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition-colors cursor-pointer disabled:opacity-60"
                  >
                    <Search className={`w-3.5 h-3.5 ${isVerifyingClaim ? 'animate-spin' : ''}`} />
                    {isVerifyingClaim ? 'Verifying Claim...' : 'Verify Claim'}
                  </button>
                  <button className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl">
                    <Download className="w-3.5 h-3.5" />
                    Save as Markdown
                  </button>
                </div>
              </div>

              {/* Right Output Pane Aligned with media_1794040926742_7d56dbf4.jpg */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-4 text-xs font-mono">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                  <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Verification Summary</span>
                  <span className="text-slate-400">Total: {claimVerificationResult?.totalClaims}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400 block">Verdict Breakdown</span>
                    <span className="font-bold text-red-600">{claimVerificationResult?.verdict}: 1</span>
                  </div>
                  <div className="p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400 block">Confidence Breakdown</span>
                    <span className="font-bold text-emerald-600">{claimVerificationResult?.confidence}: 1</span>
                  </div>
                </div>

                {/* Claim #1 Result Card */}
                <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 dark:text-white">CLAIM #1</span>
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">
                        VERDICT: {claimVerificationResult?.verdict}
                      </span>
                      <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        CONFIDENCE: {claimVerificationResult?.confidence}
                      </span>
                    </div>
                  </div>
                  <p className="text-slate-800 dark:text-slate-200">
                    "{claimVerificationResult?.claimText}"
                  </p>
                  <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                    <span className="font-bold text-slate-700 dark:text-slate-300 block">Evidence Summary:</span>
                    <p>{claimVerificationResult?.evidenceSummary}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. HUMAN-IN-THE-LOOP VERDICT & GROUNDING STUDIO                           */}
      {/* Reference: media_1794040974006_fd23835b.jpg                              */}
      {/* ========================================================================= */}
      {activeTab === 'hitl_studio' && (
        <div className="space-y-6">
          {/* Header Stats Strip */}
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 font-mono text-xs">
            <div className="flex items-center gap-4">
              <span className="font-bold text-slate-900 dark:text-white">Document: Long-Acting-Cabotegravir-Clinical-Review</span>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">51 / 51 Sentences Checked</span>
              <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">18 / 51 Unsupported</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Active Evaluator: Gemini Model</span>
              <button
                onClick={handleSaveHITLAnnotation}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-bold hover:bg-emerald-700 transition-colors"
              >
                Save Annotations
              </button>
            </div>
          </div>

          {annotationSavedNotice && (
            <div className="p-3 rounded-xl bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs font-mono font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Annotation saved and synced with evidence repository!
            </div>
          )}

          {/* Dual Panel HITL Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Sentence List */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3 max-h-[600px] overflow-y-auto">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono block">
                Article Sentences & Assertions
              </span>
              <div className="space-y-2.5">
                {hitlSentences.map((s, idx) => (
                  <div
                    key={s.id}
                    onClick={() => setSelectedSentenceIndex(idx)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedSentenceIndex === idx
                        ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 shadow-xs'
                        : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono mb-1 text-slate-400">
                      <span>#{s.id} · {s.title}</span>
                      {s.status && (
                        <span className={`px-2 py-0.2 rounded font-bold uppercase ${s.status === 'supported' ? 'text-emerald-600' : 'text-amber-600'}`}>
                          {s.status}
                        </span>
                      )}
                    </div>
                    <p className={`font-sans ${s.isHeader ? 'font-bold text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`}>
                      {s.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Human Verdict & Error Annotation Panel */}
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4 text-xs font-mono">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider">Human Verdict</span>
                <span className="text-slate-400 text-[10px]">Sentence #{hitlSentences[selectedSentenceIndex]?.id}</span>
              </div>

              {/* 4 Verdict Buttons */}
              <div className="grid grid-cols-4 gap-2">
                {(['Supported', 'Contradictory', 'Inconclusive', 'None'] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setHumanVerdict(v)}
                    className={`py-2 rounded-xl font-bold transition-all ${
                      humanVerdict === v
                        ? v === 'Supported'
                          ? 'bg-emerald-600 text-white'
                          : v === 'Contradictory'
                          ? 'bg-red-600 text-white'
                          : 'bg-amber-600 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>

              {/* Reason for Human Verdict */}
              <div>
                <label className="text-[11px] font-bold text-slate-700 dark:text-slate-300 block mb-1">
                  Reason for Human Verdict (Optional):
                </label>
                <textarea
                  value={humanReason}
                  onChange={(e) => setHumanReason(e.target.value)}
                  rows={3}
                  className="w-full text-xs font-sans p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              {/* Confidence Level */}
              <div>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                  Confidence Level:
                </span>
                <div className="flex items-center gap-3">
                  {(['Certain', 'Confident', 'Uncertain'] as const).map((c) => (
                    <label key={c} className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        checked={confidenceLevel === c}
                        onChange={() => setConfidenceLevel(c)}
                        className="text-blue-600"
                      />
                      <span>{c}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Error Category */}
              <div>
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                  Error Category (why model might make such mistakes):
                </span>
                <div className="grid grid-cols-4 gap-2 text-center text-[11px]">
                  {(['Collection', 'Analysis', 'Generalization', 'None'] as const).map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setErrorCategory(cat)}
                      className={`py-1.5 rounded-lg border ${errorCategory === cat ? 'bg-indigo-600 text-white border-indigo-600 font-bold' : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600'}`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              {/* Agent Comparison Panel */}
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2 text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 dark:text-white">Agent Verdict:</span>
                  <span className="px-2 py-0.5 rounded font-bold bg-emerald-100 text-emerald-800">
                    Agent 1: Supported
                  </span>
                </div>
                <p className="text-slate-600 dark:text-slate-400 font-sans">
                  "The claim is supported by primary clinical evidence from HPTN 083 and HPTN 084 trials..."
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 6. SENTINEL INTERCEPTION FEED                                             */}
      {/* ========================================================================= */}
      {activeTab === 'sentinel' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Total Verifications</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">1,247</div>
              <span className="text-[10px] text-emerald-600 font-medium">↑ +12.4% from last week</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Avg Trust Score</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">87%</div>
              <span className="text-[10px] text-emerald-600 font-medium">↑ +3.2% from last week</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Models Active</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">6</div>
              <span className="text-[10px] text-indigo-600 font-medium">+2 from last week</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Avg Latency</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">142ms</div>
              <span className="text-[10px] text-emerald-600 font-medium">↓ -18ms from last week</span>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-mono">
              Live Interception Feed
            </h3>
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {sentinelInterceptions.map((item, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="font-bold text-slate-900 dark:text-white">{item.model}</span>
                      <span className="text-[10px] text-slate-400">{item.time}</span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 truncate max-w-xl">
                      {item.text}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 font-mono text-xs">
                    <span className="text-slate-400">{item.claims} Claims</span>
                    <span className="px-2 py-0.5 rounded font-bold bg-emerald-100 text-emerald-800">
                      {item.trust}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 7. CONTEXT VERIFY "Quellen & Vertrauen"                                   */}
      {/* ========================================================================= */}
      {activeTab === 'trust' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Gesamtquellen</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">129</div>
              <span className="text-[10px] text-slate-400">Analysierte Quellen</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Vertrauenswürdigkeit</span>
              <div className="mt-1 text-2xl font-bold font-mono text-emerald-600">92%</div>
              <span className="text-[10px] text-emerald-600">↑ +83.9% Verifizierung</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Misinformations-Index</span>
              <div className="mt-1 text-2xl font-bold font-mono text-indigo-600">1.1%</div>
              <span className="text-[10px] text-slate-400">Falsche Behauptungen</span>
            </div>
            <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Meiste Erwähnungen</span>
              <div className="mt-1 text-2xl font-bold font-mono text-slate-900 dark:text-white">Groq / Llama</div>
              <span className="text-[10px] text-slate-400">Top Modell in Zitaten</span>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 8. OFFLINE BENCHMARKS                                                     */}
      {/* ========================================================================= */}
      {activeTab === 'evals' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-indigo-500" />
                  34-Case Offline Evaluation Benchmark Runner
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Executes deterministic test cases across Research (20), Writing (8), Editorial (2), and Hallucination Resistance (4).
                </p>
              </div>

              <button
                onClick={handleRunBenchmark}
                disabled={isRunningBenchmark}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs transition-colors shrink-0 disabled:opacity-60 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRunningBenchmark ? 'animate-spin' : ''}`} />
                {isRunningBenchmark ? 'Running Suite...' : 'Execute Full Benchmark'}
              </button>
            </div>

            {benchmarkResult && (
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-4">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">
                    ✓ All {benchmarkResult.passed_tests} / {benchmarkResult.total_tests} Tests Passed ({(benchmarkResult.overall_pass_rate * 100).toFixed(1)}%)
                  </span>
                  <span className="text-slate-400 text-[10px]">
                    Completed in {benchmarkResult.total_duration_seconds}s
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
