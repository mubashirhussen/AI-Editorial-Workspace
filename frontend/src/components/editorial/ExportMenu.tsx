import React, { useState } from 'react';
import { Copy, Download, Check, FileCode, FileText, Code } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Tabs } from '../common/Tabs';
import { EditorialExportResponse } from '../../types';

export interface ExportMenuProps {
  isOpen: boolean;
  onClose: () => void;
  exportData: EditorialExportResponse | null;
  isLoading?: boolean;
}

export const ExportMenu: React.FC<ExportMenuProps> = ({
  isOpen,
  onClose,
  exportData,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<'markdown' | 'txt' | 'html' | 'json'>('markdown');
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const getActiveContent = () => {
    if (!exportData) return '';
    if (activeTab === 'markdown') return exportData.markdown_content;
    if (activeTab === 'txt') return exportData.plain_text_content;
    if (activeTab === 'json') return exportData.json_content || JSON.stringify(exportData, null, 2);
    return exportData.html_content || exportData.markdown_content;
  };

  const handleCopy = async () => {
    const text = getActiveContent();
    if (text) {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    const text = getActiveContent();
    if (!text) return;

    const extension = activeTab === 'markdown' ? 'md' : activeTab === 'html' ? 'html' : activeTab === 'json' ? 'json' : 'txt';
    const mimeType = activeTab === 'html' ? 'text/html' : activeTab === 'json' ? 'application/json' : 'text/plain';
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `newsletter-edition.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const tabs = [
    { id: 'markdown', label: 'Markdown (.md)', icon: <FileCode className="w-3.5 h-3.5" /> },
    { id: 'txt', label: 'Plain Text (.txt)', icon: <FileText className="w-3.5 h-3.5" /> },
    { id: 'html', label: 'HTML5 (.html)', icon: <Code className="w-3.5 h-3.5" /> },
    { id: 'json', label: 'JSON (.json)', icon: <FileCode className="w-3.5 h-3.5" /> },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Export Newsletter Edition"
      description="Download or copy your finalized article copy in multi-platform formats."
      maxWidth="2xl"
    >
      <div className="space-y-4">
        {/* Format Selector Tabs */}
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onChange={(id) => setActiveTab(id as any)}
            variant="pills"
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={handleCopy}
              variant="outline"
              size="sm"
              leftIcon={copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            >
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </Button>
            <Button
              onClick={handleDownload}
              variant="primary"
              size="sm"
              leftIcon={<Download className="w-3.5 h-3.5" />}
            >
              Download File
            </Button>
          </div>
        </div>

        {/* Text Preview Display */}
        <div className="relative">
          <pre className="max-h-[380px] overflow-y-auto p-4 rounded-xl bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed whitespace-pre-wrap select-all">
            {getActiveContent()}
          </pre>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
          <span>Target Word Count: 300–500 words</span>
          <span>Actual: {exportData?.word_count || 0} words</span>
        </div>
      </div>
    </Modal>
  );
};

