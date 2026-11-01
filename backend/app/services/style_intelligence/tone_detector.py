import re
import logging
from typing import List, Dict, Any, Tuple
from backend.app.utils.text_processing import split_into_sentences

logger = logging.getLogger(__name__)

PROMOTIONAL_HYPE_PATTERNS = [
    (r'\bgame-?changers?\b', 'an impactful development', 'Replace sensationalist idiom with factual description.'),
    (r'\brevolutionar(?:y|ize|ized)\b', 'substantial', 'Avoid promotional hyperbole; describe actual technical change.'),
    (r'\bunrivaled\b', 'competitive', 'Avoid unverified superlative claim.'),
    (r'\bbest-in-class\b', 'high-performing', 'Replace marketing buzzword with objective performance terminology.'),
    (r'\bunprecedented miracle\b', 'significant milestone', 'Remove melodramatic phrasing.'),
    (r'\bmind-?blowing\b', 'notable', 'Replace sensationalism with measured analytical tone.'),
    (r'\bjaw-?dropping\b', 'unexpected', 'Maintain professional journalistic equipoise.'),
    (r'\bsilver bullet\b', 'complete solution', 'Replace overused promotional trope with direct terminology.'),
    (r'\bgroundbreaking breakthrough\b', 'technical advancement', 'Dampen redundant hype rhetoric.'),
    (r'\bparadigm shift\b', 'structural change', 'Replace overused corporate buzzword with concrete description.'),
    (r'\bskyrocketed\b', 'increased substantially', 'Quantify or describe trajectory neutrally rather than using emotive verbs.'),
]

INFORMAL_PATTERNS = [
    (r'\bgonna\b', 'going to', 'Use standard formal register.'),
    (r'\bwanna\b', 'want to', 'Use standard formal register.'),
    (r'\bcrazy good\b', 'exceptionally effective', 'Elevate casual conversational idiom.'),
    (r'\btons of\b', 'numerous', 'Replace imprecise colloquialism with measured quantifier.'),
    (r'\bsuper (?:fast|cool|smart)\b', 'highly efficient', 'Avoid juvenile intensifier in technical editorial copy.'),
    (r'\ba bunch of\b', 'several', 'Use precise editorial diction.'),
    (r'\bno-?brainer\b', 'straightforward decision', 'Replace casual idiom with professional prose.')
]

class ToneDetector:
    """
    Evaluates tone consistency and flags marketing hype, sensationalism, and informal colloquialisms.
    """

    def analyze_tone(self, text: str, target_tone: str = "Authoritative, analytical, objective") -> Dict[str, Any]:
        if not text:
            return {
                "detected_tone": "Neutral",
                "promotional_count": 0,
                "informal_count": 0,
                "suggestions": []
            }

        sentences = split_into_sentences(text)
        suggestions: List[Dict[str, Any]] = []
        promotional_count = 0
        informal_count = 0

        for sentence in sentences:
            sentence_clean = sentence.strip()
            if not sentence_clean:
                continue

            # Check promotional hype
            for pattern, rewrite_sub, explanation in PROMOTIONAL_HYPE_PATTERNS:
                match = re.search(pattern, sentence_clean, re.IGNORECASE)
                if match:
                    promotional_count += 1
                    matched_str = match.group(0)
                    suggested_sentence = re.sub(pattern, rewrite_sub, sentence_clean, count=1, flags=re.IGNORECASE)
                    suggestions.append({
                        "original_text": sentence_clean,
                        "suggested_rewrite": suggested_sentence,
                        "explanation": f"{explanation} Avoid '{matched_str}'.",
                        "category": "style_promotional_hype",
                        "style_rule": "Tone: Avoid promotional hyperbole & buzzwords",
                        "severity": "high",
                        "confidence": 0.95
                    })

            # Check informal expressions
            for pattern, rewrite_sub, explanation in INFORMAL_PATTERNS:
                match = re.search(pattern, sentence_clean, re.IGNORECASE)
                if match:
                    informal_count += 1
                    matched_str = match.group(0)
                    suggested_sentence = re.sub(pattern, rewrite_sub, sentence_clean, count=1, flags=re.IGNORECASE)
                    suggestions.append({
                        "original_text": sentence_clean,
                        "suggested_rewrite": suggested_sentence,
                        "explanation": f"{explanation} Replace colloquialism '{matched_str}'.",
                        "category": "style_tone",
                        "style_rule": "Tone: Maintain authoritative, professional register",
                        "severity": "medium",
                        "confidence": 0.90
                    })

        # Tone categorization
        if promotional_count >= 2:
            detected_tone = "Overly Promotional / Marketing Hype"
        elif informal_count >= 2:
            detected_tone = "Informal / Conversational"
        elif promotional_count == 0 and informal_count == 0:
            detected_tone = "Authoritative & Analytical"
        else:
            detected_tone = "Mostly Analytical with Minor Stylistic Inconsistencies"

        return {
            "detected_tone": detected_tone,
            "promotional_count": promotional_count,
            "informal_count": informal_count,
            "suggestions": suggestions
        }

