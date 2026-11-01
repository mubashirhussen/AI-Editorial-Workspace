import React from 'react';
import { Save, RefreshCw, PenTool, Sparkles, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { Button } from '../common/Button';
import { WordCountIndicator } from './WordCountIndicator';

export interface EditorialEditorProps {
  headline: string;
  setHeadline: (h: string) => void;
  content: string;
  setContent: (c: string) => void;
  wordCount: number;
  onSave: () => void;
  onRegenerate: () => void;
  onAnalyzeWriting: () => void;
  isSaving?: boolean;
  isGenerating?: boolean;
  isDirty?: boolean;
}

export const EditorialEditor: React.FC<EditorialEditorProps> = ({
  headline,
  setHeadline,
  content,
  setContent,
  wordCount,
  onSave,
  onRegenerate,
  onAnalyzeWriting,
  isSaving = false,
  isGenerating = false,
  isDirty = false,
}) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-xs space-y-5">
      {/* Top Header & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Article Copy Editor
          </h3>
          {isDirty && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              Unsaved Edits
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={onAnalyzeWriting}
            variant="outline"
            size="sm"
            leftIcon={<PenTool className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />}
          >
            Analyze with Writing Assistant
          </Button>

          <Button
            onClick={onRegenerate}
            isLoading={isGenerating}
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Regenerate
          </Button>

          <Button
            onClick={onSave}
            isLoading={isSaving}
            variant="primary"
            size="sm"
            leftIcon={<Save className="w-3.5 h-3.5" />}
          >
            Save Article
          </Button>
        </div>
      </div>

      {/* Headline Input */}
      <div className="space-y-1">
        <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider">
          Article Headline
        </label>
        <input
          type="text"
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          placeholder="Enter publication headline..."
          className="w-full text-base font-bold text-slate-900 dark:text-white bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
        />
      </div>

      {/* Content Textarea */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Article Body (Markdown & Citations)
          </label>
          <span className="text-[11px] text-slate-400 font-mono">
            {wordCount} words
          </span>
        </div>
        <textarea
          rows={16}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Article copy will appear here after generation..."
          className="w-full font-serif text-[14px] leading-relaxed p-4 bg-slate-50/50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-100 focus:bg-white dark:focus:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all resize-y"
        />
      </div>

      {/* Word Count Indicator Component */}
      <div className="pt-2">
        <WordCountIndicator wordCount={wordCount} minTarget={300} maxTarget={500} />
      </div>
    </div>
  );
};
