import React from 'react';

interface ArticlePreviewProps {
  headline: string;
  content: string;
  wordCount: number;
  sources: Array<{ index?: number; title: string; url?: string }>;
}

export const ArticlePreview: React.FC<ArticlePreviewProps> = ({ headline, content, wordCount, sources }) => {
  const paragraphs = content.split('\n\n').filter((p) => p.trim());

  return (
    <article className="max-w-2xl mx-auto bg-white p-8 rounded-2xl border border-slate-200/80 shadow-xs space-y-6 animate-in fade-in duration-150">
      {/* Header Meta */}
      <div className="space-y-3 border-b border-slate-100 pb-5">
        <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-blue-600 font-bold">
          <span>Newsletter Edition</span>
          <span>•</span>
          <span>This Week in AI</span>
          <span>•</span>
          <span>{wordCount} Words</span>
        </div>
        <h1 className="text-2xl font-serif font-bold text-slate-900 leading-tight">
          {headline || 'Untitled Newsletter Edition'}
        </h1>
        <p className="text-xs text-slate-400 italic">
          Published for Founders, Builders, and AI Operators
        </p>
      </div>

      {/* Body Paragraphs */}
      <div className="space-y-4 font-serif text-[15px] leading-relaxed text-slate-800">
        {paragraphs.map((p, idx) => (
          <p key={idx} className="first-of-type:font-normal first-of-type:text-base">
            {p}
          </p>
        ))}
      </div>

      {/* References Footer */}
      {sources.length > 0 && (
        <div className="mt-8 pt-6 border-t border-slate-200/80 space-y-3 font-sans">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
            Verified References & Source Material
          </h4>
          <ol className="space-y-1.5 text-xs text-slate-600">
            {sources.map((s, idx) => {
              const num = s.index ?? idx + 1;
              return (
                <li key={idx} className="flex items-baseline gap-2">
                  <span className="font-mono text-blue-600 font-bold">[{num}]</span>
                  <span>{s.title}</span>
                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-500 hover:underline text-[11px] truncate max-w-xs"
                    >
                      ({s.url})
                    </a>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </article>
  );
};

