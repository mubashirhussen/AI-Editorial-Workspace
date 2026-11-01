import logging
from typing import Dict, Any, Tuple
from backend.app.utils.text_processing import calculate_reading_ease, split_into_sentences

logger = logging.getLogger(__name__)

class StyleScorer:
    """
    Computes a composite Style Compliance Score (0-100) based on sentence length compliance,
    terminology adherence, tone alignment, and Flesch reading ease target proximity.
    """

    def compute_score(
        self,
        text: str,
        target_flesch_score: float,
        length_violations: int,
        total_sentences: int,
        terminology_deviations: int,
        avoided_words: int,
        promotional_count: int,
        informal_count: int
    ) -> Tuple[float, Dict[str, Any], str]:
        if not text or total_sentences == 0:
            return 100.0, {
                "sentence_length_score": 100.0,
                "terminology_score": 100.0,
                "tone_score": 100.0,
                "readability_score": 100.0
            }, "Empty draft."

        # 1. Sentence Length Score (0 - 100)
        # Proportion of sentences complying with length threshold
        compliant_sentences = max(0, total_sentences - length_violations)
        sentence_length_score = round((compliant_sentences / total_sentences) * 100, 1)

        # 2. Terminology Adherence Score (0 - 100)
        # Penalty of 8 points per avoided word, 4 points per unstandardized deviation
        term_penalties = (avoided_words * 8) + (terminology_deviations * 4)
        terminology_score = max(0.0, round(100.0 - term_penalties, 1))

        # 3. Tone Consistency Score (0 - 100)
        # Penalty of 10 points per promotional buzzword, 5 points per informal word
        tone_penalties = (promotional_count * 10) + (informal_count * 5)
        tone_score = max(0.0, round(100.0 - tone_penalties, 1))

        # 4. Readability Score vs Target (0 - 100)
        actual_flesch, _ = calculate_reading_ease(text)
        flesch_delta = abs(actual_flesch - target_flesch_score)
        # 100 points if within 5 points of target, decays with larger distance
        readability_score = max(20.0, round(100.0 - (flesch_delta * 1.5), 1))

        # 5. Composite Weighted Score
        # Sentence Length: 30%, Terminology: 25%, Tone: 25%, Readability: 20%
        overall_score = round(
            (sentence_length_score * 0.30) +
            (terminology_score * 0.25) +
            (tone_score * 0.25) +
            (readability_score * 0.20),
            1
        )
        overall_score = max(0.0, min(100.0, overall_score))

        # Qualitative appraisal
        if overall_score >= 88.0:
            qualitative = "Strong adherence to publication editorial style guidelines. Copy is analytical and concise."
        elif overall_score >= 70.0:
            qualitative = "Acceptable editorial baseline with minor stylistic adjustments required for terminology and sentence length."
        elif overall_score >= 50.0:
            qualitative = "Significant style deviations detected. Review flagged promotional expressions, length violations, and non-standard terms."
        else:
            qualitative = "Low style compliance. Major revision required to align with publication tone and length constraints."

        metrics = {
            "sentence_length_score": sentence_length_score,
            "terminology_score": terminology_score,
            "tone_score": tone_score,
            "readability_score": readability_score,
            "actual_flesch_reading_ease": actual_flesch,
            "target_flesch_reading_ease": target_flesch_score
        }

        return overall_score, metrics, qualitative

