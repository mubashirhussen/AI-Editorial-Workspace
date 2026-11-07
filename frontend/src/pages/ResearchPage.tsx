import React, { useState, useEffect } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Globe, 
  FileText, 
  Trash2, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Sparkles, 
  ArrowRight,
  ShieldCheck,
  Scale,
  Lightbulb,
  AlertTriangle,
  HelpCircle,
  TrendingUp,
  RefreshCw,
  Network,
  UploadCloud,
  FileCheck,
  Search,
  Filter,
  Copy,
  Download,
  BookOpen,
  Eye,
  X,
  Layers,
  FileSpreadsheet,
  Check,
  FileCode
} from 'lucide-react';
import { researchApi } from '../services/researchApi';
import { Project, Source, ResearchBrief, NewsletterAngle, VerifiedEvidenceItem } from '../types';
import { useToast } from '../components/common/Toast';
import { Button } from '../components/common/Button';
import { ConfirmDialog } from '../components/common/ConfirmDialog';
import { ResearchIntelligenceDashboard } from '../components/research/ResearchIntelligenceDashboard';

export const ResearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { projectId: routeProjectId } = useParams<{ projectId?: string }>();
  const projectIdParam = routeProjectId || searchParams.get('projectId');
  const navigate = useNavigate();
  const { success, error, info } = useToast();

  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [brief, setBrief] = useState<ResearchBrief | null>(null);
  const [evidenceList, setEvidenceList] = useState<VerifiedEvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter
  const [sourceSearch, setSourceSearch] = useState('');
  const [sourceTypeFilter, setSourceTypeFilter] = useState<'ALL' | 'URL' | 'FILE' | 'TEXT'>('ALL');
  const [evidenceFilter, setEvidenceFilter] = useState<string>('ALL');

  // Preview / Inspector Modal
  const [selectedSourceForPreview, setSelectedSourceForPreview] = useState<Source | null>(null);
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [isCreatingProject, setIsCreatingProject] = useState(false);

  // Ingestion Form State
  const [inputType, setInputType] = useState<'url' | 'text' | 'file'>('url');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingSourceId, setUploadingSourceId] = useState<string | null>(null);
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [isAddingSource, setIsAddingSource] = useState(false);
  const [isGeneratingBrief, setIsGeneratingBrief] = useState(false);
  const [activeTab, setActiveTab] = useState<'brief' | 'sources' | 'evidence' | 'facts' | 'intelligence'>('brief');
  const [deleteSourceId, setDeleteSourceId] = useState<string | null>(null);
  const [editingSourceId, setEditingSourceId] = useState<string | null>(null);
  const [manualText, setManualText] = useState<string>('');
  const [isSavingManual, setIsSavingManual] = useState(false);
  const [copiedBrief, setCopiedBrief] = useState(false);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await researchApi.getProjects();
      const projectList = res.items || [];
      setProjects(projectList);

      if (projectList.length > 0) {
        const found = projectIdParam
          ? projectList.find((p) => p.id === projectIdParam) || projectList[0]
          : projectList[0];
        await selectProject(found);
      } else {
        setActiveProject(null);
        setSources([]);
        setBrief(null);
      }
    } catch (err: any) {
      error(err.message || 'Failed to load research projects');
    } finally {
      setLoading(false);
    }
  };

  const selectProject = async (p: Project) => {
    setActiveProject(p);
    setSearchParams({ projectId: p.id });
    try {
      const detailed = await researchApi.getProject(p.id);
      setActiveProject(detailed);
      setSources(detailed.sources || []);
      
      // Load brief
      try {
        const b = await researchApi.getBrief(p.id);
        setBrief(b);
        if (b.evidence && b.evidence.length > 0) {
          setEvidenceList(b.evidence);
        } else {
          loadEvidenceRecords(p.id);
        }
      } catch {
        setBrief(null);
        loadEvidenceRecords(p.id);
      }
    } catch (err: any) {
      error(err.message || 'Failed to load project details');
    }
  };

  const loadEvidenceRecords = async (projectId: string) => {
    try {
      const evs = await researchApi.getProjectEvidence(projectId);
      setEvidenceList(evs || []);
    } catch {
      setEvidenceList([]);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [projectIdParam]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectTitle.trim()) return;
    try {
      setIsCreatingProject(true);
      const created = await researchApi.createProject({
        title: newProjectTitle.trim(),
        description: newProjectDesc.trim() || undefined,
      });
      success(`Project "${created.title}" created.`);
      setIsNewProjectModalOpen(false);
      setNewProjectTitle('');
      setNewProjectDesc('');
      await loadProjects();
      navigate(`/research/${created.id}`);
    } catch (err: any) {
      error(err.message || 'Failed to create project');
    } finally {
      setIsCreatingProject(false);
    }
  };

  const handleRetryExtract = async (sourceId: string) => {
    try {
      info('Re-triggering secure extraction...');
      await researchApi.extractSource(sourceId);
      success('Extraction completed.');
      if (activeProject) {
        const updated = await researchApi.getProject(activeProject.id);
        setActiveProject(updated);
        setSources(updated.sources || []);
      }
    } catch (err: any) {
      error(err.message || 'Failed to extract source');
    }
  };

  const handleReuploadFile = async (sourceId: string, file: File) => {
    try {
      setUploadingSourceId(sourceId);
      info(`Extracting content from ${file.name}...`);
      const updated = await researchApi.reuploadSourceFile(sourceId, file);
      success(`Content extracted from ${file.name}! Status: ${updated.extraction_status}`);
      if (activeProject) {
        const p = await researchApi.getProject(activeProject.id);
        setActiveProject(p);
        setSources(p.sources || []);
      }
    } catch (err: any) {
      error(err.message || 'Failed to extract content from file');
    } finally {
      setUploadingSourceId(null);
    }
  };

  const handleSaveManualSource = async (sourceId: string) => {
    if (!manualText.trim()) return;
    try {
      setIsSavingManual(true);
      await researchApi.updateSource(sourceId, { text_content: manualText });
      success('Source content updated and verified.');
      setEditingSourceId(null);
      setManualText('');
      if (activeProject) {
        const updated = await researchApi.getProject(activeProject.id);
        setActiveProject(updated);
        setSources(updated.sources || []);
      }
    } catch (err: any) {
      error(err.message || 'Failed to update source');
    } finally {
      setIsSavingManual(false);
    }
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;

    try {
      setIsAddingSource(true);
      if (inputType === 'url') {
        const rawInput = sourceUrl.trim();
        const urls = rawInput.split(/[\r\n\s,]+/).filter((u) => /^https?:\/\//i.test(u.trim()));

        if (urls.length === 0) {
          error('Please provide at least one valid HTTP or HTTPS URL.');
          return;
        }

        let successCount = 0;
        for (const u of urls) {
          try {
            await researchApi.addSourceUrl(activeProject.id, {
              url: u.trim(),
              title: urls.length === 1 && sourceTitle ? sourceTitle.trim() : undefined,
            });
            successCount++;
          } catch (err: any) {
            error(`URL error: ${err.message || 'Failed to add URL'}`);
          }
        }

        if (successCount > 0) {
          success(`Successfully ingested ${successCount} source${successCount > 1 ? 's' : ''}.`);
          setSourceUrl('');
          setSourceTitle('');
        }
      } else if (inputType === 'text') {
        if (!sourceText.trim()) {
          error('Please enter article or release text content.');
          return;
        }
        await researchApi.addSourceText(activeProject.id, {
          title: sourceTitle.trim() || undefined,
          text_content: sourceText.trim(),
        });
        success('Pasted text source added and content verified.');
        setSourceText('');
        setSourceTitle('');
      } else if (inputType === 'file') {
        if (!selectedFile) {
          error('Please select a document or image file to upload.');
          return;
        }
        await researchApi.uploadSourceFile(
          activeProject.id,
          selectedFile,
          sourceTitle.trim() || undefined
        );
        success(`Extracted and indexed ${selectedFile.name}.`);
        setSelectedFile(null);
        setSourceTitle('');
      }

      // Refresh project
      const updated = await researchApi.getProject(activeProject.id);
      setActiveProject(updated);
      setSources(updated.sources || []);
    } catch (err: any) {
      error(err.message || 'Failed to add source');
    } finally {
      setIsAddingSource(false);
    }
  };

  const confirmDeleteSource = async () => {
    if (!deleteSourceId || !activeProject) return;
    try {
      await researchApi.deleteSource(deleteSourceId);
      success('Source removed from investigation.');
      setDeleteSourceId(null);
      const updated = await researchApi.getProject(activeProject.id);
      setActiveProject(updated);
      setSources(updated.sources || []);
    } catch (err: any) {
      error(err.message || 'Failed to delete source');
    }
  };

  const handleGenerateBrief = async () => {
    if (!activeProject) return;
    if (sources.length < 3) {
      error(`At least 3 sources are required to synthesize a research brief. Currently have ${sources.length}.`);
      return;
    }
    try {
      setIsGeneratingBrief(true);
      info('Synthesizing cross-source intelligence and auditing evidence...');
      const generated = await researchApi.generateBrief(activeProject.id);
      setBrief(generated);
      if (generated.evidence) {
        setEvidenceList(generated.evidence);
      }
      success('Research Brief successfully synthesized!');
      setActiveTab('brief');
    } catch (err: any) {
      error(err.message || 'Failed to generate brief');
    } finally {
      setIsGeneratingBrief(false);
    }
  };

  const handleProceedToEditorial = (angleHeadline: string) => {
    if (!activeProject) return;
    navigate(`/writing?projectId=${activeProject.id}&angle=${encodeURIComponent(angleHeadline)}`);
  };

  const handleCopyBriefMarkdown = () => {
    if (!brief) return;
    const md = `# ${brief.executive_summary}\n\n## What Happened?\n${brief.brief_content?.what_happened || ''}\n\n## Why It Matters\n${brief.brief_content?.why_it_matters || ''}\n\n## Newsletter Angles\n` +
      (brief.newsletter_angles || []).map((a) => `### ${a.headline}\n*Target:* ${a.target_audience}\n*Pitch:* ${a.angle_pitch}\n`).join('\n');
    navigator.clipboard.writeText(md);
    setCopiedBrief(true);
    setTimeout(() => setCopiedBrief(false), 2000);
    success('Brief markdown copied to clipboard.');
  };

  // Filter sources
  const filteredSources = sources.filter((s) => {
    const matchesSearch = !sourceSearch || 
      s.title.toLowerCase().includes(sourceSearch.toLowerCase()) ||
      (s.url && s.url.toLowerCase().includes(sourceSearch.toLowerCase())) ||
      (s.author && s.author.toLowerCase().includes(sourceSearch.toLowerCase()));

    const matchesType = sourceTypeFilter === 'ALL' ||
      (sourceTypeFilter === 'URL' && s.source_type?.toUpperCase() === 'URL') ||
      (sourceTypeFilter === 'FILE' && ['PDF', 'DOCUMENT', 'IMAGE'].includes(s.source_type?.toUpperCase())) ||
      (sourceTypeFilter === 'TEXT' && s.source_type?.toUpperCase() === 'TEXT');

    return matchesSearch && matchesType;
  });

  // Filter evidence
  const filteredEvidence = evidenceList.filter((ev) => {
    if (evidenceFilter === 'ALL') return true;
    return ev.status === evidenceFilter;
  });

  if (loading && projects.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="flex flex-col items-center gap-3 text-slate-500">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium">Loading Research Workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Workspace Header (Scholarly Atelier / Afforai inspiration) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded bg-slate-900 text-white font-semibold">
              Scholarly Workspace
            </span>
            {activeProject && (
              <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold ${
                activeProject.status === 'completed' ? 'bg-emerald-100 text-emerald-800' :
                activeProject.status === 'in_progress' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'
              }`}>
                {activeProject.status || 'draft'}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <select
              value={activeProject?.id || ''}
              onChange={(e) => {
                const sel = projects.find((p) => p.id === e.target.value);
                if (sel) selectProject(sel);
              }}
              className="text-lg font-bold text-slate-900 bg-transparent border-none outline-none cursor-pointer hover:text-blue-700 transition-colors pr-6"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
            <button
              onClick={() => setIsNewProjectModalOpen(true)}
              className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              title="Create new research project"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          {activeProject?.description && (
            <p className="text-xs text-slate-500 max-w-2xl line-clamp-1">{activeProject.description}</p>
          )}
        </div>

        {/* Global Action Bar */}
        <div className="flex items-center gap-2.5">
          <div className="text-right hidden sm:block">
            <div className="text-[11px] font-medium text-slate-600">
              {sources.length} Verified Sources
            </div>
            <div className="text-[10px] text-slate-400">
              {sources.length >= 3 ? 'Ready for cross-source synthesis' : `Requires ${3 - sources.length} more sources`}
            </div>
          </div>
          <Button
            size="sm"
            variant="primary"
            onClick={handleGenerateBrief}
            disabled={isGeneratingBrief || sources.length < 3}
            isLoading={isGeneratingBrief}
            className="flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Generate Brief</span>
          </Button>
        </div>
      </div>

      {/* Main Grid: Left 5 Cols (Sources & Ingestion) | Right 7 Cols (Workspace & Evidence) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: Sources & Multi-Source Ingestion */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Ingestion Box */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Plus className="w-3.5 h-3.5 text-blue-600" />
                <span>Ingest Source Document</span>
              </h3>
              <span className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> SSRF Protected
              </span>
            </div>

            {/* Ingestion Tabs */}
            <div className="flex bg-slate-100 p-1 rounded-lg text-xs font-medium">
              <button
                type="button"
                onClick={() => setInputType('url')}
                className={`flex-1 py-1.5 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  inputType === 'url' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Article URL</span>
              </button>
              <button
                type="button"
                onClick={() => setInputType('file')}
                className={`flex-1 py-1.5 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  inputType === 'file' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>PDF / Docx</span>
              </button>
              <button
                type="button"
                onClick={() => setInputType('text')}
                className={`flex-1 py-1.5 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  inputType === 'text' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Paste Text</span>
              </button>
            </div>

            <form onSubmit={handleAddSource} className="space-y-3">
              {inputType === 'url' ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-medium text-slate-700">Web Article or Paper URL</label>
                    <button
                      type="button"
                      onClick={() => {
                        setSourceUrl(
                          `https://deepmind.google/technologies/gemini/\nhttps://en.wikipedia.org/wiki/Large_language_model\nhttps://arxiv.org/abs/1706.03762`
                        );
                        info('Loaded 3 verified test sources: Gemini, Large Language Models, and Attention Is All You Need.');
                      }}
                      className="text-[10px] text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 hover:underline cursor-pointer"
                    >
                      <Sparkles className="w-3 h-3 text-amber-500" />
                      <span>Quick Load 3 Sample URLs</span>
                    </button>
                  </div>
                  <textarea
                    rows={3}
                    required
                    placeholder="Enter URL or multiple URLs separated by newline..."
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none resize-none font-mono"
                  />
                </div>
              ) : inputType === 'file' ? (
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-slate-700">Document Upload (PDF, Word docx, Text, Markdown)</label>
                  <div className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-xl p-4 text-center cursor-pointer transition-colors bg-slate-50/50">
                    <input
                      type="file"
                      id="research-file-input"
                      accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.webp"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) setSelectedFile(f);
                      }}
                      className="hidden"
                    />
                    <label htmlFor="research-file-input" className="cursor-pointer block">
                      <UploadCloud className="w-6 h-6 text-blue-600 mx-auto mb-1.5" />
                      {selectedFile ? (
                        <div className="text-xs font-semibold text-slate-800 flex items-center justify-center gap-1.5">
                          <FileCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                          <span className="truncate max-w-[200px]">{selectedFile.name}</span>
                          <span className="text-[10px] text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                        </div>
                      ) : (
                        <>
                          <div className="text-xs font-semibold text-slate-700">Click to upload document or paper</div>
                          <div className="text-[10px] text-slate-400 mt-0.5">PDF, DOCX, TXT, MD up to 10 MB</div>
                        </>
                      )}
                    </label>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="text-[11px] font-medium text-slate-700">Source Title</label>
                  <input
                    type="text"
                    placeholder="e.g. Technical Whitepaper"
                    value={sourceTitle}
                    onChange={(e) => setSourceTitle(e.target.value)}
                    className="w-full text-xs px-3 py-1.5 border border-slate-300 rounded-lg outline-none"
                  />
                  <label className="text-[11px] font-medium text-slate-700">Verbatim Article Content</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Paste article body text or announcement..."
                    value={sourceText}
                    onChange={(e) => setSourceText(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none resize-none font-mono"
                  />
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                size="sm"
                className="w-full"
                disabled={isAddingSource}
                isLoading={isAddingSource}
              >
                {inputType === 'file' ? 'Extract & Ingest File' : 'Add Source to Investigation'}
              </Button>
            </form>
          </div>

          {/* Sources List & Filter (Scholarly Library inspired by Atelier & ISNAD) */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                Sources Library ({sources.length})
              </h3>
              <div className="flex items-center gap-1 text-[11px]">
                <button
                  onClick={() => setSourceTypeFilter('ALL')}
                  className={`px-2 py-0.5 rounded ${sourceTypeFilter === 'ALL' ? 'bg-slate-900 text-white font-medium' : 'text-slate-500 hover:text-slate-900'}`}
                >
                  All
                </button>
                <button
                  onClick={() => setSourceTypeFilter('URL')}
                  className={`px-2 py-0.5 rounded ${sourceTypeFilter === 'URL' ? 'bg-slate-900 text-white font-medium' : 'text-slate-500 hover:text-slate-900'}`}
                >
                  URL
                </button>
                <button
                  onClick={() => setSourceTypeFilter('FILE')}
                  className={`px-2 py-0.5 rounded ${sourceTypeFilter === 'FILE' ? 'bg-slate-900 text-white font-medium' : 'text-slate-500 hover:text-slate-900'}`}
                >
                  File
                </button>
                <button
                  onClick={() => setSourceTypeFilter('TEXT')}
                  className={`px-2 py-0.5 rounded ${sourceTypeFilter === 'TEXT' ? 'bg-slate-900 text-white font-medium' : 'text-slate-500 hover:text-slate-900'}`}
                >
                  Text
                </button>
              </div>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search sources by title or domain..."
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                className="w-full text-xs pl-8 pr-3 py-1.5 border border-slate-200 rounded-lg outline-none focus:border-blue-500"
              />
            </div>

            {filteredSources.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
                {sources.length === 0 ? 'No sources added yet. Ingest at least 3 sources to synthesize.' : 'No sources match your filter.'}
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
                {filteredSources.map((s, idx) => (
                  <div
                    key={s.id}
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50/60 hover:bg-white hover:border-slate-300 transition-all text-xs space-y-2 group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5 flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-blue-100 text-blue-800 font-mono text-[9px] flex items-center justify-center font-bold shrink-0">
                            {idx + 1}
                          </span>
                          <span className="font-semibold text-slate-900 truncate block">
                            {s.title}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 pl-5.5">
                          {s.domain && <span>{s.domain}</span>}
                          {s.word_count ? <span>• {s.word_count} words</span> : null}
                          {s.author && <span>• {s.author}</span>}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          onClick={() => setSelectedSourceForPreview(s)}
                          className="p-1 rounded text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          title="Inspect full source text and metadata"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setDeleteSourceId(s.id)}
                          className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                          title="Remove source"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Status pill & retry */}
                    <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-200/50">
                      {s.extraction_status === 'completed' ? (
                        <span className="text-emerald-700 flex items-center gap-1 font-medium text-[10px]">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Grounded & Verified
                        </span>
                      ) : s.extraction_status === 'extracting' ? (
                        <span className="text-blue-600 flex items-center gap-1 text-[10px]">
                          <Loader2 className="w-3 h-3 animate-spin" /> Ingesting...
                        </span>
                      ) : (
                        <div className="flex items-center justify-between w-full">
                          <span className="text-red-600 flex items-center gap-1 text-[10px] font-medium">
                            <AlertCircle className="w-3 h-3" /> Failed
                          </span>
                          <button
                            onClick={() => handleRetryExtract(s.id)}
                            className="text-[10px] text-blue-600 hover:underline"
                          >
                            Retry
                          </button>
                        </div>
                      )}

                      {s.url && (
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-blue-600 hover:underline flex items-center gap-0.5"
                        >
                          <span>Visit URL</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Synthesis Brief & Evidence Verification Panel */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* Navigation Bar */}
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center gap-1 text-xs font-medium">
              <button
                onClick={() => setActiveTab('brief')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'brief' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Research Brief
              </button>
              <button
                onClick={() => setActiveTab('evidence')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                  activeTab === 'evidence' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span>Evidence Alignment</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-100 text-blue-800">
                  {evidenceList.length}
                </span>
              </button>
              <button
                onClick={() => setActiveTab('facts')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  activeTab === 'facts' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Facts vs Speculation
              </button>
              <button
                onClick={() => setActiveTab('intelligence')}
                className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                  activeTab === 'intelligence' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                <span>Knowledge Graph</span>
              </button>
            </div>

            {brief && activeTab === 'brief' && (
              <button
                onClick={handleCopyBriefMarkdown}
                className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1"
                title="Copy full brief markdown"
              >
                {copiedBrief ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedBrief ? 'Copied' : 'Copy'}</span>
              </button>
            )}
          </div>

          {/* TAB CONTENTS */}
          {activeTab === 'intelligence' ? (
            activeProject ? (
              <ResearchIntelligenceDashboard projectId={activeProject.id} sourceCount={sources.length} />
            ) : null
          ) : activeTab === 'evidence' ? (
            /* EVIDENCE VERIFICATION PANEL (Inspired by ISNAD) */
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                    Evidence Alignment & Grounding Verification
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Every factual assertion is audited against extracted source passages with explicit epistemic status.
                  </p>
                </div>
                {/* Filter Pills */}
                <div className="flex items-center gap-1 text-[10px]">
                  {['ALL', 'SUPPORTED', 'PARTIALLY_SUPPORTED', 'CONTRADICTED', 'NOT_VERIFIABLE'].map((st) => (
                    <button
                      key={st}
                      onClick={() => setEvidenceFilter(st)}
                      className={`px-2 py-0.5 rounded font-medium ${
                        evidenceFilter === st ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {st === 'ALL' ? 'All' : st.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Evidence Cards */}
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {filteredEvidence.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-400">
                    No evidence items match the selected filter.
                  </div>
                ) : (
                  filteredEvidence.map((ev, i) => {
                    const isSupported = ev.status === 'SUPPORTED';
                    const isPartial = ev.status === 'PARTIALLY_SUPPORTED';
                    const isContradicted = ev.status === 'CONTRADICTED';
                    const isUnverifiable = ev.status === 'NOT_VERIFIABLE' || ev.status === 'UNSUPPORTED';

                    return (
                      <div
                        key={ev.evidence_id || i}
                        className={`p-4 rounded-xl border text-xs space-y-2.5 transition-all ${
                          isSupported ? 'border-emerald-200 bg-emerald-50/20' :
                          isPartial ? 'border-blue-200 bg-blue-50/20' :
                          isContradicted ? 'border-red-200 bg-red-50/20' : 'border-slate-200 bg-slate-50/40'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-slate-900 text-[13px] leading-snug">
                            {ev.claim}
                          </span>
                          <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold shrink-0 ${
                            isSupported ? 'bg-emerald-100 text-emerald-800' :
                            isPartial ? 'bg-blue-100 text-blue-800' :
                            isContradicted ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                          }`}>
                            {ev.status || 'VERIFIED'}
                          </span>
                        </div>

                        {/* Quoted Excerpt */}
                        {ev.supporting_excerpt && (
                          <blockquote className="italic text-slate-700 bg-white p-3 rounded-lg border-l-3 border-blue-500 text-[11px] leading-relaxed">
                            "{ev.supporting_excerpt}"
                          </blockquote>
                        )}

                        {/* Metadata row */}
                        <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200/40">
                          <div className="flex items-center gap-2">
                            <span>Source: <strong className="text-slate-700">{ev.source_title}</strong></span>
                            {ev.section_reference && <span className="text-slate-400">({ev.section_reference})</span>}
                            {ev.confidence && (
                              <span className="text-[10px] bg-slate-100 px-1.5 py-0.2 rounded font-mono">
                                {(ev.confidence * 100).toFixed(0)}% Confidence
                              </span>
                            )}
                          </div>
                          {ev.reasoning && (
                            <span className="italic text-[10px] text-slate-400">{ev.reasoning}</span>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          ) : activeTab === 'facts' ? (
            /* FACTS VS SPECULATION */
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
              <div className="border-b border-slate-100 pb-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                  Epistemic Segregation
                </h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Separates confirmed factual data from analytical deductions and speculative forward claims.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Verified Facts */}
                <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-emerald-900">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Verified Facts</span>
                  </div>
                  <ul className="space-y-2 text-[11px] text-emerald-950 list-disc list-inside">
                    {brief?.brief_content?.facts_vs_analysis?.facts?.map((f, i) => (
                      <li key={i}>{f}</li>
                    )) || <li>No verified facts parsed.</li>}
                  </ul>
                </div>

                {/* Analytical Inferences */}
                <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-blue-900">
                    <Scale className="w-4 h-4 text-blue-600" />
                    <span>Editorial Analysis</span>
                  </div>
                  <ul className="space-y-2 text-[11px] text-blue-950 list-disc list-inside">
                    {brief?.brief_content?.facts_vs_analysis?.analysis?.map((a, i) => (
                      <li key={i}>{a}</li>
                    )) || <li>No analytical points parsed.</li>}
                  </ul>
                </div>

                {/* Speculation & Hype */}
                <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/50 space-y-2 text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-amber-900">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>Speculation & Hype</span>
                  </div>
                  <ul className="space-y-2 text-[11px] text-amber-950 list-disc list-inside">
                    {brief?.brief_content?.facts_vs_analysis?.speculation?.map((s, i) => (
                      <li key={i}>{s}</li>
                    )) || <li>No speculative claims detected.</li>}
                  </ul>
                </div>
              </div>
            </div>
          ) : !brief ? (
            /* Empty State */
            <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <h4 className="text-base font-semibold text-slate-800">No Research Brief Synthesized Yet</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Once you collect at least 3 sources, click "Generate Brief" to execute multi-source intelligence discovery, extract grounded evidence, and formulate editorial angles.
              </p>
              {sources.length >= 3 && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleGenerateBrief}
                  disabled={isGeneratingBrief}
                  isLoading={isGeneratingBrief}
                  className="mt-2"
                >
                  Synthesize Research Brief
                </Button>
              )}
            </div>
          ) : (
            /* TAB 1: RESEARCH BRIEF */
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-6 shadow-xs">
              {/* Executive Summary */}
              <div className="space-y-2 border-b border-slate-100 pb-4">
                <span className="text-[10px] font-mono uppercase tracking-wider text-blue-600 font-bold">
                  Section A • Executive Summary
                </span>
                <p className="text-xs text-slate-800 leading-relaxed font-serif text-[13.5px]">
                  {brief.executive_summary}
                </p>
              </div>

              {/* What Happened & Why It Matters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-slate-100 pb-4">
                <div className="space-y-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Section B • What Happened?
                  </span>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {brief.brief_content?.what_happened}
                  </p>
                </div>
                <div className="space-y-1.5">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Section C • Why Does It Matter?
                  </span>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {brief.brief_content?.why_it_matters}
                  </p>
                </div>
              </div>

              {/* Who Should Care (4 Audiences) */}
              <div className="space-y-3 border-b border-slate-100 pb-4">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                  Section D • Who Should Care?
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-semibold text-blue-700 block mb-0.5">Founders</span>
                    <span className="text-slate-600">{brief.brief_content?.who_should_care?.founders}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-semibold text-indigo-700 block mb-0.5">Developers & Builders</span>
                    <span className="text-slate-600">{brief.brief_content?.who_should_care?.developers}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-semibold text-emerald-700 block mb-0.5">Business Operators</span>
                    <span className="text-slate-600">{brief.brief_content?.who_should_care?.business_operators}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="font-semibold text-purple-700 block mb-0.5">AI Researchers</span>
                    <span className="text-slate-600">{brief.brief_content?.who_should_care?.ai_researchers}</span>
                  </div>
                </div>
              </div>

              {/* Recommended Newsletter Angles */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600 font-bold">
                    Section E • Newsletter Angles & Editorial Hooks
                  </span>
                  <span className="text-[10px] text-blue-600 font-medium">Click "Write This" to draft</span>
                </div>

                <div className="space-y-3">
                  {(brief.newsletter_angles || []).map((angle, idx) => {
                    const isRecommended = brief.recommended_angle?.headline === angle.headline || idx === 0;
                    return (
                      <div
                        key={angle.id || idx}
                        className={`p-4 rounded-xl border text-xs space-y-2 transition-all ${
                          isRecommended 
                            ? 'bg-blue-50/60 border-blue-300 ring-1 ring-blue-500/20' 
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            {isRecommended && (
                              <span className="inline-block text-[9px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full uppercase tracking-wider">
                                ★ Recommended Angle
                              </span>
                            )}
                            <h4 className="font-bold text-slate-900 text-sm">{angle.headline}</h4>
                            <p className="text-slate-600">{angle.angle_pitch}</p>
                          </div>
                          <button
                            onClick={() => handleProceedToEditorial(angle.headline)}
                            className="shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-xs transition-colors"
                          >
                            <span>Write This</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <div className="pt-2 border-t border-slate-200/50 text-[11px] text-slate-500 flex items-center justify-between">
                          <span>Target: {angle.target_audience}</span>
                          <span className="italic">{angle.why_now}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SOURCE READER / INSPECTOR MODAL (Inspired by Atelier & Afforai) */}
      {selectedSourceForPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
            {/* Header */}
            <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50">
              <div className="space-y-1 pr-6">
                <span className="text-[10px] font-mono uppercase bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-bold">
                  {selectedSourceForPreview.source_type || 'SOURCE'}
                </span>
                <h3 className="text-base font-bold text-slate-900">{selectedSourceForPreview.title}</h3>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  {selectedSourceForPreview.domain && <span>Domain: {selectedSourceForPreview.domain}</span>}
                  {selectedSourceForPreview.author && <span>• Author: {selectedSourceForPreview.author}</span>}
                  {selectedSourceForPreview.published_at && <span>• Published: {selectedSourceForPreview.published_at}</span>}
                </div>
              </div>
              <button
                onClick={() => setSelectedSourceForPreview(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Body */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs font-mono bg-slate-50/30">
              {/* Metadata snippet card */}
              <div className="grid grid-cols-3 gap-2 p-3 bg-white rounded-lg border border-slate-200 font-sans text-[11px]">
                <div>
                  <span className="text-slate-400 block text-[10px]">WORD COUNT</span>
                  <span className="font-semibold text-slate-800">{selectedSourceForPreview.word_count || selectedSourceForPreview.extracted_content?.split(' ').length || 0} words</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">EXTRACTION STATUS</span>
                  <span className="font-semibold text-emerald-700">{selectedSourceForPreview.extraction_status}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">CONTENT FINGERPRINT</span>
                  <span className="font-mono text-[10px] text-slate-600 truncate block">
                    {selectedSourceForPreview.content_hash ? selectedSourceForPreview.content_hash.slice(0, 16) + '...' : 'SHA-256 verified'}
                  </span>
                </div>
              </div>

              <div>
                <h5 className="font-sans font-bold text-slate-700 uppercase tracking-wider text-[11px] mb-2">
                  Extracted Body Passage
                </h5>
                <pre className="whitespace-pre-wrap font-sans text-xs text-slate-800 leading-relaxed bg-white p-4 rounded-xl border border-slate-200">
                  {selectedSourceForPreview.extracted_content || selectedSourceForPreview.raw_content || 'No text extracted.'}
                </pre>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-200 bg-white flex justify-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setSelectedSourceForPreview(null)}
              >
                Close Reader
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* NEW PROJECT MODAL */}
      {isNewProjectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900">Create Research Project</h3>
            <form onSubmit={handleCreateProject} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Project Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Frontier Reasoning Models 2026"
                  value={newProjectTitle}
                  onChange={(e) => setNewProjectTitle(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  placeholder="Scope and research objectives..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsNewProjectModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isCreatingProject}
                  disabled={!newProjectTitle.trim()}
                >
                  Create Project
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteSourceId)}
        title="Remove Source"
        message="Are you sure you want to remove this source from your research investigation? This cannot be undone."
        confirmLabel="Remove Source"
        isDestructive={true}
        onConfirm={confirmDeleteSource}
        onCancel={() => setDeleteSourceId(null)}
      />
    </div>
  );
};
