import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContradictionDetector:
    """
    Detects cross-source discrepancies and contradictory claims across different sources.
    Crucially maintains journalistic neutrality and never decides which source is correct.
    """

    def detect_contradictions(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        contradictions: List[Dict[str, Any]] = []
        if len(claims) < 2:
            return []

        # Compare claim pairs from different sources
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                c1 = claims[i]
                c2 = claims[j]

                # Only compare claims from different sources
                if c1.get("source_id") == c2.get("source_id"):
                    continue

                text1 = c1.get("claim_text", "")
                text2 = c2.get("claim_text", "")

                # Must share at least one common entity or subject to be contradictory
                shared_entities = set(c1.get("entity_references", [])) & set(c2.get("entity_references", []))
                if not shared_entities:
                    continue

                common_entity = list(shared_entities)[0]

                # 1. Financial / Valuation Discrepancy
                m1_money = re.findall(r'\$([0-9]+(?:\.[0-9]+)?\s*(?:million|billion|M|B))', text1, re.I)
                m2_money = re.findall(r'\$([0-9]+(?:\.[0-9]+)?\s*(?:million|billion|M|B))', text2, re.I)
                if m1_money and m2_money and m1_money[0].strip().lower() != m2_money[0].strip().lower():
                    # Check if both sentences discuss funding/investment/valuation
                    if any(w in text1.lower() for w in ["raised", "valuation", "funding", "invested", "round"]) and \
                       any(w in text2.lower() for w in ["raised", "valuation", "funding", "invested", "round"]):
                        contradictions.append({
                            "claim_a_id": c1.get("id"),
                            "claim_b_id": c2.get("id"),
                            "source_a_id": c1.get("source_id"),
                            "source_b_id": c2.get("source_id"),
                            "source_a_title": c1.get("source_title", "Source A"),
                            "source_b_title": c2.get("source_title", "Source B"),
                            "claim_a_text": text1,
                            "claim_b_text": text2,
                            "disagreement_nature": f"Discrepancy in reported funding or capital figure for {common_entity} (${m1_money[0]} vs ${m2_money[0]}).",
                            "possible_explanations": "Source A may refer to an initial commitment or pre-money valuation, while Source B may reflect post-money total or final tranches.",
                            "unresolved_questions": f"What was the officially filed SEC Form D or corporate statement confirming the finalized financing amount for {common_entity}?"
                        })
                        continue

                # 2. Timeline / Launch Date Discrepancy
                dates1 = re.findall(r'\b(Q[1-4]\s*202[4-9]|202[4-9]|early\s*202[4-9]|late\s*202[4-9]|mid\s*202[4-9])\b', text1, re.I)
                dates2 = re.findall(r'\b(Q[1-4]\s*202[4-9]|202[4-9]|early\s*202[4-9]|late\s*202[4-9]|mid\s*202[4-9])\b', text2, re.I)
                if dates1 and dates2 and dates1[0].strip().lower() != dates2[0].strip().lower():
                    if any(w in text1.lower() for w in ["launch", "release", "ship", "available", "deploy", "rollout"]) and \
                       any(w in text2.lower() for w in ["launch", "release", "ship", "available", "deploy", "rollout"]):
                        contradictions.append({
                            "claim_a_id": c1.get("id"),
                            "claim_b_id": c2.get("id"),
                            "source_a_id": c1.get("source_id"),
                            "source_b_id": c2.get("source_id"),
                            "source_a_title": c1.get("source_title", "Source A"),
                            "source_b_title": c2.get("source_title", "Source B"),
                            "claim_a_text": text1,
                            "claim_b_text": text2,
                            "disagreement_nature": f"Conflicting deployment or launch timeline for {common_entity} ({dates1[0]} vs {dates2[0]}).",
                            "possible_explanations": "Timeline estimates may represent different development phases (internal preview vs general availability) or deliberate roadmap adjustments.",
                            "unresolved_questions": f"Which date corresponds to the public production release milestone for {common_entity}?"
                        })
                        continue

                # 3. Direct Performance / Benchmark Polarity Conflict
                pos_polarity = ["outperformed", "surpassed", "exceeded", "higher than", "superior", "won"]
                neg_polarity = ["trailed", "lagged", "fell short", "lower than", "inferior", "failed"]

                c1_pos = any(w in text1.lower() for w in pos_polarity)
                c1_neg = any(w in text1.lower() for w in neg_polarity)
                c2_pos = any(w in text2.lower() for w in pos_polarity)
                c2_neg = any(w in text2.lower() for w in neg_polarity)

                if (c1_pos and c2_neg) or (c1_neg and c2_pos):
                    contradictions.append({
                        "claim_a_id": c1.get("id"),
                        "claim_b_id": c2.get("id"),
                        "source_a_id": c1.get("source_id"),
                        "source_b_id": c2.get("source_id"),
                        "source_a_title": c1.get("source_title", "Source A"),
                        "source_b_title": c2.get("source_title", "Source B"),
                        "claim_a_text": text1,
                        "claim_b_text": text2,
                        "disagreement_nature": f"Contradictory benchmark evaluations or performance assessments regarding {common_entity}.",
                        "possible_explanations": "Evaluations may have employed disparate benchmark suites, differing prompt techniques, or unstandardized evaluation environments.",
                        "unresolved_questions": f"Were the benchmark results produced under identical hardware, temperature, and eval parameters?"
                    })

        return contradictions

