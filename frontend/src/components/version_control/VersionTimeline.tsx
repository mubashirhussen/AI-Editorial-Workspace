import React from 'react';
import { 
  GitCommit, 
  RotateCcw, 
  Eye, 
  GitCompare, 
  Clock, 
  User as UserIcon, 
  FileText 
} from 'lucide-react';
import { EditorialVersion } from '../../types/version';
import { getChangeTypeBadge } from './VersionMetadata';
import { Button } from '../common/Button';

interface VersionTimelineProps {
  versions: EditorialVersion[];
  onSelectVersion: (version: EditorialVersion) => void;
  onCompareWithHead: (version: EditorialVersion) => void;
  onOpenRestore: (version: EditorialVersion) => void;
  selectedVersionId?: string;
}

export const VersionTimeline: React.FC<VersionTimelineProps> = ({
  versions,
  onSelectVersion,
  onCompareWithHead,
  onOpenRestore,
  selectedVersionId
}) => {
  if (versions.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        No version snapshots recorded yet.
      </div>
    );
  }

  const latestVersion = versions[0];

  return (
    <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
      {versions.map((version, index) => {
        const isLatest = index === 0;
        const isSelected = selectedVersionId === version.id;
        const formattedDate = new Date(version.created_at).toLocaleString(undefined, {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });

        return (
          <div key={version.id} className="relative group">
            {/* Timeline Node Dot */}
            <span
              className={`absolute -left-6 top-2 w-3.5 h-3.5 rounded-full border-2 transition ${
                isLatest
                  ? 'bg-emerald-500 border-white ring-2 ring-emerald-300'
                  : isSelected
                  ? 'bg-blue-500 border-white ring-2 ring-blue-300'
                  : 'bg-slate-300 border-white group-hover:bg-slate-400'
              }`}
            />

            {/* Version Card */}
            <div
              className={`border rounded-lg p-3 transition shadow-xs ${
                isSelected
                  ? 'bg-blue-50/50 border-blue-300 ring-1 ring-blue-200'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-1 mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-slate-900">
                    Version {version.version_number}
                  </span>
                  {isLatest && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold tracking-wider uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                      Head
                    </span>
                  )}
                </div>
                <div>{getChangeTypeBadge(version.change_type)}</div>
              </div>

              <p className="text-xs text-slate-700 font-medium mb-2">
                {version.change_summary || 'Content snapshot'}
              </p>

              <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 mb-2.5">
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
                  {version.word_count} words
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-1.5 pt-2 border-t border-slate-100">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onSelectVersion(version)}
                  className="text-xs h-7 px-2 gap-1 text-slate-600 hover:text-slate-900"
                >
                  <Eye className="w-3 h-3" />
                  Preview
                </Button>

                {!isLatest && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onCompareWithHead(version)}
                      className="text-xs h-7 px-2 gap-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                    >
                      <GitCompare className="w-3 h-3" />
                      Diff Head
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onOpenRestore(version)}
                      className="text-xs h-7 px-2 gap-1 text-amber-600 hover:text-amber-700 hover:bg-amber-50 border-amber-200"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Restore
                    </Button>
                  </>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
