import React from 'react';
import { Sparkles, Sliders, Target, BookOpen, Layers } from 'lucide-react';
import { Button } from '../common/Button';

export interface EditorialGeneratorProps {
  audience: string;
  setAudience: (val: string) => void;
  tone: string;
  setTone: (val: string) => void;
  minWords: number;
  setMinWords: (val: number) => void;
  maxWords: number;
  setMaxWords: (val: number) => void;
  onGenerate: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
}

export const EditorialGenerator: React.FC<EditorialGeneratorProps> = ({
  audience,
  setAudience,
  tone,
  setTone,
  minWords,
  setMinWords,
  maxWords,
  setMaxWords,
  onGenerate,
  isGenerating = false,
  disabled = false,
}) => {
  const audienceOptions = [
    'founders, builders, and operators',
    'CTOs and senior software architects',
    'AI researchers and machine learning engineers',
    'venture investors and corporate strategists',
  ];

  const toneOptions = [
    'Newsletter-style',
    'Analytical',
    'Professional',
    'Technical',
    'Conversational',
  ];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-blue-600" />
          <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Editorial Parameters
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Target: {minWords}–{maxWords} words
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        {/* Target Audience */}
        <div className="space-y-1.5">
          <label className="block font-semibold text-slate-700 dark:text-slate-300">
            Target Audience
          </label>
          <select
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            {audienceOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>

        {/* Tone Selection */}
        <div className="space-y-1.5">
          <label className="block font-semibold text-slate-700 dark:text-slate-300">
            Editorial Tone
          </label>
          <select
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          >
            {toneOptions.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Word Count Range Controls */}
      <div className="pt-1 flex items-center justify-between text-xs bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-200/60 dark:border-slate-700/60">
        <span className="text-slate-600 dark:text-slate-400 font-medium">Article Length Bounds:</span>
        <div className="flex items-center gap-2 font-mono">
          <span className="font-semibold text-slate-800 dark:text-slate-200">{minWords} words (min)</span>
          <span className="text-slate-400">&bull;</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">{maxWords} words (max)</span>
        </div>
      </div>

      <div className="pt-2">
        <Button
          onClick={onGenerate}
          isLoading={isGenerating}
          disabled={disabled || isGenerating}
          variant="primary"
          size="md"
          className="w-full shadow-sm shadow-blue-500/20"
          leftIcon={<Sparkles className="w-4 h-4" />}
        >
          {isGenerating ? 'Composing Editorial Draft...' : 'Generate 300–500 Word Article'}
        </Button>
      </div>
    </div>
  );
};

