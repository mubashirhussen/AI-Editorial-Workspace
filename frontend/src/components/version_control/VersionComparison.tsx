import React, { useState } from 'react';
import { GitCompare, ArrowRight, PlusCircle, MinusCircle, FileText, SplitSquareVertical } from 'lucide-react';
import { VersionComparisonResponse } from '../../types/version';
import { Badge } from '../common/Badge';

interface VersionComparisonProps {
  comparison: VersionComparisonResponse;
}

export const VersionComparison: React.FC<VersionComparisonProps> = ({ comparison }) => {
  const [viewMode, setViewMode] = useState<'inline' | 'unified'>('inline');

  const {
    version_a,
    version_b,
    word_count_a,
    word_count_b,
    word_count_diff,
    additions_count,
    deletions_count,
    word_diff_chunks,
    diff_chunks
  } = comparison;

  return (
    <div className="space-y-4">
      {/* Comparison Header */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
            <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-xs font-mono">
              v{version_a.version_number}
            </span>
            <ArrowRight className="w-4 h-4 text-slate-400" />
            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-mono">
              v{version_b.version_number}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('inline')}
              className={`px-2.5 py-1 text-xs rounded font-medium transition ${
                viewMode === 'inline'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              Inline Highlights
            </button>
            <button
              onClick={() => setViewMode('unified')}
              className={`px-2.5 py-1 text-xs rounded font-medium transition ${
                viewMode === 'unified'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              Unified Diff
            </button>
          </div>
        </div>

        {/* Diff Metric Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 font-medium">
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>Words:</span>
            <span className="text-slate-600 font-mono">{word_count_a}</span>
            <ArrowRight className="w-3 h-3 text-slate-400" />
            <span className="text-slate-800 font-mono font-semibold">{word_count_b}</span>
            <span
              className={`px-1.5 py-0.2 rounded text-[11px] font-mono ${
                word_count_diff > 0
                  ? 'bg-emerald-100 text-emerald-800 font-bold'
                  : word_count_diff < 0
                  ? 'bg-rose-100 text-rose-800 font-bold'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {word_count_diff > 0 ? `+${word_count_diff}` : word_count_diff}
            </span>
          </div>

          <div className="flex items-center gap-1 text-emerald-700 font-medium">
            <PlusCircle className="w-3.5 h-3.5 text-emerald-500" />
            <span>{additions_count} additions</span>
          </div>

          <div className="flex items-center gap-1 text-rose-700 font-medium">
            <MinusCircle className="w-3.5 h-3.5 text-rose-500" />
            <span>{deletions_count} deletions</span>
          </div>
        </div>
      </div>

      {/* Visual Diff Body */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 max-h-[420px] overflow-y-auto">
        {viewMode === 'inline' ? (
          <div className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap font-sans">
            {word_diff_chunks.map((chunk, idx) => {
              if (chunk.type === 'insert') {
                return (
                  <mark
                    key={idx}
                    className="bg-emerald-100 text-emerald-900 border-b-2 border-emerald-500 px-0.5 rounded font-medium no-underline"
                  >
                    {chunk.text}
                  </mark>
                );
              }
              if (chunk.type === 'delete') {
                return (
                  <del
                    key={idx}
                    className="bg-rose-100 text-rose-800 line-through px-0.5 rounded opacity-80"
                  >
                    {chunk.text}
                  </del>
                );
              }
              return <span key={idx}>{chunk.text}</span>;
            })}
          </div>
        ) : (
          <div className="font-mono text-xs space-y-1">
            {diff_chunks.map((chunk, idx) => {
              if (chunk.type === 'addition') {
                return (
                  <div
                    key={idx}
                    className="bg-emerald-50 text-emerald-900 border-l-4 border-emerald-500 px-2 py-0.5 rounded-r"
                  >
                    <span className="font-bold text-emerald-600 mr-2 select-none">+</span>
                    {chunk.text}
                  </div>
                );
              }
              if (chunk.type === 'deletion') {
                return (
                  <div
                    key={idx}
                    className="bg-rose-50 text-rose-900 border-l-4 border-rose-500 px-2 py-0.5 rounded-r"
                  >
                    <span className="font-bold text-rose-600 mr-2 select-none">-</span>
                    {chunk.text}
                  </div>
                );
              }
              return (
                <div key={idx} className="text-slate-700 px-2 py-0.5">
                  <span className="text-slate-300 mr-2 select-none"> </span>
                  {chunk.text}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
