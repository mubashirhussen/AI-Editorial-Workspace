"""
Scoring and Evaluation Metrics for AI Editorial Workspace.
Calculates deterministic and statistical quality metrics:
- Precision, Recall, F1 Score
- Source Validity Rate & Evidence Support Rate
- Word Count Compliance Rate
- Suggestion Acceptance Rate
- Original Preservation Rate
- Qualitative Rubric Aggregates
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import math

def calculate_precision_recall_f1(
    true_positives: int,
    false_positives: int,
    false_negatives: int
) -> Dict[str, float]:
    """
    Computes precision, recall, and harmonic F1 score.
    Returns 1.0 for edge cases where no positives are expected and none predicted.
    """
    if true_positives == 0 and false_positives == 0 and false_negatives == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }

def calculate_source_validity_rate(
    cited_source_ids: List[str],
    valid_source_ids: List[str]
) -> float:
    """
    Computes percentage of cited sources that exist in the valid project source list.
    """
    if not cited_source_ids:
        return 1.0 if not valid_source_ids else 0.0
    
    valid_set = set(valid_source_ids)
    valid_citations = sum(1 for sid in cited_source_ids if sid in valid_set)
    return round(valid_citations / len(cited_source_ids), 4)

def calculate_evidence_support_rate(
    citations: List[Dict[str, Any]],
    sources_text: Dict[str, str]
) -> float:
    """
    Checks what proportion of citations contain supporting excerpts that actually
    exist verbatim (or near-verbatim) within the cited source's text content.
    """
    if not citations:
        return 0.0

    supported = 0
    for cit in citations:
        sid = cit.get("source_id")
        excerpt = cit.get("supporting_quote") or cit.get("quote") or cit.get("excerpt") or ""
        if not excerpt:
            continue
        
        # Check against cited source text
        source_text = sources_text.get(sid, "")
        clean_excerpt = " ".join(excerpt.strip().lower().split())
        clean_source = " ".join(source_text.strip().lower().split())
        
        if clean_excerpt and clean_excerpt in clean_source:
            supported += 1
        elif clean_excerpt and len(clean_excerpt) > 20:
            # Check 80% substring overlap
            sub_chunk = clean_excerpt[:int(len(clean_excerpt) * 0.8)]
            if sub_chunk in clean_source:
                supported += 1

    return round(supported / len(citations), 4)

def calculate_word_count_compliance(
    text: str,
    min_words: int = 300,
    max_words: int = 500
) -> Dict[str, Any]:
    """
    Evaluates whether the editorial body complies with the target word count range.
    """
    words = text.split()
    count = len(words)
    compliant = min_words <= count <= max_words
    deviation = 0
    if count < min_words:
        deviation = min_words - count
    elif count > max_words:
        deviation = count - max_words

    return {
        "word_count": count,
        "min_target": min_words,
        "max_target": max_words,
        "is_compliant": compliant,
        "deviation_words": deviation
    }

def calculate_original_preservation_rate(
    original_text: str,
    unmodified_segments: List[str]
) -> float:
    """
    Verifies that text regions outside accepted suggestion replacement ranges
    remain strictly identical.
    """
    if not unmodified_segments:
        return 1.0
    
    matches = sum(1 for seg in unmodified_segments if seg in original_text)
    return round(matches / len(unmodified_segments), 4)

def evaluate_rubric_scores(
    scores: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculates weighted summary from 1-5 qualitative rubric scores:
    Dimensions:
    - headline_relevance (1-5)
    - structure_completeness (1-5)
    - fact_vs_analysis_distinction (1-5)
    - founder_implications (1-5)
    - writing_quality (1-5)
    """
    if not scores:
        return {"average_score": 0.0, "percentage": 0.0}
    
    total = sum(scores.values())
    count = len(scores)
    avg = total / count
    max_possible = count * 5
    pct = (total / max_possible) * 100

    return {
        "scores": scores,
        "average_score": round(avg, 2),
        "percentage": round(pct, 2),
        "passed": avg >= 3.5
    }

