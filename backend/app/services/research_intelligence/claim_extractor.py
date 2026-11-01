import re
import logging
from typing import List, Dict, Any, Optional
from backend.app.utils.text_processing import split_into_sentences
from backend.app.services.research_intelligence.entity_extractor import normalize_entity_name

logger = logging.getLogger(__name__)

# Linguistic classification patterns
REPORTED_BY_SOURCE_PATTERNS = [
    r'\baccording to\b',
    r'\breported that\b',
    r'\breports indicate\b',
    r'\bsources (?:familiar with|close to|say|claim|tell)\b',
    r'\bciting (?:people|sources|insiders)\b',
    r'\bstated in (?:a report|an interview|a blog post)\b',
    r'\bspokesperson (?:said|stated|told)\b',
    r'\bquoted as saying\b',
    r'\bnamed sources\b'
]

INFERENCE_PATTERNS = [
    r'\bsuggests?(?:\s+that)?\b',
    r'\bimplies?(?:\s+that)?\b',
    r'\bindicates?(?:\s+that|\s+a|\s+an|\s+the)?\b',
    r'\blikely (?:means|leads to|results in)\b',
    r'\bsignals?(?:\s+a)?\b',
    r'\bpoints? to\b',
    r'\bcould mean\b',
    r'\bmay reflect\b'
]

UNVERIFIED_PATTERNS = [
    r'\brumors?\b',
    r'\ballegedly\b',
    r'\bunconfirmed\b',
    r'\bspeculat(?:ed?|ion|ive)\b',
    r'\bwhispers\b',
    r'\bpurportedly\b',
    r'\bunverified\b',
    r'\bclaims without evidence\b'
]

DIRECT_STATEMENTS_PATTERNS = [
    r'\b(?:announced|released|launched|published|raised|invested|reported|achieved|surpassed|acquired)\b',
    r'\b\$[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|trillion|M|B)\b',
    r'\b[0-9]+(?:\.[0-9]+)?%\b'
]

class ClaimExtractor:
    """
    Extracts evidentiary claims with epistemic classification:
    DIRECTLY_STATED, REPORTED_BY_SOURCE, INFERENCE, UNVERIFIED.
    """

    def extract_claims(
        self,
        text: str,
        source_id: str,
        source_title: str,
        known_entities: Optional[List[Dict[str, Any]]] = None,
        publication_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not text:
            return []

        sentences = split_into_sentences(text)
        claims: List[Dict[str, Any]] = []

        entity_names = set()
        if known_entities:
            for ent in known_entities:
                entity_names.add(ent.get("name", "").lower())
                entity_names.add(ent.get("normalized_name", "").lower())

        for sentence in sentences:
            sentence_clean = sentence.strip()
            # Only consider substantive sentences with meaningful information
            if len(sentence_clean.split()) < 6 or len(sentence_clean) > 400:
                continue

            lower_sentence = sentence_clean.lower()

            # 1. Epistemic Classification Check
            classification = "DIRECTLY_STATED"
            confidence = 0.90

            if any(re.search(pat, lower_sentence) for pat in UNVERIFIED_PATTERNS):
                classification = "UNVERIFIED"
                confidence = 0.70
            elif any(re.search(pat, lower_sentence) for pat in INFERENCE_PATTERNS):
                classification = "INFERENCE"
                confidence = 0.80
            elif any(re.search(pat, lower_sentence) for pat in REPORTED_BY_SOURCE_PATTERNS):
                classification = "REPORTED_BY_SOURCE"
                confidence = 0.85
            elif any(re.search(pat, lower_sentence) for pat in DIRECT_STATEMENTS_PATTERNS):
                classification = "DIRECTLY_STATED"
                confidence = 0.95
            else:
                # Default informative statement
                classification = "DIRECTLY_STATED"
                confidence = 0.85

            # 2. Extract referenced entities in this claim
            matched_entities = []
            for name in entity_names:
                if name and re.search(r'\b' + re.escape(name) + r'\b', lower_sentence):
                    matched_entities.append(normalize_entity_name(name))

            # Deduplicate matched entities
            matched_entities = sorted(list(set(matched_entities)))

            # If the sentence contains substantive claims or numbers or entities or is classified as non-default, capture it
            has_substance = (
                bool(matched_entities)
                or classification in ("UNVERIFIED", "INFERENCE", "REPORTED_BY_SOURCE")
                or any(re.search(pat, lower_sentence) for pat in DIRECT_STATEMENTS_PATTERNS)
            )

            if has_substance:
                claims.append({
                    "source_id": source_id,
                    "source_title": source_title,
                    "claim_text": sentence_clean,
                    "supporting_excerpt": sentence_clean,
                    "evidence_classification": classification,
                    "entity_references": matched_entities,
                    "confidence": confidence,
                    "publication_date": publication_date
                })

        return claims
