import React from 'react';

interface HeadlineEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const HeadlineEditor: React.FC<HeadlineEditorProps> = ({ value, onChange, disabled }) => {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
          Newsletter Headline
        </label>
        <span className="text-[10px] text-slate-400 font-mono">
          {value.length} chars
        </span>
      </div>
      <input
        type="text"
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter high-impact newsletter headline..."
        className="w-full text-lg font-serif font-bold text-slate-900 border-b border-slate-200 pb-2 focus:border-blue-600 outline-none transition-colors disabled:opacity-60"
      />
    </div>
  );
};

