import re
import uuid
from typing import List, Dict, Any, Optional
from backend.app.schemas.writing import WritingIssue, WritingAnalysisResponse
from backend.app.services.writing.metrics_service import metrics_service
from backend.app.utils.text_processing import split_into_sentences
from backend.app.services.ai_service import ai_service

# Configurable Filler Dictionary
FILLER_PATTERNS = [
    (r"\bin order to\b", "to", "Wordy prepositional opener; 'to' is direct and punchy."),
    (r"\bdue to the fact that\b", "because", "Cluttered causal phrase; replace with 'because'."),
    (r"\bit is important to note that\b", "", "Meta-commentary delays the point. State the fact directly."),
    (r"\bat the end of the day\b", "ultimately", "Cliché editorial filler. Replace with 'ultimately'."),
    (r"\bneedless to say\b", "", "If it is needless to say, omit the clause."),
    (r"\bhas the ability to\b", "can", "Wordy verbal phrase; replace with 'can'."),
    (r"\bbasically\b", "", "Informal conversational filler; omit to strengthen analytical tone."),
    (r"\bactually\b", "", "Hedge filler that weakens authoritative tone; omit unless contrasting a misconception."),
    (r"\bvery\b", "", "Vague intensifier; use a more specific verb or adjective."),
    (r"\breally\b", "", "Informal conversational hedge; omit.")
]

# Configurable Jargon Glossary
JARGON_PATTERNS = [
    (r"\bretrieval-augmented generation\b", "grounded document search", "Technical jargon; define for general editorial readership."),
    (r"\bembeddings?\b", "vector representations", "Technical AI term; define context for executive audience."),
    (r"\bvector database\b", "specialized search database", "Specialized database term; clarify practical function."),
    (r"\bagentic workflow\b", "autonomous AI process", "Emerging AI buzzword; describe explicit system behavior."),
    (r"\bparadigm shift\b", "fundamental change", "Corporate buzzword; explain the actual mechanical or structural shift."),
    (r"\bsynergy\b", "cooperation", "Business cliché; specify how components collaborate."),
    (r"\bleverage\b", "use", "Overused verb; specify 'use', 'apply', or 'build upon'."),
    (r"\bdisruptive innovation\b", "breakthrough", "Overused market buzzword; specify the direct breakthrough."),
    (r"\bscalability\b", "ability to handle growth", "Technical jargon; contextualize for executive and mixed leadership."),
    (r"\becosystem\b", "platform network", "Vague metaphorical term; name the specific tools, libraries, or network."),
    (r"\binfrastructure\b", "systems hardware", "Broad category; clarify compute, networking, or database layers.")
]

class DeterministicWritingAnalyzer:
    """
    Executes 6 deterministic writing quality checks and integrates with AI suggestions.
    """

    def analyze_text(self, text: str, draft_id: Optional[str] = None) -> WritingAnalysisResponse:
        clean_text = (text or "").strip()
        metrics = metrics_service.calculate_metrics(clean_text)
        issues: List[WritingIssue] = []

        if not clean_text:
            return WritingAnalysisResponse(
                draft_id=draft_id,
                overall_feedback="Draft is empty. Add article copy to begin writing quality analysis.",
                issues=[],
                metrics=metrics
            )

        sentences = split_into_sentences(clean_text)

        # CHECK 1: Long Sentences (>25 words)
        for s in sentences:
            words = re.findall(r"\b[a-zA-Z0-9'-]+\b", s)
            if len(words) > 25:
                # Provide split suggestion
                clauses = re.split(r",\s*(?:and|which|while|but|because)\s*", s, maxsplit=1)
                suggested = s
                if len(clauses) == 2:
                    suggested = f"{clauses[0].strip()}. Furthermore, {clauses[1].strip()}"

                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="long_sentence",
                    severity="high" if len(words) > 35 else "medium",
                    original_text=s,
                    explanation=f"Sentence contains {len(words)} words (exceeds 25-word threshold). Long sentences induce cognitive fatigue.",
                    suggested_rewrite=suggested,
                    reason=f"Word count: {len(words)} words.",
                    confidence=0.95
                ))

        # CHECK 2: Passive Voice
        passive_regex = re.compile(r"\b(is|are|was|were|been|being|be)\s+([a-zA-Z]+ed|developed|conducted|published|announced|measured|evaluated)\b", re.IGNORECASE)
        for s in sentences:
            for match in passive_regex.finditer(s):
                phrase = match.group(0)
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="passive_voice",
                    severity="medium",
                    original_text=phrase,
                    explanation=f"Passive construction '{phrase}' obscures the acting entity. Rephrase actively.",
                    suggested_rewrite=f"the team {match.group(2)}",
                    reason="Active voice attributes accountability directly to the subject.",
                    confidence=0.88
                ))

        # CHECK 3: Filler Words & Phrases
        for pattern, replacement, explanation in FILLER_PATTERNS:
            for match in re.finditer(pattern, clean_text, re.IGNORECASE):
                phrase = match.group(0)
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="filler",
                    severity="medium" if replacement else "low",
                    original_text=phrase,
                    explanation=explanation,
                    suggested_rewrite=replacement if replacement else "(remove filler)",
                    reason="Conciseness audit.",
                    confidence=0.92
                ))

        # CHECK 4: Technical & Business Jargon
        for pattern, replacement, explanation in JARGON_PATTERNS:
            for match in re.finditer(pattern, clean_text, re.IGNORECASE):
                phrase = match.group(0)
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="jargon",
                    severity="low",
                    original_text=phrase,
                    explanation=explanation,
                    suggested_rewrite=replacement,
                    reason="Jargon accessibility check.",
                    confidence=0.85
                ))

        # CHECK 5: Repetition in Nearby Sentences
        prev_first_words = []
        prev_two_words = []
        for s in sentences:
            clean_s = s.strip()
            words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9'-]+\b", clean_s)]
            if not words:
                continue
            first_word = words[0]
            two_words = f"{words[0]} {words[1]}" if len(words) >= 2 else ""

            is_repeat = False
            if first_word in prev_first_words and len(first_word) > 3 and first_word not in {"this", "that", "there", "these"}:
                is_repeat = True
            elif two_words and two_words in prev_two_words:
                is_repeat = True

            if is_repeat:
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="repetition",
                    severity="medium",
                    original_text=clean_s,
                    explanation=f"Repeated sentence opening ('{first_word.capitalize()}'). Vary sentence openings to improve rhythm and flow.",
                    suggested_rewrite=f"Furthermore, {clean_s}",
                    reason="Rhythm and variety check.",
                    confidence=0.85
                ))

            prev_first_words.append(first_word)
            if len(prev_first_words) > 3:
                prev_first_words.pop(0)

            if two_words:
                prev_two_words.append(two_words)
                if len(prev_two_words) > 3:
                    prev_two_words.pop(0)

        # CHECK 6: Complex Paragraph Detection
        paragraphs = [p for p in clean_text.split("\n\n") if p.strip()]
        for p in paragraphs:
            p_sentences = split_into_sentences(p)
            p_words = re.findall(r"\b[a-zA-Z0-9'-]+\b", p)
            if len(p_sentences) >= 5 or len(p_words) > 100:
                issues.append(WritingIssue(
                    id=str(uuid.uuid4()),
                    category="complexity",
                    severity="medium",
                    original_text=p[:120] + "...",
                    explanation=f"Paragraph is dense ({len(p_words)} words across {len(p_sentences)} sentences). Break into smaller digestible units.",
                    suggested_rewrite="Consider splitting this paragraph into two distinct focus points.",
                    reason="Paragraph scanability audit.",
                    confidence=0.80
                ))

        overall_feedback = (
            f"Audited {metrics.word_count} words across {metrics.sentence_count} sentences. "
            f"Flesch Reading Ease is {metrics.readability_score} ({metrics.readability_grade}). "
            f"Identified {len(issues)} structural improvement opportunities."
        )

        return WritingAnalysisResponse(
            draft_id=draft_id,
            overall_feedback=overall_feedback,
            issues=issues,
            metrics=metrics
        )

writing_analyzer = DeterministicWritingAnalyzer()
