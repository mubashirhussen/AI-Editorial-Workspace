import React, { useState } from 'react';
import { Sparkles, Check, RefreshCw, Edit2, Lightbulb } from 'lucide-react';
import { HeadlineOption } from '../../types';
import { Button } from '../common/Button';

export interface HeadlineSelectorProps {
  headlines: HeadlineOption[];
  selectedHeadline: string;
  onSelectHeadline: (headline: string) => void;
  onRegenerate: () => void;
  isLoading?: boolean;
}

export const HeadlineSelector: React.FC<HeadlineSelectorProps> = ({
  headlines,
  selectedHeadline,
  onSelectHeadline,
  onRegenerate,
  isLoading = false,
}) => {
  const [isCustom, setIsCustom] = useState(false);
  const [customText, setCustomText] = useState('');

  const handleApplyCustom = () => {
    if (customText.trim()) {
      onSelectHeadline(customText.trim());
      setIsCustom(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Select Newsletter Headline ({headlines.length} Options)
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setIsCustom(!isCustom)}
            variant="ghost"
            size="sm"
            leftIcon={<Edit2 className="w-3.5 h-3.5" />}
          >
            {isCustom ? 'Show Presets' : 'Custom Headline'}
          </Button>
          <Button
            onClick={onRegenerate}
            variant="outline"
            size="sm"
            isLoading={isLoading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Regenerate
          </Button>
        </div>
      </div>

      {isCustom ? (
        <div className="space-y-3 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
            Custom Headline
          </label>
          <input
            type="text"
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="Type your compelling, non-clickbait editorial headline..."
            className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            autoFocus
          />
          <div className="flex justify-end gap-2">
            <Button onClick={() => setIsCustom(false)} variant="ghost" size="sm">
              Cancel
            </Button>
            <Button onClick={handleApplyCustom} variant="primary" size="sm" disabled={!customText.trim()}>
              Apply Custom
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-2.5">
          {headlines.map((item, idx) => {
            const isSelected = item.headline === selectedHeadline;
            return (
              <div
                key={idx}
                onClick={() => onSelectHeadline(item.headline)}
                className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50/40 dark:bg-blue-950/20 ring-1 ring-blue-500/30'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="font-bold text-slate-900 dark:text-white text-xs flex items-center gap-2">
                      <span>{item.headline}</span>
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-slate-200/60 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                        {item.editorial_angle}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal">
                      {item.explanation}
                    </p>
                  </div>
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                    isSelected ? 'bg-blue-600 text-white' : 'border border-slate-300 dark:border-slate-600'
                  }`}>
                    {isSelected && <Check className="w-3 h-3" />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

