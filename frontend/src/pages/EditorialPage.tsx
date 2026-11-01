import React, { useState, useEffect } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { 
  Newspaper, 
  Sparkles, 
  Save, 
  Download, 
  ExternalLink, 
  PenTool, 
  Loader2, 
  CheckCircle2, 
  BookOpen, 
  Copy, 
  Share2,
  FileCode,
  FileText,
  Trash2,
  Plus,
  Clock,
  History,
  AlertTriangle,
  Network
} from 'lucide-react';
import { projectService } from '../services/projectService';
import { researchService } from '../services/researchService';
import { editorialService } from '../services/editorialService';
import { intelligenceService } from '../services/intelligenceService';
import { 
  Project, 
  ResearchBrief, 
  EditorialOutput, 
  HeadlineOption, 
  EditorialExportResponse,
  ContradictionItem,
  TrendItem
} from '../types';
import { useToast } from '../components/common/Toast';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { HeadlineSelector } from '../components/editorial/HeadlineSelector';
import { EditorialGenerator } from '../components/editorial/EditorialGenerator';
import { EditorialEditor } from '../components/editorial/EditorialEditor';
import { EditorialPreview } from '../components/editorial/EditorialPreview';
import { EditorialReviewPanel } from '../components/editorial/EditorialReviewPanel';
import { EditorialToolbar } from '../components/editorial/EditorialToolbar';
import { SourceReferences } from '../components/editorial/SourceReferences';
import { ExportMenu } from '../components/editorial/ExportMenu';

export const EditorialPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { editorialId: routeEditorialId } = useParams<{ editorialId?: string }>();
  const projectIdParam = searchParams.get('projectId');
  const angleParam = searchParams.get('angle');
  const navigate = useNavigate();
  const { success, error, info } = useToast();

  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [sourcesList, setSourcesList] = useState<any[]>([]);
  
  // Editorial Content & Generation State
  const [headline, setHeadline] = useState('');
  const [content, setContent] = useState('');
  const [savedContent, setSavedContent] = useState('');
  const [wordCount, setWordCount] = useState(0);
  const [activeEditorial, setActiveEditorial] = useState<EditorialOutput | null>(null);
  const [savedEditorials, setSavedEditorials] = useState<EditorialOutput[]>([]);
  const [viewMode, setViewMode] = useState<'edit' | 'preview' | 'review'>('edit');
  const [contradictions, setContradictions] = useState<ContradictionItem[]>([]);
  const [trends, setTrends] = useState<TrendItem[]>([]);

  // Generator Config
  const [audience, setAudience] = useState('founders, builders, and operators');
  const [tone, setTone] = useState('Newsletter-style');
  const [minWords, setMinWords] = useState(300);
  const [maxWords, setMaxWords] = useState(500);
  const [headlineOptions, setHeadlineOptions] = useState<HeadlineOption[]>([]);

  // Modals & Loaders
  const [isGeneratingHeadlines, setIsGeneratingHeadlines] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportData, setExportData] = useState<EditorialExportResponse | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [deleteEditorialId, setDeleteEditorialId] = useState<string | null>(null);

  const isDirty = content !== savedContent;

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (projects.length > 0) {
      if (projectIdParam) {
        selectProject(projectIdParam);
      } else {
        selectProject(projects[0].id);
      }
    }
  }, [projectIdParam, projects.length]);

  useEffect(() => {
    if (routeEditorialId) {
      loadSpecificEditorial(routeEditorialId);
    }
  }, [routeEditorialId]);

  const loadProjects = async () => {
    try {
      const res = await projectService.getProjects();
      setProjects(res.items);
    } catch (err) {
      console.error('Failed to load projects', err);
    }
  };

  const selectProject = async (id: string) => {
    try {
      setSearchParams({ projectId: id, ...(angleParam ? { angle: angleParam } : {}) });
      const proj = await projectService.getProject(id);
      setActiveProject(proj);
      setSourcesList(proj.sources || []);

      // Load project editorials
      loadProjectEditorials(id);

      // Load Brief
      try {
        const b = await researchService.getBrief(id);
        setBrief(b);
        if (b && !headline) {
          // Preload headlines
          loadHeadlineOptions(id, b.id);
        }
      } catch {
        setBrief(null);
        setHeadlineOptions([]);
      }

      // Load Intelligence data
      try {
        const [contras, trs] = await Promise.all([
          intelligenceService.getContradictions(id),
          intelligenceService.getTrends(id)
        ]);
        setContradictions(contras);
        setTrends(trs);
      } catch {
        setContradictions([]);
        setTrends([]);
      }
    } catch (err) {
      console.error('Failed to load project details', err);
    }
  };

  const loadProjectEditorials = async (projectId: string) => {
    try {
      const list = await editorialService.getEditorials(projectId);
      setSavedEditorials(list);
      if (list.length > 0 && !activeEditorial && !routeEditorialId) {
        applyEditorial(list[0]);
      }
    } catch (err) {
      console.error('Failed to load project editorials', err);
    }
  };

  const loadSpecificEditorial = async (id: string) => {
    try {
      const ed = await editorialService.getEditorial(id);
      applyEditorial(ed);
      if (ed.project_id && (!activeProject || activeProject.id !== ed.project_id)) {
        selectProject(ed.project_id);
      }
    } catch (err) {
      console.error('Failed to load specific editorial', err);
    }
  };

  const applyEditorial = (ed: EditorialOutput) => {
    setActiveEditorial(ed);
    setHeadline(ed.headline);
    setContent(ed.content);
    setSavedContent(ed.content);
    setWordCount(ed.word_count);
  };

  const loadHeadlineOptions = async (projectId: string, briefId?: string) => {
    try {
      setIsGeneratingHeadlines(true);
      const res = await editorialService.generateHeadlines({
        project_id: projectId,
        research_brief_id: briefId,
        audience,
        editorial_angle: angleParam || undefined,
        tone,
      });
      setHeadlineOptions(res.headlines);
      if (res.headlines.length > 0 && !headline) {
        setHeadline(res.recommended_headline || res.headlines[0].headline);
      }
    } catch (err) {
      console.error('Failed to generate headlines', err);
    } finally {
      setIsGeneratingHeadlines(false);
    }
  };

  const handleGenerateArticle = async () => {
    if (!activeProject) return;
    if (!brief) {
      error('A research brief must be generated before drafting an article.');
      return;
    }

    try {
      setIsGenerating(true);
      info('Synthesizing 300–500 word editorial with citations...');
      const editorial = await editorialService.generateEditorial({
        project_id: activeProject.id,
        research_brief_id: brief.id,
        selected_headline: headline || undefined,
        audience,
        tone,
        min_words: minWords,
        max_words: maxWords,
      });

      applyEditorial(editorial);
      await loadProjectEditorials(activeProject.id);
      success(`Composed newsletter edition (${editorial.word_count} words)!`);
    } catch (err: any) {
      error(err.message || 'Failed to generate newsletter draft');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveArticle = async () => {
    if (!activeEditorial) {
      // Create fresh editorial if not existing
      if (!activeProject) return;
      try {
        setIsSaving(true);
        const created = await editorialService.createEditorial({
          project_id: activeProject.id,
          headline: headline || 'Untitled Editorial',
          content,
          status: 'reviewed',
        });
        applyEditorial(created);
        await loadProjectEditorials(activeProject.id);
        success('Article saved to workspace database!');
      } catch (err: any) {
        error(err.message || 'Failed to save article');
      } finally {
        setIsSaving(false);
      }
      return;
    }

    try {
      setIsSaving(true);
      const updated = await editorialService.updateEditorial(activeEditorial.id, {
        headline,
        content,
        status: 'reviewed',
      });
      applyEditorial(updated);
      success('Article saved to workspace database!');
    } catch (err: any) {
      error(err.message || 'Failed to save article');
    } finally {
      setIsSaving(false);
    }
  };

  const handleExport = async () => {
    if (!activeEditorial) {
      error('Please generate or save an article before exporting.');
      return;
    }

    try {
      setIsExporting(true);
      const exp = await editorialService.exportEditorial(activeEditorial.id, 'markdown');
      setExportData(exp);
      setIsExportModalOpen(true);
    } catch (err: any) {
      error(err.message || 'Failed to export article');
    } finally {
      setIsExporting(false);
    }
  };

  const handleOpenInWritingAssistant = () => {
    if (activeEditorial?.draft_id) {
      navigate(`/writing/${activeEditorial.draft_id}`);
    } else {
      navigate('/writing');
    }
  };

  const confirmDeleteEditorial = async () => {
    if (!deleteEditorialId) return;
    try {
      await editorialService.deleteEditorial(deleteEditorialId);
      success('Editorial edition deleted.');
      setDeleteEditorialId(null);
      if (activeProject) {
        await loadProjectEditorials(activeProject.id);
      }
      if (activeEditorial?.id === deleteEditorialId) {
        setActiveEditorial(null);
        setContent('');
        setHeadline('');
      }
    } catch (err: any) {
      error(err.message || 'Failed to delete editorial');
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Project Context */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">Editorial Studio</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 font-semibold font-mono">
              300–500 Words
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Transform evidence-backed research briefs into publication-ready newsletter editions with verified citations.
          </p>
        </div>

        {/* Project Selector & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={activeProject?.id || ''}
            onChange={(e) => selectProject(e.target.value)}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                Project: {p.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!activeProject ? (
        <EmptyState
          icon={<Newspaper className="w-6 h-6 text-purple-600" />}
          title="No Research Projects Available"
          description="Initialize a research project and synthesize at least 3 sources to activate the Editorial Studio."
          actionLabel="Create Project"
          onAction={() => navigate('/research')}
        />
      ) : !brief ? (
        <div className="p-6 rounded-2xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 text-center space-y-3">
          <AlertTriangle className="w-8 h-8 text-amber-600 mx-auto" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Research Brief Required</h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
            Project "<strong>{activeProject.title}</strong>" does not have a synthesized research brief yet. 
            Ingest at least 3 sources in the Research Assistant and generate a brief to begin drafting.
          </p>
          <div className="pt-2">
            <Button
              onClick={() => navigate(`/research/${activeProject.id}`)}
              variant="primary"
              size="sm"
            >
              Open Research Assistant
            </Button>
          </div>
        </div>
      ) : (
        <>
          {/* Main Studio Toolbar */}
          <EditorialToolbar
            viewMode={viewMode}
            setViewMode={setViewMode}
            onSave={handleSaveArticle}
            onExport={handleExport}
            onAnalyzeWriting={handleOpenInWritingAssistant}
            isSaving={isSaving}
            hasContent={Boolean(content.trim())}
          />

          {/* 2-Column Studio Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column: Headline Selector & Generator OR Editor/Preview (8 cols) */}
            <div className="lg:col-span-8 space-y-6">
              {viewMode === 'review' ? (
                activeEditorial ? (
                  <EditorialReviewPanel
                    editorial={activeEditorial}
                    onEditorialUpdated={(updated) => {
                      setActiveEditorial(updated);
                      setContent(updated.content);
                      setHeadline(updated.headline);
                      setWordCount(updated.word_count);
                      setSavedEditorials(prev => prev.map(e => e.id === updated.id ? updated : e));
                      success('Editorial status updated: ' + updated.status);
                    }}
                  />
                ) : (
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
                    <p className="text-sm font-medium">Please generate or select an editorial draft to begin review.</p>
                  </div>
                )
              ) : viewMode === 'preview' ? (
                <EditorialPreview
                  headline={headline}
                  content={content}
                  wordCount={wordCount}
                  sourceReferences={activeEditorial?.source_references || []}
                />
              ) : (
                <>
                  {/* Step 1: Headline Options Selector */}
                  <HeadlineSelector
                    headlines={headlineOptions}
                    selectedHeadline={headline}
                    onSelectHeadline={(h) => setHeadline(h)}
                    onRegenerate={() => loadHeadlineOptions(activeProject.id, brief.id)}
                    isLoading={isGeneratingHeadlines}
                  />

                  {/* Step 2: Editorial Parameter Controls */}
                  <EditorialGenerator
                    audience={audience}
                    setAudience={setAudience}
                    tone={tone}
                    setTone={setTone}
                    minWords={minWords}
                    setMinWords={setMinWords}
                    maxWords={maxWords}
                    setMaxWords={setMaxWords}
                    onGenerate={handleGenerateArticle}
                    isGenerating={isGenerating}
                  />

                  {/* Step 3: Interactive Article Editor */}
                  {content && (
                    <EditorialEditor
                      headline={headline}
                      setHeadline={setHeadline}
                      content={content}
                      setContent={(c) => {
                        setContent(c);
                        setWordCount(c.trim() ? c.trim().split(/\s+/).length : 0);
                      }}
                      wordCount={wordCount}
                      onSave={handleSaveArticle}
                      onRegenerate={handleGenerateArticle}
                      onAnalyzeWriting={handleOpenInWritingAssistant}
                      isSaving={isSaving}
                      isGenerating={isGenerating}
                      isDirty={isDirty}
                    />
                  )}
                </>
              )}
            </div>

            {/* Right Column: Source References & Editorial Editions History (4 cols) */}
            <div className="lg:col-span-4 space-y-6">
              {/* Verified Sources Card */}
              <SourceReferences
                sources={activeEditorial?.source_references || sourcesList}
                angleHeadline={angleParam || headline}
              />

              {/* Research Intelligence Insights & Discrepancies */}
              {(trends.length > 0 || contradictions.length > 0) && (
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-indigo-200/80 dark:border-indigo-900/40 p-5 shadow-xs space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-indigo-100 dark:border-indigo-900/30">
                    <h3 className="text-xs font-bold text-indigo-950 dark:text-indigo-200 uppercase tracking-wider flex items-center gap-1.5">
                      <Network className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Research Intelligence Findings</span>
                    </h3>
                  </div>

                  {contradictions.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-[11px] font-bold text-rose-700 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-rose-600" />
                        <span>Conflicting Claims to Reconcile ({contradictions.length})</span>
                      </div>
                      {contradictions.slice(0, 2).map((cd, idx) => (
                        <div key={idx} className="p-2.5 bg-rose-50/60 rounded-lg border border-rose-100 text-[11px] space-y-1">
                          <div className="font-semibold text-rose-900">{cd.disagreement_nature}</div>
                          <div className="text-slate-600 italic line-clamp-2">Q: {cd.unresolved_questions}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {trends.length > 0 && (
                    <div className="space-y-2 pt-1">
                      <div className="text-[11px] font-bold text-blue-700 flex items-center gap-1">
                        <Sparkles className="w-3 h-3 text-blue-600" />
                        <span>Corroborated Themes ({trends.length})</span>
                      </div>
                      {trends.slice(0, 2).map((td, idx) => (
                        <div key={idx} className="p-2.5 bg-blue-50/60 rounded-lg border border-blue-100 text-[11px] flex justify-between items-center gap-2">
                          <span className="font-medium text-slate-800 line-clamp-1">{td.theme}</span>
                          <button
                            type="button"
                            onClick={() => {
                              setContent(prev => prev ? `${prev}\n\nCross-source research corroborates: ${td.evidence_summary}` : td.evidence_summary);
                              info('Inserted trend insight into draft');
                            }}
                            className="text-[10px] text-blue-600 hover:text-blue-800 font-bold whitespace-nowrap cursor-pointer px-1.5 py-0.5 rounded bg-blue-100/60"
                          >
                            + Insert
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Saved Editions History */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-blue-600" />
                    <span>Saved Editions ({savedEditorials.length})</span>
                  </h3>
                </div>

                {savedEditorials.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">No editions saved yet.</p>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800/80 max-h-[300px] overflow-y-auto">
                    {savedEditorials.map((ed) => (
                      <div
                        key={ed.id}
                        onClick={() => applyEditorial(ed)}
                        className={`py-2.5 px-2 rounded-xl text-xs cursor-pointer transition-all flex items-center justify-between gap-2 ${
                          activeEditorial?.id === ed.id
                            ? 'bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 font-semibold'
                            : 'hover:bg-slate-50 dark:hover:bg-slate-800/40 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <div className="truncate space-y-0.5">
                          <div className="truncate">{ed.headline}</div>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {ed.word_count} words
                          </span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteEditorialId(ed.id);
                          }}
                          className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950"
                          title="Delete edition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Export Menu Modal */}
      <ExportMenu
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        exportData={exportData}
        isLoading={isExporting}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteEditorialId)}
        title="Delete Editorial Edition"
        message="Are you sure you want to delete this saved article edition? This action cannot be undone."
        confirmLabel="Delete Edition"
        isDestructive={true}
        onConfirm={confirmDeleteEditorial}
        onCancel={() => setDeleteEditorialId(null)}
      />
    </div>
  );
};
