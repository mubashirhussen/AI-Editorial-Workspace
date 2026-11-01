import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  BookOpen,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Plus,
  ArrowRight,
  Check,
  X,
  Gauge
} from 'lucide-react';
import { styleService } from '../../services/styleService';
import { StyleProfile, StyleCheckResponse, StyleSuggestionItem } from '../../types/style';
import { useToast } from '../common/Toast';

interface Props {
  draftId?: string;
  currentContent: string;
  onAcceptSuggestion?: (suggestionId: string) => void;
  onRejectSuggestion?: (suggestionId: string) => void;
}

export const StyleIntelligencePanel: React.FC<Props> = ({
  draftId,
  currentContent,
  onAcceptSuggestion,
  onRejectSuggestion
}) => {
  const { success, error, info } = useToast();
  const [profiles, setProfiles] = useState<StyleProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  const [styleResult, setStyleResult] = useState<StyleCheckResponse | null>(null);
  const [isAuditing, setIsAuditing] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);

  // Profile Form State
  const [profileName, setProfileName] = useState('');
  const [pubName, setPubName] = useState('This Week in AI');
  const [tone, setTone] = useState('Authoritative, analytical, objective');
  const [audience, setAudience] = useState('Founders, builders, and operators');
  const [maxSentenceLen, setMaxSentenceLen] = useState(22);
  const [avoidedTerms, setAvoidedTerms] = useState('game-changer, delve, revolutionary, paradigm shift, pivotal');

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const list = await styleService.getProfiles();
      setProfiles(list);
      const defaultProf = list.find((p) => p.is_default) || list[0];
      if (defaultProf) {
        setSelectedProfileId(defaultProf.id);
      }
    } catch (err) {
      console.error('Failed to load style profiles', err);
    }
  };

  const runStyleAudit = async () => {
    if (!draftId) {
      error('Please select or save a writing draft first.');
      return;
    }
    try {
      setIsAuditing(true);
      const res = await styleService.checkDraftStyle(draftId, {
        style_profile_id: selectedProfileId || undefined,
        content: currentContent
      });
      setStyleResult(res);
      success(`Style audit completed: ${res.style_score}% compliance score.`);
    } catch (err: any) {
      error(err.response?.data?.detail || 'Style audit failed.');
    } finally {
      setIsAuditing(false);
    }
  };

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const avoidedList = avoidedTerms.split(',').map((t) => t.trim()).filter(Boolean);
      const newProf = await styleService.createProfile({
        name: profileName,
        publication_name: pubName,
        tone,
        target_audience: audience,
        max_sentence_length: maxSentenceLen,
        words_to_avoid: avoidedList,
        is_default: false
      });
      success(`Style profile "${newProf.name}" created!`);
      setShowProfileModal(false);
      await loadProfiles();
      setSelectedProfileId(newProf.id);
    } catch (err: any) {
      error(err.response?.data?.detail || 'Failed to create style profile.');
    }
  };

  const activeProfile = profiles.find((p) => p.id === selectedProfileId);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-4">
      {/* Header & Profile Switcher */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Editorial Style Intelligence
          </h3>
          <span className="text-[10px] font-mono bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded border border-indigo-100">
            Phase 26
          </span>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={selectedProfileId}
            onChange={(e) => setSelectedProfileId(e.target.value)}
            className="text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} {p.is_default ? '(Default)' : ''}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowProfileModal(true)}
            className="p-1.5 text-slate-400 hover:text-indigo-600 rounded-lg border border-slate-200 hover:bg-indigo-50"
            title="Create Style Profile"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={runStyleAudit}
            disabled={isAuditing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs transition-all whitespace-nowrap cursor-pointer"
          >
            {isAuditing ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5" />
            )}
            <span>Audit Style</span>
          </button>
        </div>
      </div>

      {/* Profile Active Guidelines Summary */}
      {activeProfile && (
        <div className="text-[11px] bg-slate-50 p-2.5 rounded-xl border border-slate-100 flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-600">
          <span>Target Tone: <strong>{activeProfile.tone}</strong></span>
          <span>Max Sentence: <strong>{activeProfile.max_sentence_length} words</strong></span>
          <span>Target Flesch: <strong>{activeProfile.target_flesch_score}</strong></span>
          <span>Words to Avoid: <strong>{activeProfile.words_to_avoid?.length || 0} terms</strong></span>
        </div>
      )}

      {/* Style Results Banner & Metrics */}
      {styleResult && (
        <div className="space-y-3 pt-1">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white shadow-xs">
            <div>
              <div className="text-[10px] uppercase font-mono text-indigo-300">Style Compliance Score</div>
              <div className="text-2xl font-bold tracking-tight text-white mt-0.5">
                {styleResult.style_score}%
              </div>
            </div>
            <div className="text-right">
              <span className="inline-block px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30">
                {styleResult.tone_detected}
              </span>
              <p className="text-[11px] text-slate-300 mt-1 max-w-xs line-clamp-1">
                {styleResult.qualitative_feedback}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
            <div className="p-2 rounded-lg border border-slate-100 bg-slate-50/50">
              <span className="text-[10px] text-slate-500 block uppercase">Sentence Length</span>
              <span className="font-bold text-slate-800">{styleResult.metrics.sentence_length_score}%</span>
            </div>
            <div className="p-2 rounded-lg border border-slate-100 bg-slate-50/50">
              <span className="text-[10px] text-slate-500 block uppercase">Terminology</span>
              <span className="font-bold text-slate-800">{styleResult.metrics.terminology_score}%</span>
            </div>
            <div className="p-2 rounded-lg border border-slate-100 bg-slate-50/50">
              <span className="text-[10px] text-slate-500 block uppercase">Tone Alignment</span>
              <span className="font-bold text-slate-800">{styleResult.metrics.tone_score}%</span>
            </div>
            <div className="p-2 rounded-lg border border-slate-100 bg-slate-50/50">
              <span className="text-[10px] text-slate-500 block uppercase">Flesch Reading Ease</span>
              <span className="font-bold text-slate-800">{styleResult.metrics.actual_flesch_reading_ease ?? 65}</span>
            </div>
          </div>

          {/* Style Suggestions */}
          {styleResult.suggestions && styleResult.suggestions.length > 0 ? (
            <div className="space-y-2 pt-2">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Style Corrections ({styleResult.suggestions.length})
              </h4>
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {styleResult.suggestions.map((sug, idx) => (
                  <div key={sug.id || idx} className="p-3 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {sug.style_rule}
                      </span>
                      {sug.id && onAcceptSuggestion && onRejectSuggestion && (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => onAcceptSuggestion(sug.id!)}
                            className="flex items-center gap-1 px-2 py-1 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded text-[11px] font-semibold cursor-pointer"
                          >
                            <Check className="w-3 h-3" /> Accept
                          </button>
                          <button
                            onClick={() => onRejectSuggestion(sug.id!)}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded hover:bg-slate-100 cursor-pointer"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="text-slate-600 line-through italic bg-slate-50 p-1.5 rounded">
                      "{sug.original_text}"
                    </div>

                    <div className="text-emerald-700 font-semibold bg-emerald-50/50 p-1.5 rounded border border-emerald-100">
                      &rarr; {sug.suggested_rewrite}
                    </div>

                    <p className="text-[11px] text-slate-500">{sug.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-100 text-xs text-emerald-800 text-center font-medium">
              Zero style violations detected! Copy adheres strictly to editorial guidelines.
            </div>
          )}
        </div>
      )}

      {/* Modal: Create Profile */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Create Editorial Style Profile</h3>
            <form onSubmit={handleCreateProfile} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Profile Name</label>
                <input
                  type="text"
                  required
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  placeholder="e.g. Executive Deep Dive"
                  className="w-full p-2 border rounded-lg focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Publication Name</label>
                <input
                  type="text"
                  value={pubName}
                  onChange={(e) => setPubName(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Target Tone</label>
                <input
                  type="text"
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Max Sentence Length (words)</label>
                <input
                  type="number"
                  value={maxSentenceLen}
                  onChange={(e) => setMaxSentenceLen(Number(e.target.value))}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Words to Avoid (comma-separated)</label>
                <textarea
                  rows={2}
                  value={avoidedTerms}
                  onChange={(e) => setAvoidedTerms(e.target.value)}
                  className="w-full p-2 border rounded-lg"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowProfileModal(false)}
                  className="px-3 py-1.5 rounded-lg border text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-xs cursor-pointer"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

