import React, { useState, useEffect } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { 
  PenTool, 
  Sparkles, 
  Check, 
  X, 
  CheckCheck, 
  RotateCcw, 
  GitCompare, 
  Save, 
  Loader2, 
  AlertTriangle,
  Info,
  BookOpen,
  ArrowRight,
  Eye,
  Edit3,
  Plus,
  Trash2,
  FileText,
  Clock,
  Layers,
  ChevronDown
} from 'lucide-react';
import { writingService } from '../services/writingService';
import { WritingIssue, WritingMetrics, WritingDraft, DraftComparisonResponse } from '../types';
import { useToast } from '../components/common/Toast';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { StyleIntelligencePanel } from '../components/writing/StyleIntelligencePanel';

export const WritingPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { draftId: routeDraftId } = useParams<{ draftId?: string }>();
  const draftIdParam = routeDraftId || searchParams.get('draftId');
  const navigate = useNavigate();
  const { success, error, info } = useToast();

  const [text, setText] = useState<string>(
    `In order to understand the significance of recent reasoning benchmarks, it is important to note that a large number of tests were conducted by the research team. Due to the fact that retrieval-augmented generation relies on embeddings and vector database search, basically the architecture has the ability to process unstructured technical documentation with high throughput.\n\nFurthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous subordinate clauses and technical parameters without giving the reader a single moment of pause or cognitive respite, which obviously makes it exceedingly difficult to parse in a fast-paced executive editorial environment.\n\nAt the end of the day, founders who implement verifiable evaluation metrics will dominate the commercial landscape, while fragile wrapper applications will face commoditization.`
  );
  const [draftTitle, setDraftTitle] = useState('Production Reasoning Architecture Review');
  const [activeDraftId, setActiveDraftId] = useState<string | null>(draftIdParam || null);
  const [originalDraft, setOriginalDraft] = useState<string>('');
  const [savedContent, setSavedContent] = useState<string>(text);
  
  const [savedDrafts, setSavedDrafts] = useState<WritingDraft[]>([]);
  const [issues, setIssues] = useState<WritingIssue[]>([]);
  const [metrics, setMetrics] = useState<WritingMetrics | null>(null);
  const [overallFeedback, setOverallFeedback] = useState<string>('');
  const [comparisonData, setComparisonData] = useState<DraftComparisonResponse | null>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  
  // Modals
  const [isNewDraftOpen, setIsNewDraftOpen] = useState(false);
  const [newDraftTitle, setNewDraftTitle] = useState('');
  const [newDraftInitialText, setNewDraftInitialText] = useState('');
  const [deleteDraftId, setDeleteDraftId] = useState<string | null>(null);

  const isDirty = text !== savedContent;

  useEffect(() => {
    loadDraftsList();
  }, []);

  useEffect(() => {
    if (draftIdParam) {
      loadDraft(draftIdParam);
    } else if (!activeDraftId) {
      // Analyze default sample on mount
      handleAnalyze(text);
    }
  }, [draftIdParam]);

  const loadDraftsList = async () => {
    try {
      const drafts = await writingService.getDrafts();
      setSavedDrafts(drafts);
    } catch (err) {
      console.error('Failed to load saved drafts', err);
    }
  };

  const loadDraft = async (id: string) => {
    try {
      setIsAnalyzing(true);
      const draft = await writingService.getDraft(id);
      setActiveDraftId(draft.id);
      setDraftTitle(draft.title);
      const activeContent = draft.revised_content || draft.original_content;
      setText(activeContent);
      setSavedContent(activeContent);
      setOriginalDraft(draft.original_content);
      
      // Update route
      navigate(`/writing/${draft.id}`, { replace: true });

      // Run analysis
      await handleAnalyze(activeContent, draft.id);
    } catch (err) {
      console.error('Failed to load draft', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyze = async (contentToAnalyze: string, explicitDraftId?: string) => {
    try {
      setIsAnalyzing(true);
      const res = await writingService.analyzeWriting({
        text: contentToAnalyze,
        title: draftTitle,
        draft_id: explicitDraftId || activeDraftId || undefined,
      });

      if (res.draft_id && res.draft_id !== activeDraftId) {
        setActiveDraftId(res.draft_id);
        navigate(`/writing/${res.draft_id}`, { replace: true });
        loadDraftsList();
      }
      setIssues(res.issues);
      setMetrics(res.metrics);
      setOverallFeedback(res.overall_feedback);
      if (!originalDraft) {
        setOriginalDraft(contentToAnalyze);
      }
      info('Writing quality audit completed.');
    } catch (err: any) {
      error(err.message || 'Failed to analyze text');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAcceptSuggestion = async (issue: WritingIssue) => {
    if (!activeDraftId) {
      await handleAnalyze(text);
      return;
    }

    try {
      const res = await writingService.acceptSuggestion(activeDraftId, issue.id);
      if (res.success) {
        setText(res.revised_content);
        setSavedContent(res.revised_content);
        setIssues((prev) =>
          prev.map((i) => (i.id === issue.id ? { ...i, status: 'accepted' } : i))
        );
        if (res.metrics) {
          setMetrics(res.metrics);
        }
        success(`Applied rewrite for ${issue.category.replace('_', ' ')}.`);
        
        // Refresh comparison if open
        if (showCompare) {
          fetchComparison(activeDraftId);
        }
      }
    } catch (err: any) {
      error(err.message || 'Failed to accept suggestion');
    }
  };

  const handleRejectSuggestion = async (issue: WritingIssue) => {
    if (!activeDraftId) return;

    try {
      const res = await writingService.rejectSuggestion(activeDraftId, issue.id);
      if (res.success) {
        setIssues((prev) =>
          prev.map((i) => (i.id === issue.id ? { ...i, status: 'rejected' } : i))
        );
        info('Suggestion marked as rejected.');
        if (showCompare) {
          fetchComparison(activeDraftId);
        }
      }
    } catch (err: any) {
      error(err.message || 'Failed to reject suggestion');
    }
  };

  const handleAcceptSuggestionId = async (suggestionId: string) => {
    if (!activeDraftId) return;
    try {
      const res = await writingService.acceptSuggestion(activeDraftId, suggestionId);
      if (res.success && res.revised_content) {
        setText(res.revised_content);
        setSavedContent(res.revised_content);
        setIssues((prev) =>
          prev.map((i) => (i.id === suggestionId ? { ...i, status: 'accepted' } : i))
        );
        success('Style correction applied non-destructively!');
      }
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to apply style suggestion');
    }
  };

  const handleRejectSuggestionId = async (suggestionId: string) => {
    if (!activeDraftId) return;
    try {
      await writingService.rejectSuggestion(activeDraftId, suggestionId);
      setIssues((prev) =>
        prev.map((i) => (i.id === suggestionId ? { ...i, status: 'rejected' } : i))
      );
      info('Style suggestion rejected');
    } catch (err: any) {
      error('Failed to reject suggestion');
    }
  };

  const handleAcceptAll = async () => {
    if (!activeDraftId) return;

    try {
      const res = await writingService.acceptAll(activeDraftId);
      if (res.success) {
        setText(res.revised_content);
        setSavedContent(res.revised_content);
        setIssues((prev) =>
          prev.map((i) => (i.status === 'pending' ? { ...i, status: 'accepted' } : i))
        );
        if (res.metrics) {
          setMetrics(res.metrics);
        }
        success(`Applied ${res.applied_count} suggested rewrites!`);
        if (showCompare) {
          fetchComparison(activeDraftId);
        }
      }
    } catch (err: any) {
      error(err.message || 'Failed to accept all');
    }
  };

  const handleSaveDraft = async () => {
    if (!activeDraftId) {
      await handleAnalyze(text);
      return;
    }
    try {
      setIsSaving(true);
      await writingService.updateDraft(activeDraftId, {
        title: draftTitle,
        revised_content: text,
        final_content: text,
        status: 'in_review',
      });
      setSavedContent(text);
      success('Draft saved successfully to workspace database!');
      loadDraftsList();
    } catch (err: any) {
      error(err.message || 'Failed to save draft');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreateNewDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDraftTitle.trim()) return;

    try {
      const draft = await writingService.createDraft({
        title: newDraftTitle.trim(),
        original_content: newDraftInitialText.trim() || 'Start drafting your newsletter article...',
      });
      setIsNewDraftOpen(false);
      setNewDraftTitle('');
      setNewDraftInitialText('');
      success(`Draft "${draft.title}" created.`);
      await loadDraftsList();
      navigate(`/writing/${draft.id}`);
    } catch (err: any) {
      error(err.message || 'Failed to create draft');
    }
  };

  const confirmDeleteDraft = async () => {
    if (!deleteDraftId) return;
    try {
      await writingService.deleteDraft(deleteDraftId);
      success('Draft deleted successfully.');
      setDeleteDraftId(null);
      await loadDraftsList();
      if (activeDraftId === deleteDraftId) {
        setActiveDraftId(null);
        navigate('/writing');
      }
    } catch (err: any) {
      error(err.message || 'Failed to delete draft');
    }
  };

  const fetchComparison = async (draftId: string) => {
    try {
      const data = await writingService.compareDraft(draftId);
      setComparisonData(data);
    } catch (err) {
      console.error('Failed to fetch draft comparison', err);
    }
  };

  const toggleComparison = async () => {
    if (!showCompare && activeDraftId) {
      await fetchComparison(activeDraftId);
    }
    setShowCompare(!showCompare);
  };

  // Group issue counts
  const pendingIssues = issues.filter((i) => i.status === 'pending');
  const countLong = pendingIssues.filter((i) => i.category === 'long_sentence').length;
  const countPassive = pendingIssues.filter((i) => i.category === 'passive_voice').length;
  const countFiller = pendingIssues.filter((i) => i.category === 'filler').length;
  const countJargon = pendingIssues.filter((i) => i.category === 'jargon').length;
  const countRepetition = pendingIssues.filter((i) => i.category === 'repetition').length;
  const countComplexity = pendingIssues.filter((i) => i.category === 'complexity').length;

  const filteredIssues = issues.filter((i) => {
    if (filterCategory === 'all') return true;
    if (filterCategory === 'pending') return i.status === 'pending';
    return i.category === filterCategory;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Writing Assistant & Auditor</h2>
            <Badge variant="success" size="sm">
              6 Deterministic Checks
            </Badge>
            {isDirty && (
              <Badge variant="warning" size="sm">
                Unsaved Edits
              </Badge>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Detects long sentences, passive voice, filler phrases, technical jargon, repetition, and complex paragraphs.
          </p>
        </div>

        {/* Action Controls & Draft Switcher */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Draft Selector Dropdown */}
          <div className="relative">
            <select
              value={activeDraftId || ''}
              onChange={(e) => {
                if (isDirty && !window.confirm('You have unsaved edits in the current draft. Discard and switch?')) {
                  return;
                }
                if (e.target.value) {
                  loadDraft(e.target.value);
                }
              }}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">Select saved draft...</option>
              {savedDrafts.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title} ({d.readability_score ? `Flesch ${Math.round(d.readability_score)}` : 'Draft'})
                </option>
              ))}
            </select>
          </div>

          <Button
            onClick={() => setIsNewDraftOpen(true)}
            variant="outline"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            New Draft
          </Button>

          {activeDraftId && (
            <Button
              onClick={() => setDeleteDraftId(activeDraftId)}
              variant="outline"
              size="sm"
              className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
              title="Delete current draft"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}

          <Button
            onClick={toggleComparison}
            variant="outline"
            size="sm"
            leftIcon={<GitCompare className="w-3.5 h-3.5" />}
          >
            {showCompare ? 'Hide Comparison' : 'Compare Original vs Revised'}
          </Button>

          <Button
            onClick={handleSaveDraft}
            isLoading={isSaving}
            variant="outline"
            size="sm"
            leftIcon={<Save className="w-3.5 h-3.5 text-blue-600" />}
          >
            Save Draft
          </Button>

          <Button
            onClick={() => handleAnalyze(text)}
            isLoading={isAnalyzing}
            variant="primary"
            size="sm"
            leftIcon={<Sparkles className="w-3.5 h-3.5" />}
          >
            Audit Quality
          </Button>
        </div>
      </div>

      {/* Main 2-Column Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Draft Editor & Diff Comparison (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs p-6 space-y-4">
            {/* Draft Title Input */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <input
                type="text"
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                className="text-base font-bold text-slate-900 dark:text-white bg-transparent border-none outline-none focus:ring-0 w-full"
                placeholder="Draft Title..."
              />
              <span className="text-[11px] text-slate-400 font-mono whitespace-nowrap">
                {metrics?.word_count ?? 0} words • {metrics?.sentence_count ?? 0} sentences
              </span>
            </div>

            {/* Comparison Mode vs Standard Editor */}
            {showCompare ? (
              <div className="space-y-4">
                {comparisonData && (
                  <div className="grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-center text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase">Diff Words</span>
                      <div className="font-bold text-slate-800 dark:text-slate-100 mt-0.5">
                        {comparisonData.diff_summary.word_count_delta >= 0 ? `+${comparisonData.diff_summary.word_count_delta}` : comparisonData.diff_summary.word_count_delta}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase">Flesch Delta</span>
                      <div className="font-bold text-emerald-600 mt-0.5">
                        {comparisonData.diff_summary.readability_delta >= 0 ? `+${comparisonData.diff_summary.readability_delta}` : comparisonData.diff_summary.readability_delta}
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase">Accepted / Rejected</span>
                      <div className="font-bold text-blue-600 mt-0.5">
                        {comparisonData.suggestions_applied.accepted} / {comparisonData.suggestions_applied.rejected}
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Original Draft (Immutable)
                    </span>
                    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 text-xs font-serif leading-relaxed text-slate-700 dark:text-slate-300 whitespace-pre-wrap min-h-[350px]">
                      {originalDraft || text}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-600">
                      Revised Draft (Accepted Changes)
                    </span>
                    <div className="p-4 rounded-xl bg-emerald-50/30 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 text-xs font-serif leading-relaxed text-slate-900 dark:text-slate-100 whitespace-pre-wrap min-h-[350px]">
                      {text}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <textarea
                  rows={16}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste or write your newsletter draft here..."
                  className="w-full text-slate-800 dark:text-slate-100 font-serif text-[14px] leading-relaxed p-4 bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-y"
                />

                {/* Overall Feedback Banner */}
                {overallFeedback && (
                  <div className="p-3.5 rounded-xl bg-blue-50/80 dark:bg-blue-950/40 border border-blue-200/80 dark:border-blue-800/80 flex items-start gap-3">
                    <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
                    <p className="text-xs text-blue-900 dark:text-blue-200 leading-relaxed font-sans">
                      {overallFeedback}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Metrics Sidebar & Suggestions (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Readability & Metrics Card */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800 space-y-5">
            {/* Top Grade Box */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-[11px] text-slate-400 font-mono uppercase tracking-wider">
                  Readability Index
                </span>
                <div className="text-xl font-bold text-white mt-0.5">
                  {metrics?.readability_grade || 'Standard'}
                </div>
                <div className="text-[11px] text-slate-400">
                  Flesch Reading Ease: <strong className="text-emerald-400">{metrics?.readability_score ?? '--'}</strong> / 100
                </div>
              </div>
              <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-mono font-bold text-base">
                {metrics?.readability_score ? Math.round(metrics.readability_score) : '--'}
              </div>
            </div>

            {/* Stats Breakdown */}
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/50">
                <div className="text-base font-bold text-slate-100">{metrics?.word_count ?? 0}</div>
                <div className="text-[10px] text-slate-400 uppercase mt-0.5">Words</div>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/50">
                <div className="text-base font-bold text-slate-100">{metrics?.average_sentence_length ?? 0}</div>
                <div className="text-[10px] text-slate-400 uppercase mt-0.5">Avg Words/Sent</div>
              </div>
              <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700/50">
                <div className="text-base font-bold text-slate-100">{metrics?.reading_time_minutes ?? 0}m</div>
                <div className="text-[10px] text-slate-400 uppercase mt-0.5">Read Time</div>
              </div>
            </div>

            {/* Category Counter Pills */}
            <div className="space-y-1.5 pt-1 text-xs">
              <div 
                onClick={() => setFilterCategory(filterCategory === 'filler' ? 'all' : 'filler')}
                className="flex items-center justify-between p-2 rounded-lg bg-purple-950/40 border border-purple-800/50 text-purple-200 cursor-pointer hover:bg-purple-950/70 transition-colors"
              >
                <span><strong>{countFiller}</strong> filler phrases to tighten</span>
                <span className="text-[10px] font-mono uppercase bg-purple-900/60 px-1.5 py-0.5 rounded">Filler</span>
              </div>

              <div 
                onClick={() => setFilterCategory(filterCategory === 'passive_voice' ? 'all' : 'passive_voice')}
                className="flex items-center justify-between p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-emerald-200 cursor-pointer hover:bg-emerald-950/70 transition-colors"
              >
                <span><strong>{countPassive}</strong> passive constructions</span>
                <span className="text-[10px] font-mono uppercase bg-emerald-900/60 px-1.5 py-0.5 rounded">Passive</span>
              </div>

              <div 
                onClick={() => setFilterCategory(filterCategory === 'jargon' ? 'all' : 'jargon')}
                className="flex items-center justify-between p-2 rounded-lg bg-blue-950/40 border border-blue-800/50 text-blue-200 cursor-pointer hover:bg-blue-950/70 transition-colors"
              >
                <span><strong>{countJargon}</strong> jargon phrases to clarify</span>
                <span className="text-[10px] font-mono uppercase bg-blue-900/60 px-1.5 py-0.5 rounded">Jargon</span>
              </div>

              <div 
                onClick={() => setFilterCategory(filterCategory === 'long_sentence' ? 'all' : 'long_sentence')}
                className="flex items-center justify-between p-2 rounded-lg bg-amber-950/40 border border-amber-800/50 text-amber-200 cursor-pointer hover:bg-amber-950/70 transition-colors"
              >
                <span><strong>{countLong}</strong> long sentences (&gt;25 words)</span>
                <span className="text-[10px] font-mono uppercase bg-amber-900/60 px-1.5 py-0.5 rounded">Length</span>
              </div>

              <div 
                onClick={() => setFilterCategory(filterCategory === 'repetition' ? 'all' : 'repetition')}
                className="flex items-center justify-between p-2 rounded-lg bg-indigo-950/40 border border-indigo-800/50 text-indigo-200 cursor-pointer hover:bg-indigo-950/70 transition-colors"
              >
                <span><strong>{countRepetition}</strong> repeated sentence openers</span>
                <span className="text-[10px] font-mono uppercase bg-indigo-900/60 px-1.5 py-0.5 rounded">Repetition</span>
              </div>

              <div 
                onClick={() => setFilterCategory(filterCategory === 'complexity' ? 'all' : 'complexity')}
                className="flex items-center justify-between p-2 rounded-lg bg-rose-950/40 border border-rose-800/50 text-rose-200 cursor-pointer hover:bg-rose-950/70 transition-colors"
              >
                <span><strong>{countComplexity}</strong> dense paragraphs</span>
                <span className="text-[10px] font-mono uppercase bg-rose-900/60 px-1.5 py-0.5 rounded">Density</span>
              </div>
            </div>
          </div>

          {/* Editorial Style Intelligence Panel */}
          <StyleIntelligencePanel
            draftId={activeDraftId || undefined}
            currentContent={text}
            onAcceptSuggestion={handleAcceptSuggestionId}
            onRejectSuggestion={handleRejectSuggestionId}
          />

          {/* Interactive Suggestions Panel */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                Editorial Suggestions ({pendingIssues.length} pending)
              </h3>
              {pendingIssues.length > 0 && (
                <button
                  onClick={handleAcceptAll}
                  className="flex items-center gap-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span>Accept All</span>
                </button>
              )}
            </div>

            {filteredIssues.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                No active issues in this category. Click "Audit Quality" to re-scan.
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                {filteredIssues.map((issue) => (
                  <div
                    key={issue.id}
                    className={`p-3.5 rounded-xl border text-xs space-y-2.5 transition-all ${
                      issue.status === 'accepted'
                        ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 opacity-60'
                        : issue.status === 'rejected'
                        ? 'bg-slate-50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-800 opacity-40 line-through'
                        : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 shadow-2xs'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full ${
                        issue.category === 'long_sentence' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' :
                        issue.category === 'passive_voice' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                        issue.category === 'filler' ? 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300' :
                        issue.category === 'repetition' ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300' :
                        issue.category === 'complexity' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' :
                        'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
                      }`}>
                        {issue.category.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] text-slate-400 capitalize">
                        {issue.status}
                      </span>
                    </div>

                    {/* Original Target Text */}
                    <div className="text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-800 p-2 rounded border border-slate-100 dark:border-slate-700 font-mono text-[11px]">
                      "{issue.original_text}"
                    </div>

                    {/* Explanation */}
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-normal">
                      {issue.explanation}
                    </p>

                    {/* Suggested Rewrite */}
                    {issue.suggested_rewrite && (
                      <div className="p-2 rounded bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-950 dark:text-emerald-200 font-serif text-[12px]">
                        <span className="text-[10px] font-sans font-bold text-emerald-700 dark:text-emerald-400 uppercase block mb-0.5">Suggested Rewrite:</span>
                        {issue.suggested_rewrite}
                      </div>
                    )}

                    {/* Accept / Reject Buttons */}
                    {issue.status === 'pending' && (
                      <div className="flex items-center justify-end gap-2 pt-1">
                        <Button
                          onClick={() => handleRejectSuggestion(issue)}
                          variant="ghost"
                          size="sm"
                          leftIcon={<X className="w-3.5 h-3.5" />}
                        >
                          Reject
                        </Button>
                        <Button
                          onClick={() => handleAcceptSuggestion(issue)}
                          variant="primary"
                          size="sm"
                          leftIcon={<Check className="w-3.5 h-3.5" />}
                        >
                          Accept & Apply
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New Draft Modal */}
      <Modal
        isOpen={isNewDraftOpen}
        onClose={() => setIsNewDraftOpen(false)}
        title="Create Writing Draft"
        description="Initialize a new draft for sentence audits, readability analysis, and style refinement."
      >
        <form onSubmit={handleCreateNewDraft} className="space-y-4">
          <Input
            label="Draft Title"
            placeholder="e.g. Weekly AI Edition #43"
            value={newDraftTitle}
            onChange={(e) => setNewDraftTitle(e.target.value)}
            required
            autoFocus
          />
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Initial Content (Optional)
            </label>
            <textarea
              rows={4}
              value={newDraftInitialText}
              onChange={(e) => setNewDraftInitialText(e.target.value)}
              placeholder="Paste initial text to audit..."
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsNewDraftOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={!newDraftTitle.trim()}>
              Create Draft
            </Button>
          </div>
        </form>
      </Modal>

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteDraftId)}
        title="Delete Writing Draft"
        message="Are you sure you want to delete this draft and all associated suggestion logs? This action is permanent."
        confirmLabel="Delete Draft"
        isDestructive={true}
        onConfirm={confirmDeleteDraft}
        onCancel={() => setDeleteDraftId(null)}
      />
    </div>
  );
};
