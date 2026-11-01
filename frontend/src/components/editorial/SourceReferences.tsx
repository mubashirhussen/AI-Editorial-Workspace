import React from 'react';
import { ExternalLink, BookOpen, ShieldCheck } from 'lucide-react';
import { SourceReference } from '../../types';

interface SourceReferencesProps {
  sources: SourceReference[];
  angleHeadline?: string;
}

export const SourceReferences: React.FC<SourceReferencesProps> = ({ sources, angleHeadline }) => {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
          <BookOpen className="w-3.5 h-3.5 text-blue-600" />
          <span>Source Material</span>
        </h3>
        <span className="text-[10px] font-mono bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full font-bold">
          {sources.length} Verified
        </span>
      </div>

      {angleHeadline && (
        <div className="p-3 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-800/60 text-xs space-y-1">
          <span className="text-[10px] font-mono uppercase text-blue-700 dark:text-blue-300 font-bold block">
            Selected Story Angle
          </span>
          <p className="text-slate-800 dark:text-slate-200 font-medium leading-relaxed font-serif">
            {angleHeadline}
          </p>
        </div>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium">
          <span>Numbered Inline Citations</span>
          <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="w-3 h-3" /> Fact-Checked
          </span>
        </div>

        <div className="space-y-1.5 max-h-[350px] overflow-y-auto pr-1">
          {sources.map((s, idx) => {
            const num = s.index ?? idx + 1;
            return (
              <div key={s.source_id || idx} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-700 text-[11px] space-y-1">
                <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-start gap-1.5">
                  <span className="w-4 h-4 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-mono text-[10px] flex items-center justify-center font-bold shrink-0 mt-0.5">
                    [{num}]
                  </span>
                  <span className="line-clamp-2 leading-tight">{s.title}</span>
                </div>
                {s.supported_claim && (
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 italic line-clamp-2">
                    "{s.supported_claim}"
                  </p>
                )}
                {s.url && (
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 mt-0.5 truncate"
                  >
                    <span className="truncate">{s.url}</span>
                    <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                  </a>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
