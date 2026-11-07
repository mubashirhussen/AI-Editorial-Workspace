import re
from typing import Dict, Any

class ReadabilityService:
    """
    Computes Flesch Reading Ease and syllable metrics for text.
    Flesch Formula: 206.835 - 1.015 * (Total Words / Total Sentences) - 84.6 * (Total Syllables / Total Words)
    """

    def count_syllables_in_word(self, word: str) -> int:
        clean = re.sub(r'[^a-zA-Z]', '', word).lower()
        if not clean:
            return 0
        if len(clean) <= 3:
            return 1
        # Count vowel clusters
        vowels = "aeiouy"
        count = 0
        prev_is_vowel = False
        for char in clean:
            is_vowel = char in vowels
            if is_vowel and not prev_is_vowel:
                count += 1
            prev_is_vowel = is_vowel

        # Subtract silent 'e' at end
        if clean.endswith('e') and not clean.endswith('le') and count > 1:
            count -= 1
        return max(1, count)

    def calculate_flesch_reading_ease(self, total_words: int, total_sentences: int, total_syllables: int) -> float:
        if total_words == 0 or total_sentences == 0:
            return 100.0
        asl = total_words / total_sentences
        asw = total_syllables / total_words
        score = 206.835 - (1.015 * asl) - (84.6 * asw)
        return max(0.0, min(100.0, round(score, 1)))

    def calculate_flesch_kincaid_grade(self, total_words: int, total_sentences: int, total_syllables: int) -> float:
        if total_words == 0 or total_sentences == 0:
            return 0.0
        asl = total_words / total_sentences
        asw = total_syllables / total_words
        grade = (0.39 * asl) + (11.8 * asw) - 15.59
        return max(0.0, round(grade, 1))

    def calculate_automated_readability_index(self, total_characters: int, total_words: int, total_sentences: int) -> float:
        if total_words == 0 or total_sentences == 0:
            return 0.0
        ari = 4.71 * (total_characters / total_words) + 0.5 * (total_words / total_sentences) - 21.43
        return max(0.0, round(ari, 1))

    def calculate_gunning_fog(self, total_words: int, total_sentences: int, complex_words: int) -> float:
        if total_words == 0 or total_sentences == 0:
            return 0.0
        asl = total_words / total_sentences
        pct_complex = (complex_words / total_words) * 100.0
        fog = 0.4 * (asl + pct_complex)
        return max(0.0, round(fog, 1))

    def get_readability_interpretation(self, score: float) -> Dict[str, str]:
        """
        Interprets Flesch Reading Ease score:
        90-100: Very easy
        70-89: Easy
        60-69: Fairly easy
        30-59: Difficult
        0-29: Very difficult
        """
        if score >= 90:
            grade = "Very Easy"
            explanation = "Conversational and accessible to almost all readers."
        elif score >= 70:
            grade = "Easy"
            explanation = "Plain English; clear and engaging for general audiences."
        elif score >= 60:
            grade = "Fairly Easy"
            explanation = "Standard executive reading level; balanced professional prose."
        elif score >= 30:
            grade = "Difficult"
            explanation = "Dense academic or technical writing; requires focused reading."
        else:
            grade = "Very Difficult"
            explanation = "Highly convoluted or specialized prose; difficult to scan."

        return {
            "grade": grade,
            "explanation": explanation,
            "disclaimer": "Diagnostic scanning indicator, not a definitive measure of technical nuance or writing quality."
        }

readability_service = ReadabilityService()

