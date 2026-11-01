import React from 'react';
import { Clock, User as UserIcon, FileText, Tag, Sparkles, Edit, RotateCcw, CheckCircle2 } from 'lucide-react';
import { EditorialVersion, ChangeType } from '../../types/version';
import { Badge } from '../common/Badge';

interface VersionMetadataProps {
  version: EditorialVersion;
  isLatest?: boolean;
}

export const getChangeTypeBadge = (changeType: ChangeType) => {
  switch (changeType) {
    case 'INITIAL':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3 h-3" /> Initial Creation</Badge>;
    case 'AI_REVISION':
      return <Badge variant="primary" className="gap-1 bg-purple-100 text-purple-800 border-purple-200"><Sparkles className="w-3 h-3 text-purple-600" /> AI Revision</Badge>;
    case 'MANUAL_EDIT':
      return <Badge variant="primary" className="gap-1 bg-sky-100 text-sky-800 border-sky-200"><Edit className="w-3 h-3 text-sky-600" /> Manual Edit</Badge>;
    case 'SUGGESTION_ACCEPTED':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3 h-3" /> Suggestion Applied</Badge>;
    case 'RESTORE':
      return <Badge variant="warning" className="gap-1 bg-amber-100 text-amber-800 border-amber-200"><RotateCcw className="w-3 h-3 text-amber-600" /> Restored Version</Badge>;
    default:
      return <Badge variant="neutral">{changeType}</Badge>;
  }
};

export const VersionMetadata: React.FC<VersionMetadataProps> = ({ version, isLatest }) => {
  const formattedDate = new Date(version.created_at).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800 text-sm">Version {version.version_number}</span>
          {isLatest && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
              Active Head
            </span>
          )}
        </div>
        <div>{getChangeTypeBadge(version.change_type)}</div>
      </div>

      <p className="text-slate-600 italic">"{version.change_summary || 'No summary recorded'}"</p>

      <div className="flex flex-wrap items-center gap-4 text-slate-500 pt-1 border-t border-slate-200">
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-slate-400" />
          {formattedDate}
        </span>
        <span className="flex items-center gap-1">
          <UserIcon className="w-3 h-3 text-slate-400" />
          {version.author_name || 'System'}
        </span>
        <span className="flex items-center gap-1">
          <FileText className="w-3 h-3 text-slate-400" />
          {version.word_count} words ({version.char_count} chars)
        </span>
      </div>
    </div>
  );
};
