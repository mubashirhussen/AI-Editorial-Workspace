import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  FileCheck,
  RefreshCw,
  ExternalLink,
  BookOpen,
  Filter,
  Search,
  Sparkles,
  Layers,
  ArrowRight,
  Clock,
  Check,
  X,
  FileText,
  TrendingUp,
  Scale
} from 'lucide-react';
import {
  researchReliabilityService,
  ResearchQualityReport,
  ClaimVerification,
  CitationValidationItem,
  SourceCredibility,
  SectionRegenerateResult
} from '../../services/researchReliabilityService';
import { useToast } from '../common/Toast';
import { Button } from '../common/Button';

interface Props {
  projectId: string;
  briefId?: string;
  sourceCount: number;
}

export const ResearchReliabilityPanel: React.FC<Props> = ({ projectId, briefId, sourceCount }) => {
  const { success, error, info } = useToast();
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'claims' | 'citations' | 'sources' | 'regeneration'>('overview');
  const [loading, setLoading] = useState(false);

  // Data states
  const [report, setReport] = useState<ResearchQualityReport | null>(null);
  const [claims, setClaims] = useState<ClaimVerification[]>([]);
  const [citations, setCitations] = useState<CitationValidationItem[]>([]);
  const [claimFilter, setClaimFilter] = useState<string>('ALL');
  const [citationFilter, setCitationFilter] = useState<string>('ALL');

  // Regeneration state
  const [selectedSection, setSelectedSection] = useState<string>('executive_summary');
  const [instructions, setInstructions] = useState<string>('');
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenResult, setRegenResult] = useState<SectionRegenerateResult | null>(null);
  const [isAcceptingRevision, setIsAcceptingRevision] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadReliabilityData();
    }
  }, [projectId, briefId]);

  const loadReliabilityData = async () => {
    try {
      setLoading(true);
      const [repData, claimsData, citData] = await Promise.all([
        researchReliabilityService.getQualityReport(projectId, briefId).catch(() => null),
        researchReliabilityService.verifyProjectClaims(projectId, briefId).catch(() => []),
        researchReliabilityService.getProjectCitations(projectId, briefId).catch(() => [])
      ]);
      setReport(repData);
      setClaims(claimsData);
      setCitations(citData);
    } catch (err: any) {
      console.error('Failed to load research reliability data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateCitations = async () => {
    try {
      setLoading(true);
      const updated = await researchReliabilityService.validateProjectCitations(projectId, briefId);
      setCitations(updated);
      success('Citation audit completed successfully.');
      const rep = await researchReliabilityService.getQualityReport(projectId, briefId);
      setReport(rep);
    } catch (err: any) {
      error('Citation audit failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerRegeneration = async () => {
    if (!briefId) {
      info('Generate a research brief first to enable section-level regeneration.');
      return;
    }
    try {
      setIsRegenerating(true);
      const res = await researchReliabilityService.regenerateSection(projectId, briefId, {
        section_key: selectedSection,
        instructions: instructions.trim() || undefined
      });
      setRegenResult(res);
      success('Evidence-grounded section regenerated!');
    } catch (err: any) {
      error('Regeneration failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleAcceptRevision = async () => {
    if (!regenResult) return;
    try {
      setIsAcceptingRevision(true);
      const res = await researchReliabilityService.acceptRevision(regenResult.revision_id);
      success(`Section revision accepted (Brief v${res.new_version}).`);
      setRegenResult(null);
      await loadReliabilityData();
    } catch (err: any) {
      error('Accepting revision failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsAcceptingRevision(false);
    }
  };

  const filteredClaims = claims.filter(c => {
    if (claimFilter === 'ALL') return true;
    return c.verification_status === claimFilter;
  });

  const filteredCitations = citations.filter(c => {
    if (citationFilter === 'ALL') return true;
    if (citationFilter === 'FABRICATED') return c.is_fabricated;
    return c.status === citationFilter;
  });

  return (
    <div className="bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-emerald-50/50 via-white to-blue-50/30">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-slate-900">Research Reliability & Citation Intelligence</h2>
            {report && (
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                report.overall_quality_grade === 'A' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                report.overall_quality_grade === 'B' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                report.overall_quality_grade === 'C' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                'bg-rose-100 text-rose-800 border border-rose-200'
              }`}>
                Grade: {report.overall_quality_grade}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Grounded claim-to-evidence verification, referential citation validation, and anti-fabrication defense.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadReliabilityData}
            disabled={loading}
            leftIcon={<RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />}
          >
            Re-Audit
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleValidateCitations}
            disabled={loading}
            leftIcon={<FileCheck className="w-4 h-4" />}
          >
            Audit Citations
          </Button>
        </div>
      </div>

      {/* Sub-tab Navigation */}
      <div className="flex border-b border-slate-200 bg-slate-50/60 px-6 gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={`py-3 px-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeSubTab === 'overview'
              ? 'border-emerald-600 text-emerald-700 bg-white shadow-xs rounded-t-lg'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText className="w-4 h-4" />
          Quality Report
        </button>

        <button
          onClick={() => setActiveSubTab('claims')}
          className={`py-3 px-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeSubTab === 'claims'
              ? 'border-emerald-600 text-emerald-700 bg-white shadow-xs rounded-t-lg'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          Claim Verification
          <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded-full text-xs font-bold">
            {claims.length}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('citations')}
          className={`py-3 px-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeSubTab === 'citations'
              ? 'border-emerald-600 text-emerald-700 bg-white shadow-xs rounded-t-lg'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Citation Integrity
          <span className="px-1.5 py-0.2 bg-slate-100 text-slate-600 rounded-full text-xs font-bold">
            {citations.length}
          </span>
        </button>

        <button
          onClick={() => setActiveSubTab('regeneration')}
          className={`py-3 px-4 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeSubTab === 'regeneration'
              ? 'border-emerald-600 text-emerald-700 bg-white shadow-xs rounded-t-lg'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Grounded Regeneration
        </button>
      </div>

      {/* Main Content Body */}
      <div className="p-6">
        {/* SUBTAB 1: OVERVIEW QUALITY REPORT */}
        {activeSubTab === 'overview' && (
          <div className="space-y-6">
            {report ? (
              <>
                {/* Metrics Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                  <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-100">
                    <p className="text-xs font-medium text-emerald-700 uppercase">Evidence Coverage</p>
                    <p className="text-2xl font-bold text-emerald-950 mt-1">{report.evidence_coverage_score}%</p>
                    <div className="w-full bg-emerald-200/50 rounded-full h-1.5 mt-2 overflow-hidden">
                      <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: `${report.evidence_coverage_score}%` }} />
                    </div>
                  </div>

                  <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-100">
                    <p className="text-xs font-medium text-blue-700 uppercase">Citation Health</p>
                    <p className="text-2xl font-bold text-blue-950 mt-1">{report.citation_health_score}%</p>
                    <div className="w-full bg-blue-200/50 rounded-full h-1.5 mt-2 overflow-hidden">
                      <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${report.citation_health_score}%` }} />
                    </div>
                  </div>

                  <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-100">
                    <p className="text-xs font-medium text-indigo-700 uppercase">Supported Claims</p>
                    <p className="text-2xl font-bold text-indigo-950 mt-1">
                      {report.supported_claims} <span className="text-sm font-normal text-slate-500">/ {report.total_claims}</span>
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      {report.unsupported_claims > 0 ? `${report.unsupported_claims} unsupported` : 'All factual claims verified'}
                    </p>
                  </div>

                  <div className="p-4 bg-purple-50/60 rounded-xl border border-purple-100">
                    <p className="text-xs font-medium text-purple-700 uppercase">Corroboration Tier</p>
                    <p className="text-base font-bold text-purple-950 mt-1 truncate">
                      {report.corroboration_summary?.corroboration_tier?.replace(/_/g, ' ') || 'Single Source'}
                    </p>
                    <p className="text-xs text-purple-700 mt-2 truncate">
                      {report.corroboration_summary?.unique_domains_count || 1} independent domains
                    </p>
                  </div>
                </div>

                {/* Audit Findings */}
                <div className="border border-slate-200 rounded-xl p-5 bg-white">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Audit Findings & Actionable Remediation
                  </h3>

                  {report.audit_findings && report.audit_findings.length > 0 ? (
                    <div className="mt-4 space-y-3">
                      {report.audit_findings.map((finding, idx) => (
                        <div
                          key={idx}
                          className={`p-3.5 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                            finding.severity === 'CRITICAL'
                              ? 'bg-rose-50/60 border-rose-200 text-rose-900'
                              : finding.severity === 'HIGH'
                              ? 'bg-amber-50/60 border-amber-200 text-amber-900'
                              : 'bg-slate-50 border-slate-200 text-slate-800'
                          }`}
                        >
                          <div className="flex items-start gap-2.5">
                            <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase mt-0.5 ${
                              finding.severity === 'CRITICAL' ? 'bg-rose-200 text-rose-900' :
                              finding.severity === 'HIGH' ? 'bg-amber-200 text-amber-900' : 'bg-slate-200 text-slate-700'
                            }`}>
                              {finding.severity}
                            </span>
                            <div>
                              <p className="text-sm font-semibold">{finding.finding}</p>
                              <p className="text-xs opacity-85 mt-0.5">Remediation: {finding.remediation}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 bg-emerald-50/60 rounded-lg border border-emerald-100 text-emerald-800 text-sm mt-3 flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                      Zero audit warnings. All factual claims are grounded and citations are verified against primary sources.
                    </div>
                  )}

                  {/* Limitations Statement */}
                  {report.limitations_summary && (
                    <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <p className="text-xs font-bold text-slate-600 uppercase">Methodological Limitations</p>
                      <p className="text-xs text-slate-600 mt-1">{report.limitations_summary}</p>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-12 text-slate-500">
                <ShieldCheck className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="font-medium text-slate-700">No Quality Report Generated</p>
                <p className="text-sm mt-1">Generate a research brief or click "Re-Audit" to evaluate source grounding.</p>
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 2: CLAIM-TO-EVIDENCE VERIFICATION */}
        {activeSubTab === 'claims' && (
          <div className="space-y-4">
            {/* Filter Pills */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Status:</span>
                {(['ALL', 'SUPPORTED', 'PARTIALLY_SUPPORTED', 'UNSUPPORTED', 'CONTRADICTED', 'NOT_APPLICABLE'] as const).map(st => (
                  <button
                    key={st}
                    onClick={() => setClaimFilter(st)}
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                      claimFilter === st
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
              <span className="text-xs text-slate-500">{filteredClaims.length} statements evaluated</span>
            </div>

            {filteredClaims.length > 0 ? (
              <div className="space-y-3">
                {filteredClaims.map((claim) => (
                  <div
                    key={claim.id}
                    className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-2xs"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                            claim.verification_status === 'SUPPORTED' ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                            claim.verification_status === 'PARTIALLY_SUPPORTED' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                            claim.verification_status === 'UNSUPPORTED' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                            claim.verification_status === 'CONTRADICTED' ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                            'bg-slate-100 text-slate-600 border border-slate-200'
                          }`}>
                            {claim.verification_status.replace(/_/g, ' ')}
                          </span>
                          <span className="text-xs font-semibold text-slate-500 uppercase px-2 py-0.5 bg-slate-50 rounded">
                            {claim.claim_type}
                          </span>
                          {claim.claim_location && (
                            <span className="text-xs text-slate-400">({claim.claim_location})</span>
                          )}
                        </div>

                        <p className="text-sm font-semibold text-slate-900">{claim.claim_text}</p>
                        <p className="text-xs text-slate-500 mt-1 italic">{claim.explanation}</p>
                      </div>

                      <div className="text-right shrink-0">
                        <span className="text-xs font-mono font-bold text-slate-600">
                          {Math.round(claim.confidence * 100)}% match
                        </span>
                      </div>
                    </div>

                    {/* Supporting Evidence Passage */}
                    {claim.supporting_evidence && claim.supporting_evidence.length > 0 && (
                      <div className="mt-3 p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
                        <p className="text-xs font-bold text-emerald-900 uppercase flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          Grounded Evidence Excerpt:
                        </p>
                        <p className="text-xs text-emerald-950 mt-1 leading-relaxed">
                          "{claim.supporting_evidence[0].excerpt}"
                        </p>
                        {claim.supporting_evidence[0].source_title && (
                          <p className="text-2xs text-emerald-700 mt-1 font-semibold">
                            — Source: {claim.supporting_evidence[0].source_title}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Conflicting Contradiction */}
                    {claim.conflicting_evidence && claim.conflicting_evidence.length > 0 && (
                      <div className="mt-3 p-3 bg-rose-50/50 rounded-lg border border-rose-100">
                        <p className="text-xs font-bold text-rose-900 uppercase flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                          Material Contradiction in Ingested Literature:
                        </p>
                        <p className="text-xs text-rose-950 mt-1">
                          "{claim.conflicting_evidence[0].disagreement || 'Conflicting figures or dates identified in literature.'}"
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                <CheckCircle2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="font-medium text-slate-700">No Claims Found Matching Filter</p>
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 3: CITATION VALIDATION */}
        {activeSubTab === 'citations' && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Filter:</span>
                {(['ALL', 'VALID', 'INVALID', 'BROKEN', 'FABRICATED'] as const).map(st => (
                  <button
                    key={st}
                    onClick={() => setCitationFilter(st)}
                    className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                      citationFilter === st
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
              <span className="text-xs text-slate-500">{filteredCitations.length} citations audited</span>
            </div>

            {filteredCitations.length > 0 ? (
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm text-slate-600">
                  <thead className="bg-slate-50 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">#</th>
                      <th className="px-4 py-3">Citation Reference</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Anti-Fabrication Check</th>
                      <th className="px-4 py-3 text-right">URL Link</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredCitations.map((cit) => (
                      <tr key={cit.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-4 py-3 font-mono text-xs font-bold text-slate-400">
                          [{cit.citation_number || '•'}]
                        </td>
                        <td className="px-4 py-3">
                          <p className="font-semibold text-slate-900">{cit.citation_text}</p>
                          {cit.validation_details?.reason && (
                            <p className="text-xs text-rose-600 mt-0.5">{cit.validation_details.reason}</p>
                          )}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                            cit.status === 'VALID' ? 'bg-emerald-100 text-emerald-800' :
                            cit.status === 'BROKEN' ? 'bg-rose-100 text-rose-800' :
                            cit.status === 'INVALID' ? 'bg-rose-100 text-rose-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {cit.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {cit.is_fabricated ? (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                              <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                              Fabricated (No Source Match)
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              Verified Source Record
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          {cit.citation_url ? (
                            <a
                              href={cit.citation_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1 text-xs font-semibold"
                            >
                              Open <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-xs text-slate-400">No URL</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="font-medium text-slate-700">No Citations Audited</p>
                <p className="text-sm mt-1">Click "Audit Citations" to evaluate referential integrity.</p>
              </div>
            )}
          </div>
        )}

        {/* SUBTAB 4: GROUNDED SECTION REGENERATION */}
        {activeSubTab === 'regeneration' && (
          <div className="space-y-6">
            <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100 text-sm text-blue-900">
              <p className="font-bold flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-blue-600" />
                Evidence-Constrained Section Regeneration
              </p>
              <p className="text-xs mt-1 text-blue-800">
                Regenerates a selected brief section strictly constrained to verified primary evidence passages.
                Zero ungrounded assertions or hallucinated claims are permitted. Review unified diff before applying.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 uppercase mb-1">Target Section</label>
                <select
                  value={selectedSection}
                  onChange={(e) => setSelectedSection(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="executive_summary">Executive Summary</option>
                  <option value="key_developments">Key Developments</option>
                  <option value="strategic_implications">Strategic Implications</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-bold text-slate-600 uppercase mb-1">Steering Instructions (Optional)</label>
                <input
                  type="text"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Incorporate benchmark accuracy metrics and hardware specifications..."
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500"
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleTriggerRegeneration}
              disabled={isRegenerating || !briefId}
              leftIcon={<Sparkles className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />}
            >
              {isRegenerating ? 'Regenerating with Verified Passages...' : 'Regenerate Section'}
            </Button>

            {/* Regeneration Diff & Acceptance Preview */}
            {regenResult && (
              <div className="mt-6 border border-slate-200 rounded-xl p-5 bg-white space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900 uppercase">Unified Diff Preview</h4>
                    <p className="text-xs text-slate-500">Status: {regenResult.status}</p>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleAcceptRevision}
                    disabled={isAcceptingRevision}
                    leftIcon={<Check className="w-4 h-4" />}
                  >
                    {isAcceptingRevision ? 'Updating Brief...' : 'Accept Revision & Bump Version'}
                  </Button>
                </div>

                <div className="p-3 bg-slate-900 text-emerald-400 font-mono text-xs rounded-lg overflow-x-auto max-h-64 whitespace-pre">
                  {regenResult.diff_summary}
                </div>

                <div className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <p className="text-xs font-bold text-slate-700 uppercase mb-1">Proposed Regenerated Text:</p>
                  <p className="text-sm text-slate-900 whitespace-pre-line leading-relaxed">
                    {regenResult.regenerated_text}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
