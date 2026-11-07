import React, { useState } from 'react';
import { 
  Search, 
  BookOpen, 
  Check, 
  Copy, 
  RefreshCw, 
  Send, 
  AtSign, 
  FileText, 
  X, 
  Sparkles,
  Plus,
  MessageSquare,
  BookmarkCheck
} from 'lucide-react';
import { Source } from '../../types/research';
import { Button } from '../common/Button';
import { useToast } from '../common/Toast';

interface AfforaiCiteModalProps {
  isOpen: boolean;
  onClose: () => void;
  sources: Source[];
  onInsertCitation: (citationTag: string) => void;
  onReplaceTextWithProposal?: (proposal: string) => void;
}

export const AfforaiCiteModal: React.FC<AfforaiCiteModalProps> = ({
  isOpen,
  onClose,
  sources,
  onInsertCitation,
  onReplaceTextWithProposal
}) => {
  const { success, info } = useToast();
  const [activeTab, setActiveTab] = useState<'cite' | 'research' | 'write'>('cite');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedReferenceIds, setSelectedReferenceIds] = useState<Set<string>>(new Set());
  
  // Interactive Chat State
  const [chatPrompt, setChatPrompt] = useState('');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    text: string;
    sourcesCited?: string[];
  }>>([
    {
      id: '1',
      role: 'user',
      text: 'Rephrase this text "The findings indicate that a uniform distribution of nanoparticles within the polymer matrix significantly improves mechanical performance, with tensile strength increasing by approximately 25%."'
    },
    {
      id: '2',
      role: 'assistant',
      text: 'The results demonstrate that evenly distributing nanoparticles throughout the polymer matrix markedly enhances its mechanical properties, leading to a roughly 25% increase in tensile strength.',
      sourcesCited: ['Garcia, M. L. (2002)', 'Lee, K. W. (1999)']
    }
  ]);

  if (!isOpen) return null;

  // Curated fallback reference library if empty
  const referenceList = sources.length > 0 ? sources : [
    {
      id: 'ref-1',
      project_id: 'default',
      title: 'Analyzing the Effects of Artificial Intelligence on Global Workforce Dynamics',
      author: 'Smith, J. A., & Brown, L. B.',
      published_at: '2020',
      source_type: 'journal',
      extraction_status: 'completed' as const,
      created_at: new Date().toISOString()
    },
    {
      id: 'ref-2',
      project_id: 'default',
      title: 'The Impact of Climate Change on Coastal Ecosystems',
      author: 'Lee, K. W.',
      published_at: '1999',
      source_type: 'paper',
      extraction_status: 'completed' as const,
      created_at: new Date().toISOString()
    },
    {
      id: 'ref-3',
      project_id: 'default',
      title: 'Machine Learning Algorithms in Predicting Stock Market Trends',
      author: 'Garcia, M. L.',
      published_at: '2002',
      source_type: 'paper',
      extraction_status: 'completed' as const,
      created_at: new Date().toISOString()
    },
    {
      id: 'ref-4',
      project_id: 'default',
      title: 'The Role of Social Media in Shaping Public Opinion',
      author: 'Chen, X.',
      published_at: '1982',
      source_type: 'monograph',
      extraction_status: 'completed' as const,
      created_at: new Date().toISOString()
    }
  ];

  const filteredReferences = referenceList.filter(r =>
    r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (r.author && r.author.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const toggleSelectReference = (id: string) => {
    setSelectedReferenceIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedReferences = referenceList.filter(r => selectedReferenceIds.has(r.id));

  const handleInsertSelected = () => {
    if (selectedReferences.length === 0) return;
    const citationString = `[${selectedReferences.map(r => `${r.author || r.title} ${r.published_at || ''}`.trim()).join('; ')}]`;
    onInsertCitation(citationString);
    success(`Inserted ${selectedReferences.length} selected citation(s) into editor!`);
    onClose();
  };

  const handleSendChat = () => {
    if (!chatPrompt.trim()) return;
    const userMsg = chatPrompt;
    setChatPrompt('');
    setChatMessages(prev => [...prev, { id: String(Date.now()), role: 'user', text: userMsg }]);
    setIsAiThinking(true);

    setTimeout(() => {
      let reply = `Based on empirical research synthesis, here is an optimized, research-grounded formulation: "${userMsg.replace(/rephrase|rewrite|summarize/gi, '').trim()}"`;
      if (selectedReferences.length > 0) {
        reply += ` Corroborated by ${selectedReferences.map(r => r.author || r.title).join(' and ')}.`;
      }
      setChatMessages(prev => [
        ...prev,
        {
          id: String(Date.now() + 1),
          role: 'assistant',
          text: reply,
          sourcesCited: selectedReferences.map(r => `${r.author || r.title} (${r.published_at || 'n.d.'})`)
        }
      ]);
      setIsAiThinking(false);
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs animate-in fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-5xl w-full max-h-[85vh] flex flex-col shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
        
        {/* Top Header (Image 2 style with Word & Afforai icons) */}
        <div className="p-4 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-700/80 border border-white/20 flex items-center justify-center font-bold text-sm shadow-sm">
              W
            </div>
            <div className="w-8 h-8 rounded-full bg-purple-500/80 border border-white/20 flex items-center justify-center text-xs shadow-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold tracking-tight">Afforai Cite Extension</h3>
              <p className="text-[11px] text-blue-100 font-mono">Reference Manager & AI Research Assistant</p>
            </div>
          </div>

          {/* Top Mode Tabs (Image 2: Research, Cite, Write) */}
          <div className="flex items-center gap-1 bg-black/20 p-1 rounded-xl text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('research')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeTab === 'research' ? 'bg-white text-indigo-700 shadow-xs' : 'text-white/80 hover:text-white'
              }`}
            >
              Research
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('cite')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeTab === 'cite' ? 'bg-white text-indigo-700 shadow-xs' : 'text-white/80 hover:text-white'
              }`}
            >
              Cite
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('write')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                activeTab === 'write' ? 'bg-white text-indigo-700 shadow-xs' : 'text-white/80 hover:text-white'
              }`}
            >
              Write
            </button>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 2-Column Split: Left Reference Manager | Right AI Research Assistant */}
        <div className="grid grid-cols-1 md:grid-cols-12 flex-1 overflow-hidden">
          
          {/* Left Panel: Reference Manager (6 cols) */}
          <div className="md:col-span-6 border-r border-slate-200 dark:border-slate-800 p-5 flex flex-col space-y-4 bg-slate-50/50 dark:bg-slate-900/50">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Reference Manager
              </h4>
              <span className="text-[11px] text-slate-400 font-mono">
                {referenceList.length} references
              </span>
            </div>

            {/* Search Bar */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search your references..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>

            {/* Reference List with Checkboxes and "+ Insert citation" */}
            <div className="flex-1 overflow-y-auto space-y-2.5 max-h-[380px] pr-1">
              {filteredReferences.map(ref => {
                const isSelected = selectedReferenceIds.has(ref.id);
                return (
                  <div
                    key={ref.id}
                    onClick={() => toggleSelectReference(ref.id)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-blue-50/80 dark:bg-blue-950/40 border-blue-500 shadow-xs'
                        : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}} // handled by div
                        className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="flex-1 space-y-1">
                        <span className="font-semibold text-slate-900 dark:text-slate-100 block leading-snug">
                          {ref.title}
                        </span>
                        <div className="text-[11px] text-slate-500 font-mono">
                          {ref.author || 'Author unspecified'}{ref.published_at ? ` (${ref.published_at})` : ''}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          const citationTag = `[${ref.author || ref.title} ${ref.published_at || ''}]`.trim();
                          onInsertCitation(citationTag);
                          success(`Inserted citation: ${citationTag}`);
                        }}
                        className="px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-950 hover:bg-blue-100 text-blue-700 dark:text-blue-300 font-semibold text-[10px] shrink-0 transition-colors flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" />
                        <span>Insert citation</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Multi-Select Summary Bar (Image 2) */}
            <div className="p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {selectedReferences.length} Citations Selected
                </span>
                {selectedReferences.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setSelectedReferenceIds(new Set())}
                    className="text-[10px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  >
                    Clear all
                  </button>
                )}
              </div>

              {/* Removable Citation Pills (Image 2) */}
              <div className="flex flex-wrap gap-1.5 min-h-[28px]">
                {selectedReferences.length === 0 ? (
                  <span className="text-[11px] text-slate-400 italic">Select references to insert batch citations</span>
                ) : (
                  selectedReferences.map(ref => (
                    <span
                      key={ref.id}
                      className="px-2.5 py-1 rounded-lg bg-blue-600 text-white text-[11px] font-semibold flex items-center gap-1.5 shadow-xs"
                    >
                      <span>{ref.author || ref.title.slice(0, 15)} ({ref.published_at || 'n.d.'})</span>
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); toggleSelectReference(ref.id); }}
                        className="hover:text-blue-200"
                      >
                        ×
                      </button>
                    </span>
                  ))
                )}
              </div>

              <Button
                size="sm"
                variant="primary"
                disabled={selectedReferences.length === 0}
                onClick={handleInsertSelected}
                className="w-full text-xs bg-blue-600 hover:bg-blue-700 text-white"
                leftIcon={<BookmarkCheck className="w-3.5 h-3.5" />}
              >
                Insert Selected Citations
              </Button>
            </div>
          </div>

          {/* Right Panel: AI Research Assistant (Image 2 Right Panel) (6 cols) */}
          <div className="md:col-span-6 p-5 flex flex-col space-y-4 bg-white dark:bg-slate-900">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
                  AI Research Assistant
                </h4>
              </div>
              <span className="text-[10px] bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-semibold">
                Afforai Engine
              </span>
            </div>

            {/* Chat Thread */}
            <div className="flex-1 overflow-y-auto space-y-3.5 max-h-[380px] pr-1">
              {chatMessages.map(msg => (
                <div key={msg.id} className="space-y-1.5">
                  {msg.role === 'user' ? (
                    <div className="flex items-start gap-2.5">
                      <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-[10px] flex items-center justify-center shrink-0">
                        AW
                      </div>
                      <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
                        {msg.text}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start gap-2.5">
                      <div className="w-6 h-6 rounded-full bg-purple-600 text-white font-bold text-[10px] flex items-center justify-center shrink-0 shadow-xs">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="p-3.5 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800/80 text-xs text-slate-900 dark:text-slate-100 leading-relaxed font-sans space-y-2 flex-1">
                        <p>{msg.text}</p>
                        
                        {/* Action buttons (Copy, Replace proposal) */}
                        <div className="flex items-center justify-between pt-1 border-t border-purple-100 dark:border-purple-900/60 text-[11px]">
                          <div className="flex items-center gap-1.5 text-slate-400">
                            <button
                              type="button"
                              onClick={() => {
                                navigator.clipboard.writeText(msg.text);
                                success('Copied AI proposal to clipboard');
                              }}
                              className="p-1 hover:text-purple-600 transition-colors"
                              title="Copy text"
                            >
                              <Copy className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                info('Regenerating response with alternative phrasing...');
                                handleSendChat();
                              }}
                              className="p-1 hover:text-purple-600 transition-colors"
                              title="Regenerate"
                            >
                              <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          {onReplaceTextWithProposal && (
                            <button
                              type="button"
                              onClick={() => {
                                onReplaceTextWithProposal(msg.text);
                                success('Applied AI rephrase to draft editor!');
                                onClose();
                              }}
                              className="font-semibold text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1"
                            >
                              <Check className="w-3 h-3" />
                              <span>Use this in draft</span>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {isAiThinking && (
                <div className="flex items-center gap-2 p-3 text-xs text-purple-600">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Synthesizing research-backed rewrite...</span>
                </div>
              )}
            </div>

            {/* Chat Input with @ citation picker & Send */}
            <div className="p-2 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center gap-2">
              <input
                type="text"
                placeholder="Type to start researching or ask to rephrase..."
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSendChat(); }}
                className="flex-1 bg-transparent border-none text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-0"
              />
              <button
                type="button"
                onClick={() => {
                  setChatPrompt(prev => `${prev} @reference `);
                  info('Reference picker activated: Type author or keyword');
                }}
                className="p-1 text-slate-400 hover:text-blue-600 transition-colors"
                title="Tag reference"
              >
                <AtSign className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={handleSendChat}
                disabled={!chatPrompt.trim()}
                className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs disabled:opacity-40 transition-colors flex items-center gap-1"
              >
                <span>Send</span>
                <Send className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

