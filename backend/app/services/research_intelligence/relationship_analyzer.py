import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Explicit relational syntax patterns connecting two entities in a sentence
RELATION_PATTERNS = [
    # INVESTED_IN
    (
        "INVESTED_IN",
        r'(?i)\b(?:invested(?:\s+in)?|poured\s+\$[0-9]+|backed|funded|acquired\s+a\s+stake\s+in)\b',
        "{source} invested capital or financial resources into {target}."
    ),
    # ANNOUNCED
    (
        "ANNOUNCED",
        r'(?i)\b(?:announced|unveiled|revealed|introduced|published\s+details\s+of)\b',
        "{source} publicly announced {target}."
    ),
    # DEVELOPED
    (
        "DEVELOPED",
        r'(?i)\b(?:developed|engineered|built|trained|created|designed|manufactured)\b',
        "{source} developed or engineered {target}."
    ),
    # COMPETES_WITH
    (
        "COMPETES_WITH",
        r'(?i)\b(?:competes?\s+with|rivals?|challenges?|alternative\s+to|vies?\s+with|counter\s+to)\b',
        "{source} directly competes with {target} in the market."
    ),
    # USES
    (
        "USES",
        r'(?i)\b(?:uses|utilizes|deploys|integrates|powers|built\s+on\s+top\s+of|relies\s+on|adopts)\b',
        "{source} uses or integrates {target} as a core dependency."
    ),
]

class RelationshipAnalyzer:
    """
    Identifies high-confidence semantic relationships between extracted entities.
    Enforces the rule that co-occurrence alone is never sufficient to assert a relationship.
    """

    def analyze_relationships(
        self,
        claims: List[Dict[str, Any]],
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        relationships: List[Dict[str, Any]] = []
        seen_pairs = set()

        # Build quick normalized entity map
        entity_names = set(e["normalized_name"] for e in entities if "normalized_name" in e)

        for claim in claims:
            sentence = claim.get("supporting_excerpt", "") or claim.get("claim_text", "")
            if not sentence:
                continue

            # Find all entities appearing in this specific sentence
            present_entities = []
            for name in entity_names:
                pattern = r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])'
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    present_entities.append((name, match.start(), match.end()))

            # If fewer than 2 entities are present in this sentence, no relationship can be asserted from this sentence
            if len(present_entities) < 2:
                continue

            # Sort by appearance order
            present_entities.sort(key=lambda x: x[1])

            # Inspect pairs of entities in the sentence for explicit relational predicates
            for i in range(len(present_entities)):
                for j in range(i + 1, len(present_entities)):
                    ent1_name, s1, e1 = present_entities[i]
                    ent2_name, s2, e2 = present_entities[j]

                    if ent1_name.lower() == ent2_name.lower():
                        continue

                    # Slice text between the two entities
                    intervening_text = sentence[e1:s2].strip()

                    # Also inspect the full sentence if the entities are within 120 characters of each other
                    if len(intervening_text) > 150:
                        continue

                    for rel_type, pattern, expl_template in RELATION_PATTERNS:
                        if re.search(pattern, intervening_text) or re.search(pattern, sentence):
                            # Pair key to avoid duplicate identical edges
                            pair_key = (ent1_name, ent2_name, rel_type)
                            if pair_key in seen_pairs:
                                continue
                            seen_pairs.add(pair_key)

                            explanation = expl_template.format(source=ent1_name, target=ent2_name)

                            relationships.append({
                                "source_entity_name": ent1_name,
                                "target_entity_name": ent2_name,
                                "relationship_type": rel_type,
                                "source_id": claim.get("source_id"),
                                "source_title": claim.get("source_title"),
                                "supporting_evidence": sentence,
                                "confidence": 0.88,
                                "explanation": explanation
                            })
                            break

        return relationships

