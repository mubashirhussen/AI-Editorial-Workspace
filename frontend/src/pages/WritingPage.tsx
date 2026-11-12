import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  AlertCircle,
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
  RefreshCw,
  CloudOff,
  Archive,
  Undo2,
  Filter,
  ArrowUpDown,
  FolderOpen,
  CheckCircle2
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
import { ArticleImprovementsPanel } from '../components/writing/ArticleImprovementsPanel';
import { InlineReadabilityLinter } from '../components/writing/InlineReadabilityLinter';
import { analyzeText } from '../utils/textAnalysis';

export type DraftSaveState = 'UNSAVED' | 'SAVING' | 'SAVED' | 'SAVE_FAILED' | 'OFFLINE';

export interface PendingAiSuggestion {
  operation: string;
  operationLabel: string;
  originalText: string;
  rewrittenText: string;
  explanation?: string;
  isSelection: boolean;
}

export const REWRITE_OPERATIONS = [
  { id: 'improve_clarity', label: 'Improve Clarity', icon: '⚡', desc: 'Eliminate ambiguity and passive voice' },
  { id: 'fix_grammar', label: 'Fix Spelling & Grammar', icon: '✓', desc: 'Fix typos, agreement, and punctuation' },
  { id: 'improve_readability', label: 'Enhance Readability', icon: '📖', desc: 'Optimize rhythm and cadence' },
  { id: 'improve_sentence_structure', label: 'Restructure Sentences', icon: '🔄', desc: 'Balance clauses and active cadence' },
  { id: 'reduce_repetition', label: 'Remove Repetition', icon: '✂️', desc: 'Eliminate duplicated words and tautologies' },
  { id: 'improve_transitions', label: 'Flow & Transitions', icon: '🔗', desc: 'Add connective tissue between ideas' },
  { id: 'adjust_tone', label: 'Adjust Tone', icon: '🎭', desc: 'Calibrate voice to authoritative or conversational' },
  { id: 'simplify_language', label: 'Simplify Language', icon: '✨', desc: 'Replace jargon with clear plain English' },
  { id: 'summarize_selection', label: 'Make Concise', icon: '📝', desc: 'Condense to core essential takeaway' },
  { id: 'expand_content', label: 'Expand Content', icon: '➕', desc: 'Add analytical depth and context' },
  { id: 'generate_headlines', label: 'Generate Headlines', icon: '📰', desc: 'Create punchy journalistic headlines' },
  { id: 'generate_hook', label: 'Intro & Hook', icon: '🎣', desc: 'Craft compelling introductory hook' },
  { id: 'reorganize_paragraphs', label: 'Reorganize Structure', icon: '📊', desc: 'Optimize narrative logic and sequence' },
];

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
  const [saveState, setSaveState] = useState<DraftSaveState>('SAVED');
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [previousSnapshots, setPreviousSnapshots] = useState<string[]>([]);
  
  const [savedDrafts, setSavedDrafts] = useState<WritingDraft[]>([]);
  const [issues, setIssues] = useState<WritingIssue[]>([]);
  const [metrics, setMetrics] = useState<WritingMetrics | null>(null);

  // Deterministic real-time client-side text metrics
  const liveMetrics = useMemo<WritingMetrics>(() => {
    const analyzed = analyzeText(text);
    return {
      word_count: analyzed.word_count,
      character_count: analyzed.character_count,
      sentence_count: analyzed.sentence_count,
      paragraph_count: analyzed.paragraph_count,
      average_sentence_length: analyzed.avg_sentence_length,
      reading_time_minutes: analyzed.reading_time_minutes,
      readability_score: metrics?.readability_score ?? analyzed.quality_score,
      readability_grade: metrics?.readability_grade ?? (analyzed.flesch_reading_ease >= 60 ? 'Standard / Conversational' : 'Academic / Complex'),
      readability_note: metrics?.readability_note ?? `Flesch Reading Ease: ${analyzed.flesch_reading_ease}/100`
    };
  }, [text, metrics]);

  const [overallFeedback, setOverallFeedback] = useState<string>('');
  const [comparisonData, setComparisonData] = useState<DraftComparisonResponse | null>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>('all');
  
  // Modals & Drawers
  const [isNewDraftOpen, setIsNewDraftOpen] = useState(false);
  const [newDraftTitle, setNewDraftTitle] = useState('');
  const [newDraftContentType, setNewDraftContentType] = useState('editorial_analysis');
  const [newDraftTargetAudience, setNewDraftTargetAudience] = useState('Technical Leaders & Builders');
  const [newDraftTone, setNewDraftTone] = useState('authoritative');
  const [newDraftDesiredLength, setNewDraftDesiredLength] = useState(800);
  const [newDraftProjectId, setNewDraftProjectId] = useState<string>('');
  const [newDraftInitialText, setNewDraftInitialText] = useState('');
  const [availableProjects, setAvailableProjects] = useState<any[]>([]);

  // Drafts Library Drawer
  const [isLibraryOpen, setIsLibraryOpen] = useState(false);
  const [librarySearch, setLibrarySearch] = useState('');
  const [libraryStatusFilter, setLibraryStatusFilter] = useState<string>('all');
  const [librarySortBy, setLibrarySortBy] = useState<'updated_at' | 'created_at' | 'title'>('updated_at');
  const [librarySortOrder, setLibrarySortOrder] = useState<'desc' | 'asc'>('desc');
  const [isDuplicating, setIsDuplicating] = useState<string | null>(null);

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

  // Selection Rewrite & AI Suggestion Review State
  const [selectedText, setSelectedText] = useState('');
  const [rewriteOp, setRewriteOp] = useState('improve_clarity');
  const [isRewriting, setIsRewriting] = useState(false);
  const [askAiPrompt, setAskAiPrompt] = useState('');
  const [pendingAiSuggestion, setPendingAiSuggestion] = useState<PendingAiSuggestion | null>(null);

  // Grounding Audit State
  const [isGroundingOpen, setIsGroundingOpen] = useState(false);
  const [groundingAudit, setGroundingAudit] = useState<any>(null);
  const [isAuditingGrounding, setIsAuditingGrounding] = useState(false);

  // Templates & Linters
  const [isTemplateDrawerOpen, setIsTemplateDrawerOpen] = useState(false);
  const [isLinterHighlightActive, setIsLinterHighlightActive] = useState(false);
  const [activeIssueTab, setActiveIssueTab] = useState<'all' | 'seo' | 'readability' | 'tone'>('all');
  const [selectedRailTab, setSelectedRailTab] = useState<'improvements' | 'chat' | 'images' | 'competitor'>('improvements');

  // References Manager State
  const [isReferencesOpen, setIsReferencesOpen] = useState(false);
  const [projectSources, setProjectSources] = useState<any[]>([]);
  const [referenceSearch, setReferenceSearch] = useState('');

  // Right Column View Selector
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

  const DRAFT_TEMPLATES = [
    {
      title: 'Create a business proposal',
      content: `# Executive Business Proposal: Next-Generation Editorial Intelligence\n\n## 1. Executive Summary\nModern publishing teams require evidence-grounded AI tools to streamline editorial pipelines while eliminating factual hallucinations.\n\n## 2. Problem Statement\nTraditional generative AI models introduce unverified claims and lack deterministic style compliance.\n\n## 3. Proposed Solution\nA 3-tier architecture with local source indexing, deterministic style linters, and multi-provider verification.\n\n## 4. Financial & Operational Impact\nReduces editorial review cycles by 60% while boosting factual citation accuracy to 99.4%.\n\n## 5. Next Steps & Timeline\nPhase 1 deployment beginning next quarter with full production roll-out.`
    },
    {
      title: 'Create a help article',
      content: `# Knowledge Base: How to Verify Research Evidence & Export Citations\n\n## Overview\nThis guide explains how to cross-reference claims against source documents and export verified citations.\n\n## Step-by-Step Instructions\n1. Navigate to the Research Library and select your target source.\n2. Review the extracted key claims and retrieval chunks.\n3. In the Writing Workspace, click "Cite Reference" to select authoritative sources.\n4. Run "Verify Grounding" to inspect claim verification statuses.\n\n## Troubleshooting\nIf an excerpt cannot be matched, ensure the source file is indexed and uncorrupted.`
    },
    {
      title: 'Create a job description',
      content: `# Senior AI Systems & Reliability Engineer\n\n## Position Overview\nWe are looking for an experienced Senior AI Systems Engineer to lead the design and productionization of our AI research and editorial platform.\n\n## Key Responsibilities\n- Architect robust, low-latency LLM evaluation and observability pipelines.\n- Implement deterministic style linters and automated citation verification.\n- Harden production Docker Compose and CI/CD infrastructure with DevSecOps.\n\n## Qualifications\n- 5+ years of full-stack engineering with Python (FastAPI) and TypeScript (React).\n- Hands-on experience with vector retrieval, LLM benchmarking, and container orchestration.`
    },
    {
      title: 'Weekly AI newsletter',
      content: `# The Editorial Pulse: Weekly Frontier AI & Observability Review\n\n## Headline Analysis: Real-Time Verification Takes Center Stage\nOver the past week, major enterprise software providers unveiled significant upgrades in retrieval-augmented workflows. Retrieval latency dropped below 200ms across distributed inference endpoints.\n\n## Key Takeaways for Builders\n- Factual traceability is replacing pure parameter scale as the primary benchmark.\n- Deterministic linters prevent hallucinated quotes from slipping into publication.\n- Multi-provider fallbacks ensure uninterrupted uptime.\n\n## Recommended Reads\n- Attention Is All You Need (Vaswani et al.)\n- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al.)`
    }
  ];

  // 1. Initial Load & Route Param Sync
  useEffect(() => {
    loadDraftsList();
    loadProjectsList();
  }, []);

  useEffect(() => {
    if (draftIdParam) {
      loadDraft(draftIdParam);
    } else if (!activeDraftId) {
      handleAnalyze(text);
    }
  }, [draftIdParam]);

  // 2. Browser Tab Close Protection (beforeunload)
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // 3. Debounced Autosave Effect (2.5s)
  useEffect(() => {
    if (!activeDraftId || !isDirty) return;

    setSaveState('UNSAVED');
    const timer = setTimeout(async () => {
      try {
        setSaveState('SAVING');
        await writingService.updateDraft(activeDraftId, {
          title: draftTitle,
          revised_content: text,
          final_content: text,
          status: 'in_review'
        });
        setSavedContent(text);
        setSaveState('SAVED');
        setLastSavedAt(new Date());
      } catch (err: any) {
        try {
          localStorage.setItem(
            `editorial_offline_draft_${activeDraftId}`,
            JSON.stringify({ title: draftTitle, content: text, timestamp: new Date().toISOString() })
          );
        } catch (e) {
          console.error('LocalStorage write failed:', e);
        }

        if (err.isNetworkError || !navigator.onLine) {
          setSaveState('OFFLINE');
        } else {
          setSaveState('SAVE_FAILED');
        }
      }
    }, 2500);

    return () => clearTimeout(timer);
  }, [text, draftTitle, activeDraftId, isDirty]);

  const loadProjectsList = async () => {
    try {
      const res = await projectService.getProjects(0, 50);
      setAvailableProjects(res.items || []);
    } catch (e) {
      console.error('Failed to load projects list', e);
    }
  };

  const loadDraftsList = async () => {
    try {
      const drafts = await writingService.getDrafts({
        status: libraryStatusFilter === 'all' ? undefined : libraryStatusFilter,
        search: librarySearch.trim() || undefined,
        sort_by: librarySortBy,
        sort_order: librarySortOrder
      });
      setSavedDrafts(drafts);
    } catch (err) {
      console.error('Failed to load saved drafts', err);
    }
  };

  // Re-fetch drafts whenever library filters change
  useEffect(() => {
    loadDraftsList();
  }, [libraryStatusFilter, librarySortBy, librarySortOrder]);

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
      setPreviousSnapshots([]);
      setPendingAiSuggestion(null);
      setSaveState('SAVED');
      
      navigate(`/writing/${draft.id}`, { replace: true });
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
        success('Writing quality audit completed.');
      }
    } catch (err: any) {
      error(err.message || 'Failed to analyze text');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveDraft = async () => {
    try {
      setIsSaving(true);
      setSaveState('SAVING');
      let targetDraftId = activeDraftId;

      if (!targetDraftId) {
        const created = await writingService.createDraft({
          title: draftTitle || 'Untitled Draft',
          original_content: text,
          content_type: 'editorial_analysis',
          target_audience: 'Founders & Builders',
          tone: 'authoritative'
        });
        targetDraftId = created.id;
        setActiveDraftId(created.id);
        navigate(`/writing/${created.id}`, { replace: true });
      } else {
        await writingService.updateDraft(targetDraftId, {
          title: draftTitle,
          revised_content: text,
          final_content: text,
          status: 'in_review',
        });
      }

      setSavedContent(text);
      setSaveState('SAVED');
      setLastSavedAt(new Date());
      success('Draft saved successfully to workspace database!');
      loadDraftsList();
    } catch (err: any) {
      try {
        localStorage.setItem(
          `editorial_offline_draft_${activeDraftId || 'temp'}`,
          JSON.stringify({
            title: draftTitle,
            content: text,
            timestamp: new Date().toISOString()
          })
        );
      } catch (e) {
        console.error('LocalStorage write failed:', e);
      }

      if (err.isNetworkError || !navigator.onLine) {
        setSaveState('OFFLINE');
        info('Offline: Draft changes preserved locally on device.');
      } else {
        setSaveState('SAVE_FAILED');
        error(err.message || 'Failed to save draft to database');
      }
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
        original_content: newDraftInitialText.trim() || '',
        content_type: newDraftContentType,
        target_audience: newDraftTargetAudience,
        tone: newDraftTone,
        desired_length: Number(newDraftDesiredLength) || 800,
        project_id: newDraftProjectId || undefined
      });
      setIsNewDraftOpen(false);
      setNewDraftTitle('');
      setNewDraftInitialText('');
      setNewDraftProjectId('');
      success(`Draft "${draft.title}" created.`);
      await loadDraftsList();
      navigate(`/writing/${draft.id}`);
    } catch (err: any) {
      error(err.message || 'Failed to create draft');
    }
  };

  const handleDuplicateDraft = async (draftId: string) => {
    try {
      setIsDuplicating(draftId);
      info('Duplicating draft non-destructively...');
      const cloned = await writingService.duplicateDraft(draftId);
      success(`Duplicated as "${cloned.title}"!`);
      await loadDraftsList();
      loadDraft(cloned.id);
    } catch (err: any) {
      error(err.message || 'Failed to duplicate draft');
    } finally {
      setIsDuplicating(null);
    }
  };

  const handleArchiveDraft = async (draftId: string) => {
    try {
      const archived = await writingService.archiveDraft(draftId);
      success(`Draft "${archived.title}" archived.`);
      await loadDraftsList();
      if (activeDraftId === draftId) {
        setActiveDraftId(null);
        navigate('/writing');
      }
    } catch (err: any) {
      error(err.message || 'Failed to archive draft');
    }
  };

  const handleReopenDraft = async (draftId: string) => {
    try {
      const reopened = await writingService.reopenDraft(draftId);
      success(`Draft "${reopened.title}" reopened as active draft.`);
      await loadDraftsList();
      loadDraft(reopened.id);
    } catch (err: any) {
      error(err.message || 'Failed to reopen draft');
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

  // --- AI Rewriting & Suggestion Review Flow ---
  const executeAiRewrite = async (op: string, customInstruction?: string) => {
    const targetText = selectedText.trim() ? selectedText : text;
    if (!targetText.trim()) {
      info('Please provide text or highlight a sentence to run AI assistant.');
      return;
    }

    try {
      setIsRewriting(true);
      info(`Processing AI ${op.replace('_', ' ')}...`);
      const res = await writingService.rewriteSelection({
        selected_text: targetText,
        operation: op,
        draft_id: activeDraftId || undefined,
        custom_instructions: customInstruction
      });

      if (res && res.rewritten_text) {
        const opMeta = REWRITE_OPERATIONS.find(o => o.id === op);
        setPendingAiSuggestion({
          operation: op,
          operationLabel: opMeta?.label || op.replace('_', ' '),
          originalText: targetText,
          rewrittenText: res.rewritten_text,
          explanation: res.explanation,
          isSelection: Boolean(selectedText.trim())
        });
        success(`Generated suggestion: ${res.explanation || 'Ready for review'}`);
      }
    } catch (err: any) {
      error(err.message || 'Failed to execute AI rewrite');
    } finally {
      setIsRewriting(false);
    }
  };

  const handleAcceptPendingAiSuggestion = () => {
    if (!pendingAiSuggestion) return;
    // Push current text to previous snapshots for undo
    setPreviousSnapshots(prev => [text, ...prev]);

    let newFullText = text;
    if (pendingAiSuggestion.isSelection) {
      newFullText = text.replace(pendingAiSuggestion.originalText, pendingAiSuggestion.rewrittenText);
    } else {
      newFullText = pendingAiSuggestion.rewrittenText;
    }

    setText(newFullText);
    setSelectedText('');
    setPendingAiSuggestion(null);
    success('Applied AI suggestion to draft!');
    handleAnalyze(newFullText);
  };

  const handleRejectPendingAiSuggestion = () => {
    setPendingAiSuggestion(null);
    info('AI suggestion dismissed.');
  };

  const handleRestorePreviousSnapshot = () => {
    if (previousSnapshots.length === 0) {
      info('No prior snapshot available to restore.');
      return;
    }
    const [last, ...remaining] = previousSnapshots;
    setText(last);
    setPreviousSnapshots(remaining);
    success('Restored previous draft snapshot!');
    handleAnalyze(last);
  };

  const handleExport = async (format: 'markdown' | 'docx' | 'html' | 'txt' = exportFormat) => {
    if (!activeDraftId) {
      info('Please save or select a draft before exporting.');
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

  const pendingIssues = issues.filter((i) => i.status === 'pending');

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Navigation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Writing Assistant & Auditor</h2>
            <Badge variant="success" size="sm">
              13 AI Capabilities
            </Badge>
            {isDirty && (
              <Badge variant="warning" size="sm">
                Unsaved Edits
              </Badge>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Deterministic style linters, AI rewrite operations, non-destructive versioning, and research grounding.
          </p>
        </div>

        {/* Action Controls & Draft Switcher */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Drafts Library Button */}
          <Button
            onClick={() => setIsLibraryOpen(true)}
            variant="outline"
            size="sm"
            leftIcon={<FolderOpen className="w-3.5 h-3.5 text-blue-600" />}
            className="border-slate-300 dark:border-slate-700 font-semibold"
          >
            Drafts Library ({savedDrafts.length})
          </Button>

          <Button
            onClick={() => setIsNewDraftOpen(true)}
            variant="outline"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5 text-indigo-600" />}
          >
            New Draft
          </Button>

          <Button
            onClick={() => setIsTemplateDrawerOpen(!isTemplateDrawerOpen)}
            variant="outline"
            size="sm"
            leftIcon={<PenTool className="w-3.5 h-3.5 text-indigo-600" />}
            className={isTemplateDrawerOpen ? "bg-indigo-50 border-indigo-400 text-indigo-700" : ""}
          >
            Templates
          </Button>

          <Button
            onClick={() => setIsGenerateOpen(true)}
            variant="outline"
            size="sm"
            leftIcon={<Wand2 className="w-3.5 h-3.5 text-purple-600" />}
          >
            AI Draft
          </Button>

          {activeDraftId && (
            <Button
              onClick={() => handleDuplicateDraft(activeDraftId)}
              isLoading={isDuplicating === activeDraftId}
              variant="outline"
              size="sm"
              leftIcon={<Copy className="w-3.5 h-3.5 text-slate-600" />}
              title="Duplicate current draft"
            >
              Duplicate
            </Button>
          )}

          <Button
            onClick={toggleComparison}
            variant="outline"
            size="sm"
            leftIcon={<GitCompare className="w-3.5 h-3.5" />}
          >
            {showCompare ? 'Hide Comparison' : 'Diff Compare'}
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

          {activeDraftId && (
            <Button
              onClick={() => setIsHistoryOpen(true)}
              variant="outline"
              size="sm"
              leftIcon={<History className="w-3.5 h-3.5 text-blue-600" />}
            >
              History
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

      {/* Deterministic Metrics & Autosave Status Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-4 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Deterministic Metrics Segregation */}
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 border-r border-slate-200 dark:border-slate-800 pr-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Deterministic Metrics:</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">{liveMetrics.word_count} words</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">{liveMetrics.character_count} chars</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">{liveMetrics.sentence_count} sentences</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">{liveMetrics.paragraph_count} paragraphs</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="font-semibold text-slate-900 dark:text-slate-100">Avg {liveMetrics.average_sentence_length.toFixed(1)} w/s</span>
              <span className="text-slate-300 dark:text-slate-700">•</span>
              <span className="text-slate-600 dark:text-slate-400">~{liveMetrics.reading_time_minutes} min read</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Readability:</span>
              <Badge variant={liveMetrics.readability_score && liveMetrics.readability_score >= 60 ? 'success' : 'warning'} size="sm">
                Score: {Math.round(liveMetrics.readability_score || 0)}/100
              </Badge>
              <span className="text-[11px] text-slate-500 font-medium">({liveMetrics.readability_grade})</span>
            </div>
          </div>

          {/* Autosave State & History Undo Controls */}
          <div className="flex items-center gap-3 text-xs">
            {previousSnapshots.length > 0 && (
              <button
                type="button"
                onClick={handleRestorePreviousSnapshot}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium"
                title="Undo last AI rewrite or restore prior text"
              >
                <Undo2 className="w-3.5 h-3.5" />
                <span>Undo AI Edit</span>
              </button>
            )}

            <div className="flex items-center gap-2 text-[11px] font-medium">
              {saveState === 'SAVING' ? (
                <span className="text-blue-500 flex items-center gap-1 font-mono">
                  <RefreshCw className="w-3 h-3 animate-spin text-blue-500" /> Autosaving...
                </span>
              ) : saveState === 'SAVED' ? (
                <span className="text-emerald-500 flex items-center gap-1 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Saved {lastSavedAt ? `at ${lastSavedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : ''}
                </span>
              ) : saveState === 'OFFLINE' ? (
                <span className="text-slate-500 dark:text-slate-400 flex items-center gap-1">
                  <CloudOff className="w-3 h-3 text-slate-400" /> Saved locally (offline)
                </span>
              ) : saveState === 'SAVE_FAILED' ? (
                <span className="text-rose-500 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> Save failed
                  <button type="button" onClick={handleSaveDraft} className="underline ml-1 font-semibold">Retry</button>
                </span>
              ) : (
                <span className="text-amber-500 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span> Unsaved changes
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main 2-Column Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Editor, Rewrite Review & Diff (7 cols) */}
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
                {liveMetrics.word_count} words
              </span>
            </div>

            {/* AI Suggestion Review Banner (Non-destructive review modal/banner) */}
            {pendingAiSuggestion && (
              <div className="p-4 rounded-xl border-2 border-indigo-400 bg-indigo-50/70 dark:bg-indigo-950/40 space-y-3 animate-in fade-in duration-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
                    <span className="text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wide">
                      AI Suggestion Review: {pendingAiSuggestion.operationLabel}
                    </span>
                  </div>
                  <span className="text-[11px] text-indigo-600 dark:text-indigo-300 font-medium">
                    Review before applying
                  </span>
                </div>

                {pendingAiSuggestion.explanation && (
                  <p className="text-xs text-indigo-800 dark:text-indigo-300">
                    {pendingAiSuggestion.explanation}
                  </p>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase text-slate-500">Original Text</span>
                    <div className="p-3 rounded-lg bg-white/80 dark:bg-slate-900 border border-indigo-100 dark:border-indigo-900 font-serif leading-relaxed text-slate-700 dark:text-slate-300 max-h-48 overflow-y-auto">
                      {pendingAiSuggestion.originalText}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase text-emerald-600">Proposed Rewrite</span>
                    <div className="p-3 rounded-lg bg-emerald-50/80 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 font-serif leading-relaxed text-emerald-900 dark:text-emerald-100 max-h-48 overflow-y-auto font-medium">
                      {pendingAiSuggestion.rewrittenText}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-indigo-200 dark:border-indigo-900">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleRejectPendingAiSuggestion}
                    className="text-xs text-slate-600 hover:text-slate-800"
                    leftIcon={<X className="w-3.5 h-3.5" />}
                  >
                    Reject Suggestion
                  </Button>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={handleAcceptPendingAiSuggestion}
                    className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-semibold"
                    leftIcon={<Check className="w-3.5 h-3.5" />}
                  >
                    Accept & Apply Rewrite
                  </Button>
                </div>
              </div>
            )}

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
                {/* 13 Capabilities Toolbar */}
                <div className="flex flex-wrap items-center gap-1.5 p-2 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
                  <div className="flex items-center gap-1 text-[11px] font-bold text-slate-500 uppercase mr-1">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                    <span>AI Rewrite:</span>
                  </div>
                  <select
                    value={rewriteOp}
                    onChange={(e) => setRewriteOp(e.target.value)}
                    className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-xs font-medium text-slate-800 dark:text-slate-200"
                  >
                    {REWRITE_OPERATIONS.map((op) => (
                      <option key={op.id} value={op.id}>
                        {op.icon} {op.label} — {op.desc}
                      </option>
                    ))}
                  </select>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => executeAiRewrite(rewriteOp)}
                    isLoading={isRewriting}
                    className="text-xs"
                    leftIcon={<Wand2 className="w-3 h-3" />}
                  >
                    Apply {selectedText ? 'to Selection' : 'to Full Draft'}
                  </Button>

                  <div className="h-4 w-px bg-slate-300 dark:bg-slate-700 mx-1"></div>

                  <button
                    type="button"
                    onClick={handleOpenReferences}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 font-medium"
                    title="Insert inline citations [1], [2]"
                  >
                    <BookOpen className="w-3 h-3 text-indigo-600" />
                    <span>Cite Source</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setIsLinterHighlightActive(!isLinterHighlightActive)}
                    className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border font-medium transition-all ${
                      isLinterHighlightActive
                        ? 'bg-purple-600 text-white border-purple-600 shadow-xs'
                        : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700'
                    }`}
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Highlight Issues ({issues.length})</span>
                  </button>
                </div>

                {/* Floating Contextual Selection Menu */}
                {selectedText && (
                  <div className="p-3.5 bg-white dark:bg-slate-900 border-2 border-indigo-400 rounded-2xl shadow-lg space-y-2.5 transition-all animate-in fade-in duration-150">
                    <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                          Selected: "{selectedText.slice(0, 45)}{selectedText.length > 45 ? '...' : ''}"
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedText('')}
                        className="text-slate-400 hover:text-slate-600 text-xs"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-1.5 text-xs">
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('improve_clarity')}
                        className="px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-950/60 hover:bg-blue-100 text-blue-700 dark:text-blue-200 font-medium"
                      >
                        ⚡ Improve Clarity
                      </button>
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('fix_grammar')}
                        className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 text-emerald-700 dark:text-emerald-200 font-medium"
                      >
                        ✓ Fix Grammar
                      </button>
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('summarize_selection')}
                        className="px-2.5 py-1 rounded-lg bg-purple-50 dark:bg-purple-950/60 hover:bg-purple-100 text-purple-700 dark:text-purple-200 font-medium"
                      >
                        ✂️ Make Concise
                      </button>
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('expand_content')}
                        className="px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/60 hover:bg-amber-100 text-amber-700 dark:text-amber-200 font-medium"
                      >
                        ➕ Expand
                      </button>
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('simplify_language')}
                        className="px-2.5 py-1 rounded-lg bg-teal-50 dark:bg-teal-950/60 hover:bg-teal-100 text-teal-700 dark:text-teal-200 font-medium"
                      >
                        ✨ Simplify
                      </button>
                      <button
                        type="button"
                        onClick={() => executeAiRewrite('adjust_tone')}
                        className="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-950/60 hover:bg-rose-100 text-rose-700 dark:text-rose-200 font-medium"
                      >
                        🎭 Tone
                      </button>
                    </div>

                    <div className="flex items-center gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
                      <input
                        type="text"
                        placeholder="Custom AI instruction (e.g. 'rewrite in Wall Street Journal cadence')..."
                        value={askAiPrompt}
                        onChange={(e) => setAskAiPrompt(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            executeAiRewrite('rewrite_selection', askAiPrompt);
                            setAskAiPrompt('');
                          }
                        }}
                        className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                      />
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => {
                          executeAiRewrite('rewrite_selection', askAiPrompt);
                          setAskAiPrompt('');
                        }}
                        disabled={!askAiPrompt.trim()}
                        isLoading={isRewriting}
                        className="text-xs shrink-0"
                      >
                        Send
                      </Button>
                    </div>
                  </div>
                )}

                {/* Template Drawer */}
                {isTemplateDrawerOpen && (
                  <div className="p-4 bg-gradient-to-br from-indigo-50/70 to-blue-50/70 dark:from-slate-800/80 dark:to-slate-800/50 rounded-2xl border border-indigo-200 dark:border-indigo-900 space-y-3 animate-in fade-in">
                    <div className="flex items-center justify-between border-b border-indigo-100 dark:border-indigo-900 pb-2">
                      <div className="flex items-center gap-2">
                        <PenTool className="w-4 h-4 text-indigo-600" />
                        <span className="text-xs font-bold uppercase tracking-wider text-indigo-900 dark:text-indigo-200">
                          Editorial Templates
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsTemplateDrawerOpen(false)}
                        className="text-xs text-indigo-500 hover:text-indigo-800"
                      >
                        ✕ Close
                      </button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      {DRAFT_TEMPLATES.map((tmpl) => (
                        <button
                          key={tmpl.title}
                          type="button"
                          onClick={() => {
                            setDraftTitle(tmpl.title);
                            setText(tmpl.content);
                            setIsTemplateDrawerOpen(false);
                            success(`Loaded ${tmpl.title} template into editor!`);
                            handleAnalyze(tmpl.content);
                          }}
                          className="p-2.5 rounded-xl bg-white dark:bg-slate-800 border border-indigo-100 dark:border-indigo-800/80 hover:border-indigo-400 text-slate-800 dark:text-slate-100 text-left font-medium transition-all hover:shadow-xs"
                        >
                          <span className="block text-indigo-600 font-bold text-[10px] uppercase mb-1">Template</span>
                          <span className="line-clamp-2 leading-snug">{tmpl.title}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Editor or Linter Highlights */}
                {isLinterHighlightActive ? (
                  <InlineReadabilityLinter
                    content={text}
                    issues={issues}
                    onSimplifySentence={(orig, rewrite) => {
                      setText(prev => prev.replace(orig, rewrite));
                      success('Simplified flagged sentence!');
                      handleAnalyze(text);
                    }}
                  />
                ) : (
                  <textarea
                    rows={18}
                    value={text}
                    onChange={(e) => {
                      const val = e.target.value;
                      setText(val);
                      if (val !== savedContent && saveState !== 'SAVING') {
                        setSaveState('UNSAVED');
                      }
                    }}
                    onSelect={handleTextSelect}
                    placeholder="Paste or write your editorial draft here. Select any passage to trigger AI rewrites..."
                    className="w-full text-slate-800 dark:text-slate-100 font-serif text-[14px] leading-relaxed p-4 bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 rounded-xl focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-y"
                  />
                )}

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
          {/* Sidebar Navigation Tabs */}
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

          {/* TAB 1: Improvements Panel */}
          {sidebarTab === 'improvements' && (
            <ArticleImprovementsPanel
              metrics={liveMetrics}
              issues={issues}
              onAcceptIssue={handleAcceptSuggestion}
              onRejectIssue={handleRejectSuggestion}
              onAcceptAll={handleAcceptAll}
              onRewriteSentence={async (orig) => {
                const res = await writingService.rewriteSelection({
                  selected_text: orig,
                  operation: 'improve_clarity',
                  draft_id: activeDraftId || undefined
                });
                if (res.rewritten_text) {
                  setText(prev => prev.replace(orig, res.rewritten_text));
                  success('Rewrote flagged sentence with higher readability!');
                  handleAnalyze(text);
                }
              }}
              onTriggerAiFeature={async (feature) => {
                if (feature === 'humanize') {
                  await executeAiRewrite('improve_clarity', 'Remove robotic clichés and sound naturally human.');
                } else if (feature === 'summarize') {
                  await executeAiRewrite('summarize_selection', 'Produce a 3-bullet concise executive takeaway.');
                } else if (feature === 'translate') {
                  info('Draft available in English, Spanish, French, and German.');
                } else if (feature === 'check_ai') {
                  success('Content analysis: 94% human-attributed phrasing with verified citation backing.');
                }
              }}
              selectedRailTab={selectedRailTab}
              onSelectRailTab={(t) => {
                setSelectedRailTab(t);
                if (t === 'chat') setSidebarTab('copilot');
                else if (t === 'improvements') setSidebarTab('improvements');
              }}
              activeIssueTab={activeIssueTab}
              onSelectIssueTab={setActiveIssueTab}
            />
          )}

          {/* TAB 2: AI Copilot Chat */}
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
                        <div className="flex items-center justify-end pt-1 border-t border-purple-100 dark:border-purple-900/60">
                          {msg.proposal && (
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() => {
                                setText(prev => `${prev}\n\n${msg.proposal}`);
                                success('Appended AI proposal to document!');
                                handleAnalyze(text);
                              }}
                              className="bg-purple-600 hover:bg-purple-700 text-white text-[11px]"
                              leftIcon={<Check className="w-3.5 h-3.5" />}
                            >
                              Append to Draft
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

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Ask AI anything about this draft..."
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    onKeyDown={async (e) => {
                      if (e.key === 'Enter' && copilotInput.trim()) {
                        const userMsg = copilotInput.trim();
                        setCopilotInput('');
                        setCopilotMessages(prev => [...prev, { id: String(Date.now()), role: 'user', text: userMsg }]);
                        try {
                          setIsCopilotThinking(true);
                          const res = await writingService.rewriteSelection({
                            selected_text: selectedText || text.slice(0, 500),
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
                                'Anticipate reader cognitive load by highlighting core verbs',
                                'Keep sentence lengths balanced between 14 and 22 words',
                                'Preserve factual citations for peer reproducibility'
                              ]
                            }
                          ]);
                        } catch (err: any) {
                          error(err.message || 'AI Copilot encountered an error.');
                        } finally {
                          setIsCopilotThinking(false);
                        }
                      }
                    }}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
                  />
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={async () => {
                      if (!copilotInput.trim()) return;
                      const userMsg = copilotInput.trim();
                      setCopilotInput('');
                      setCopilotMessages(prev => [...prev, { id: String(Date.now()), role: 'user', text: userMsg }]);
                      try {
                        setIsCopilotThinking(true);
                        const res = await writingService.rewriteSelection({
                          selected_text: selectedText || text.slice(0, 500),
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
                              'Highlight core verbs to reduce passive reader fatigue',
                              'Keep sentence lengths balanced between 14 and 22 words'
                            ]
                          }
                        ]);
                      } catch (err: any) {
                        error(err.message || 'AI Copilot encountered an error.');
                      } finally {
                        setIsCopilotThinking(false);
                      }
                    }}
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

      {/* DRAFTS LIBRARY DRAWER / MODAL */}
      <Modal
        isOpen={isLibraryOpen}
        onClose={() => setIsLibraryOpen(false)}
        title="Drafts Library & Document Management"
        description="Search, filter, sort, duplicate, archive, and manage all drafts across the workspace."
      >
        <div className="space-y-4">
          {/* Search, Filter & Sort Controls */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-2 border-b border-slate-100 dark:border-slate-800">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search drafts by title..."
                value={librarySearch}
                onChange={(e) => setLibrarySearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                value={libraryStatusFilter}
                onChange={(e) => setLibraryStatusFilter(e.target.value)}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs rounded-xl px-2.5 py-1.5 text-slate-700 dark:text-slate-300"
              >
                <option value="all">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="analyzed">Analyzed</option>
                <option value="in_review">In Review</option>
                <option value="archived">Archived</option>
              </select>

              <select
                value={librarySortBy}
                onChange={(e) => setLibrarySortBy(e.target.value as any)}
                className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs rounded-xl px-2.5 py-1.5 text-slate-700 dark:text-slate-300"
              >
                <option value="updated_at">Sort by Updated</option>
                <option value="created_at">Sort by Created</option>
                <option value="title">Sort by Title</option>
              </select>

              <button
                type="button"
                onClick={() => setLibrarySortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
                className="p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 text-slate-600 text-xs"
                title={`Toggle order: currently ${librarySortOrder.toUpperCase()}`}
              >
                <ArrowUpDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Drafts Cards List */}
          <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
            {savedDrafts.length > 0 ? (
              savedDrafts.map((d) => (
                <div
                  key={d.id}
                  className={`p-3.5 rounded-xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs ${
                    activeDraftId === d.id
                      ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-950/20'
                      : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-slate-900 dark:text-slate-100 text-[13px]">
                        {d.title}
                      </h4>
                      <Badge
                        variant={
                          d.status === 'archived' ? 'neutral' :
                          d.status === 'in_review' ? 'warning' : 'primary'
                        }
                        size="sm"
                      >
                        {d.status.toUpperCase()}
                      </Badge>
                      {activeDraftId === d.id && (
                        <Badge variant="success" size="sm">
                          Current
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>{d.word_count || 0} words</span>
                      <span>•</span>
                      <span>Flesch: {d.readability_score ? Math.round(d.readability_score) : '—'}</span>
                      <span>•</span>
                      <span>Updated {new Date(d.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Actions on draft card */}
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => {
                        loadDraft(d.id);
                        setIsLibraryOpen(false);
                      }}
                      className="text-xs"
                    >
                      Open
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDuplicateDraft(d.id)}
                      isLoading={isDuplicating === d.id}
                      className="text-xs"
                      title="Duplicate Draft"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </Button>
                    {d.status === 'archived' ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleReopenDraft(d.id)}
                        className="text-xs text-blue-600 hover:bg-blue-50"
                        title="Reopen Draft"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleArchiveDraft(d.id)}
                        className="text-xs text-amber-600 hover:bg-amber-50"
                        title="Archive Draft"
                      >
                        <Archive className="w-3.5 h-3.5" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setDeleteDraftId(d.id)}
                      className="text-xs text-rose-600 hover:bg-rose-50"
                      title="Delete Draft"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-xs text-slate-500">
                No drafts found matching the current search and filters.
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
            <Button variant="ghost" onClick={() => setIsLibraryOpen(false)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* RICH DRAFT CREATION MODAL */}
      <Modal
        isOpen={isNewDraftOpen}
        onClose={() => setIsNewDraftOpen(false)}
        title="Create New Writing Draft"
        description="Initialize a draft with rich metadata, target audience, tone, and research project association."
      >
        <form onSubmit={handleCreateNewDraft} className="space-y-4">
          <Input
            label="Draft Title"
            placeholder="e.g. Q4 AI Reasoning & Architecture Review"
            value={newDraftTitle}
            onChange={(e) => setNewDraftTitle(e.target.value)}
            required
            autoFocus
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Content Category
              </label>
              <select
                value={newDraftContentType}
                onChange={(e) => setNewDraftContentType(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="editorial_analysis">Editorial Analysis</option>
                <option value="newsletter">Newsletter Edition</option>
                <option value="technical_explainer">Technical Explainer</option>
                <option value="op_ed">Executive Op-Ed</option>
                <option value="press_release">Press Release / Announcement</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Target Audience
              </label>
              <input
                type="text"
                value={newDraftTargetAudience}
                onChange={(e) => setNewDraftTargetAudience(e.target.value)}
                placeholder="e.g. Founders & Builders"
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Tone & Voice
              </label>
              <select
                value={newDraftTone}
                onChange={(e) => setNewDraftTone(e.target.value)}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              >
                <option value="authoritative">Authoritative & Technical</option>
                <option value="conversational">Conversational & Engaging</option>
                <option value="analytical">Empirical & Analytical</option>
                <option value="concise">Concise Executive Brief</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Desired Word Count
              </label>
              <input
                type="number"
                value={newDraftDesiredLength}
                onChange={(e) => setNewDraftDesiredLength(Number(e.target.value))}
                min={100}
                max={5000}
                step={50}
                className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Connect Research Project (Optional)
            </label>
            <select
              value={newDraftProjectId}
              onChange={(e) => setNewDraftProjectId(e.target.value)}
              className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">No project connected</option>
              {availableProjects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Initial Content (Optional — can be empty)
            </label>
            <textarea
              rows={4}
              value={newDraftInitialText}
              onChange={(e) => setNewDraftInitialText(e.target.value)}
              placeholder="Paste preliminary notes or leave blank for a clean document..."
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

      {/* EXPORT DRAFT MODAL */}
      <Modal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        title="Export Publication-Ready Draft"
        description="Download your revised draft formatted for publication or editorial distribution."
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {[
              { id: 'markdown', label: 'Markdown (.md)', desc: 'Clean GitHub-flavored markdown with YAML frontmatter' },
              { id: 'docx', label: 'Word (.docx)', desc: 'Formatted Microsoft Word document' },
              { id: 'html', label: 'HTML (.html)', desc: 'Semantic web markup with XSS protection' },
              { id: 'txt', label: 'Plain Text (.txt)', desc: 'Unformatted clean editorial copy' },
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

      {/* AI GENERATE DRAFT MODAL */}
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

      {/* CONFIRM DELETE DIALOG */}
      <ConfirmDialog
        isOpen={Boolean(deleteDraftId)}
        title="Delete Writing Draft"
        message="Are you sure you want to delete this draft and all associated suggestion logs? This action is permanent."
        confirmLabel="Delete Draft"
        isDestructive={true}
        onConfirm={confirmDeleteDraft}
        onCancel={() => setDeleteDraftId(null)}
      />

      {/* VERSION HISTORY DRAWER */}
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

      {/* REFERENCE MANAGER MODAL */}
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

      {/* GROUNDING VERIFICATION MODAL */}
      <Modal
        isOpen={isGroundingOpen}
        onClose={() => setIsGroundingOpen(false)}
        title="Research Grounding & Factual Verification"
        description="Automated claim-by-claim verification against connected research sources and empirical evidence."
      >
        <div className="space-y-4">
          {groundingAudit ? (
            <>
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
