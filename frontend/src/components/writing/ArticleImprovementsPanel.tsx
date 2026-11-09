import React, { useState } from 'react';
import { 
  Sparkles, 
  Check, 
  X, 
  RefreshCw, 
  Layers, 
  Search, 
  FileText, 
  SlidersHorizontal, 
  MessageSquare, 
  Image as ImageIcon, 
  TrendingUp, 
  CheckCheck, 
  AlertTriangle, 
  ChevronRight,
  Globe,
  ShieldCheck,
  Languages,
  UserCheck
} from 'lucide-react';
import { WritingIssue, WritingMetrics } from '../../types/writing';
import { Button } from '../common/Button';
import { useToast } from '../common/Toast';

interface ArticleImprovementsPanelProps {
  metrics: WritingMetrics | null;
  issues: WritingIssue[];
  onAcceptIssue: (issue: WritingIssue) => void;
  onRejectIssue: (issue: WritingIssue) => void;
  onAcceptAll: () => void;
  onRewriteSentence: (originalSentence: string, targetTone?: string) => Promise<void>;
  onTriggerAiFeature: (feature: 'humanize' | 'summarize' | 'translate' | 'check_ai') => void;
  selectedRailTab: 'improvements' | 'chat' | 'images' | 'competitor';
  onSelectRailTab: (tab: 'improvements' | 'chat' | 'images' | 'competitor') => void;
  activeIssueTab: 'all' | 'seo' | 'readability' | 'tone';
  onSelectIssueTab: (tab: 'all' | 'seo' | 'readability' | 'tone') => void;
}

export const ArticleImprovementsPanel: React.FC<ArticleImprovementsPanelProps> = ({
  metrics,
  issues,
  onAcceptIssue,
  onRejectIssue,
  onAcceptAll,
  onRewriteSentence,
  onTriggerAiFeature,
  selectedRailTab,
  onSelectRailTab,
  activeIssueTab,
  onSelectIssueTab
}) => {
  const { success, info } = useToast();
  const [rewritingIssueId, setRewritingIssueId] = useState<string | null>(null);

  const readabilityScore = metrics?.readability_score ?? 80;
  const isGoodScore = readabilityScore >= 60;

  // Categorized counts
  const hardToReadIssues = issues.filter(i => i.category === 'long_sentence' || i.category === 'complexity');
  const passiveVoiceIssues = issues.filter(i => i.category === 'passive_voice');
  const complexWordIssues = issues.filter(i => i.category === 'jargon' || i.category === 'filler');

  const seoCount = 1; // e.g. "Add images / headings"
  const readabilityCount = hardToReadIssues.length + passiveVoiceIssues.length;
  const toneCount = complexWordIssues.length;

  const handleRewrite = async (issue: WritingIssue) => {
    try {
      setRewritingIssueId(issue.id);
      await onRewriteSentence(issue.original_text);
      success('Rewrote flagged sentence with higher readability!');
    } catch {
      // handled by parent
    } finally {
      setRewritingIssueId(null);
    }
  };

  return (
    <div className="flex bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md overflow-hidden">
      
      {/* Main Column: Score, Filters, Issues & Statistics */}
      <div className="flex-1 p-5 space-y-5 overflow-y-auto max-h-[780px]">
        
        {/* Header: Article Improvements & Edit targets (Image 4) */}
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
            Article Improvements
          </h3>
          <button
            type="button"
            onClick={() => info('Targets: Word count: 1500-2500, Flesch Reading Ease: >60, Tone: Clear & Authoritative')}
            className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            <SlidersHorizontal className="w-3 h-3" />
            <span>Edit targets</span>
          </button>
        </div>

        {/* Overall Scorecard with Segmented Progress Bar (Image 4) */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                Overall score
              </span>
              <div className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2 mt-0.5">
                <span>{isGoodScore ? 'Good' : 'Needs Polish'}</span>
                <span className="text-xs font-mono font-semibold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                  {Math.round(readabilityScore)}/100
                </span>
              </div>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Tips ^
            </span>
          </div>

          {/* Segmented Color Meter Bar (Image 4) */}
          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden flex">
            <div 
              className="h-full bg-emerald-500 transition-all duration-500" 
              style={{ width: `${Math.min(100, Math.max(15, readabilityScore))}%` }} 
            />
            <div className="h-full bg-blue-400/40" style={{ width: '15%' }} />
          </div>

          {/* Metric Filter Tabs: SEO, Readability, Tone (Image 4) */}
          <div className="flex items-center gap-2 pt-1 text-xs">
            <button
              type="button"
              onClick={() => onSelectIssueTab('seo')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeIssueTab === 'seo'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
              }`}
            >
              SEO {seoCount}
            </button>
            <button
              type="button"
              onClick={() => onSelectIssueTab('readability')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeIssueTab === 'readability'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
              }`}
            >
              Readability {readabilityCount}
            </button>
            <button
              type="button"
              onClick={() => onSelectIssueTab('tone')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeIssueTab === 'tone'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
              }`}
            >
              Tone {toneCount}
            </button>
          </div>
        </div>

        {/* Real-time Statistics Card (Image 3 Notalx style) */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
              Statistics
            </span>
            <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 px-1.5 py-0.5 rounded">
              Ready
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-[10px] text-slate-400 block">Sentences</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100 font-mono">
                {metrics?.sentence_count ?? 0}
              </span>
            </div>
            <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-[10px] text-slate-400 block">Reading Time</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100 font-mono">
                {Math.round((metrics?.reading_time_minutes ?? 0) * 60)}s
              </span>
            </div>
            <div className="p-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-[10px] text-slate-400 block">Word Count</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-100 font-mono">
                {metrics?.word_count ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* AI Features (Beta) Buttons (Image 3 Notalx style) */}
        <div className="p-4 rounded-xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800/60 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300">
                AI Features (BETA)
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => onTriggerAiFeature('humanize')}
              className="p-2 bg-white dark:bg-slate-800 hover:bg-purple-50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5 text-purple-600" />
              <span>Humanize</span>
            </button>
            <button
              type="button"
              onClick={() => onTriggerAiFeature('summarize')}
              className="p-2 bg-white dark:bg-slate-800 hover:bg-purple-50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors"
            >
              <FileText className="w-3.5 h-3.5 text-blue-600" />
              <span>Summarize</span>
            </button>
            <button
              type="button"
              onClick={() => onTriggerAiFeature('translate')}
              className="p-2 bg-white dark:bg-slate-800 hover:bg-purple-50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors"
            >
              <Languages className="w-3.5 h-3.5 text-emerald-600" />
              <span>Translate</span>
            </button>
            <button
              type="button"
              onClick={() => onTriggerAiFeature('check_ai')}
              className="p-2 bg-white dark:bg-slate-800 hover:bg-purple-50 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg font-medium flex items-center justify-center gap-1.5 transition-colors"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
              <span>Check AI Content</span>
            </button>
          </div>
        </div>

        {/* Actionable Content Issues List (Images 4 & 5) */}
        <div className="space-y-4 pt-1">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Content Issues ({issues.length})
            </h4>
            {issues.length > 0 && (
              <button
                type="button"
                onClick={onAcceptAll}
                className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Fix All</span>
              </button>
            )}
          </div>

          <p className="text-[11px] text-slate-500 leading-normal">
            The text is well optimized for your target readability. Fix highlighted issues below for maximum clarity:
          </p>

          {/* Category 1: Rewrite hard-to-read sentences (Images 4 & 5) */}
          {(activeIssueTab === 'all' || activeIssueTab === 'readability') && hardToReadIssues.length > 0 && (
            <div className="space-y-2">
              <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1">
                <span>●</span> Rewrite hard-to-read sentence ({hardToReadIssues.length})
              </span>
              <div className="space-y-2">
                {hardToReadIssues.map((issue, idx) => (
                  <div
                    key={issue.id}
                    className="p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2 text-xs transition-all hover:border-slate-300 shadow-2xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-slate-700 dark:text-slate-200 font-sans italic line-clamp-2">
                        "{issue.original_text.slice(0, 80)}..."
                      </span>
                      <button
                        type="button"
                        disabled={rewritingIssueId === issue.id}
                        onClick={() => handleRewrite(issue)}
                        className="px-2.5 py-1 rounded-md bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] shrink-0 transition-colors flex items-center gap-1"
                      >
                        {rewritingIssueId === issue.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                        <span>Rewrite</span>
                      </button>
                    </div>
                    {issue.suggested_rewrite && (
                      <div className="p-2 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg border border-emerald-200 dark:border-emerald-800 text-[11px] text-emerald-800 dark:text-emerald-200 font-sans flex items-center justify-between">
                        <span>{issue.suggested_rewrite}</span>
                        <button
                          type="button"
                          onClick={() => onAcceptIssue(issue)}
                          className="text-emerald-700 hover:underline font-bold text-[10px] ml-2 shrink-0"
                        >
                          Apply
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Category 2: Consider using active voice (Image 5) */}
          {(activeIssueTab === 'all' || activeIssueTab === 'readability') && passiveVoiceIssues.length > 0 && (
            <div className="space-y-2 pt-1">
              <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <span>●</span> Consider using active voice ({passiveVoiceIssues.length})
              </span>
              <div className="space-y-2">
                {passiveVoiceIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className="p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2 text-xs"
                  >
                    <span className="text-slate-700 dark:text-slate-200 font-sans italic block">
                      "{issue.original_text}"
                    </span>
                    <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-700">
                      <span className="text-[11px] text-slate-500">{issue.suggested_rewrite}</span>
                      <button
                        type="button"
                        onClick={() => onAcceptIssue(issue)}
                        className="px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-semibold text-[10px] hover:bg-amber-100"
                      >
                        Use Active Voice
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Category 3: Replace too complex words (Image 5) */}
          {(activeIssueTab === 'all' || activeIssueTab === 'tone') && complexWordIssues.length > 0 && (
            <div className="space-y-2 pt-1">
              <span className="text-[11px] font-bold text-teal-600 dark:text-teal-400 flex items-center gap-1">
                <span>●</span> Replace too complex words ({complexWordIssues.length})
              </span>
              <div className="space-y-1.5">
                {complexWordIssues.map((issue, idx) => (
                  <div
                    key={issue.id}
                    className="flex items-center justify-between p-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400 font-mono text-[10px]">{idx + 1}</span>
                      <span className="font-semibold text-rose-600 dark:text-rose-400 line-through">
                        {issue.original_text}
                      </span>
                      <span>→</span>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {issue.suggested_rewrite}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => onAcceptIssue(issue)}
                      className="text-[10px] text-blue-600 hover:underline font-semibold"
                    >
                      Replace
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SEO Improvements (Image 4) */}
          {(activeIssueTab === 'all' || activeIssueTab === 'seo') && (
            <div className="space-y-2 pt-1">
              <span className="text-[11px] font-bold text-blue-600 dark:text-blue-400 flex items-center gap-1">
                <span>●</span> SEO Improvements (1)
              </span>
              <div className="p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl flex items-center justify-between text-xs">
                <span className="font-medium text-slate-800 dark:text-slate-200">Add relevant illustrative diagrams</span>
                <button
                  type="button"
                  onClick={() => info('Opening media library to add contextual figures')}
                  className="px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-semibold text-[10px]"
                >
                  Add Images
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Far Right Vertical Tool Tab Rail (Image 4: Improvements, AI chat, Images, Competitor data) */}
      <div className="w-12 bg-slate-100/80 dark:bg-slate-800/80 border-l border-slate-200 dark:border-slate-700/80 flex flex-col items-center py-4 space-y-5">
        <button
          type="button"
          onClick={() => onSelectRailTab('improvements')}
          className={`p-2 rounded-xl transition-all ${
            selectedRailTab === 'improvements'
              ? 'bg-blue-600 text-white shadow-xs'
              : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
          title="Article Improvements"
        >
          <Layers className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => onSelectRailTab('chat')}
          className={`p-2 rounded-xl transition-all ${
            selectedRailTab === 'chat'
              ? 'bg-purple-600 text-white shadow-xs'
              : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
          title="AI Assistant Chat"
        >
          <MessageSquare className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => onSelectRailTab('images')}
          className={`p-2 rounded-xl transition-all ${
            selectedRailTab === 'images'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
          title="Images & Media"
        >
          <ImageIcon className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => onSelectRailTab('competitor')}
          className={`p-2 rounded-xl transition-all ${
            selectedRailTab === 'competitor'
              ? 'bg-amber-600 text-white shadow-xs'
              : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
          title="Competitor & Market Research Data"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

