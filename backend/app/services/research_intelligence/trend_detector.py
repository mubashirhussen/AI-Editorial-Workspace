import re
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Categories and trigger keyword sets for trend discovery
TREND_CATEGORIES = {
    "EMERGING_TECHNOLOGY": [
        "immersion cooling", "liquid cooling", "two-phase", "small modular reactor", "smr",
        "mixture of experts", "moe", "rag", "retrieval-augmented", "lora", "hbm3e", "hbm4",
        "flashattention", "inference optimization", "agentic", "synthetic data"
    ],
    "MARKET_DEVELOPMENT": [
        "capex", "hyperscaler", "datacenter capacity", "power constraints", "grid bottleneck",
        "megawatt", "cluster scaling", "consolidation", "enterprise spending", "sovereign ai"
    ],
    "DEVELOPER_ADOPTION": [
        "open source", "developer adoption", "hugging face downloads", "github stars",
        "api usage", "developer ecosystem", "sdk integration", "tooling"
    ],
    "FUNDING_PATTERN": [
        "seed round", "series a", "series b", "series c", "raised", "venture funding",
        "valuation", "valuation surge", "billion valuation", "sovereign wealth"
    ],
    "PRODUCT_LAUNCH": [
        "general availability", "preview release", "shipped", "rollout", "commercial release",
        "model launch", "flagship release"
    ],
    "REPEATED_ANNOUNCEMENT": [
        "partnership", "collaboration", "strategic alliance", "joint venture", "multi-year agreement"
    ]
}

PREDICTION_MARKERS = [
    r'\bpredict(?:s|ed|ing|ion)?\b',
    r'\bforecast(?:s|ed|ing)?\b',
    r'\bproject(?:ed|ing|ion)?\s+to\b',
    r'\bby\s+202[7-9]\b',
    r'\bby\s+203[0-9]\b',
    r'\bexpected\s+to\s+reach\b',
    r'\bwill\s+likely\s+grow\b'
]

class TrendDetector:
    """
    Discovers recurring patterns across multiple sources.
    Enforces the strict threshold that at least 2 distinct sources must corroborate a trend.
    Distinguishes observed historical patterns from speculative forward-looking predictions.
    """

    def detect_trends(
        self,
        claims: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Map source_id to source_title
        source_title_map = {s["id"]: s.get("title", f"Source {s['id']}") for s in sources}

        # Cluster claims by matching keyword concepts
        # concept -> { "category": cat, "source_ids": set(), "evidence": [] }
        clusters: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "source_ids": set(),
            "evidence": [],
            "category": "MARKET_DEVELOPMENT"
        })

        for claim in claims:
            text = claim.get("claim_text", "")
            src_id = claim.get("source_id")
            if not text or not src_id:
                continue

            lower_text = text.lower()

            for cat, keywords in TREND_CATEGORIES.items():
                for kw in keywords:
                    if kw in lower_text:
                        cluster_name = kw.title()
                        clusters[cluster_name]["category"] = cat
                        clusters[cluster_name]["source_ids"].add(src_id)
                        clusters[cluster_name]["evidence"].append(text)

        trends: List[Dict[str, Any]] = []

        # Only retain clusters corroborated by >= 2 distinct sources
        for theme_name, data in clusters.items():
            distinct_source_ids = list(data["source_ids"])
            if len(distinct_source_ids) < 2:
                # Does not meet cross-source corroboration threshold!
                continue

            # Determine whether this trend is an observed pattern or a forward prediction
            combined_evidence = " ".join(data["evidence"])
            is_prediction = any(re.search(pat, combined_evidence, re.IGNORECASE) for pat in PREDICTION_MARKERS)

            # Produce concise evidence summary from representative claim sentences
            summary_sentences = data["evidence"][:2]
            evidence_summary = " Cross-source corroboration: " + " ".join(summary_sentences)

            src_titles = [source_title_map.get(sid, sid) for sid in distinct_source_ids]

            confidence = min(0.95, 0.75 + (0.05 * len(distinct_source_ids)))

            trends.append({
                "theme": f"Trend: {theme_name}",
                "category": data["category"],
                "supporting_source_ids": distinct_source_ids,
                "supporting_source_titles": src_titles,
                "evidence_summary": evidence_summary[:500],
                "is_prediction": is_prediction,
                "confidence": round(confidence, 2)
            })

        return trends

