import re
from typing import Dict, Any, Optional
from backend.app.schemas.writing import WritingMetrics
from backend.app.services.writing.readability_service import readability_service
from backend.app.utils.text_processing import split_into_sentences

class WritingMetricsService:
    """
    Computes text length, cadence, reading duration, and reading ease metrics.
    """

    def calculate_metrics(self, text: str) -> WritingMetrics:
        clean_text = (text or "").strip()
        if not clean_text:
            return WritingMetrics(
                word_count=0,
                character_count=0,
                sentence_count=0,
                paragraph_count=0,
                average_sentence_length=0.0,
                reading_time_minutes=0.0,
                readability_score=100.0,
                readability_grade="Very Easy",
                readability_note="Readability scores are diagnostic scanning indicators, not definitive measures of technical nuance or writing quality."
            )

        words = re.findall(r"\b[a-zA-Z0-9'-]+\b", clean_text)
        word_count = len(words)

        sentences = split_into_sentences(clean_text)
        sentence_count = max(1, len([s for s in sentences if s.strip()]))

        paragraphs = [p for p in clean_text.split("\n\n") if p.strip()]
        paragraph_count = max(1, len(paragraphs))

        asl = round(word_count / sentence_count, 1)
        reading_time = round(word_count / 225.0, 1)

        total_syllables = sum(readability_service.count_syllables_in_word(w) for w in words)
        complex_words = sum(1 for w in words if readability_service.count_syllables_in_word(w) >= 3)
        letters_count = sum(len(w) for w in words)

        flesch_score = readability_service.calculate_flesch_reading_ease(word_count, sentence_count, total_syllables)
        fk_grade = readability_service.calculate_flesch_kincaid_grade(word_count, sentence_count, total_syllables)
        ari = readability_service.calculate_automated_readability_index(letters_count, word_count, sentence_count)
        gunning_fog = readability_service.calculate_gunning_fog(word_count, sentence_count, complex_words)
        interp = readability_service.get_readability_interpretation(flesch_score)

        return WritingMetrics(
            word_count=word_count,
            character_count=len(clean_text),
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            average_sentence_length=asl,
            reading_time_minutes=reading_time,
            readability_score=flesch_score,
            readability_grade=interp["grade"],
            flesch_kincaid_grade=fk_grade,
            automated_readability_index=ari,
            gunning_fog_index=gunning_fog,
            readability_note=f"Readability score is a diagnostic heuristic scanning indicator ({interp['grade']}). {interp['explanation']} It is not a definitive measure of technical nuance or writing quality."
        )

metrics_service = WritingMetricsService()

