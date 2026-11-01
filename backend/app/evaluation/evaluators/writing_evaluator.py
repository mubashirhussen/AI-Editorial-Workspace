"""
Writing Assistant Evaluator.
Measures detection precision, recall, false positives, false negatives,
suggestion acceptance behavior, and original text preservation.
"""

from typing import Dict, Any, List
try:
    from backend.app.services.writing.writing_analyzer import (
        DeterministicWritingAnalyzer,
        writing_analyzer
    )
    from backend.app.evaluation.metrics.scoring import (
        calculate_precision_recall_f1,
        calculate_original_preservation_rate
    )
except ImportError:
    from app.services.writing.writing_analyzer import (
        DeterministicWritingAnalyzer,
        writing_analyzer
    )
    from app.evaluation.metrics.scoring import (
        calculate_precision_recall_f1,
        calculate_original_preservation_rate
    )

class WritingEvaluator:
    def __init__(self, analyzer: DeterministicWritingAnalyzer = None):
        self.analyzer = analyzer or writing_analyzer

    def evaluate_test_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs writing analysis on a test case and compares detected suggestions
        against expected defect categories.
        """
        text = case["text"]
        result = self.analyzer.analyze_text(text)

        issues = result.issues or []
        metrics = result.metrics
        expected_issues = case.get("expected_issues", {})

        # Count detected issues by type
        detected_types: Dict[str, int] = {}
        for iss in issues:
            cat = iss.category
            detected_types[cat] = detected_types.get(cat, 0) + 1

        # Evaluate Precision & Recall per category
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        # Mapping between dataset keys and analyzer issue categories
        key_map = {
            "long_sentences": "long_sentence",
            "passive_voice": "passive_voice",
            "filler_phrases": "filler",
            "jargon": "jargon",
            "repeated_expressions": "repetition",
            "complex_paragraphs": "complexity"
        }

        for exp_key, mapped_cat in key_map.items():
            exp_count = expected_issues.get(exp_key, 0)
            det_count = detected_types.get(mapped_cat, 0)

            tp = min(exp_count, det_count)
            fp = max(0, det_count - exp_count)
            fn = max(0, exp_count - det_count)

            true_positives += tp
            false_positives += fp
            false_negatives += fn

        # Edge case: control text with 0 expected issues
        if case.get("category") == "control":
            fp_control = len(issues)
            false_positives += fp_control
            prf = calculate_precision_recall_f1(0, fp_control, 0)
        else:
            prf = calculate_precision_recall_f1(true_positives, false_positives, false_negatives)

        # Suggestion Acceptance & Preservation Test
        preservation_rate = 1.0
        if issues:
            # Simulate accepting the first valid replacement suggestion
            first_iss = issues[0]
            orig_seg = getattr(first_iss, "original_text", "")
            repl = getattr(first_iss, "suggested_rewrite", "")
            
            if orig_seg and orig_seg in text and repl:
                modified_text = text.replace(orig_seg, repl, 1)
                other_words = [w for w in text.split() if w not in orig_seg.split()]
                if other_words:
                    preservation_rate = calculate_original_preservation_rate(modified_text, other_words[:5])

        passed = prf["precision"] >= 0.70 and prf["recall"] >= 0.70

        return {
            "case_id": case["id"],
            "title": case["title"],
            "category": case["category"],
            "passed": passed,
            "metrics": {
                "precision": prf["precision"],
                "recall": prf["recall"],
                "f1": prf["f1"],
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "detected_counts": detected_types,
                "original_preservation_rate": preservation_rate,
                "readability_score": getattr(metrics, "readability_score", None),
                "total_issues": len(issues)
            }
        }
