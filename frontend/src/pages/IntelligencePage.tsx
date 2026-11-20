import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Lightbulb, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  TrendingUp, 
  ShieldCheck, 
  RefreshCw, 
  Play, 
  ThumbsUp, 
  ThumbsDown, 
  ArrowRight,
  Filter,
  Check,
  X,
  Layers,
  Sparkles,
  Zap,
  Info
} from 'lucide-react';
import { 
  productIntelligenceService, 
  IntelligenceOverview, 
  IntelligenceInsight, 
  IntelligenceRecommendation,
  ImpactEvaluation,
  DataQualityReport 
} from '../services/productIntelligenceService';

export const IntelligencePage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<IntelligenceOverview | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'insights' | 'optimization'>('recommendations');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Selected item states
  const [selectedInsight, setSelectedInsight] = useState<IntelligenceInsight | null>(null);
  const [selectedRecForImpact, setSelectedRecForImpact] = useState<IntelligenceRecommendation | null>(null);
  const [impactData, setImpactData] = useState<ImpactEvaluation | null>(null);
  const [loadingImpact, setLoadingImpact] = useState<boolean>(false);

  // Feedback modal state
  const [feedbackRec, setFeedbackRec] = useState<IntelligenceRecommendation | null>(null);
  const [feedbackType, setFeedbackType] = useState<string>('helpful');
  const [feedbackRating, setFeedbackRating] = useState<number>(5);
  const [feedbackComment, setFeedbackComment] = useState<string>('');
  const [submittingFeedback, setSubmittingFeedback] = useState<boolean>(false);

  const loadIntelligenceData = async (silent = false) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const data = await productIntelligenceService.getOverview();
      setOverview(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load product intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntelligenceData();
  }, []);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    try {
      await productIntelligenceService.runAnalysis(30);
      await loadIntelligenceData(true);
    } catch (err: any) {
      alert('Analysis execution failed: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAccept = async (id: string) => {
    try {
      await productIntelligenceService.acceptRecommendation(id, 'Accepted by operator for implementation.');
      await loadIntelligenceData(true);
    } catch (err: any) {
      alert('Failed to accept recommendation: ' + err.message);
    }
  };

  const handleReject = async (id: string) => {
    const reason = prompt('Please enter reason for rejection (optional):', 'Not applicable to current workflow');
    if (reason === null) return;
    try {
      await productIntelligenceService.rejectRecommendation(id, reason);
      await loadIntelligenceData(true);
    } catch (err: any) {
      alert('Failed to reject recommendation: ' + err.message);
    }
  };

  const handleImplement = async (id: string) => {
    try {
      await productIntelligenceService.implementRecommendation(id, 'Implementation completed.');
      await loadIntelligenceData(true);
    } catch (err: any) {
      alert('Failed to update recommendation status: ' + err.message);
    }
  };

  const handleVerify = async (id: string) => {
    try {
      await productIntelligenceService.verifyRecommendation(id, 'Impact demonstrated and certified.');
      await loadIntelligenceData(true);
    } catch (err: any) {
      alert('Failed to verify recommendation: ' + err.message);
    }
  };

  const handleExecuteAutomated = async (rec: IntelligenceRecommendation) => {
    if (!confirm(`Execute safe automated action: "${rec.title}"?`)) return;
    try {
      await productIntelligenceService.executeOptimization('cache_reuse_optimization', rec.id);
      await loadIntelligenceData(true);
      alert('Automated optimization executed successfully.');
    } catch (err: any) {
      alert('Optimization failed: ' + err.message);
    }
  };

  const handleViewImpact = async (rec: IntelligenceRecommendation) => {
    setSelectedRecForImpact(rec);
    setLoadingImpact(true);
    try {
      const imp = await productIntelligenceService.getImpact(rec.id);
      setImpactData(imp);
    } catch (err: any) {
      alert('Failed to calculate impact delta: ' + err.message);
      setSelectedRecForImpact(null);
    } finally {
      setLoadingImpact(false);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackRec) return;
    setSubmittingFeedback(true);
    try {
      await productIntelligenceService.submitFeedback(feedbackRec.id, {
        feedback_type: feedbackType,
        rating: feedbackRating,
        comment: feedbackComment.trim() || undefined
      });
      alert('Feedback recorded. Thank you for refining product intelligence!');
      setFeedbackRec(null);
      setFeedbackComment('');
    } catch (err: any) {
      alert('Could not submit feedback: ' + err.message);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[70vh] flex-col items-center justify-center gap-3">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        <p className="text-sm font-medium text-slate-400">Loading AI Product Intelligence & Optimization Engine...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400 shrink-0" />
            <h3 className="font-bold text-lg text-rose-200">Product Intelligence Unavailable</h3>
          </div>
          <p className="text-sm text-rose-300/80">{error}</p>
          <div>
            <button
              onClick={() => loadIntelligenceData()}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl transition-all"
            >
              Retry Loading
            </button>
          </div>
        </div>
      </div>
    );
  }

  const recommendations = overview?.recommendations || [];
  const filteredRecs = statusFilter === 'ALL' 
    ? recommendations 
    : recommendations.filter(r => r.status === statusFilter);

  const dq = overview?.data_quality;

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">AI Product Intelligence</h1>
              <p className="text-xs text-slate-400">Continuous operational analysis, evidence-backed recommendations & safe optimization</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <span className="text-slate-400">Data Quality:</span>
            <span className={`font-mono font-bold px-2 py-0.5 rounded-md text-[10px] ${
              dq?.status === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              dq?.status === 'WARNING' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
              'bg-slate-800 text-slate-400'
            }`}>
              {dq?.status ?? 'UNKNOWN'} ({dq?.score ?? 0}%)
            </span>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition-all shadow-md shadow-blue-600/20"
          >
            <Play className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Analyzing Telemetry...' : 'Run Analysis'}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Active Detected Insights</span>
            <Lightbulb className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.active_insights_count ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">patterns</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Evidence-backed anomalies</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">High-Priority Actions</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.high_priority_recommendations_count ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">critical</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Immediate impact opportunities</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Verified Improvements</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.implemented_improvements_count ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">verified</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Measured throughput gains</p>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Pending Review</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{overview?.pending_recommendations_count ?? 0}</span>
            <span className="text-[11px] text-slate-500 font-mono">in pipeline</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Awaiting operator sign-off</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'recommendations' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Actionable Recommendations ({recommendations.length})
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'insights' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          Evidence-Backed Insights ({overview?.insights.length ?? 0})
        </button>
        <button
          onClick={() => setActiveTab('optimization')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'optimization' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          Workflow Optimization & Impact
        </button>
      </div>

      {/* TAB 1: Actionable Recommendations */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Prioritized workflow optimizations based on verified analytics:</span>
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Filter status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-slate-300 rounded-lg px-2.5 py-1 text-xs focus:outline-hidden"
              >
                <option value="ALL">All States</option>
                <option value="READY">Ready</option>
                <option value="ACCEPTED">Accepted</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="IMPLEMENTED">Implemented</option>
                <option value="VERIFIED">Verified</option>
                <option value="REJECTED">Rejected</option>
                <option value="DEFERRED">Deferred</option>
              </select>
            </div>
          </div>

          {filteredRecs.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 text-slate-500 text-xs">
              No recommendations matching the selected criteria. Run analysis or log additional workflow events.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRecs.map((rec) => (
                <div key={rec.id} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase font-mono ${
                        rec.priority === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        rec.priority === 'HIGH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                        rec.priority === 'MEDIUM' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {rec.priority} Priority
                      </span>
                      <span className="text-xs font-bold text-slate-400 capitalize px-2 py-0.5 rounded-md bg-slate-800/80">
                        {rec.category.replace('_', ' ')}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500">
                        Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                      </span>
                      {rec.is_automated && (
                        <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                          <Zap className="w-3 h-3" /> Auto-Eligible
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md font-mono ${
                        rec.status === 'VERIFIED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        rec.status === 'IMPLEMENTED' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                        rec.status === 'ACCEPTED' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                        rec.status === 'REJECTED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        'bg-slate-800 text-slate-400'
                      }`}>
                        Status: {rec.status}
                      </span>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-white">{rec.title}</h3>
                    <p className="mt-1 text-xs text-slate-400 leading-relaxed">{rec.description}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/40 text-xs">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-slate-500">Proposed Action:</span>
                      <p className="text-slate-300 mt-0.5">{rec.proposed_action}</p>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase text-slate-500">Expected Benefit:</span>
                      <p className="text-emerald-300 mt-0.5">{rec.expected_benefit}</p>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span>Effort: <strong className="text-slate-200 font-mono">{rec.estimated_effort}</strong></span>
                      <span>Risk: <strong className="text-slate-200 font-mono">{rec.risk_level}</strong></span>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      {rec.status === 'READY' && (
                        <>
                          <button
                            onClick={() => handleAccept(rec.id)}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                          >
                            <Check className="w-3.5 h-3.5" /> Accept
                          </button>
                          <button
                            onClick={() => handleReject(rec.id)}
                            className="px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                          >
                            <X className="w-3.5 h-3.5" /> Reject
                          </button>
                        </>
                      )}

                      {rec.status === 'ACCEPTED' && (
                        <button
                          onClick={() => handleImplement(rec.id)}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" /> Mark Implemented
                        </button>
                      )}

                      {rec.status === 'IMPLEMENTED' && (
                        <>
                          <button
                            onClick={() => handleVerify(rec.id)}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Verify Impact
                          </button>
                          <button
                            onClick={() => handleViewImpact(rec)}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition-all"
                          >
                            View Delta
                          </button>
                        </>
                      )}

                      {rec.is_automated && rec.status !== 'VERIFIED' && rec.status !== 'IMPLEMENTED' && (
                        <button
                          onClick={() => handleExecuteAutomated(rec)}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-all flex items-center gap-1"
                        >
                          <Zap className="w-3.5 h-3.5" /> Run Auto-Fix
                        </button>
                      )}

                      <button
                        onClick={() => setFeedbackRec(rec)}
                        className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs transition-all"
                        title="Provide recommendation feedback"
                      >
                        Feedback
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Evidence-Backed Insights */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <p className="text-xs text-slate-400">Deterministic and AI-assisted insights grounded strictly in validated product telemetry:</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {overview?.insights.map((ins) => (
              <div key={ins.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="text-[10px] font-mono uppercase font-bold text-slate-400">{ins.category}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono ${
                      ins.severity === 'critical' ? 'bg-rose-500/10 text-rose-400' :
                      ins.severity === 'high' ? 'bg-amber-500/10 text-amber-400' :
                      'bg-blue-500/10 text-blue-400'
                    }`}>
                      {ins.severity}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white mt-2.5">{ins.title}</h3>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{ins.description}</p>
                </div>

                <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 space-y-2 text-xs">
                  <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Underlying Evidence:</span>
                  <div className="space-y-1 font-mono text-[11px] text-slate-300">
                    {Object.entries(ins.evidence).map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-slate-400">{k.replace('_', ' ')}:</span>
                        <span className="text-emerald-400 font-semibold">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Workflow Optimization & Impact */}
      {activeTab === 'optimization' && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-6">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400" />
              Workflow Optimization Governance & Impact Measurement
            </h2>
            <p className="text-xs text-slate-400">Pre/post implementation metric comparison verifying real-world throughput gains</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/40">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Research Pipeline</span>
              <p className="text-xs text-slate-300 mt-1">Automatic source pre-validation active to prevent SSRF socket blocks.</p>
              <div className="mt-3 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Optimization Ready
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/40">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Writing Pipeline</span>
              <p className="text-xs text-slate-300 mt-1">Deterministic Linguistic Auditor pre-checks style and word limits.</p>
              <div className="mt-3 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> 9 Checks Active
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/40">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Editorial Studio</span>
              <p className="text-xs text-slate-300 mt-1">Author self-approval protection and peer review auditing.</p>
              <div className="mt-3 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Governance Certified
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Impact Evaluation Modal */}
      {selectedRecForImpact && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Impact Evaluation Delta</h3>
              <button onClick={() => setSelectedRecForImpact(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingImpact ? (
              <div className="py-8 text-center text-slate-400 text-xs">Computing metric delta...</div>
            ) : impactData ? (
              <div className="space-y-4 text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/60">
                  <span className="text-slate-300 font-semibold">Evaluation Status:</span>
                  <span className={`px-2.5 py-0.5 rounded-full font-mono text-[10px] font-bold uppercase ${
                    impactData.evaluation_status === 'IMPROVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    impactData.evaluation_status === 'REGRESSED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    'bg-slate-800 text-slate-300'
                  }`}>
                    {impactData.evaluation_status}
                  </span>
                </div>

                <div className="space-y-2">
                  <span className="text-slate-400 text-[11px] font-mono uppercase font-semibold">Metric Deltas (Current vs Baseline):</span>
                  <div className="space-y-1.5 font-mono text-[11px]">
                    {Object.entries(impactData.metric_delta).map(([k, v]) => (
                      <div key={k} className="flex justify-between p-2 rounded-lg bg-slate-800/40">
                        <span className="text-slate-400">{k.replace('_', ' ')}:</span>
                        <span className={Number(v) > 0 ? "text-emerald-400 font-bold" : Number(v) < 0 ? "text-amber-400 font-bold" : "text-slate-300"}>
                          {Number(v) > 0 ? `+${v}` : v}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {impactData.notes && (
                  <p className="text-[11px] text-slate-400 italic">{impactData.notes}</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400">No impact data available for this recommendation.</p>
            )}
          </div>
        </div>
      )}

      {/* Recommendation Feedback Modal */}
      {feedbackRec && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <form onSubmit={handleSubmitFeedback} className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">Recommendation Feedback</h3>
              <button type="button" onClick={() => setFeedbackRec(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Evaluating: <strong className="text-white">{feedbackRec.title}</strong>
            </p>

            <div className="space-y-1.5 text-xs">
              <label className="text-slate-300 font-medium">Feedback Category</label>
              <select
                value={feedbackType}
                onChange={(e) => setFeedbackType(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-hidden"
              >
                <option value="helpful">Helpful & Relevant</option>
                <option value="irrelevant">Not Applicable to Workflow</option>
                <option value="inaccurate_evidence">Evidence Appears Inaccurate</option>
                <option value="implemented">Implemented with Success</option>
                <option value="difficult">Difficult to Implement</option>
              </select>
            </div>

            <div className="space-y-1.5 text-xs">
              <label className="text-slate-300 font-medium">Relevance Rating (1 - 5)</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setFeedbackRating(star)}
                    className={`flex-1 py-1.5 rounded-lg font-mono font-bold text-xs transition-all ${
                      feedbackRating >= star ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    {star}★
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5 text-xs">
              <label className="text-slate-300 font-medium">Additional Commentary (Optional)</label>
              <textarea
                value={feedbackComment}
                onChange={(e) => setFeedbackComment(e.target.value)}
                placeholder="Share context on how this recommendation performed..."
                rows={3}
                className="w-full bg-slate-800 border border-slate-700 text-slate-200 rounded-xl p-3 text-xs focus:outline-hidden resize-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setFeedbackRec(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingFeedback}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-all"
              >
                {submittingFeedback ? 'Saving...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
