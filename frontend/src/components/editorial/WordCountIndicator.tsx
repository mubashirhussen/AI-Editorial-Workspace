import React from 'react';

interface WordCountIndicatorProps {
  wordCount: number;
  minTarget?: number;
  maxTarget?: number;
}

export const WordCountIndicator: React.FC<WordCountIndicatorProps> = ({
  wordCount,
  minTarget = 300,
  maxTarget = 500,
}) => {
  const isOptimal = wordCount >= minTarget && wordCount <= maxTarget;
  const isUnder = wordCount < minTarget;
  const isOver = wordCount > maxTarget;

  return (
    <div className="flex items-center justify-between text-xs py-2 border-b border-slate-100 text-slate-500">
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px]">
          Word Count: <strong className={isOptimal ? 'text-emerald-600' : isUnder ? 'text-amber-600' : 'text-blue-600'}>
            {wordCount}
          </strong> / {minTarget}–{maxTarget} Words
        </span>
        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
          isOptimal ? 'bg-emerald-50 text-emerald-700' :
          isUnder ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'
        }`}>
          {isOptimal ? 'Target Met' : isUnder ? `${minTarget - wordCount} Words Below Target` : `${wordCount - maxTarget} Words Extended`}
        </span>
      </div>
      <span className="text-[11px] text-slate-400 font-serif italic hidden sm:inline">
        This Week in AI • Publication Ready
      </span>
    </div>
  );
};

