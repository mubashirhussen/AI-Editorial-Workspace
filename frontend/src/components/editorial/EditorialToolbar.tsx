import React from 'react';
import { Eye, Edit3, Download, Save, RefreshCw, PenTool, CheckCircle2 } from 'lucide-react';
import { Button } from '../common/Button';

export interface EditorialToolbarProps {
  viewMode: 'edit' | 'preview' | 'review';
  setViewMode: (mode: 'edit' | 'preview' | 'review') => void;
  onSave: () => void;
  onExport: () => void;
  onAnalyzeWriting: () => void;
  isSaving?: boolean;
  hasContent?: boolean;
}

export const EditorialToolbar: React.FC<EditorialToolbarProps> = ({
  viewMode,
  setViewMode,
  onSave,
  onExport,
  onAnalyzeWriting,
  isSaving = false,
  hasContent = false,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
      {/* Mode Switcher */}
      <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl gap-1">
        <button
          onClick={() => setViewMode('edit')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === 'edit'
              ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
              : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Editor</span>
        </button>
        <button
          onClick={() => setViewMode('preview')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === 'preview'
              ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
              : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Newsletter Preview</span>
        </button>
        <button
          onClick={() => setViewMode('review')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            viewMode === 'review'
              ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-2xs'
              : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Review & Workflow</span>
        </button>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        <Button
          onClick={onAnalyzeWriting}
          disabled={!hasContent}
          variant="outline"
          size="sm"
          leftIcon={<PenTool className="w-3.5 h-3.5 text-blue-600" />}
        >
          Writing Assistant
        </Button>

        <Button
          onClick={onExport}
          disabled={!hasContent}
          variant="outline"
          size="sm"
          leftIcon={<Download className="w-3.5 h-3.5" />}
        >
          Export
        </Button>

        <Button
          onClick={onSave}
          disabled={!hasContent}
          isLoading={isSaving}
          variant="primary"
          size="sm"
          leftIcon={<Save className="w-3.5 h-3.5" />}
        >
          Save
        </Button>
      </div>
    </div>
  );
};

