import re
import logging
from typing import List, Dict, Any
from backend.app.utils.text_processing import split_into_sentences

logger = logging.getLogger(__name__)

COMMON_TECH_ACRONYMS = ["RAG", "GPU", "TPU", "LLM", "MoE", "API", "CUDA", "PUE", "SMR", "RLHF", "AGI"]

class ConsistencyChecker:
    """
    Evaluates sentence length limits, paragraph length constraints, and technical acronym consistency.
    """

    def check_consistency(
        self,
        text: str,
        max_sentence_length: int = 25,
        max_paragraph_length: int = 75
    ) -> Dict[str, Any]:
        if not text:
            return {
                "length_violations_count": 0,
                "paragraph_violations_count": 0,
                "acronym_deviations_count": 0,
                "suggestions": []
            }

        sentences = split_into_sentences(text)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        suggestions: List[Dict[str, Any]] = []
        length_violations = 0
        paragraph_violations = 0
        acronym_deviations = 0

        # 1. Sentence Length Violations
        for sentence in sentences:
            sentence_clean = sentence.strip()
            words = sentence_clean.split()
            word_count = len(words)

            if word_count > max_sentence_length:
                length_violations += 1
                # Suggest split point around midpoint conjunction or comma
                mid_point = word_count // 2
                first_half = " ".join(words[:mid_point])
                second_half = " ".join(words[mid_point:])
                rewrite_split = f"{first_half}. {second_half.capitalize()}"

                suggestions.append({
                    "original_text": sentence_clean,
                    "suggested_rewrite": rewrite_split,
                    "explanation": f"Sentence contains {word_count} words, exceeding the publication maximum limit of {max_sentence_length} words.",
                    "category": "style_sentence_length",
                    "style_rule": f"Sentence Length: Keep under {max_sentence_length} words",
                    "severity": "medium",
                    "confidence": 0.90
                })

        # 2. Paragraph Length Violations
        for para in paragraphs:
            words = para.split()
            p_len = len(words)
            if p_len > max_paragraph_length:
                paragraph_violations += 1
                suggestions.append({
                    "original_text": para[:120] + "...",
                    "suggested_rewrite": "[Split paragraph into two shorter sections]",
                    "explanation": f"Paragraph is {p_len} words, exceeding the {max_paragraph_length}-word maximum limit.",
                    "category": "style_paragraph_length",
                    "style_rule": f"Paragraph Length: Max {max_paragraph_length} words",
                    "severity": "low",
                    "confidence": 0.85
                })

        # 3. Technical Acronym Casing Consistency
        for acronym in COMMON_TECH_ACRONYMS:
            # E.g. "Gpu" or "gpu" or "Rag" instead of "RAG"
            casing_pattern = r'\b(' + re.escape(acronym.capitalize()) + r'|' + re.escape(acronym.lower()) + r')\b'
            for sentence in sentences:
                sentence_clean = sentence.strip()
                match = re.search(casing_pattern, sentence_clean)
                if match and match.group(0) != acronym:
                    acronym_deviations += 1
                    matched_str = match.group(0)
                    suggested_sentence = re.sub(casing_pattern, acronym, sentence_clean, count=1)
                    suggestions.append({
                        "original_text": sentence_clean,
                        "suggested_rewrite": suggested_sentence,
                        "explanation": f"Standardize technical acronym '{matched_str}' to uppercase '{acronym}'.",
                        "category": "style_consistency",
                        "style_rule": f"Acronym Consistency: Use '{acronym}'",
                        "severity": "low",
                        "confidence": 0.95
                    })

        return {
            "length_violations_count": length_violations,
            "paragraph_violations_count": paragraph_violations,
            "acronym_deviations_count": acronym_deviations,
            "suggestions": suggestions
        }

