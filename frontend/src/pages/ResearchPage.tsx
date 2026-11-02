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
  FileUp,
  FileCheck,
  Paperclip
} from 'lucide-react';
import { researchApi } from '../services/researchApi';
import { Project, Source, ResearchBrief, NewsletterAngle } from '../types';
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
  const [loading, setLoading] = useState(true);

  // Form State
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

  const handleRetryExtract = async (sourceId: string) => {
    try {
      await researchApi.extractSource(sourceId);
      success('Source extraction re-triggered.');
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

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (projects.length > 0) {
      if (projectIdParam) {
        const found = projects.find((p) => p.id === projectIdParam);
        if (found) {
          selectProject(found.id);
        } else {
          selectProject(projects[0].id);
        }
      } else {
        selectProject(projects[0].id);
      }
    } else {
      setLoading(false);
    }
  }, [projectIdParam, projects.length]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await researchApi.getProjects();
      setProjects(res.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const selectProject = async (id: string) => {
    try {
      setSearchParams({ projectId: id });
      const proj = await researchApi.getProject(id);
      setActiveProject(proj);
      setSources(proj.sources || []);
      
      // Try to load brief if available
      try {
        const b = await researchApi.getBrief(id);
        setBrief(b);
      } catch {
        setBrief(null);
      }
    } catch (err) {
      console.error('Failed to load project details', err);
    }
  };

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) return;

    if (inputType === 'url' && !sourceUrl.trim()) return;
    if (inputType === 'text' && !sourceText.trim()) return;
    if (inputType === 'file') {
      if (!selectedFile) {
        error('Please select a document or image file to upload.');
        return;
      }
      try {
        setIsAddingSource(true);
        info(`Extracting multi-modal content from ${selectedFile.name}...`);
        const newSource = await researchApi.uploadSourceFile(
          activeProject.id,
          selectedFile,
          sourceTitle.trim() || undefined
        );
        setSources((prev) => [...prev, newSource]);
        setSelectedFile(null);
        setSourceTitle('');
        success(`Extracted & ingested: "${newSource.title}"`);
        const updated = await researchApi.getProject(activeProject.id);
        setActiveProject(updated);
        setSources(updated.sources || []);
      } catch (err: any) {
        error(err.message || 'Failed to extract file content');
      } finally {
        setIsAddingSource(false);
      }
      return;
    }

    try {
      setIsAddingSource(true);
      const newSource = await researchApi.addSource(activeProject.id, {
        source_type: inputType,
        url: inputType === 'url' ? sourceUrl.trim() : undefined,
        title: sourceTitle.trim() || undefined,
        text_content: inputType === 'text' ? sourceText.trim() : undefined,
      });

      setSources((prev) => [...prev, newSource]);
      setSourceUrl('');
      setSourceTitle('');
      setSourceText('');
      success(`Source "${newSource.title}" added to investigation!`);

      // Refresh project in background to sync
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
    if (!deleteSourceId) return;
    try {
      await researchApi.deleteSource(deleteSourceId);
      setSources((prev) => prev.filter((s) => s.id !== deleteSourceId));
      success('Source removed from investigation.');
    } catch (err: any) {
      error(err.message || 'Failed to delete source');
    } finally {
      setDeleteSourceId(null);
    }
  };

  const handleGenerateBrief = async () => {
    if (!activeProject) return;
    if (sources.length < 3) {
      error(`At least 3 verified sources are required. Currently: ${sources.length}`);
      return;
    }

    try {
      setIsGeneratingBrief(true);
      info('Synthesizing cross-source evidence and newsletter angles...');
      const b = await researchApi.generateBrief(activeProject.id);
      setBrief(b);
      setActiveTab('brief');
      success('Research brief generated and persisted successfully!');
    } catch (err: any) {
      error(err.message || 'Failed to generate brief');
    } finally {
      setIsGeneratingBrief(false);
    }
  };

  const handleProceedToEditorial = (angleHeadline?: string) => {
    if (!activeProject) return;
    const query = new URLSearchParams({
      projectId: activeProject.id,
      ...(angleHeadline ? { angle: angleHeadline } : {}),
    });
    navigate(`/editorial?${query.toString()}`);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header & Project Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Research Assistant</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 font-medium">
              Module A
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Aggregate 3+ sources, verify direct claims against excerpts, and synthesize a founder-ready research brief.
          </p>
        </div>

        {/* Project Selector */}
        <div className="flex items-center gap-3">
          <select
            value={activeProject?.id || ''}
            onChange={(e) => selectProject(e.target.value)}
            className="text-xs bg-white border border-slate-300 rounded-lg px-3 py-2 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                Project: {p.title} ({p.sources?.length || 0} sources)
              </option>
            ))}
          </select>

          <button
            onClick={handleGenerateBrief}
            disabled={isGeneratingBrief || sources.length < 3}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold shadow-xs transition-all ${
              sources.length >= 3
                ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-500/20 shadow-md ring-2 ring-blue-500/40'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-200 dark:border-slate-700 cursor-not-allowed'
            }`}
            title={sources.length < 3 ? `Requires 3 sources to synthesize (currently ${sources.length}/3)` : 'Click to synthesize research brief'}
          >
            {isGeneratingBrief ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Synthesizing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>
                  {sources.length >= 3 ? 'Generate Research Brief' : `Generate Brief (${sources.length}/3 Sources)`}
                </span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Workspace Layout (Two-Column) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Source Collection & Ingestion (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Add Source Card */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-2">
              <Plus className="w-3.5 h-3.5 text-blue-600" />
              Ingest Source Material
            </h3>

            {/* Input Type Toggle */}
            <div className="flex p-1 bg-slate-100 rounded-lg text-xs font-medium mb-3">
              <button
                type="button"
                onClick={() => setInputType('url')}
                className={`flex-1 py-1.5 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  inputType === 'url' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Web URL</span>
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
              <button
                type="button"
                onClick={() => setInputType('file')}
                className={`flex-1 py-1.5 rounded-md flex items-center justify-center gap-1.5 transition-all ${
                  inputType === 'file' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <UploadCloud className="w-3.5 h-3.5" />
                <span>Upload File</span>
              </button>
            </div>

            <form onSubmit={handleAddSource} className="space-y-3">
              {inputType === 'url' ? (
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Article or Release URL
                  </label>
                  <input
                    type="url"
                    required
                    placeholder="https://openai.com/index/o3-model-overview"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                  />
                  <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-500" /> SSRF Protected • Trafilatura + BS4
                  </p>
                </div>
              ) : inputType === 'text' ? (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Source Title / Publisher
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Anthropic Research Paper"
                      value={sourceTitle}
                      onChange={(e) => setSourceTitle(e.target.value)}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Pasted Article Content
                    </label>
                    <textarea
                      rows={4}
                      required
                      placeholder="Paste verbatim announcement or article text..."
                      value={sourceText}
                      onChange={(e) => setSourceText(e.target.value)}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none resize-none font-mono"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Source Title (Optional)
                    </label>
                    <input
                      type="text"
                      placeholder={selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, "") : "e.g. Research Paper or Technical Spec"}
                      value={sourceTitle}
                      onChange={(e) => setSourceTitle(e.target.value)}
                      className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">
                      Document, PDF or Image
                    </label>
                    <div className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-xl p-4 text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-blue-50/20">
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
                            <div className="text-xs font-semibold text-slate-700">Click to upload or drag & drop</div>
                            <div className="text-[10px] text-slate-400 mt-0.5">PDF, Word (.docx), Plaintext, or Images (PNG, JPG)</div>
                          </>
                        )}
                      </label>
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={isAddingSource}
                className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
              >
                {isAddingSource ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Extracting Content...</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-3.5 h-3.5" />
                    <span>{inputType === 'file' ? 'Extract & Ingest File' : 'Add Source to Investigation'}</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Sources List Panel (Inspired by Image 2 - 4 References panel) */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                Verified Sources ({sources.length})
              </h3>
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                sources.length >= 3 ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
              }`}>
                {sources.length >= 3 ? 'Ready for Brief' : `Requires ${3 - sources.length} more`}
              </span>
            </div>

            {sources.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
                No sources added. Add at least 3 URLs or pasted texts to unlock cross-source synthesis.
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                {sources.map((s, idx) => (
                  <div
                    key={s.id}
                    className="p-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300 transition-all text-xs space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-blue-100 text-blue-700 font-mono text-[10px] flex items-center justify-center font-bold">
                            {idx + 1}
                          </span>
                          <span className="font-semibold text-slate-900 line-clamp-1">{s.title}</span>
                        </div>
                        {s.url && (
                          <a
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-blue-600 hover:underline flex items-center gap-1"
                          >
                            <span className="max-w-[200px] truncate">{s.url}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                      <button
                        onClick={() => setDeleteSourceId(s.id)}
                        className="text-slate-400 hover:text-red-600 p-1 rounded transition-colors"
                        title="Remove source"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Extraction Status */}
                    <div className="flex items-center gap-2 text-[11px]">
                      {s.extraction_status === 'completed' ? (
                        <span className="text-emerald-700 flex items-center gap-1 font-medium">
                          <CheckCircle2 className="w-3 h-3" /> Content Verified ({s.extracted_content ? `${s.extracted_content.split(' ').length} words` : 'parsed'})
                        </span>
                      ) : s.extraction_status === 'extracting' ? (
                        <span className="text-blue-600 flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" /> Extracting...
                        </span>
                      ) : (
                        <div className="flex flex-col gap-1.5 w-full">
                          <div className="flex items-center justify-between w-full">
                            <span className="text-red-600 flex items-center gap-1 font-medium">
                              <AlertCircle className="w-3 h-3" /> Extraction failed
                            </span>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleRetryExtract(s.id)}
                                className="text-[11px] text-blue-600 hover:underline"
                              >
                                Retry
                              </button>
                              <label className="text-[11px] text-blue-600 hover:underline cursor-pointer flex items-center gap-0.5 font-medium">
                                {uploadingSourceId === s.id ? (
                                  <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
                                ) : (
                                  <UploadCloud className="w-3 h-3 text-blue-600" />
                                )}
                                <span>{uploadingSourceId === s.id ? 'Extracting...' : 'Upload File'}</span>
                                <input
                                  type="file"
                                  accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.webp"
                                  className="hidden"
                                  disabled={uploadingSourceId === s.id}
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) handleReuploadFile(s.id, file);
                                  }}
                                />
                              </label>
                              <button
                                onClick={() => {
                                  setEditingSourceId(editingSourceId === s.id ? null : s.id);
                                  setManualText('');
                                }}
                                className="text-[11px] text-indigo-600 font-semibold hover:underline"
                              >
                                {editingSourceId === s.id ? 'Cancel' : 'Paste Text'}
                              </button>
                            </div>
                          </div>
                          {editingSourceId === s.id && (
                            <div className="mt-2 p-2.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2">
                              <div className="text-[10px] text-slate-500 font-medium">
                                Paste article content to verify this source directly:
                              </div>
                              <textarea
                                value={manualText}
                                onChange={(e) => setManualText(e.target.value)}
                                placeholder="Paste full article text or press release here..."
                                className="w-full h-20 p-2 text-xs border border-slate-200 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100"
                              />
                              <div className="flex justify-end gap-2">
                                <Button
                                  size="sm"
                                  variant="secondary"
                                  onClick={() => setEditingSourceId(null)}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  size="sm"
                                  variant="primary"
                                  disabled={!manualText.trim()}
                                  isLoading={isSavingManual}
                                  onClick={() => handleSaveManualSource(s.id)}
                                >
                                  Verify Content
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {s.summary && (
                      <p className="text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-100 line-clamp-3">
                        {s.summary}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Cross-Source Synthesis & Brief Viewer (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2 text-xs font-medium">
            <button
              onClick={() => setActiveTab('brief')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'brief' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Research Brief
            </button>
            <button
              onClick={() => setActiveTab('intelligence')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                activeTab === 'intelligence' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              Intelligence & Graph
            </button>
            <button
              onClick={() => setActiveTab('evidence')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'evidence' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Evidence Verification ({brief?.evidence?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab('facts')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                activeTab === 'facts' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Facts vs Analysis vs Speculation
            </button>
          </div>

          {activeTab === 'intelligence' ? (
            activeProject ? (
              <ResearchIntelligenceDashboard projectId={activeProject.id} sourceCount={sources.length} />
            ) : null
          ) : !brief ? (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
                <Sparkles className="w-6 h-6" />
              </div>
              <h4 className="text-base font-semibold text-slate-800">No Combined Brief Generated Yet</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Once you collect at least 3 sources, click "Generate Research Brief" to trigger cross-source synthesis, extract verified evidence, and formulate newsletter angles.
              </p>
              {sources.length >= 3 && (
                <button
                  onClick={handleGenerateBrief}
                  disabled={isGeneratingBrief}
                  className="mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                >
                  Generate Brief Now
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* TAB 1: RESEARCH BRIEF */}
              {activeTab === 'brief' && (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-6 shadow-xs">
                  {/* Executive Summary */}
                  <div className="space-y-2 border-b border-slate-100 pb-4">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-blue-600 font-semibold">
                      Section A • Executive Summary
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed font-serif text-[13px]">
                      {brief.executive_summary}
                    </p>
                  </div>

                  {/* What Happened & Why It Matters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-slate-100 pb-4">
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-semibold">
                        Section B • What Happened?
                      </span>
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {brief.brief_content?.what_happened}
                      </p>
                    </div>
                    <div className="space-y-1.5">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-semibold">
                        Section C • Why Does It Matter?
                      </span>
                      <p className="text-xs text-slate-700 leading-relaxed">
                        {brief.brief_content?.why_it_matters}
                      </p>
                    </div>
                  </div>

                  {/* Who Should Care (4 Audiences) */}
                  <div className="space-y-3 border-b border-slate-100 pb-4">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-semibold">
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
                      <span className="text-[11px] font-mono uppercase tracking-wider text-slate-600 font-semibold">
                        Section H • Newsletter Angles & Pitches
                      </span>
                      <span className="text-[10px] text-blue-600 font-medium">Select angle to draft</span>
                    </div>

                    <div className="space-y-3">
                      {(brief.newsletter_angles || []).map((angle, idx) => {
                        const isRecommended = brief.recommended_angle?.headline === angle.headline;
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
                              <div>
                                {isRecommended && (
                                  <span className="inline-block text-[10px] font-semibold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-full mb-1">
                                    ★ Recommended Angle
                                  </span>
                                )}
                                <h4 className="font-semibold text-slate-900 text-sm">{angle.headline}</h4>
                                <p className="text-slate-600 mt-1">{angle.angle_pitch}</p>
                              </div>
                              <button
                                onClick={() => handleProceedToEditorial(angle.headline)}
                                className="shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-xs"
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

              {/* TAB 2: EVIDENCE VERIFICATION */}
              {activeTab === 'evidence' && (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                        Section E • Source Verification & Claims
                      </h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Every factual assertion is audited against verbatim source text excerpts.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {brief.evidence && brief.evidence.length > 0 ? (
                      brief.evidence.map((ev, i) => (
                        <div key={i} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-900">Claim: {ev.claim}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono font-medium">
                              Direct Excerpt
                            </span>
                          </div>
                          <blockquote className="italic text-slate-600 bg-white p-2.5 rounded border-l-2 border-blue-500 text-[11px]">
                            "{ev.supporting_excerpt}"
                          </blockquote>
                          <div className="text-[11px] text-slate-400 flex items-center gap-2">
                            <span>Source: <strong>{ev.source_title}</strong></span>
                            {ev.source_url && (
                              <a href={ev.source_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                                [view link]
                              </a>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-400 py-4 text-center">No explicit evidence items logged.</p>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 3: FACTS VS ANALYSIS VS SPECULATION */}
              {activeTab === 'facts' && (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
                  <div className="border-b border-slate-100 pb-3">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                      Section F • Epistemic Classification
                    </h4>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Strictly segregates confirmed facts from analytical deductions and speculative forward projections.
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
                        {brief.brief_content?.facts_vs_analysis?.facts?.map((f, i) => (
                          <li key={i}>{f}</li>
                        )) || <li>No verified facts logged.</li>}
                      </ul>
                    </div>

                    {/* Editorial Analysis */}
                    <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2 text-xs">
                      <div className="flex items-center gap-1.5 font-semibold text-blue-900">
                        <Scale className="w-4 h-4 text-blue-600" />
                        <span>Editorial Analysis</span>
                      </div>
                      <ul className="space-y-2 text-[11px] text-blue-950 list-disc list-inside">
                        {brief.brief_content?.facts_vs_analysis?.analysis?.map((a, i) => (
                          <li key={i}>{a}</li>
                        )) || <li>No analytical points logged.</li>}
                      </ul>
                    </div>

                    {/* Speculation & Predictions */}
                    <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/50 space-y-2 text-xs">
                      <div className="flex items-center gap-1.5 font-semibold text-amber-900">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>Speculation & Hype</span>
                      </div>
                      <ul className="space-y-2 text-[11px] text-amber-950 list-disc list-inside">
                        {brief.brief_content?.facts_vs_analysis?.speculation?.map((s, i) => (
                          <li key={i}>{s}</li>
                        )) || <li>No unverified speculation detected.</li>}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
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

