import React, { useState, useEffect } from 'react';
import { 
  History, 
  RotateCcw, 
  GitCompare, 
  Eye, 
  X, 
  Loader2, 
  Clock, 
  Layers,
  RefreshCw
} from 'lucide-react';
import { 
  DocumentType, 
  EditorialVersion, 
  VersionComparisonResponse 
} from '../../types/version';
import { versionService } from '../../services/versionService';
import { VersionTimeline } from './VersionTimeline';
import { VersionComparison } from './VersionComparison';
import { RestoreVersionDialog } from './RestoreVersionDialog';
import { useToast } from '../common/Toast';
import { Button } from '../common/Button';

interface VersionHistoryPanelProps {
  documentType: DocumentType;
  documentId: string;
  isOpen: boolean;
  onClose: () => void;
  onVersionRestored?: (newContent: string) => void;
}

export const VersionHistoryPanel: React.FC<VersionHistoryPanelProps> = ({
  documentType,
  documentId,
  isOpen,
  onClose,
  onVersionRestored
}) => {
  const [versions, setVersions] = useState<EditorialVersion[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'compare' | 'preview'>('timeline');

  // Preview state
  const [previewVersion, setPreviewVersion] = useState<EditorialVersion | null>(null);

  // Compare state
  const [compareVersionAId, setCompareVersionAId] = useState<string>('');
  const [compareVersionBId, setCompareVersionBId] = useState<string>('');
  const [comparisonData, setComparisonData] = useState<VersionComparisonResponse | null>(null);
  const [isComparing, setIsComparing] = useState<boolean>(false);

  // Restore dialog state
  const [restoreTargetVersion, setRestoreTargetVersion] = useState<EditorialVersion | null>(null);
  const [isRestoreOpen, setIsRestoreOpen] = useState<boolean>(false);

  const { success, error, info } = useToast();

  const loadVersions = async () => {
    if (!documentId) return;
    try {
      setIsLoading(true);
      const data = await versionService.getVersions(documentType, documentId);
      setVersions(data);
      if (data.length > 0 && !previewVersion) {
        setPreviewVersion(data[0]);
      }
      if (data.length >= 2) {
        setCompareVersionAId(String(data[1].version_number));
        setCompareVersionBId(String(data[0].version_number));
      }
    } catch (err: any) {
      error('Failed to load version history: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && documentId) {
      loadVersions();
    }
  }, [isOpen, documentId, documentType]);

  const handleSelectPreview = (v: EditorialVersion) => {
    setPreviewVersion(v);
    setActiveTab('preview');
  };

  const handleCompareWithHead = async (v: EditorialVersion) => {
    if (versions.length === 0) return;
    const head = versions[0];
    try {
      setIsComparing(true);
      setActiveTab('compare');
      setCompareVersionAId(String(v.version_number));
      setCompareVersionBId(String(head.version_number));
      const res = await versionService.compareVersions(
        documentType,
        documentId,
        v.version_number,
        head.version_number
      );
      setComparisonData(res);
    } catch (err: any) {
      error('Failed to compare versions: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsComparing(false);
    }
  };

  const handleRunComparison = async () => {
    if (!compareVersionAId || !compareVersionBId) return;
    try {
      setIsComparing(true);
      const res = await versionService.compareVersions(
        documentType,
        documentId,
        compareVersionAId,
        compareVersionBId
      );
      setComparisonData(res);
    } catch (err: any) {
      error('Failed to compare versions: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsComparing(false);
    }
  };

  const handleOpenRestoreDialog = (v: EditorialVersion) => {
    setRestoreTargetVersion(v);
    setIsRestoreOpen(true);
  };

  const handleExecuteRestore = async (versionId: string, note?: string) => {
    try {
      const res = await versionService.restoreVersion(documentType, documentId, versionId, note);
      success(res.message);
      await loadVersions();
      if (onVersionRestored) {
        onVersionRestored(res.updated_content);
      }
      setActiveTab('timeline');
    } catch (err: any) {
      error('Restoration failed: ' + (err.response?.data?.detail || err.message));
      throw err;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-xl bg-white shadow-2xl z-50 flex flex-col border-l border-slate-200">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-slate-800 text-sm">Version Control & Audit History</h3>
            <p className="text-xs text-slate-500">
              {versions.length} immutable {versions.length === 1 ? 'snapshot' : 'snapshots'} recorded
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadVersions}
            disabled={isLoading}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition"
            title="Close panel"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-5">
        <button
          onClick={() => setActiveTab('timeline')}
          className={`py-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
            activeTab === 'timeline'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Timeline ({versions.length})
        </button>

        <button
          onClick={() => {
            setActiveTab('compare');
            if (!comparisonData && versions.length >= 2) {
              handleRunComparison();
            }
          }}
          className={`py-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
            activeTab === 'compare'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <GitCompare className="w-3.5 h-3.5" />
          Compare Diffs
        </button>

        {previewVersion && (
          <button
            onClick={() => setActiveTab('preview')}
            className={`py-2.5 px-3 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'preview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            Snapshot v{previewVersion.version_number}
          </button>
        )}
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {isLoading && versions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-xs">Loading immutable version logs...</span>
          </div>
        ) : activeTab === 'timeline' ? (
          <VersionTimeline
            versions={versions}
            onSelectVersion={handleSelectPreview}
            onCompareWithHead={handleCompareWithHead}
            onOpenRestore={handleOpenRestoreDialog}
            selectedVersionId={previewVersion?.id}
          />
        ) : activeTab === 'compare' ? (
          <div className="space-y-4">
            {/* Version Selectors */}
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 grid grid-cols-2 gap-3 items-end">
              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Base Version (From):
                </label>
                <select
                  value={compareVersionAId}
                  onChange={(e) => setCompareVersionAId(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded px-2 py-1.5 bg-white text-slate-700"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      v{v.version_number} — {v.change_summary.slice(0, 30)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-600 block mb-1">
                  Target Version (To):
                </label>
                <select
                  value={compareVersionBId}
                  onChange={(e) => setCompareVersionBId(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded px-2 py-1.5 bg-white text-slate-700"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      v{v.version_number} — {v.change_summary.slice(0, 30)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-span-2 flex justify-end">
                <Button
                  size="sm"
                  onClick={handleRunComparison}
                  disabled={isComparing || compareVersionAId === compareVersionBId}
                  className="text-xs gap-1.5"
                >
                  {isComparing ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Computing Diff...
                    </>
                  ) : (
                    <>
                      <GitCompare className="w-3.5 h-3.5" />
                      Calculate Comparison
                    </>
                  )}
                </Button>
              </div>
            </div>

            {comparisonData ? (
              <VersionComparison comparison={comparisonData} />
            ) : (
              <div className="text-center py-10 text-slate-400 text-xs">
                Select any two versions above and click "Calculate Comparison".
              </div>
            )}
          </div>
        ) : (
          /* Preview Tab */
          previewVersion && (
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                <div>
                  <h4 className="font-semibold text-slate-800 text-sm">
                    Version {previewVersion.version_number}: {previewVersion.title || 'Untitled'}
                  </h4>
                  <p className="text-xs text-slate-500">
                    {previewVersion.word_count} words • Captured {new Date(previewVersion.created_at).toLocaleString()}
                  </p>
                </div>

                {versions[0]?.id !== previewVersion.id && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenRestoreDialog(previewVersion)}
                    className="text-xs gap-1 text-amber-700 border-amber-300 hover:bg-amber-50"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Restore this version
                  </Button>
                )}
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-xs leading-relaxed text-slate-800 whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                {previewVersion.content_snapshot}
              </div>
            </div>
          )
        )}
      </div>

      {/* Restore Confirmation Dialog */}
      <RestoreVersionDialog
        isOpen={isRestoreOpen}
        version={restoreTargetVersion}
        onClose={() => setIsRestoreOpen(false)}
        onConfirm={handleExecuteRestore}
      />
    </div>
  );
};
