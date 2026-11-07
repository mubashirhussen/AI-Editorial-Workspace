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
  ChevronDown,
  History,
  FileDown,
  Wand2,
  ShieldCheck,
  BookmarkCheck,
  Search,
  ExternalLink,
  MessageSquare,
  Send,
  Copy,
  SlidersHorizontal,
  RefreshCw
} from 'lucide-react';
import { writingService } from '../services/writingService';
import { projectService } from '../services/projectService';
import { WritingIssue, WritingMetrics, WritingDraft, DraftComparisonResponse } from '../types';
import { useToast } from '../components/common/Toast';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { StyleIntelligencePanel } from '../components/writing/StyleIntelligencePanel';
import { VersionHistoryPanel } from '../components/version_control/VersionHistoryPanel';

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
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  
  // Modals
  const [isNewDraftOpen, setIsNewDraftOpen] = useState(false);
  const [newDraftTitle, setNewDraftTitle] = useState('');
  const [newDraftInitialText, setNewDraftInitialText] = useState('');
  const [deleteDraftId, setDeleteDraftId] = useState<string | null>(null);

  // Export State
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'markdown' | 'docx' | 'html' | 'txt'>('markdown');
  const [isExporting, setIsExporting] = useState(false);

  // AI Generation State
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [generateTopic, setGenerateTopic] = useState('');
  const [generateAudience, setGenerateAudience] = useState('Founders, builders, and operators');
  const [isGenerating, setIsGenerating] = useState(false);

  // Selection Rewrite State
  const [selectedText, setSelectedText] = useState('');
  const [rewriteOp, setRewriteOp] = useState('improve_clarity');
  const [isRewriting, setIsRewriting] = useState(false);
  const [askAiPrompt, setAskAiPrompt] = useState('');

  // Grounding Audit State
  const [isGroundingOpen, setIsGroundingOpen] = useState(false);
  const [groundingAudit, setGroundingAudit] = useState<any>(null);
  const [isAuditingGrounding, setIsAuditingGrounding] = useState(false);

  // References Manager State
  const [isReferencesOpen, setIsReferencesOpen] = useState(false);
  const [projectSources, setProjectSources] = useState<any[]>([]);
  const [referenceSearch, setReferenceSearch] = useState('');

  // Right Column View Selector (Improvements, Copilot Chat, Style)
  const [sidebarTab, setSidebarTab] = useState<'improvements' | 'copilot' | 'style'>('improvements');
  const [copilotMessages, setCopilotMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    text: string;
    proposal?: string;
    recommendations?: string[];
  }>>([
    {
      id: '1',
      role: 'user',
      text: 'Please rewrite this sentence to sound more insightful: "Founders who implement verifiable evaluation metrics will dominate the commercial landscape."'
    },
    {
      id: '2',
      role: 'assistant',
      text: 'Here is a more thoughtful, publication-ready version:',
      proposal: 'Rather than competing on fragile prompt wrappers, enduring enterprise teams establish decoupled evaluation benchmarks to maintain factual defensibility under load.',
      recommendations: [
        'Anticipate production latency trade-offs before scaling context windows',
        'Decouple claim verification from generative token streaming',
        'Preserve audit trails for compliance and factual reproducibility'
      ]
    }
  ]);
  const [copilotInput, setCopilotInput] = useState('');
  const [isCopilotThinking, setIsCopilotThinking] = useState(false);

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

  const handleExport = async (format: 'markdown' | 'docx' | 'html' | 'txt' = exportFormat) => {
    if (!activeDraftId) {
      info('Please select or save a draft before exporting.');
      return;
    }
    try {
      setIsExporting(true);
      info(`Exporting draft as ${format.toUpperCase()}...`);
      const { blob, filename } = await writingService.exportDraft(activeDraftId, format);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      success(`Draft exported successfully as ${filename}!`);
      setIsExportOpen(false);
    } catch (err: any) {
      error(err.message || 'Failed to export draft document.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateDraft = async () => {
    if (!generateTopic.trim()) {
      error('Please specify a topic or editorial focus.');
      return;
    }
    try {
      setIsGenerating(true);
      info('Synthesizing initial article draft with AI...');
      const res = await writingService.generateDraft({
        topic: generateTopic,
        target_audience: generateAudience,
        content_type: 'editorial_analysis',
        desired_length: 800,
      });
      setText(res.content);
      const title = res.title || res.headline || generateTopic;
      setDraftTitle(title);
      setOriginalDraft(res.content);
      setIsGenerateOpen(false);
      setGenerateTopic('');
      success('Article draft generated! Click Audit Quality to evaluate readability.');
      if (res.draft_id) {
        setActiveDraftId(res.draft_id);
        navigate(`/writing/${res.draft_id}`, { replace: true });
        loadDraftsList();
      }
    } catch (err: any) {
      error(err.message || 'Failed to generate draft.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRewriteSelection = async () => {
    if (!selectedText.trim()) {
      info('Select a section of text in the draft editor to rewrite.');
      return;
    }
    try {
      setIsRewriting(true);
      info('AI is rewriting selected text...');
      const res = await writingService.rewriteSelection({
        selected_text: selectedText,
        operation: rewriteOp,
        draft_id: activeDraftId || undefined,
      });
      if (res.rewritten_text) {
        const newText = text.replace(selectedText, res.rewritten_text);
        setText(newText);
        setSelectedText('');
        success(`Applied AI rewrite: ${res.explanation || 'Content updated!'}`);
        handleAnalyze(newText);
      }
    } catch (err: any) {
      error(err.message || 'Failed to rewrite selected text.');
    } finally {
      setIsRewriting(false);
    }
  };

  const handleAskAiCustom = async (customPrompt?: string) => {
    const promptToUse = customPrompt || askAiPrompt;
    if (!promptToUse.trim()) return;
    try {
      setIsRewriting(true);
      info('AI is processing your editorial request...');
      const targetText = selectedText || text;
      const res = await writingService.rewriteSelection({
        selected_text: targetText,
        operation: 'rewrite_selection',
        draft_id: activeDraftId || undefined,
        custom_instructions: promptToUse,
      });
      if (res.rewritten_text) {
        if (selectedText) {
          const newText = text.replace(selectedText, res.rewritten_text);
          setText(newText);
          setSelectedText('');
        } else {
          setText(res.rewritten_text);
        }
        setAskAiPrompt('');
        success(`Applied AI update: ${res.explanation || 'Content revised!'}`);
        handleAnalyze(text);
      }
    } catch (err: any) {
      error(err.message || 'Failed to process AI request.');
    } finally {
      setIsRewriting(false);
    }
  };

  const handleSendCopilotMessage = async () => {
    if (!copilotInput.trim()) return;
    const userMsg = copilotInput.trim();
    setCopilotInput('');
    const newMsgId = String(Date.now());
    setCopilotMessages(prev => [...prev, { id: newMsgId, role: 'user', text: userMsg }]);

    try {
      setIsCopilotThinking(true);
      const targetText = selectedText || text.slice(0, 500);
      const res = await writingService.rewriteSelection({
        selected_text: targetText,
        operation: 'rewrite_selection',
        draft_id: activeDraftId || undefined,
        custom_instructions: userMsg,
      });

      setCopilotMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          text: 'Here is an optimized version for your draft:',
          proposal: res.rewritten_text,
          recommendations: [
            'Anticipate distracted reader behavior by highlighting core nouns',
            'Reduce cognitive load through shorter clause structures',
            'Preserve verified source citations [1] in subsequent drafts'
          ]
        }
      ]);
    } catch (err: any) {
      error(err.message || 'AI Copilot encountered an error.');
    } finally {
      setIsCopilotThinking(false);
    }
  };

  const handleApplyCopilotProposal = (proposal: string) => {
    if (selectedText) {
      const newText = text.replace(selectedText, proposal);
      setText(newText);
      setSelectedText('');
    } else {
      setText(prev => `${prev}\n\n${proposal}`);
    }
    success('Applied AI proposal to document!');
    handleAnalyze(text);
  };

  const handleGiveAnotherOption = async (originalProposal: string) => {
    try {
      setIsCopilotThinking(true);
      const res = await writingService.rewriteSelection({
        selected_text: originalProposal,
        operation: 'adjust_tone',
        draft_id: activeDraftId || undefined,
        custom_instructions: 'Provide an alternative punchy and concise version with identical factual substance.'
      });
      setCopilotMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 2),
          role: 'assistant',
          text: 'Here is an alternative formulation:',
          proposal: res.rewritten_text,
          recommendations: [
            'Clearer cadence with punchy concluding verb',
            'Maintains 100% empirical grounding with research archive'
          ]
        }
      ]);
    } catch (err: any) {
      error(err.message || 'Failed to generate alternative option.');
    } finally {
      setIsCopilotThinking(false);
    }
  };

  const handleRunGroundingAudit = async () => {
    if (!activeDraftId) {
      info('Please save the draft first to run research grounding audit.');
      return;
    }
    try {
      setIsAuditingGrounding(true);
      info('Cross-referencing factual claims against research corpus...');
      const audit = await writingService.getGroundingAudit(activeDraftId);
      setGroundingAudit(audit);
      setIsGroundingOpen(true);
      success(`Grounding audit complete! Score: ${audit.grounding_score}% verified.`);
    } catch (err: any) {
      error(err.message || 'Failed to complete grounding audit.');
    } finally {
      setIsAuditingGrounding(false);
    }
  };

  const handleOpenReferences = async () => {
    setIsReferencesOpen(true);
    try {
      const activeDraft = savedDrafts.find(d => d.id === activeDraftId);
      if (activeDraft && activeDraft.project_id) {
        const proj = await projectService.getProject(activeDraft.project_id);
        if (proj && proj.sources) {
          setProjectSources(proj.sources);
        }
      } else {
        // Fetch recent project sources as reference corpus
        const projs = await projectService.getProjects(0, 5);
        if (projs.items && projs.items.length > 0) {
          const firstProj = await projectService.getProject(projs.items[0].id);
          if (firstProj && firstProj.sources) {
            setProjectSources(firstProj.sources);
          }
        }
      }
    } catch (e) {
      console.error('Failed to load project references', e);
    }
  };

  const handleInsertCitation = (citationTag: string) => {
    const textarea = document.querySelector('textarea') as HTMLTextAreaElement | null;
    if (textarea) {
      const start = textarea.selectionStart ?? text.length;
      const end = textarea.selectionEnd ?? text.length;
      const newText = text.substring(0, start) + ` ${citationTag} ` + text.substring(end);
      setText(newText);
      success(`Inserted citation ${citationTag}`);
    } else {
      setText(prev => `${prev} ${citationTag}`);
      success(`Inserted citation ${citationTag}`);
    }
    setIsReferencesOpen(false);
  };

  const handleTextSelect = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    const target = e.currentTarget;
    const start = target.selectionStart;
    const end = target.selectionEnd;
    if (start !== end) {
      setSelectedText(target.value.substring(start, end));
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

  const handleAnalyze = async (contentToAnalyze: string, explicitDraftId?: string, isUserAction: boolean = false) => {
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
      if (isUserAction) {
        info('Writing quality audit completed.');
      }
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
            onClick={() => setIsGenerateOpen(true)}
            variant="outline"
            size="sm"
            leftIcon={<Wand2 className="w-3.5 h-3.5 text-purple-600" />}
          >
            AI Draft
          </Button>

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

          {activeDraftId && (
            <Button
              onClick={handleRunGroundingAudit}
              isLoading={isAuditingGrounding}
              variant="outline"
              size="sm"
              leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />}
              title="Audit claim-by-claim grounding against research corpus"
            >
              Verify Grounding
            </Button>
          )}

          <Button
            onClick={handleOpenReferences}
            variant="outline"
            size="sm"
            leftIcon={<BookOpen className="w-3.5 h-3.5 text-indigo-600" />}
            title="Search connected project references"
          >
            References
          </Button>

          {activeDraftId && (
            <Button
              onClick={() => setIsHistoryOpen(true)}
              variant="outline"
              size="sm"
              leftIcon={<History className="w-3.5 h-3.5 text-blue-600" />}
            >
              Version History
            </Button>
          )}

          {activeDraftId && (
            <Button
              onClick={() => setIsExportOpen(true)}
              variant="outline"
              size="sm"
              leftIcon={<FileDown className="w-3.5 h-3.5 text-emerald-600" />}
            >
              Export
            </Button>
          )}

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
            onClick={() => handleAnalyze(text, undefined, true)}
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

                {/* Version Comparison View (Compare Versions style) */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                  <div className="flex items-center gap-2">
                    <GitCompare className="w-4 h-4 text-blue-600" />
                    <span className="font-semibold text-slate-800 dark:text-slate-100">
                      Comparing: Baseline Original vs Revised Publication Draft
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      if (originalDraft) {
                        setText(originalDraft);
                        success('Restored draft content to baseline original!');
                        handleAnalyze(originalDraft);
                      }
                    }}
                    className="text-xs bg-white dark:bg-slate-900 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                  >
                    Restore Baseline Content
                  </Button>
                </div>

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
                {/* Floating Contextual Selection Menu & Ask AI bar (Notalx style) */}
                {selectedText && (
                  <div className="p-3.5 bg-white dark:bg-slate-900 border-2 border-blue-500/40 dark:border-blue-500/60 rounded-2xl shadow-lg space-y-3 transition-all animate-in fade-in duration-150">
                    <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-blue-600 animate-pulse" />
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                          Selected: "{selectedText.slice(0, 40)}{selectedText.length > 40 ? '...' : ''}"
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedText('')}
                        className="text-slate-400 hover:text-slate-600 text-xs"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Quick Selection Actions (Notalx style) */}
                    <div className="flex flex-wrap items-center gap-1.5 text-xs">
                      <span className="text-[10px] uppercase font-bold text-slate-400 mr-1">Edit / Review:</span>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('improve_clarity'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 text-blue-700 dark:text-blue-200 font-medium transition-colors"
                      >
                        ⚡ Improve Writing
                      </button>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('fix_grammar'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-200 font-medium transition-colors"
                      >
                        ✓ Fix Spelling & Grammar
                      </button>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('summarize_selection'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-purple-50 dark:bg-purple-950/60 hover:bg-purple-100 text-purple-700 dark:text-purple-200 font-medium transition-colors"
                      >
                        ✂️ Make Shorter
                      </button>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('expand_content'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/60 hover:bg-amber-100 text-amber-700 dark:text-amber-200 font-medium transition-colors"
                      >
                        ➕ Make Longer
                      </button>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('simplify_language'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-teal-50 dark:bg-teal-950/60 hover:bg-teal-100 text-teal-700 dark:text-teal-200 font-medium transition-colors"
                      >
                        ✨ Simplify
                      </button>
                      <button
                        type="button"
                        onClick={() => { setRewriteOp('adjust_tone'); handleRewriteSelection(); }}
                        className="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/60 hover:bg-rose-100 text-rose-700 dark:text-rose-200 font-medium transition-colors"
                      >
                        🎭 Tone
                      </button>
                    </div>

                    {/* Custom Ask AI Prompt Input (Notalx style) */}
                    <div className="flex items-center gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
                      <input
                        type="text"
                        placeholder="Ask AI what to do next with this selection (e.g. 'rewrite in Wall Street Journal style')..."
                        value={askAiPrompt}
                        onChange={(e) => setAskAiPrompt(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleAskAiCustom();
                        }}
                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleAskAiCustom()}
                        disabled={!askAiPrompt.trim()}
                        isLoading={isRewriting}
                        className="text-xs shrink-0"
                      >
                        Send
                      </Button>
                    </div>
                  </div>
                )}

                {/* In-Editor Quick Actions Bar (Afforai & Knowee Writer style) */}
                <div className="flex flex-wrap items-center justify-between gap-2 px-3 py-1.5 bg-slate-100/70 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/60 text-xs">
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={handleOpenReferences}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                      title="Browse project references and insert citation tags"
                    >
                      <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Cite Reference</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setRewriteOp('improve_clarity');
                        if (selectedText) handleRewriteSelection();
                        else info('Select text to improve clarity');
                      }}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                      title="Eliminate ambiguity and verbose phrasing"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                      <span>Simplify</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setRewriteOp('fix_grammar');
                        if (selectedText) handleRewriteSelection();
                        else info('Select text to fix grammar');
                      }}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                      title="Fix grammatical flaws and spelling"
                    >
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Fix Grammar</span>
                    </button>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    {isDirty ? (
                      <span className="text-amber-500 font-medium flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Unsaved changes
                      </span>
                    ) : (
                      <span className="text-emerald-500 font-medium flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> Saved
                      </span>
                    )}
                  </div>
                </div>
                <textarea
                  rows={16}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onSelect={handleTextSelect}
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

        {/* Right Column: Multi-Tab Intelligence Sidebar (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Sidebar Navigation Tabs (Improvements, AI Copilot, Style) */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/80 text-xs">
            <button
              type="button"
              onClick={() => setSidebarTab('improvements')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg font-semibold transition-all ${
                sidebarTab === 'improvements'
                  ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Review ({pendingIssues.length})</span>
            </button>
            <button
              type="button"
              onClick={() => setSidebarTab('copilot')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg font-semibold transition-all ${
                sidebarTab === 'copilot'
                  ? 'bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>AI Copilot</span>
            </button>
            <button
              type="button"
              onClick={() => setSidebarTab('style')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg font-semibold transition-all ${
                sidebarTab === 'style'
                  ? 'bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Style Guide</span>
            </button>
          </div>

          {/* TAB 1: Improvements & Review Mode (Surfer / CKEditor / TinyMCE style) */}
          {sidebarTab === 'improvements' && (
            <div className="space-y-4">
              {/* Article Improvements Score Header (Clearscope / Surfer style) */}
              <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-md border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">
                      Article Quality & Readiness
                    </span>
                    <div className="text-lg font-bold text-white mt-0.5 flex items-center gap-2">
                      <span>{(metrics?.readability_score ?? 60) >= 60 ? 'Good' : 'Needs Polish'}</span>
                      <span className="text-xs font-mono font-normal text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800">
                        {metrics?.readability_score ? Math.round(metrics.readability_score) : 60}/100
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-slate-400 uppercase">Grade</span>
                    <div className="text-sm font-semibold text-slate-200">
                      {metrics?.readability_grade || 'Standard'}
                    </div>
                  </div>
                </div>

                {/* Multi-Segment Quality Meter Bar */}
                <div className="space-y-1">
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden flex">
                    <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${Math.min(100, metrics?.readability_score ?? 60)}%` }} />
                    <div className="h-full bg-blue-500/40" style={{ width: '20%' }} />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>{metrics?.word_count ?? 0} words</span>
                    <span>{metrics?.reading_time_minutes ?? 0}m reading time</span>
                    <span>{metrics?.sentence_count ?? 0} sentences</span>
                  </div>
                </div>

                {/* Interactive Tone Adjuster (Wordo style) */}
                <div className="space-y-2 pt-1 border-t border-slate-800">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
                    Adjust Tone Preset:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { label: 'Authoritative', tone: 'authoritative, analytical, objective' },
                      { label: 'Conversational', tone: 'conversational, engaging, accessible' },
                      { label: 'Assertive', tone: 'assertive, bold, decisive' },
                      { label: 'Confident', tone: 'confident, executive, strategic' },
                      { label: 'Constructive', tone: 'constructive, technical, empirical' }
                    ].map(t => (
                      <button
                        key={t.label}
                        type="button"
                        onClick={async () => {
                          const target = selectedText || text;
                          info(`Adjusting tone to ${t.label}...`);
                          try {
                            const res = await writingService.rewriteSelection({
                              selected_text: target,
                              operation: 'adjust_tone',
                              draft_id: activeDraftId || undefined,
                              target_tone: t.tone
                            });
                            if (res.rewritten_text) {
                              if (selectedText) {
                                setText(text.replace(selectedText, res.rewritten_text));
                                setSelectedText('');
                              } else {
                                setText(res.rewritten_text);
                              }
                              success(`Tone adjusted to ${t.label}!`);
                              handleAnalyze(text);
                            }
                          } catch (e: any) {
                            error(e.message || 'Failed to adjust tone');
                          }
                        }}
                        className="px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-medium text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
                      >
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Suggestions Panel with Inline Diffs */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Review Recommendations ({pendingIssues.length} pending)
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

                        {/* Inline Visual Diff (CKEditorAI & TinyMCE style) */}
                        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 font-serif text-[13px] leading-relaxed">
                          <span className="line-through bg-rose-100 dark:bg-rose-950/70 text-rose-800 dark:text-rose-300 px-1 py-0.5 rounded mr-1.5 font-normal">
                            {issue.original_text}
                          </span>
                          {issue.suggested_rewrite && (
                            <span className="bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 px-1.5 py-0.5 rounded font-medium no-underline">
                              {issue.suggested_rewrite}
                            </span>
                          )}
                        </div>

                        {/* Editorial Rationale */}
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-normal font-sans">
                          {issue.explanation}
                        </p>

                        {/* Accept / Reject Buttons (matching TinyMCE Apply & Skip) */}
                        {issue.status === 'pending' && (
                          <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
                            <Button
                              onClick={() => handleRejectSuggestion(issue)}
                              variant="ghost"
                              size="sm"
                              className="text-slate-500 hover:text-slate-700 hover:bg-slate-100 text-[11px]"
                              leftIcon={<X className="w-3.5 h-3.5" />}
                            >
                              ✕ Skip
                            </Button>
                            <Button
                              onClick={() => handleAcceptSuggestion(issue)}
                              variant="primary"
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 text-white text-[11px]"
                              leftIcon={<Check className="w-3.5 h-3.5" />}
                            >
                              ✓ Apply
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: AI Copilot Chat Panel (Notelify style) */}
          {sidebarTab === 'copilot' && (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                    Editorial AI Copilot
                  </h3>
                </div>
                <span className="text-[10px] text-purple-600 dark:text-purple-400 font-medium bg-purple-50 dark:bg-purple-950/60 px-2 py-0.5 rounded-full">
                  Interactive Assistant
                </span>
              </div>

              {/* Chat Thread */}
              <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                {copilotMessages.map(msg => (
                  <div key={msg.id} className="space-y-2">
                    {msg.role === 'user' ? (
                      <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 font-medium">
                        {msg.text}
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-purple-50/50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 space-y-3 text-xs">
                        <span className="text-[10px] uppercase font-bold text-purple-700 dark:text-purple-300 tracking-wider block">
                          AI Answer & Editorial Proposal:
                        </span>
                        {msg.proposal && (
                          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-purple-200 dark:border-purple-800/80 font-serif text-[13px] leading-relaxed text-slate-900 dark:text-slate-100">
                            {msg.proposal}
                          </div>
                        )}
                        {msg.recommendations && msg.recommendations.length > 0 && (
                          <div className="space-y-1">
                            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
                              Consider focusing on:
                            </span>
                            <ul className="text-[11px] text-slate-600 dark:text-slate-400 space-y-0.5 list-disc list-inside">
                              {msg.recommendations.map((rec, i) => (
                                <li key={i}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <div className="flex items-center justify-between pt-1 border-t border-purple-100 dark:border-purple-900/60">
                          <button
                            type="button"
                            onClick={() => msg.proposal && handleGiveAnotherOption(msg.proposal)}
                            className="text-[11px] text-purple-600 hover:text-purple-700 hover:underline flex items-center gap-1"
                          >
                            <RefreshCw className="w-3 h-3" />
                            <span>Give me another option</span>
                          </button>
                          {msg.proposal && (
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => handleApplyCopilotProposal(msg.proposal!)}
                              className="bg-purple-600 hover:bg-purple-700 text-white text-[11px]"
                              leftIcon={<Check className="w-3.5 h-3.5" />}
                            >
                              Replace in Draft
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {isCopilotThinking && (
                  <div className="flex items-center gap-2 p-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-purple-600 text-xs">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Copilot is formulating editorial recommendations...</span>
                  </div>
                )}
              </div>

              {/* Bottom Copilot Input (Notelify style) */}
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Ask me anything about this draft..."
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSendCopilotMessage();
                    }}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                  />
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleSendCopilotMessage}
                    disabled={!copilotInput.trim() || isCopilotThinking}
                    className="bg-purple-600 hover:bg-purple-700 text-white shrink-0"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Style Intelligence Guide */}
          {sidebarTab === 'style' && (
            <StyleIntelligencePanel
              draftId={activeDraftId || undefined}
              currentContent={text}
              onAcceptSuggestion={handleAcceptSuggestionId}
              onRejectSuggestion={handleRejectSuggestionId}
            />
          )}
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

      {/* Export Draft Modal */}
      <Modal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        title="Export Publication-Ready Draft"
        description="Download your revised draft formatted for publication or editorial distribution."
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {[
              { id: 'markdown', label: 'Markdown (.md)', desc: 'With YAML frontmatter and section headers' },
              { id: 'docx', label: 'Word (.docx)', desc: 'Clean formatted Microsoft Word document' },
              { id: 'html', label: 'HTML (.html)', desc: 'Semantic web article markup' },
              { id: 'txt', label: 'Plain Text (.txt)', desc: 'Clean unformatted editorial copy' },
            ].map((fmt) => (
              <button
                key={fmt.id}
                type="button"
                onClick={() => setExportFormat(fmt.id as any)}
                className={`p-3 text-left rounded-xl border transition-all ${
                  exportFormat === fmt.id
                    ? 'border-blue-600 bg-blue-50/50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-100 shadow-xs'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:border-slate-300'
                }`}
              >
                <div className="text-xs font-bold">{fmt.label}</div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">{fmt.desc}</div>
              </button>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsExportOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              isLoading={isExporting}
              onClick={() => handleExport(exportFormat)}
              leftIcon={<FileDown className="w-3.5 h-3.5" />}
            >
              Export {exportFormat.toUpperCase()}
            </Button>
          </div>
        </div>
      </Modal>

      {/* AI Generate Draft Modal */}
      <Modal
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        title="Generate AI Editorial Draft"
        description="Synthesize an evidence-based draft tailored to your target audience."
      >
        <div className="space-y-4">
          <Input
            label="Editorial Topic or Headline"
            placeholder="e.g. Frontiers in Superconducting Quantum Computing"
            value={generateTopic}
            onChange={(e) => setGenerateTopic(e.target.value)}
            required
            autoFocus
          />
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Target Audience
            </label>
            <input
              type="text"
              value={generateAudience}
              onChange={(e) => setGenerateAudience(e.target.value)}
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setIsGenerateOpen(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              isLoading={isGenerating}
              onClick={handleGenerateDraft}
              disabled={!generateTopic.trim()}
              leftIcon={<Wand2 className="w-3.5 h-3.5" />}
            >
              Generate Draft
            </Button>
          </div>
        </div>
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

      {/* Version History Drawer */}
      {activeDraftId && (
        <VersionHistoryPanel
          documentType="WRITING_DRAFT"
          documentId={activeDraftId}
          isOpen={isHistoryOpen}
          onClose={() => setIsHistoryOpen(false)}
          onVersionRestored={(newContent) => {
            setText(newContent);
            setSavedContent(newContent);
            handleAnalyze(newContent);
          }}
        />
      )}

      {/* Reference Manager Modal (Afforai Cite Extension & Knowee Writer style) */}
      <Modal
        isOpen={isReferencesOpen}
        onClose={() => setIsReferencesOpen(false)}
        title="Reference Manager & Citation Library"
        description="Select verified sources from your research projects to insert inline citations [1], [2] at cursor."
      >
        <div className="space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search references by title, author, or keyword..."
              value={referenceSearch}
              onChange={(e) => setReferenceSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
            {projectSources.length > 0 ? (
              projectSources
                .filter(s => !referenceSearch || s.title?.toLowerCase().includes(referenceSearch.toLowerCase()))
                .map((src, idx) => (
                  <div
                    key={src.id || idx}
                    className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 hover:border-blue-300 dark:hover:border-blue-700 transition-all flex items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-blue-600 bg-blue-50 dark:bg-blue-950/60 px-1.5 py-0.5 rounded text-[11px]">
                          [{idx + 1}]
                        </span>
                        <h4 className="font-semibold text-slate-900 dark:text-slate-100 leading-snug">
                          {src.title || 'Untitled Source'}
                        </h4>
                      </div>
                      {src.url && (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 text-[11px] text-blue-600 hover:underline"
                        >
                          <span className="truncate max-w-[280px]">{src.url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      )}
                      {src.summary && (
                        <p className="text-[11px] text-slate-500 line-clamp-2 mt-1">
                          {src.summary}
                        </p>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleInsertCitation(`[${idx + 1}]`)}
                      className="shrink-0 text-[11px]"
                      leftIcon={<Plus className="w-3 h-3" />}
                    >
                      Insert [{idx + 1}]
                    </Button>
                  </div>
                ))
            ) : (
              <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center space-y-3">
                <p className="text-xs text-slate-500">
                  No connected project sources found for this draft yet.
                </p>
                <div className="flex justify-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleInsertCitation('[1]')}
                    className="text-xs"
                  >
                    Insert [1]
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleInsertCitation('[2]')}
                    className="text-xs"
                  >
                    Insert [2]
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button variant="ghost" onClick={() => setIsReferencesOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Grounding Verification Modal (ISNAD Research Workspace style) */}
      <Modal
        isOpen={isGroundingOpen}
        onClose={() => setIsGroundingOpen(false)}
        title="Research Grounding & Factual Verification"
        description="Automated claim-by-claim verification against connected research sources and empirical evidence."
      >
        <div className="space-y-4">
          {groundingAudit ? (
            <>
              {/* Score Header */}
              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                <div className="p-2.5 rounded-xl bg-slate-900 text-white">
                  <div className="text-base font-bold text-emerald-400">
                    {groundingAudit.grounding_score}%
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase">Grounded Score</div>
                </div>
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200">
                  <div className="text-base font-bold">{groundingAudit.grounded_count ?? 0}</div>
                  <div className="text-[10px] uppercase">Grounded</div>
                </div>
                <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200">
                  <div className="text-base font-bold">{groundingAudit.inferred_count ?? 0}</div>
                  <div className="text-[10px] uppercase">Inferred</div>
                </div>
                <div className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200">
                  <div className="text-base font-bold">{groundingAudit.unsupported_count ?? 0}</div>
                  <div className="text-[10px] uppercase">Unsupported</div>
                </div>
              </div>

              {/* Recommendations */}
              {groundingAudit.actionable_recommendations && groundingAudit.actionable_recommendations.length > 0 && (
                <div className="p-3 bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl space-y-1.5">
                  <span className="text-[11px] font-semibold text-blue-900 dark:text-blue-200 uppercase tracking-wider block">
                    Editorial Recommendations
                  </span>
                  <ul className="text-xs text-blue-800 dark:text-blue-300 space-y-1 list-disc list-inside">
                    {groundingAudit.actionable_recommendations.map((rec: string, i: number) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Claims Breakdown */}
              <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                {groundingAudit.claims && groundingAudit.claims.length > 0 ? (
                  groundingAudit.claims.map((claim: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-full ${
                          claim.classification === 'grounded' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                          claim.classification === 'inferred' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' :
                          'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                        }`}>
                          {claim.classification}
                        </span>
                        {claim.citation_tag && (
                          <span className="font-mono font-semibold text-blue-600 bg-blue-50 dark:bg-blue-950/60 px-1.5 py-0.5 rounded text-[11px]">
                            {claim.citation_tag}
                          </span>
                        )}
                      </div>
                      <p className="font-medium text-slate-800 dark:text-slate-200">
                        "{claim.claim_text}"
                      </p>
                      {claim.supporting_excerpt && (
                        <div className="p-2 rounded bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-[11px] text-slate-600 dark:text-slate-300">
                          <span className="font-semibold text-slate-700 dark:text-slate-200 block mb-0.5">Source Evidence:</span>
                          {claim.supporting_excerpt}
                        </div>
                      )}
                      {claim.warning && (
                        <p className="text-[11px] text-rose-600 dark:text-rose-400">
                          Warning: {claim.warning}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 text-center py-4">No individual claims flagged.</p>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-6 text-xs text-slate-500">
              Loading grounding data...
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button variant="ghost" onClick={() => setIsGroundingOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
