import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ShieldCheck, 
  Send, 
  FileCheck2, 
  Sparkles, 
  MessageSquare, 
  FileDiff, 
  Lock, 
  RotateCcw,
  Check,
  X
} from 'lucide-react';
import { EditorialOutput, EditorialReview, EditorialComment } from '../../types';
import { editorialService } from '../../services/editorialService';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../common/Button';

interface EditorialReviewPanelProps {
  editorial: EditorialOutput;
  onEditorialUpdated: (updated: EditorialOutput) => void;
  onClose?: () => void;
}

export const EditorialReviewPanel: React.FC<EditorialReviewPanelProps> = ({
  editorial,
  onEditorialUpdated,
  onClose
}) => {
  const { user } = useAuth();
  const [reviews, setReviews] = useState<EditorialReview[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'review' | 'diff' | 'ai_audit'>('review');
  const [reviewerName, setReviewerName] = useState(user?.full_name || 'Senior Editor');

  useEffect(() => {
    if (user?.full_name) {
      setReviewerName(user.full_name);
    }
  }, [user?.full_name]);
  
  // Action states
  const [changeFeedback, setChangeFeedback] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');
  const [showChangeModal, setShowChangeModal] = useState(false);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [newCommentText, setNewCommentText] = useState('');
  const [newCommentSection, setNewCommentSection] = useState('Strategic Analysis');
  const [newCommentSuggestedRevision, setNewCommentSuggestedRevision] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    loadReviews();
  }, [editorial.id]);

  const loadReviews = async () => {
    try {
      setLoading(true);
      const data = await editorialService.getReviews(editorial.id);
      setReviews(data);
    } catch (err: any) {
      console.error('Failed to load reviews', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAiReview = async () => {
    try {
      setLoading(true);
      setActionError(null);
      const res = await editorialService.runAiReview(editorial.id);
      const updated = await editorialService.getEditorial(editorial.id);
      onEditorialUpdated(updated);
      setActiveTab('ai_audit');
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to execute AI pre-review.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setLoading(true);
      setActionError(null);
      await editorialService.approveEditorial(editorial.id, {
        reviewer_name: reviewerName,
        approval_notes: approvalNotes || 'Approved by editorial desk.'
      });
      const updated = await editorialService.getEditorial(editorial.id);
      onEditorialUpdated(updated);
      setShowApproveModal(false);
      await loadReviews();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to approve editorial.');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestChanges = async () => {
    if (changeFeedback.trim().length < 10) {
      setActionError('Meaningful, constructive feedback (at least 10 characters) is required when requesting revisions.');
      return;
    }
    try {
      setLoading(true);
      setActionError(null);
      await editorialService.requestChanges(editorial.id, {
        reviewer_name: reviewerName,
        feedback: changeFeedback
      });
      const updated = await editorialService.getEditorial(editorial.id);
      onEditorialUpdated(updated);
      setShowChangeModal(false);
      setChangeFeedback('');
      await loadReviews();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to request changes.');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async () => {
    try {
      setLoading(true);
      setActionError(null);
      await editorialService.finalizeEditorial(editorial.id, {
        finalized_by: reviewerName,
        publication_notes: 'Finalized for newsletter distribution.'
      });
      const updated = await editorialService.getEditorial(editorial.id);
      onEditorialUpdated(updated);
      await loadReviews();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to finalize editorial. Ensure it is approved first.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (reviewId: string) => {
    if (!newCommentText.trim()) return;
    try {
      setLoading(true);
      await editorialService.addComment(reviewId, {
        comment: newCommentText,
        section_reference: newCommentSection,
        suggested_revision: newCommentSuggestedRevision || undefined
      });
      setNewCommentText('');
      setNewCommentSuggestedRevision('');
      await loadReviews();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || 'Failed to add comment.');
    } finally {
      setLoading(false);
    }
  };

  const handleResolveComment = async (commentId: string, status: 'resolved' | 'rejected') => {
    try {
      await editorialService.updateComment(commentId, { resolution_status: status });
      await loadReviews();
    } catch (err: any) {
      console.error('Failed to update comment resolution', err);
    }
  };

  const isFinalized = editorial.status === 'FINALIZED';
  const isApproved = editorial.status === 'APPROVED';
  const isPending = editorial.status === 'HUMAN_REVIEW_PENDING' || editorial.status === 'AI_REVIEW_COMPLETED';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-6">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <span className={`px-2.5 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${
              isFinalized 
                ? 'bg-purple-900/50 text-purple-300 border border-purple-700/50' 
                : isApproved 
                ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50'
                : editorial.status === 'CHANGES_REQUESTED'
                ? 'bg-amber-900/50 text-amber-300 border border-amber-700/50'
                : 'bg-blue-900/50 text-blue-300 border border-blue-700/50'
            }`}>
              {editorial.status}
            </span>
            <span className="text-xs text-slate-400">Version {editorial.version || 1}</span>
            <span className="text-xs text-slate-400">• {editorial.word_count} words (Target: 300-500)</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100 mt-2">{editorial.headline}</h2>
        </div>

        {/* Tab switchers */}
        <div className="flex bg-slate-800/80 p-1 rounded-lg border border-slate-700/60">
          <button
            onClick={() => setActiveTab('review')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeTab === 'review' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Review & Comments
          </button>
          <button
            onClick={() => setActiveTab('ai_audit')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'ai_audit' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Sparkles className="w-3 h-3 text-amber-300" />
            AI Pre-Review
          </button>
          <button
            onClick={() => setActiveTab('diff')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'diff' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileDiff className="w-3 h-3 text-cyan-300" />
            Version History
          </button>
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400">Reviewer:</label>
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            disabled={isFinalized}
            className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 w-36"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {!isFinalized && (
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRunAiReview}
                disabled={loading}
                className="text-xs flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                Run AI Audit
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowChangeModal(true)}
                disabled={loading}
                className="text-xs text-amber-300 border-amber-800/50 hover:bg-amber-950/30"
              >
                Request Changes
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowApproveModal(true)}
                disabled={loading || isApproved}
                className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
              >
                <Check className="w-3.5 h-3.5 mr-1" />
                Approve
              </Button>
            </>
          )}

          {isApproved && !isFinalized && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleFinalize}
              disabled={loading}
              className="text-xs bg-purple-600 hover:bg-purple-500 text-white"
            >
              <Lock className="w-3.5 h-3.5 mr-1" />
              Finalize & Lock
            </Button>
          )}

          {isFinalized && (
            <div className="flex items-center gap-2 text-xs text-purple-300 bg-purple-950/40 px-3 py-1.5 rounded-md border border-purple-800/60">
              <Lock className="w-3.5 h-3.5" />
              Finalized & Locked (Immutable)
            </div>
          )}
        </div>
      </div>

      {/* Tab 1: Review & Comments Thread */}
      {activeTab === 'review' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Article Copy */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-slate-950 p-5 rounded-lg border border-slate-800 text-slate-300 font-serif leading-relaxed text-sm whitespace-pre-line max-h-[500px] overflow-y-auto">
                {editorial.content}
              </div>
            </div>

            {/* Right: Comments Thread */}
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-indigo-400" />
                Reviewer Audit Trail ({reviews.length})
              </h3>

              {reviews.length === 0 ? (
                <div className="p-4 bg-slate-950/40 border border-dashed border-slate-800 rounded-lg text-center text-xs text-slate-500">
                  No review audit records logged yet.
                </div>
              ) : (
                <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
                  {reviews.map((rev) => (
                    <div key={rev.id} className="bg-slate-950/80 border border-slate-800 rounded-lg p-3.5 space-y-2.5 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="font-semibold text-slate-200">{rev.reviewer_name}</span>
                        <span className="text-[10px] text-slate-500">{new Date(rev.created_at).toLocaleString()}</span>
                      </div>
                      <div className="inline-block px-2 py-0.5 text-[10px] rounded bg-slate-800 text-indigo-300 font-mono">
                        {rev.review_status}
                      </div>
                      {rev.overall_feedback && (
                        <p className="text-slate-300 bg-slate-900/60 p-2 rounded border border-slate-800">
                          {rev.overall_feedback}
                        </p>
                      )}

                      {/* Comments inside this review */}
                      {rev.comments && rev.comments.length > 0 && (
                        <div className="mt-2 space-y-2 border-t border-slate-800/80 pt-2">
                          {rev.comments.map((c) => (
                            <div key={c.id} className="bg-slate-900/90 p-2.5 rounded border border-slate-800 text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-medium text-amber-400 uppercase">
                                  [{c.section_reference || 'General'}]
                                </span>
                                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                                  c.resolution_status === 'resolved' 
                                    ? 'bg-emerald-950 text-emerald-400' 
                                    : 'bg-amber-950 text-amber-400'
                                }`}>
                                  {c.resolution_status}
                                </span>
                              </div>
                              <p className="text-slate-200">{c.comment}</p>
                              {c.suggested_revision && (
                                <div className="text-[11px] text-emerald-300 bg-emerald-950/30 p-1.5 rounded font-mono border border-emerald-900/40">
                                  Suggested: {c.suggested_revision}
                                </div>
                              )}
                              {c.resolution_status === 'open' && !isFinalized && (
                                <div className="flex gap-2 pt-1">
                                  <button
                                    onClick={() => handleResolveComment(c.id, 'resolved')}
                                    className="text-[10px] text-emerald-400 hover:underline"
                                  >
                                    Mark Resolved
                                  </button>
                                  <button
                                    onClick={() => handleResolveComment(c.id, 'rejected')}
                                    className="text-[10px] text-slate-500 hover:underline"
                                  >
                                    Reject
                                  </button>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add comment input for latest review */}
                      {!isFinalized && (
                        <div className="mt-3 pt-2 border-t border-slate-800/80 space-y-2">
                          <input
                            type="text"
                            placeholder="Add targeted revision comment..."
                            value={newCommentText}
                            onChange={(e) => setNewCommentText(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                          />
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Optional suggested rewrite..."
                              value={newCommentSuggestedRevision}
                              onChange={(e) => setNewCommentSuggestedRevision(e.target.value)}
                              className="flex-1 bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none"
                            />
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleAddComment(rev.id)}
                              className="text-[10px] px-2 py-1"
                            >
                              Post
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: AI Pre-Review Quality Audit */}
      {activeTab === 'ai_audit' && (
        <div className="space-y-4">
          {!editorial.ai_review_results ? (
            <div className="text-center py-8 bg-slate-950 p-6 rounded-lg border border-slate-800 space-y-3">
              <Sparkles className="w-8 h-8 text-amber-400 mx-auto" />
              <p className="text-sm text-slate-300 font-medium">No automated pre-review audit recorded yet.</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Running the AI pre-review executes automated word count, writing quality, section completeness, and source reference verification before human sign-off.
              </p>
              <Button size="sm" onClick={handleRunAiReview} disabled={loading}>
                Run Automated Pre-Review
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Word Count & Readability */}
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Length & Readability Standards
                </h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-400">Word Count:</span>
                    <span className={`font-mono font-semibold ${
                      editorial.ai_review_results.word_count_compliance?.is_compliant ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {editorial.ai_review_results.word_count_compliance?.word_count} words (300-500 standard)
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-400">Readability Score:</span>
                    <span className="text-slate-200 font-mono">
                      {editorial.ai_review_results.readability_score} ({editorial.ai_review_results.readability_grade})
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-400">Automated Verdict:</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-950 text-indigo-300 font-mono">
                      {editorial.ai_review_results.ai_verdict}
                    </span>
                  </div>
                </div>
              </div>

              {/* Citations & Sections */}
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FileCheck2 className="w-4 h-4 text-cyan-400" />
                  Traceability & Section Integrity
                </h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-400">Citations Found:</span>
                    <span className="text-slate-200 font-mono">
                      {editorial.ai_review_results.citations_found_count} references
                    </span>
                  </div>
                  <div className="py-1 border-b border-slate-800">
                    <span className="text-slate-400 block mb-1">Missing Sections:</span>
                    {editorial.ai_review_results.missing_sections?.length === 0 ? (
                      <span className="text-emerald-400 text-[11px]">All required sections present</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {editorial.ai_review_results.missing_sections?.map((sec: string) => (
                          <span key={sec} className="bg-rose-950/60 text-rose-300 px-1.5 py-0.5 rounded text-[10px]">
                            Missing: {sec}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Version Diff Viewer */}
      {activeTab === 'diff' && (
        <div className="bg-slate-950 p-5 rounded-lg border border-slate-800 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-3">
            <span>Original Version (v1) vs Current Draft (v{editorial.version || 1})</span>
            <span className="text-slate-500">Preserved original copy is locked against modification</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <h5 className="font-sans font-semibold text-slate-400 mb-2">Original Generated Content (v1)</h5>
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800 text-slate-400 max-h-[400px] overflow-y-auto whitespace-pre-line leading-relaxed">
                {editorial.original_content || editorial.content}
              </div>
            </div>
            <div>
              <h5 className="font-sans font-semibold text-emerald-400 mb-2">Current Working Revision (v{editorial.version || 1})</h5>
              <div className="bg-slate-900/60 p-3 rounded border border-slate-800 text-slate-200 max-h-[400px] overflow-y-auto whitespace-pre-line leading-relaxed">
                {editorial.content}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Request Changes */}
      {showChangeModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-lg w-full space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-400" />
              Request Editorial Changes
            </h3>
            <p className="text-xs text-slate-400">
              Provide specific, actionable guidance for the writing desk. Meaningful feedback (at least 10 characters) is required.
            </p>
            <textarea
              rows={4}
              value={changeFeedback}
              onChange={(e) => setChangeFeedback(e.target.value)}
              placeholder="e.g. Please clarify the distinction between proprietary and open-weight models in Section 3, and add supporting citations..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2.5">
              <Button variant="secondary" size="sm" onClick={() => setShowChangeModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleRequestChanges} disabled={loading}>
                Submit Change Request
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Approve Editorial */}
      {showApproveModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-lg w-full space-y-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              Approve Editorial for Publication
            </h3>
            <p className="text-xs text-slate-400">
              Confirm that you have reviewed the factual attributions, writing clarity, and word count compliance.
            </p>
            <textarea
              rows={3}
              value={approvalNotes}
              onChange={(e) => setApprovalNotes(e.target.value)}
              placeholder="Optional approval notes for editorial record..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            />
            <div className="flex justify-end gap-2.5">
              <Button variant="secondary" size="sm" onClick={() => setShowApproveModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleApprove} disabled={loading} className="bg-emerald-600 hover:bg-emerald-500">
                Confirm Approval
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

