import React, { useState } from 'react';
import { RotateCcw, AlertTriangle, Loader2 } from 'lucide-react';
import { EditorialVersion } from '../../types/version';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { VersionMetadata } from './VersionMetadata';

interface RestoreVersionDialogProps {
  isOpen: boolean;
  version: EditorialVersion | null;
  onClose: () => void;
  onConfirm: (versionId: string, note?: string) => Promise<void>;
}

export const RestoreVersionDialog: React.FC<RestoreVersionDialogProps> = ({
  isOpen,
  version,
  onClose,
  onConfirm
}) => {
  const [note, setNote] = useState('');
  const [isRestoring, setIsRestoring] = useState(false);

  if (!version) return null;

  const handleRestore = async () => {
    try {
      setIsRestoring(true);
      await onConfirm(version.id, note.trim() || undefined);
      setNote('');
      onClose();
    } catch {
      // Error handled by parent toast
    } finally {
      setIsRestoring(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => !isRestoring && onClose()}
      title={`Restore Version ${version.version_number}`}
    >
      <div className="space-y-4 text-sm text-slate-700">
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3 text-amber-900">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-xs uppercase tracking-wide">Non-Destructive Restoration</p>
            <p className="text-xs text-amber-800 leading-relaxed">
              Restoring will replace the active working copy with this snapshot's content.
              A <strong>new version</strong> will be recorded to capture this action. 
              <strong> All later versions and historical drafts are preserved and will never be deleted.</strong>
            </p>
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">Target Version Snapshot:</label>
          <VersionMetadata version={version} />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">
            Restoration Note (Optional):
          </label>
          <Input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g., Reverting unapproved editorial angle..."
            disabled={isRestoring}
          />
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          <Button variant="outline" onClick={onClose} disabled={isRestoring}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleRestore}
            disabled={isRestoring}
            className="gap-2 bg-amber-600 hover:bg-amber-700 text-white border-transparent"
          >
            {isRestoring ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Restoring...
              </>
            ) : (
              <>
                <RotateCcw className="w-4 h-4" />
                Confirm Restoration
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
