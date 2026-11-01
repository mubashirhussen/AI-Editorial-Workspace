import React, { useState, useEffect } from 'react';
import {
  Network,
  Sparkles,
  Layers,
  AlertTriangle,
  TrendingUp,
  ShieldCheck,
  FileText,
  Search,
  Filter,
  ExternalLink,
  Copy,
  Check,
  ChevronRight,
  Info,
  Clock,
  ArrowRight
} from 'lucide-react';
import { intelligenceService } from '../../services/intelligenceService';
import {
  EntityItem,
  IntelClaimItem,
  RelationshipItem,
  ContradictionItem,
  TrendItem,
  KnowledgeGraphResponse,
  EntityType,
  EvidenceClassification
} from '../../types/intelligence';
import { useToast } from '../common/Toast';

interface Props {
  projectId: string;
  sourceCount: number;
}

export const ResearchIntelligenceDashboard: React.FC<Props> = ({ projectId, sourceCount }) => {
  const { success, error, info } = useToast();
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'entities' | 'claims' | 'relationships' | 'contradictions' | 'trends'>('overview');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loading, setLoading] = useState(false);

  // Data states
  const [entities, setEntities] = useState<EntityItem[]>([]);
  const [claims, setClaims] = useState<IntelClaimItem[]>([]);
  const [relationships, setRelationships] = useState<RelationshipItem[]>([]);
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([]);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [graphData, setGraphData] = useState<KnowledgeGraphResponse | null>(null);

  // Filters
  const [entityFilter, setEntityFilter] = useState<string>('ALL');
  const [claimFilter, setClaimFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      loadAllIntelligenceData();
    }
  }, [projectId]);

  const loadAllIntelligenceData = async () => {
    try {
      setLoading(true);
      const [ents, cls, rels, contras, trs, gr] = await Promise.all([
        intelligenceService.getEntities(projectId).catch(() => []),
        intelligenceService.getClaims(projectId).catch(() => []),
        intelligenceService.getRelationships(projectId).catch(() => []),
        intelligenceService.getContradictions(projectId).catch(() => []),
        intelligenceService.getTrends(projectId).catch(() => []),
        intelligenceService.getKnowledgeGraph(projectId).catch(() => null)
      ]);
      setEntities(ents);
      setClaims(cls);
      setRelationships(rels);
      setContradictions(contras);
      setTrends(trs);
      setGraphData(gr);
    } catch (err: any) {
      console.error('Failed to load intelligence data', err);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      const res = await intelligenceService.analyzeProject(projectId);
      success(res.summary || 'Cross-source intelligence discovery completed!');
      await loadAllIntelligenceData();
    } catch (err: any) {
      error(err.response?.data?.detail || 'Intelligence analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const copyForEditorial = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    info('Copied verified evidence reference to clipboard for Editorial Studio');
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredEntities = entities.filter((ent) => {
    const matchesType = entityFilter === 'ALL' || ent.entity_type === entityFilter;
    const matchesSearch =
      ent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ent.normalized_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const filteredClaims = claims.filter((c) => {
    const matchesClass = claimFilter === 'ALL' || c.evidence_classification === claimFilter;
    const matchesSearch =
      c.claim_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.entity_references.some((e) => e.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesClass && matchesSearch;
  });

  const getClassificationBadge = (classification: EvidenceClassification) => {
    switch (classification) {
      case 'DIRECTLY_STATED':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">Directly Stated</span>;
      case 'REPORTED_BY_SOURCE':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">Reported by Source</span>;
      case 'INFERENCE':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">Inference</span>;
      case 'UNVERIFIED':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">Unverified / Rumor</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Trigger */}
      <div className="bg-slate-900 text-white rounded-xl p-6 shadow-md border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Network className="w-5 h-5 text-indigo-400" />
            <h2 className="text-xl font-bold tracking-tight">Research Intelligence & Knowledge Graph</h2>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono">
              Phase 25
            </span>
          </div>
          <p className="text-slate-300 text-sm max-w-2xl">
            Extracts entities, evidentiary claims, cross-source contradictions, and corroborated trends across all research sources.
            Every claim and relational edge is traceable to supporting source excerpts.
          </p>
        </div>

        <button
          onClick={runAnalysis}
          disabled={isAnalyzing || sourceCount === 0}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow transition-all whitespace-nowrap"
        >
          {isAnalyzing ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Analyzing Intelligence...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Run Intelligence Discovery</span>
            </>
          )}
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Entities</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{entities.length}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Claims</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{claims.length}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Relationships</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{relationships.length}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Contradictions</div>
          <div className="text-2xl font-bold text-rose-600 mt-1">{contradictions.length}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Trends</div>
          <div className="text-2xl font-bold text-blue-600 mt-1">{trends.length}</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-medium text-slate-500 uppercase tracking-wider">Graph Nodes</div>
          <div className="text-2xl font-bold text-indigo-600 mt-1">{graphData?.stats?.total_nodes || 0}</div>
        </div>
      </div>

      {/* Sub Navigation Bar */}
      <div className="flex border-b border-slate-200 gap-2 overflow-x-auto pb-1 text-sm">
        <button
          onClick={() => setActiveSubTab('overview')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'overview'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Knowledge Graph Overview
        </button>
        <button
          onClick={() => setActiveSubTab('entities')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'entities'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Extracted Entities ({entities.length})
        </button>
        <button
          onClick={() => setActiveSubTab('claims')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'claims'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Evidentiary Claims ({claims.length})
        </button>
        <button
          onClick={() => setActiveSubTab('relationships')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'relationships'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Semantic Relationships ({relationships.length})
        </button>
        <button
          onClick={() => setActiveSubTab('contradictions')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'contradictions'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Contradictions & Gaps ({contradictions.length})
        </button>
        <button
          onClick={() => setActiveSubTab('trends')}
          className={`px-4 py-2 font-medium border-b-2 transition-all whitespace-nowrap ${
            activeSubTab === 'trends'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          Corroborated Trends ({trends.length})
        </button>
      </div>

      {/* Tab 1: Knowledge Graph Overview */}
      {activeSubTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900 mb-2">Relational Knowledge Network</h3>
            <p className="text-slate-600 text-sm mb-4">
              Visual overview of entities, semantic relational edges, and source citations connected within this project.
            </p>

            {graphData && graphData.nodes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Nodes Card */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-sm text-slate-800">Primary Graph Entities</span>
                    <span className="text-xs text-slate-500">{graphData.nodes.length} nodes</span>
                  </div>
                  <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto pr-1">
                    {graphData.nodes.slice(0, 30).map((n) => (
                      <div
                        key={n.id}
                        className="px-2.5 py-1 rounded-md text-xs font-medium border bg-white shadow-xs flex items-center gap-1.5"
                      >
                        <span className="w-2 h-2 rounded-full bg-indigo-500" />
                        <span className="text-slate-900 font-semibold">{n.label}</span>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider">{n.type}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Edges Card */}
                <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-sm text-slate-800">Verified Relational Edges</span>
                    <span className="text-xs text-slate-500">{graphData.edges.length} edges</span>
                  </div>
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1 text-xs">
                    {graphData.edges.slice(0, 15).map((e) => (
                      <div key={e.id} className="p-2 bg-white rounded border border-slate-200 shadow-2xs">
                        <div className="flex items-center gap-1.5 font-medium text-slate-800 mb-1">
                          <span className="text-indigo-600">{e.source.replace('ent-', '').replace('source-', '')}</span>
                          <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px]">
                            {e.relationship}
                          </span>
                          <span className="text-indigo-600">{e.target.replace('ent-', '').replace('source-', '')}</span>
                        </div>
                        {e.evidence && <div className="text-slate-500 line-clamp-1 italic">"{e.evidence}"</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 border border-dashed rounded-lg">
                No intelligence data discovered yet. Click "Run Intelligence Discovery" above to analyze your sources.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Entities */}
      {activeSubTab === 'entities' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex gap-1 overflow-x-auto w-full sm:w-auto">
              {['ALL', 'COMPANY', 'PERSON', 'AI_MODEL', 'PRODUCT', 'TECHNOLOGY', 'INVESTOR'].map((t) => (
                <button
                  key={t}
                  onClick={() => setEntityFilter(t)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                    entityFilter === t ? 'bg-indigo-600 text-white' : 'bg-white border text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredEntities.map((ent, idx) => (
              <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <h4 className="font-bold text-slate-900 text-sm">{ent.name}</h4>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {ent.entity_type}
                    </span>
                  </div>
                  {ent.normalized_name !== ent.name && (
                    <div className="text-xs text-slate-400 mb-2">Canonical: {ent.normalized_name}</div>
                  )}
                  {ent.supporting_excerpt && (
                    <div className="text-xs text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic line-clamp-3 mb-2">
                      "{ent.supporting_excerpt}"
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-100 mt-2">
                  <span>Confidence: {(ent.confidence * 100).toFixed(0)}%</span>
                  {ent.source_title && <span className="line-clamp-1 max-w-[120px]">{ent.source_title}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Evidentiary Claims */}
      {activeSubTab === 'claims' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 justify-between items-center">
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search claims or entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex gap-1 overflow-x-auto w-full sm:w-auto">
              {['ALL', 'DIRECTLY_STATED', 'REPORTED_BY_SOURCE', 'INFERENCE', 'UNVERIFIED'].map((c) => (
                <button
                  key={c}
                  onClick={() => setClaimFilter(c)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                    claimFilter === c ? 'bg-indigo-600 text-white' : 'bg-white border text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {c.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {filteredClaims.map((claim, idx) => (
              <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-2">
                    {getClassificationBadge(claim.evidence_classification)}
                    {claim.source_title && (
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5" />
                        {claim.source_title}
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => copyForEditorial(`[${claim.source_title || 'Source'}]: "${claim.claim_text}"`, claim.id || String(idx))}
                    className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-medium cursor-pointer"
                  >
                    {copiedId === (claim.id || String(idx)) ? (
                      <>
                        <Check className="w-3.5 h-3.5" /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" /> Copy for Studio
                      </>
                    )}
                  </button>
                </div>

                <div className="text-sm font-medium text-slate-900 mb-2">
                  "{claim.claim_text}"
                </div>

                {claim.entity_references && claim.entity_references.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {claim.entity_references.map((ent, eIdx) => (
                      <span key={eIdx} className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-medium">
                        {ent}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Relationships */}
      {activeSubTab === 'relationships' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {relationships.map((rel, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-1.5 font-bold text-sm text-slate-900">
                  <span className="text-indigo-600">{rel.source_entity_name}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-indigo-600">{rel.target_entity_name}</span>
                </div>
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                  {rel.relationship_type}
                </span>
              </div>
              <p className="text-xs text-slate-700 mb-3">{rel.explanation}</p>
              <div className="p-2.5 bg-slate-50 rounded border border-slate-100 text-xs text-slate-600 italic">
                "{rel.supporting_evidence}"
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 5: Contradictions */}
      {activeSubTab === 'contradictions' && (
        <div className="space-y-4">
          {contradictions.map((cd, idx) => (
            <div key={idx} className="bg-white p-5 rounded-xl border border-rose-200 shadow-xs">
              <div className="flex items-center gap-2 text-rose-700 font-bold text-sm mb-3">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>{cd.disagreement_nature}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="p-3 bg-rose-50/50 rounded-lg border border-rose-100">
                  <div className="text-xs font-bold text-rose-800 mb-1">{cd.source_a_title || 'Source A'}</div>
                  <div className="text-xs text-slate-700 italic">"{cd.claim_a_text}"</div>
                </div>
                <div className="p-3 bg-rose-50/50 rounded-lg border border-rose-100">
                  <div className="text-xs font-bold text-rose-800 mb-1">{cd.source_b_title || 'Source B'}</div>
                  <div className="text-xs text-slate-700 italic">"{cd.claim_b_text}"</div>
                </div>
              </div>

              <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200">
                <div>
                  <span className="font-semibold text-slate-800">Possible Explanations: </span>
                  {cd.possible_explanations}
                </div>
                <div>
                  <span className="font-semibold text-slate-800">Unresolved Editorial Question: </span>
                  {cd.unresolved_questions}
                </div>
              </div>
            </div>
          ))}
          {contradictions.length === 0 && (
            <div className="p-8 text-center text-slate-500 bg-white border border-dashed rounded-lg">
              No conflicting claims or contradictions detected across current sources.
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Trends */}
      {activeSubTab === 'trends' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trends.map((td, idx) => (
            <div key={idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                  <h4 className="font-bold text-slate-900 text-sm">{td.theme}</h4>
                </div>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                  td.is_prediction
                    ? 'bg-amber-50 text-amber-800 border-amber-200'
                    : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                }`}>
                  {td.is_prediction ? 'Forward Prediction' : 'Observed Pattern'}
                </span>
              </div>

              <p className="text-xs text-slate-700 mb-3">{td.evidence_summary}</p>

              <div className="flex flex-wrap gap-1.5 mb-3">
                {td.supporting_source_titles?.map((st, sIdx) => (
                  <span key={sIdx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-medium border border-blue-100">
                    {st}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-100">
                <span>Corroboration Confidence: {(td.confidence * 100).toFixed(0)}%</span>
                <button
                  onClick={() => copyForEditorial(`Trend analysis: ${td.theme} (${td.supporting_source_titles.join(', ')})`, `trend-${idx}`)}
                  className="text-indigo-600 hover:text-indigo-800 font-medium cursor-pointer"
                >
                  {copiedId === `trend-${idx}` ? 'Copied!' : 'Copy to Studio'}
                </button>
              </div>
            </div>
          ))}
          {trends.length === 0 && (
            <div className="p-8 text-center text-slate-500 bg-white border border-dashed rounded-lg col-span-2">
              No recurring cross-source trends meeting the minimum 2-source threshold yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
