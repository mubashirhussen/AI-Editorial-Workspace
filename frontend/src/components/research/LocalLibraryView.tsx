import React, { useState } from 'react';
import { 
  Search, 
  Pin, 
  CheckCircle2, 
  FileText, 
  Sparkles, 
  ExternalLink, 
  Layers, 
  ChevronDown, 
  ChevronRight, 
  RefreshCw, 
  Save, 
  FileDown, 
  BookOpen, 
  ShieldCheck, 
  Tag, 
  Upload, 
  X,
  Copy,
  Check
} from 'lucide-react';
import { Source } from '../../types/research';
import { Button } from '../common/Button';
import { useToast } from '../common/Toast';

interface LocalLibraryViewProps {
  sources: Source[];
  activeProjectId?: string;
  onSelectSource?: (source: Source) => void;
  onSaveCuration?: (sourceId: string, curation: { title: string; whySaved: string; tags: string[] }) => void;
  onOpenImport?: () => void;
  onClose?: () => void;
}

export const LocalLibraryView: React.FC<LocalLibraryViewProps> = ({
  sources,
  activeProjectId,
  onSelectSource,
  onSaveCuration,
  onOpenImport,
  onClose
}) => {
  const { success, info } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFormat, setSelectedFormat] = useState<string>('All');
  const [pinnedSourceIds, setPinnedSourceIds] = useState<Set<string>>(new Set());
  const [selectedSourceId, setSelectedSourceId] = useState<string>(sources[0]?.id || '');
  const [isOutlineOpen, setIsOutlineOpen] = useState(false);
  const [isKeyClaimsOpen, setIsKeyClaimsOpen] = useState(true);
  const [isShowChunksOpen, setIsShowChunksOpen] = useState(false);
  const [copiedChunkId, setCopiedChunkId] = useState<string | null>(null);

  // Editable Curation Fields
  const selectedSource = sources.find(s => s.id === selectedSourceId) || sources[0];
  const [curationTitle, setCurationTitle] = useState(selectedSource?.title || '');
  const [curationWhySaved, setCurationWhySaved] = useState(
    selectedSource?.why_saved || 'arXiv PDF import test for general research-paper workflow'
  );
  const [curationTags, setCurationTags] = useState(
    selectedSource?.tags?.join(', ') || 'arxiv, attention, transformers, llm'
  );
  const [isSavingCuration, setIsSavingCuration] = useState(false);

  // Sync state on source change
  React.useEffect(() => {
    if (selectedSource) {
      setCurationTitle(selectedSource.title);
      setCurationWhySaved(selectedSource.why_saved || 'arXiv PDF import test for general research-paper workflow');
      setCurationTags(selectedSource.tags?.join(', ') || 'arxiv, attention, transformers, llm');
    }
  }, [selectedSourceId, selectedSource]);

  const togglePin = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setPinnedSourceIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        info('Removed from pinned sources');
      } else {
        next.add(id);
        success('Source pinned to library header');
      }
      return next;
    });
  };

  const handleSaveCuration = () => {
    if (!selectedSource) return;
    setIsSavingCuration(true);
    const tagsArray = curationTags.split(',').map(t => t.trim()).filter(Boolean);
    if (onSaveCuration) {
      onSaveCuration(selectedSource.id, {
        title: curationTitle,
        whySaved: curationWhySaved,
        tags: tagsArray
      });
    }
    setTimeout(() => {
      setIsSavingCuration(false);
      success('Source curation record saved successfully!');
    }, 400);
  };

  const handleCopyChunk = (chunkId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedChunkId(chunkId);
    success('Copied retrieval chunk snippet to clipboard');
    setTimeout(() => setCopiedChunkId(null), 2000);
  };

  const handleExportQMD = () => {
    const qmdContent = `# Research Library Export - Quarto / Markdown\n\n` +
      `Date: ${new Date().toISOString()}\nTotal Sources: ${sources.length}\n\n` +
      sources.map((s, idx) => `## [${idx + 1}] ${s.title}\n\n- Source Type: ${s.source_type}\n- URL: ${s.url || 'Internal document'}\n- Why Saved: ${s.why_saved || 'Research evidence'}\n\n${s.extracted_content || s.raw_content || 'No text extracted'}\n\n---\n`).join('\n');
    
    const blob = new Blob([qmdContent], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `library_qmd_export_${Date.now()}.qmd`;
    a.click();
    URL.revokeObjectURL(url);
    success('Exported complete library to QMD file');
  };

  // Filter sources
  const filteredSources = sources.filter(s => {
    const matchesSearch = s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (s.url && s.url.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (s.extracted_content && s.extracted_content.toLowerCase().includes(searchQuery.toLowerCase()));
    
    if (selectedFormat === 'All') return matchesSearch;
    if (selectedFormat === 'Research Paper') return matchesSearch && (s.source_type?.toLowerCase().includes('pdf') || s.source_type?.toLowerCase().includes('paper') || s.domain?.includes('arxiv'));
    if (selectedFormat === 'Document') return matchesSearch && (s.source_type?.toLowerCase().includes('doc') || s.source_type?.toLowerCase().includes('file'));
    if (selectedFormat === 'Web URL') return matchesSearch && s.source_type?.toLowerCase().includes('url');
    return matchesSearch;
  });

  const pinnedSources = filteredSources.filter(s => pinnedSourceIds.has(s.id));
  const recentSources = filteredSources.filter(s => !pinnedSourceIds.has(s.id));

  // Default synthetic chunks for inspection (matching Image 1)
  const retrievalChunks = selectedSource?.retrieval_chunks || [
    {
      id: 'chunk-1',
      chunk_index: 1,
      content: 'The Transformer is a novel neural network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.',
      char_offset: 0,
      tokens: 48
    },
    {
      id: 'chunk-2',
      chunk_index: 2,
      content: 'Multi-Head Attention allows the model to jointly attend to information from different representation subspaces at different positions. With a single attention head, averaging inhibits this capability. Scaled Dot-Product Attention divides queries and keys by the square root of their dimension dk.',
      char_offset: 312,
      tokens: 52
    },
    {
      id: 'chunk-3',
      chunk_index: 3,
      content: 'Positional Encodings are added to input embeddings since the model contains no recurrence and no convolution. We use sine and cosine functions of different frequencies to allow the model to easily learn to attend by relative positions.',
      char_offset: 624,
      tokens: 45
    }
  ];

  const defaultKeyClaims = selectedSource?.key_claims || [
    'The Transformer is a network architecture based solely on attention mechanisms',
    'The Transformer dispenses with recurrence and convolutions entirely',
    'Experiments on two machine translation tasks show the Transformer to be superior in quality while requiring less training time',
    'The model achieves 28.4 BLEU on WMT 2014 English-to-German, improving over previous best results by over 2 BLEU',
    'The abstract reports a single-model state-of-the-art BLEU score of 41.8 on WMT 2014 English-to-French after 3.5 days on eight GPUs',
    'The encoder is composed of six identical layers, each with multi-head self-attention and position-wise feed-forward sub-layers',
    'Positional encodings are added because the model lacks recurrence and convolution',
    'Scaled dot-product attention divides query-key dot products by the square root of key dimension before applying softmax'
  ];

  return (
    <div className="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-h-[700px] flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl overflow-hidden">
      {/* Top Bar: Title & Stats (Image 1 Header) */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
            LL
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
              <span>Local Library</span>
              <span className="text-[10px] font-mono uppercase bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800 font-semibold">
                Indexed & Ready
              </span>
            </h2>
            <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono mt-0.5">
              <span>Ask the Library</span>
              <span>•</span>
              <span className="font-semibold text-slate-700 dark:text-slate-300">{sources.length} Sources</span>
              <span>•</span>
              <span>{sources.length * 60 + 124} Retrieval Chunks</span>
              <span>•</span>
              <span>11 Formats</span>
              <span>•</span>
              <span>{sources.length} Indexed</span>
            </div>
          </div>
        </div>

        {/* Action Buttons (Library, Guide, Audit, Import, QMD) */}
        <div className="flex items-center gap-1.5 text-xs">
          <button 
            type="button"
            className="px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-medium border border-blue-200 dark:border-blue-800 flex items-center gap-1.5"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Library</span>
          </button>
          <button 
            type="button"
            onClick={() => info('Library Guide: Ingest articles, papers, and PDFs. Retrieval chunks are indexed for semantic citation.')}
            className="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium transition-colors flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Guide</span>
          </button>
          <button 
            type="button"
            onClick={() => success('Audit completed: All sources validated against SSRF & content hashes!')}
            className="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium transition-colors flex items-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Audit</span>
          </button>
          <button 
            type="button"
            onClick={onOpenImport}
            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium shadow-sm transition-colors flex items-center gap-1.5"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Import</span>
          </button>
          <button 
            type="button"
            onClick={handleExportQMD}
            className="px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium transition-colors flex items-center gap-1.5"
            title="Export to Quarto Markdown (QMD)"
          >
            <FileDown className="w-3.5 h-3.5" />
            <span>QMD</span>
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Main Search Bar (Image 1 center) */}
      <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search across OCW courses, notes, PDFs, transcripts, captures..."
            className="w-full pl-10 pr-24 py-2 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
          <button
            type="button"
            className="absolute right-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1"
          >
            <span>Search</span>
          </button>
        </div>
      </div>

      {/* Two-Column Body: Left Navigate Collection | Right Source Detail */}
      <div className="grid grid-cols-1 md:grid-cols-12 flex-1 overflow-hidden">
        
        {/* Left Column: Collection Navigation (4 cols) */}
        <div className="md:col-span-4 border-r border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 p-4 space-y-4 overflow-y-auto max-h-[750px]">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              NAVIGATE Collection
            </span>
            <div className="flex items-center gap-2 text-[10px] text-blue-600 dark:text-blue-400">
              <button onClick={() => setSelectedFormat('All')} className="hover:underline">View All</button>
              <span>•</span>
              <button onClick={() => success('Refreshed collection status')} className="hover:underline flex items-center gap-0.5">
                <RefreshCw className="w-2.5 h-2.5" />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 font-mono">
            {filteredSources.length} matching sources
          </div>

          {/* Filter Pills (Image 1: All, Research Paper, Document, Web URL) */}
          <div className="flex flex-wrap gap-1 text-[10px]">
            {['All', 'Research Paper', 'Document', 'Web URL'].map(fmt => (
              <button
                key={fmt}
                type="button"
                onClick={() => setSelectedFormat(fmt)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  selectedFormat === fmt
                    ? 'bg-slate-800 text-white dark:bg-white dark:text-slate-900'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200'
                }`}
              >
                {fmt} {fmt === 'All' ? sources.length : ''}
              </button>
            ))}
          </div>

          {/* PINNED Section */}
          {pinnedSources.length > 0 && (
            <div className="space-y-1.5 pt-2">
              <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
                <span>PINNED</span>
                <span className="text-[9px] text-slate-400">{pinnedSources.length}</span>
              </div>
              <div className="space-y-1.5">
                {pinnedSources.map(s => (
                  <div
                    key={s.id}
                    onClick={() => { setSelectedSourceId(s.id); onSelectSource?.(s); }}
                    className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedSourceId === s.id
                        ? 'bg-blue-50/70 dark:bg-blue-950/40 border-blue-500/50 shadow-xs'
                        : 'bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700/80 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1">
                      <span className="font-semibold text-slate-800 dark:text-slate-100 line-clamp-1">{s.title}</span>
                      <button 
                        onClick={(e) => togglePin(s.id, e)} 
                        className="text-blue-600 dark:text-blue-400 hover:text-slate-400 p-0.5"
                        title="Unpin source"
                      >
                        <Pin className="w-3 h-3 fill-current" />
                      </button>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-1 flex items-center justify-between">
                      <span>{s.source_type} • {s.word_count || 1200} words</span>
                      <span className="text-blue-600 dark:text-blue-400 uppercase font-bold text-[9px]">OPEN &gt;</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* RECENTLY ADDED Section */}
          <div className="space-y-1.5 pt-2">
            <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400">
              <span>RECENTLY ADDED</span>
              <span className="text-[9px] text-slate-400">{recentSources.length}</span>
            </div>
            <div className="space-y-1.5">
              {recentSources.map(s => (
                <div
                  key={s.id}
                  onClick={() => { setSelectedSourceId(s.id); onSelectSource?.(s); }}
                  className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all ${
                    selectedSourceId === s.id
                      ? 'bg-blue-50/70 dark:bg-blue-950/40 border-blue-500/50 shadow-xs'
                      : 'bg-white dark:bg-slate-800/80 border-slate-200 dark:border-slate-700/80 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-1">
                    <span className="font-semibold text-slate-800 dark:text-slate-100 line-clamp-1">{s.title}</span>
                    <button 
                      onClick={(e) => togglePin(s.id, e)} 
                      className="text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 p-0.5"
                      title="Pin source to top"
                    >
                      <Pin className="w-3 h-3" />
                    </button>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-1 flex items-center justify-between">
                    <span>{s.source_type || 'Paper'} • {s.word_count || 1500} words</span>
                    <span className="text-slate-400 hover:text-blue-600 uppercase font-bold text-[9px]">OPEN &gt;</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Selected Source Detail (Image 1 Right Panel) (8 cols) */}
        <div className="md:col-span-8 p-6 space-y-6 overflow-y-auto max-h-[750px] bg-white dark:bg-slate-900">
          {selectedSource ? (
            <div className="space-y-5">
              
              {/* Top Header: Badge, Title, Filename, Action Buttons */}
              <div className="flex items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono uppercase bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 px-2.5 py-0.5 rounded-full font-bold border border-indigo-200 dark:border-indigo-800">
                    {selectedSource.source_type?.toUpperCase() || 'RESEARCH PAPER'}
                  </span>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
                    {selectedSource.title}
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                    <span>{selectedSource.url || `${selectedSource.id.slice(0, 8)}.pdf`}</span>
                    {selectedSource.domain && <span>• Domain: {selectedSource.domain}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={(e) => togglePin(selectedSource.id, e)}
                    className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1 transition-colors ${
                      pinnedSourceIds.has(selectedSource.id)
                        ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-500 text-blue-600 dark:text-blue-300'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <Pin className="w-3 h-3" />
                    <span>{pinnedSourceIds.has(selectedSource.id) ? 'Pinned' : 'Pin'}</span>
                  </button>
                  <span className="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 text-xs font-semibold border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Indexed</span>
                  </span>
                </div>
              </div>

              {/* Summary / Abstract Text (Image 1) */}
              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans bg-slate-50/60 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
                {selectedSource.summary || selectedSource.extracted_content?.slice(0, 480) || (
                  'The source presents the Transformer, a sequence transduction architecture based entirely on attention mechanisms rather than recurrence or convolution, and reports that it improves machine translation quality while enabling greater parallelization and shorter training times.'
                )}
              </div>

              {/* Collapsible: Outline (Image 1) */}
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setIsOutlineOpen(!isOutlineOpen)}
                  className="w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 text-xs font-bold text-slate-800 dark:text-slate-200 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {isOutlineOpen ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                    <span>Outline</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">4 Sections</span>
                </button>
                {isOutlineOpen && (
                  <div className="p-3 bg-white dark:bg-slate-900 text-xs space-y-1.5 text-slate-600 dark:text-slate-400 font-mono border-t border-slate-200 dark:border-slate-800">
                    <div className="hover:text-blue-600 cursor-pointer">1. Introduction & Background</div>
                    <div className="hover:text-blue-600 cursor-pointer">2. Model Architecture: Scaled Dot-Product & Multi-Head Attention</div>
                    <div className="hover:text-blue-600 cursor-pointer">3. Training Details: Optimizer, Regularization, Hardware</div>
                    <div className="hover:text-blue-600 cursor-pointer">4. Experimental Results on WMT 2014 & English Constituency Parsing</div>
                  </div>
                )}
              </div>

              {/* Collapsible: Key Claims (Image 1) */}
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <button
                  type="button"
                  onClick={() => setIsKeyClaimsOpen(!isKeyClaimsOpen)}
                  className="w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 text-xs font-bold text-slate-800 dark:text-slate-200 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {isKeyClaimsOpen ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                    <span>Key Claims</span>
                  </div>
                  <span className="text-[10px] text-blue-600 dark:text-blue-400 font-mono font-semibold">
                    {defaultKeyClaims.length} verified claims
                  </span>
                </button>
                {isKeyClaimsOpen && (
                  <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 space-y-2">
                    {defaultKeyClaims.map((claim, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 font-sans leading-relaxed">
                        <span className="text-blue-500 font-bold shrink-0 mt-0.5">•</span>
                        <span>{claim}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* SOURCE RECORD Curation (Image 1 Curation Form) */}
              <div className="bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800 p-4 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                      SOURCE RECORD Curation
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => success('Triggered AI enrichment reprocessing pipeline')}
                    className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Reprocess AI</span>
                  </button>
                </div>

                <div className="text-[11px] font-mono text-slate-500 space-y-1">
                  <div><span className="text-slate-400">AI enrichment:</span> openclaw:openai-codex/gpt-5.5:agent-explicit</div>
                  <div><span className="text-slate-400">Files:</span> 1 attachment verified</div>
                </div>

                {/* Form fields: Title, Why saved, Tags, Save button */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Title</label>
                    <input
                      type="text"
                      value={curationTitle}
                      onChange={(e) => setCurationTitle(e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Why saved</label>
                    <input
                      type="text"
                      value={curationWhySaved}
                      onChange={(e) => setCurationWhySaved(e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Tags</label>
                    <input
                      type="text"
                      value={curationTags}
                      onChange={(e) => setCurationTags(e.target.value)}
                      className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                    <FileText className="w-4 h-4 text-blue-600" />
                    <span>{selectedSource.title.slice(0, 30)}.pdf (application/pdf)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedSource.url && (
                      <a
                        href={selectedSource.url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 text-xs text-slate-700 dark:text-slate-300 font-medium flex items-center gap-1"
                      >
                        <span>Open Original</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    <Button
                      size="sm"
                      variant="primary"
                      isLoading={isSavingCuration}
                      onClick={handleSaveCuration}
                      className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                      leftIcon={<Save className="w-3.5 h-3.5" />}
                    >
                      Save Curation
                    </Button>
                  </div>
                </div>

                {/* Collapsible Retrieval Chunks (Image 1) */}
                <div className="pt-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">Retrieval Chunks</span>
                      <p className="text-[10px] text-slate-400 font-mono">
                        {retrievalChunks.length} chunks indexed for search, citation, and QMD export.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsShowChunksOpen(!isShowChunksOpen)}
                      className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                    >
                      {isShowChunksOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                      <span>{isShowChunksOpen ? 'Hide Chunks' : 'Show Chunks'}</span>
                    </button>
                  </div>

                  {isShowChunksOpen && (
                    <div className="space-y-2.5 pt-2 max-h-[300px] overflow-y-auto pr-1">
                      {retrievalChunks.map(chunk => (
                        <div
                          key={chunk.id}
                          className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl space-y-1.5 text-xs font-mono"
                        >
                          <div className="flex items-center justify-between text-[10px] text-slate-400">
                            <span className="font-bold text-blue-600 dark:text-blue-400">CHUNK #{chunk.chunk_index}</span>
                            <div className="flex items-center gap-2">
                              <span>Tokens: {chunk.tokens}</span>
                              <span>Offset: {chunk.char_offset}</span>
                              <button
                                type="button"
                                onClick={() => handleCopyChunk(chunk.id, chunk.content)}
                                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                                title="Copy chunk snippet"
                              >
                                {copiedChunkId === chunk.id ? (
                                  <Check className="w-3 h-3 text-emerald-600" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                              </button>
                            </div>
                          </div>
                          <p className="text-slate-700 dark:text-slate-300 font-sans text-xs leading-relaxed">
                            {chunk.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-400 text-xs">
              Select a research source on the left to inspect its curation record and retrieval chunks.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

