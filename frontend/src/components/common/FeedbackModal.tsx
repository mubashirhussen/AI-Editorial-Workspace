import React, { useState } from 'react';
import { MessageSquarePlus, AlertCircle, CheckCircle2, Loader2, X } from 'lucide-react';
import { feedbackService, FeedbackCategory, FeedbackSeverity } from '../../services/feedbackService';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultModule?: string;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  defaultModule = 'editorial'
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<FeedbackCategory>('bug_report');
  const [severity, setSeverity] = useState<FeedbackSeverity>('medium');
  const [moduleRef, setModuleRef] = useState(defaultModule);

  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (title.trim().length < 3) {
      setError('Title must be at least 3 characters.');
      return;
    }
    if (description.trim().length < 10) {
      setError('Description must be at least 10 characters.');
      return;
    }

    setSubmitting(true);
    try {
      await feedbackService.submitFeedback({
        title: title.trim(),
        description: description.trim(),
        category,
        severity,
        module_reference: moduleRef
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setTitle('');
        setDescription('');
        onClose();
      }, 1500);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to submit feedback.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 text-slate-100">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
            <MessageSquarePlus className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Submit User Feedback & Defect Report</h2>
            <p className="text-xs text-slate-400">Help us continuously improve reliability, evidence accuracy, and UX.</p>
          </div>
        </div>

        {success ? (
          <div className="py-8 text-center flex flex-col items-center gap-2">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-bounce" />
            <h3 className="text-base font-semibold text-emerald-300">Feedback Submitted Successfully!</h3>
            <p className="text-xs text-slate-400">Thank you for helping us harden the platform.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 p-3 text-xs bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as FeedbackCategory)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="bug_report">Bug Report</option>
                  <option value="feature_request">Feature Request</option>
                  <option value="ux_improvement">UX Improvement</option>
                  <option value="ai_output_quality">AI Output Quality</option>
                  <option value="research_accuracy">Research Accuracy</option>
                  <option value="citation_issue">Citation Issue</option>
                  <option value="writing_quality">Writing Quality</option>
                  <option value="editorial_workflow">Editorial Workflow</option>
                  <option value="general">General</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Severity</label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value as FeedbackSeverity)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="low">Low (Cosmetic / Suggestion)</option>
                  <option value="medium">Medium (Standard Issue)</option>
                  <option value="high">High (Workflow Impairment)</option>
                  <option value="critical">Critical (Blocking Defect)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Module</label>
              <select
                value={moduleRef}
                onChange={(e) => setModuleRef(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="research">Research Assistant</option>
                <option value="writing">Writing Assistant</option>
                <option value="editorial">Editorial Studio</option>
                <option value="dashboard">Dashboard</option>
                <option value="observability">Observability & Health</option>
                <option value="auth">Authentication & RBAC</option>
                <option value="general">Other / General</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Title</label>
              <input
                type="text"
                placeholder="Brief summary of the issue or idea..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 placeholder:text-slate-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
              <textarea
                placeholder="Detailed steps to reproduce, observed behavior vs expected, or suggestion..."
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 placeholder:text-slate-500 resize-none"
                required
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Submitting...</span>
                  </>
                ) : (
                  <span>Submit Feedback</span>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
