import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.base import WritingDraft, WritingSuggestion, EditorialStyleProfile
from backend.app.schemas.style import StyleProfileResponse, StyleCheckResponse, StyleSuggestionItem
from backend.app.utils.text_processing import split_into_sentences
from backend.app.services.style_intelligence.tone_detector import ToneDetector
from backend.app.services.style_intelligence.terminology_checker import TerminologyChecker
from backend.app.services.style_intelligence.consistency_checker import ConsistencyChecker
from backend.app.services.style_intelligence.style_scorer import StyleScorer

logger = logging.getLogger(__name__)

class StyleAnalyzer:
    def __init__(self):
        self.tone_detector = ToneDetector()
        self.terminology_checker = TerminologyChecker()
        self.consistency_checker = ConsistencyChecker()
        self.style_scorer = StyleScorer()

    def analyze_text(
        self,
        text: str,
        profile: EditorialStyleProfile
    ) -> Dict[str, Any]:
        """
        Executes multidimensional style evaluation against an EditorialStyleProfile.
        """
        sentences = split_into_sentences(text or "")
        total_sentences = len(sentences)

        # 1. Tone Analysis
        tone_results = self.tone_detector.analyze_tone(text, target_tone=profile.tone)

        # 2. Terminology Analysis
        term_results = self.terminology_checker.check_terminology(
            text,
            preferred_terms=profile.preferred_terminology or {},
            words_to_avoid=profile.words_to_avoid or []
        )

        # 3. Consistency Analysis
        consistency_results = self.consistency_checker.check_consistency(
            text,
            max_sentence_length=profile.max_sentence_length,
            max_paragraph_length=profile.max_paragraph_length
        )

        # 4. Multidimensional Scoring
        overall_score, metrics, qualitative = self.style_scorer.compute_score(
            text=text,
            target_flesch_score=profile.target_flesch_score,
            length_violations=consistency_results["length_violations_count"],
            total_sentences=total_sentences,
            terminology_deviations=term_results["terminology_deviations_count"],
            avoided_words=term_results["avoided_words_count"],
            promotional_count=tone_results["promotional_count"],
            informal_count=tone_results["informal_count"]
        )

        # 5. Collate all suggestions
        combined_suggestions: List[Dict[str, Any]] = []
        combined_suggestions.extend(tone_results["suggestions"])
        combined_suggestions.extend(term_results["suggestions"])
        combined_suggestions.extend(consistency_results["suggestions"])

        return {
            "style_score": overall_score,
            "metrics": metrics,
            "qualitative_feedback": qualitative,
            "tone_detected": tone_results["detected_tone"],
            "terminology_deviations_count": term_results["terminology_deviations_count"],
            "avoided_words_count": term_results["avoided_words_count"],
            "suggestions": combined_suggestions
        }

    def analyze_and_update_draft(
        self,
        db: Session,
        draft: WritingDraft,
        profile: EditorialStyleProfile,
        override_content: Optional[str] = None
    ) -> StyleCheckResponse:
        """
        Runs style check on a WritingDraft, updates draft.style_score, draft.style_profile_id,
        and saves new style suggestions as WritingSuggestion records for interactive review.
        """
        content_to_check = override_content or draft.revised_content or draft.original_content

        analysis = self.analyze_text(content_to_check, profile)

        # Update draft
        draft.style_profile_id = profile.id
        draft.style_score = analysis["style_score"]

        # Persist suggestions as WritingSuggestion models (marking status='PENDING')
        persisted_suggestions: List[StyleSuggestionItem] = []
        for s in analysis["suggestions"]:
            sug_model = WritingSuggestion(
                draft_id=draft.id,
                category=s["category"],
                original_text=s["original_text"],
                suggested_rewrite=s["suggested_rewrite"],
                explanation=s["explanation"],
                severity=s.get("severity", "medium"),
                confidence=s.get("confidence", 0.9),
                reason=s.get("style_rule", "Editorial Style Rule"),
                status="pending"
            )
            db.add(sug_model)
            db.flush()

            persisted_suggestions.append(
                StyleSuggestionItem(
                    id=sug_model.id,
                    original_text=sug_model.original_text,
                    suggested_rewrite=sug_model.suggested_rewrite or "",
                    explanation=sug_model.explanation,
                    category=sug_model.category,
                    style_rule=sug_model.reason or "Style Rule",
                    severity=sug_model.severity,
                    confidence=sug_model.confidence,
                    status=sug_model.status
                )
            )

        db.commit()

        return StyleCheckResponse(
            draft_id=draft.id,
            style_profile_id=profile.id,
            style_profile_name=profile.name,
            style_score=analysis["style_score"],
            metrics=analysis["metrics"],
            qualitative_feedback=analysis["qualitative_feedback"],
            tone_detected=analysis["tone_detected"],
            terminology_deviations_count=analysis["terminology_deviations_count"],
            avoided_words_count=analysis["avoided_words_count"],
            suggestions=persisted_suggestions
        )

style_analyzer = StyleAnalyzer()
