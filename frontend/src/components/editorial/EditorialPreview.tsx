import React from 'react';
import { Newspaper, ExternalLink, BookOpen, Clock, FileCheck } from 'lucide-react';
import { SourceReference } from '../../types';

export interface EditorialPreviewProps {
  headline: string;
  content: string;
  wordCount: number;
  sourceReferences?: SourceReference[];
}

export const EditorialPreview: React.FC<EditorialPreviewProps> = ({
  headline,
  content,
  wordCount,
  sourceReferences = [],
}) => {
  const paragraphs = content.trim().split('\n\n').filter((p) => p.trim());

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-8 shadow-xs space-y-6 max-w-3xl mx-auto">
      {/* Newsletter Header Banner */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5 space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
          <span className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-semibold">
            <Newspaper className="w-4 h-4" />
            This Week in AI • Editorial Edition
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {Math.round(wordCount / 225) || 1} min read &bull; {wordCount} words
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight pt-1">
          {headline || 'Untitled Newsletter Article'}
        </h1>
      </div>

      {/* Article Body */}
      <article className="prose prose-slate dark:prose-invert max-w-none space-y-4 font-serif text-[15px] leading-relaxed text-slate-800 dark:text-slate-200">
        {paragraphs.map((para, i) => {
          if (para.startsWith('### ')) {
            return (
              <h3 key={i} className="text-base font-sans font-bold text-slate-900 dark:text-white pt-3 border-t border-slate-100 dark:border-slate-800">
                {para.replace('### ', '')}
              </h3>
            );
          }
          if (para.startsWith('## ')) {
            return (
              <h2 key={i} className="text-lg font-sans font-bold text-slate-900 dark:text-white pt-4">
                {para.replace('## ', '')}
              </h2>
            );
          }

          // Format bullet points if present
          if (para.includes('\n• ') || para.startsWith('• ')) {
            const bullets = para.split('\n').filter((b) => b.trim());
            return (
              <ul key={i} className="space-y-1.5 list-none pl-0 font-sans text-xs">
                {bullets.map((b, bIdx) => (
                  <li key={bIdx} className="p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700">
                    {b}
                  </li>
                ))}
              </ul>
            );
          }

          return (
            <p key={i} className="leading-relaxed">
              {para}
            </p>
          );
        })}
      </article>

      {/* Verified Sources & References Section */}
      {sourceReferences.length > 0 && (
        <div className="pt-6 border-t border-slate-200 dark:border-slate-800 space-y-3">
          <h4 className="text-xs font-sans font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            Verified Source References
          </h4>
          <ol className="divide-y divide-slate-100 dark:divide-slate-800 text-xs">
            {sourceReferences.map((ref, idx) => (
              <li key={idx} className="py-2.5 flex items-start justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="font-semibold text-slate-800 dark:text-slate-200">
                    [{ref.index || idx + 1}] {ref.title}
                  </div>
                  {ref.supported_claim && (
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 italic">
                      "{ref.supported_claim}"
                    </p>
                  )}
                </div>
                {ref.url && (
                  <a
                    href={ref.url}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0 flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <span>View link</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};

