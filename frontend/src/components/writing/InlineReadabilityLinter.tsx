import React, { useState } from 'react';
import { Sparkles, Wand2, Check, AlertCircle, ArrowRight, X } from 'lucide-react';
import { WritingIssue } from '../../types/writing';
import { Button } from '../common/Button';

interface InlineReadabilityLinterProps {
  content: string;
  issues: WritingIssue[];
  onSimplifySentence: (originalText: string, suggestedRewrite: string) => void;
  onSelectIssue?: (issue: WritingIssue) => void;
}

export const InlineReadabilityLinter: React.FC<InlineReadabilityLinterProps> = ({
  content,
  issues,
  onSimplifySentence,
  onSelectIssue
}) => {
  const [activeTooltipIssue, setActiveTooltipIssue] = useState<WritingIssue | null>(null);

  // Parse text into sentences and match against issues
  const paragraphs = content.split('\n\n');

  return (
    <div className="font-serif text-[15px] leading-relaxed p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs relative">
      {paragraphs.map((p, pIdx) => {
        // Find if any issue matches within this paragraph
        let remainingText = p;
        const elements: React.ReactNode[] = [];

        // Simple sentence match
        issues.forEach((issue, issueIdx) => {
          const matchIdx = remainingText.indexOf(issue.original_text);
          if (matchIdx !== -1) {
            const before = remainingText.slice(0, matchIdx);
            const matched = issue.original_text;
            remainingText = remainingText.slice(matchIdx + matched.length);

            if (before) elements.push(<span key={`before-${pIdx}-${issueIdx}`}>{before}</span>);

            const isHardToRead = issue.category === 'long_sentence' || issue.category === 'complexity';
            const isPassive = issue.category === 'passive_voice';

            elements.push(
              <span
                key={`matched-${pIdx}-${issueIdx}`}
                onClick={() => setActiveTooltipIssue(issue)}
                className={`cursor-pointer px-1 py-0.5 rounded transition-colors relative inline-block group ${
                  isHardToRead
                    ? 'bg-purple-100/80 dark:bg-purple-950/60 text-purple-900 dark:text-purple-200 border-b-2 border-purple-400'
                    : isPassive
                    ? 'bg-blue-100/80 dark:bg-blue-950/60 text-blue-900 dark:text-blue-200 border-b-2 border-blue-400'
                    : 'bg-amber-100/80 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border-b-2 border-amber-400'
                }`}
              >
                <span>{matched}</span>
                <span className="ml-1 inline-flex items-center text-[10px] text-purple-600 bg-purple-200/60 px-1 rounded font-sans font-bold">
                  ✎
                </span>
              </span>
            );
          }
        });

        if (remainingText) {
          elements.push(<span key={`rem-${pIdx}`}>{remainingText}</span>);
        }

        return (
          <p key={pIdx} className="mb-4 text-slate-800 dark:text-slate-100">
            {elements.length > 0 ? elements : p}
          </p>
        );
      })}

      {/* Interactive Tooltip Popover (Image 5 style: ● Readability: Hard-to-read sentence. [Simplify]) */}
      {activeTooltipIssue && (
        <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 p-4 bg-slate-900 text-white rounded-2xl shadow-2xl border border-slate-700 max-w-lg w-full flex items-center justify-between gap-4 animate-in fade-in slide-in-from-bottom-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-rose-400">
              <span>●</span>
              <span>
                {activeTooltipIssue.category === 'long_sentence' || activeTooltipIssue.category === 'complexity'
                  ? 'Readability: Hard-to-read sentence. Consider rewriting it.'
                  : activeTooltipIssue.category === 'passive_voice'
                  ? 'Clarity: Passive voice detected. Consider active voice.'
                  : 'Word choice: Consider simpler phrasing.'}
              </span>
            </div>
            {activeTooltipIssue.suggested_rewrite && (
              <p className="text-xs text-slate-300 font-sans italic line-clamp-2">
                Suggestion: "{activeTooltipIssue.suggested_rewrite}"
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                onSimplifySentence(
                  activeTooltipIssue.original_text,
                  activeTooltipIssue.suggested_rewrite || activeTooltipIssue.original_text
                );
                setActiveTooltipIssue(null);
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold"
              leftIcon={<Sparkles className="w-3.5 h-3.5" />}
            >
              Simplify
            </Button>
            <button
              type="button"
              onClick={() => setActiveTooltipIssue(null)}
              className="text-slate-400 hover:text-white p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
