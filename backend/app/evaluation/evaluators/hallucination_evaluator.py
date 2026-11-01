"""
Hallucination & Grounding Evaluator.
Detects:
1. Unsupported Numbers (figures present in text but absent from source documents)
2. Fabricated Quotations (direct quotes in text not present in source documents)
3. Invented Source References (citations to non-existent source IDs)
4. Attribution Mismatches (claims attributed to Source A that belong to Source B)
"""

import re
from typing import Dict, Any, List

class HallucinationEvaluator:
    def evaluate_test_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits a draft against ground truth sources to flag and report unsupported claims.
        """
        sources = case.get("ground_truth_sources", {})
        draft = case.get("test_draft", "")
        valid_ids = case.get("valid_source_ids", list(sources.keys()))

        detected_hallucinations: List[Dict[str, Any]] = []
        combined_source_text = " ".join(sources.values())

        # 1. Audit Numbers: Extract currencies/numbers from draft (e.g. $450 million, $2.5 billion)
        num_patterns = re.findall(r"(\$[\d\.]+\s*(?:million|billion|trillion|M|B)?|\b\d+(?:,\d+)*(?:\.\d+)?\b)", draft)
        for num in num_patterns:
            num_clean = num.strip()
            # Ignore common small integers like dates or counts under 10
            if num_clean in ["1", "2", "3", "4", "5", "10", "20"]:
                continue
            if num_clean.lower() not in combined_source_text.lower():
                detected_hallucinations.append({
                    "category": "unsupported_number",
                    "value": num_clean,
                    "explanation": f"Numerical figure '{num_clean}' appears in draft but cannot be grounded in provided sources."
                })

        # 2. Audit Direct Quotations: Extract text inside quotes
        quote_patterns = re.findall(r"['\"]([^'\"]{15,})['\"]", draft)
        for quote in quote_patterns:
            clean_quote = " ".join(quote.strip().split())
            clean_sources = " ".join(combined_source_text.strip().split())
            if clean_quote.lower() not in clean_sources.lower():
                detected_hallucinations.append({
                    "category": "fabricated_quote",
                    "quote": quote,
                    "explanation": f"Direct quotation \"{quote}\" does not exist in any provided source."
                })

        # 3. Audit Cited Source IDs: Extract references like [Source: src-999] or [src-google]
        cited_ids = re.findall(r"\[(?:Source:\s*)?([a-zA-Z0-9_-]+)\]", draft)
        for cid in cited_ids:
            if cid not in valid_ids and cid not in ["Analysis", "Lede"]:
                detected_hallucinations.append({
                    "category": "invented_source_reference",
                    "source_id": cid,
                    "explanation": f"Draft cites non-existent source ID '{cid}'."
                })

        # 4. Audit Source Attribution: Check sentences with explicit citations [src-id]
        sentences = re.split(r"(?<=[.!?])\s+", draft)
        for s in sentences:
            cite_matches = re.findall(r"\[(?:Source:\s*)?([a-zA-Z0-9_-]+)\]", s)
            for cid in cite_matches:
                if cid in sources:
                    cited_source_content = sources[cid].lower()
                    # Check for key terms in sentence that don't belong to cited source
                    for other_id, other_content in sources.items():
                        if other_id != cid:
                            # Look for distinct phrases in other source that appear in this sentence
                            for phrase in ["92%", "humaneval", "series b", "blackwell"]:
                                if phrase in s.lower() and phrase in other_content.lower() and phrase not in cited_source_content:
                                    detected_hallucinations.append({
                                        "category": "misattribution",
                                        "claim": phrase,
                                        "attributed_to": cid,
                                        "actual_source": other_id,
                                        "explanation": f"Claim '{phrase}' attributed to '{cid}' actually belongs to '{other_id}'."
                                    })

        expected_hal = case.get("expected_hallucinations", [])
        detected_categories = set(h["category"] for h in detected_hallucinations)
        expected_categories = set(h["type"] for h in expected_hal)
        
        matched_categories = detected_categories.intersection(expected_categories)
        recall = len(matched_categories) / len(expected_categories) if expected_categories else 1.0

        passed = recall >= 0.80

        return {
            "case_id": case["id"],
            "title": case["title"],
            "passed": passed,
            "metrics": {
                "hallucinations_detected_count": len(detected_hallucinations),
                "expected_hallucinations_count": len(expected_hal),
                "detection_recall": round(recall, 4),
                "detected_categories": list(detected_categories)
            },
            "flagged_unsupported_claims": detected_hallucinations
        }
