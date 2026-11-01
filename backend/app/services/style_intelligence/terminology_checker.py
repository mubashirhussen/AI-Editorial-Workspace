import re
import logging
from typing import List, Dict, Any
from backend.app.utils.text_processing import split_into_sentences

logger = logging.getLogger(__name__)

DEFAULT_AVOIDED_TERMS = [
    "delve", "tapestry", "game-changer", "pivotal", "synergistic",
    "paradigm shift", "unrivaled", "best-in-class", "revolutionary"
]

class TerminologyChecker:
    """
    Validates terminology consistency and enforces publication-specific glossary mappings and forbidden word lists.
    """

    def check_terminology(
        self,
        text: str,
        preferred_terms: Dict[str, str],
        words_to_avoid: List[str]
    ) -> Dict[str, Any]:
        if not text:
            return {
                "terminology_deviations_count": 0,
                "avoided_words_count": 0,
                "suggestions": []
            }

        sentences = split_into_sentences(text)
        suggestions: List[Dict[str, Any]] = []
        deviations_count = 0
        avoided_count = 0

        # Combine configured words to avoid with sensible defaults if empty
        effective_avoid = list(set(words_to_avoid or DEFAULT_AVOIDED_TERMS))

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            # 1. Preferred Terminology Mapping
            for raw_term, preferred_term in preferred_terms.items():
                pattern = r'(?<![A-Za-z0-9_])' + re.escape(raw_term) + r'(?![A-Za-z0-9_])'
                match = re.search(pattern, sentence_clean, re.IGNORECASE)
                if match:
                    deviations_count += 1
                    matched_str = match.group(0)
                    suggested_sentence = re.sub(pattern, preferred_term, sentence_clean, count=1, flags=re.IGNORECASE)
                    suggestions.append({
                        "original_text": sentence_clean,
                        "suggested_rewrite": suggested_sentence,
                        "explanation": f"Publication style prefers '{preferred_term}' instead of '{matched_str}'.",
                        "category": "style_terminology",
                        "style_rule": f"Terminology: Use '{preferred_term}'",
                        "severity": "medium",
                        "confidence": 0.95
                    })

            # 2. Words and Phrases to Avoid
            for avoid_term in effective_avoid:
                pattern = r'(?<![A-Za-z0-9_])' + re.escape(avoid_term) + r'(?![A-Za-z0-9_])'
                match = re.search(pattern, sentence_clean, re.IGNORECASE)
                if match:
                    avoided_count += 1
                    matched_str = match.group(0)
                    suggestions.append({
                        "original_text": sentence_clean,
                        "suggested_rewrite": f"[Remove or rephrase '{matched_str}']",
                        "explanation": f"'{matched_str}' is explicitly forbidden by publication editorial guidelines.",
                        "category": "style_avoided_phrase",
                        "style_rule": f"Avoid Forbidden Term: '{avoid_term}'",
                        "severity": "high",
                        "confidence": 0.95
                    })

        return {
            "terminology_deviations_count": deviations_count,
            "avoided_words_count": avoided_count,
            "suggestions": suggestions
        }

