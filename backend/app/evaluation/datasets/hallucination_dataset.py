"""
Hallucination & Source Traceability Evaluation Dataset.
Provides targeted test scenarios with known adversarial or flawed editorial drafts:
1. Unsupported Numbers (e.g., claiming $500M when source says $50M)
2. Fabricated Quotations (e.g., fake quotes from executives not present in sources)
3. Invented Source References (e.g., citing non-existent source IDs)
4. Misattribution (e.g., attributing Source B claims to Source A)
5. Unsubstantiated High-Confidence Assertions
"""

from typing import List, Dict, Any

HALLUCINATION_EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "hal-num-01",
        "title": "Unsupported Financial Numbers",
        "ground_truth_sources": {
            "src-real-01": (
                "DataCorp raised $45 million in Series B funding led by Index Ventures at a $250 million post-money valuation."
            )
        },
        "test_draft": (
            "DataCorp recently announced a staggering $450 million Series B round, achieving a $2.5 billion valuation. "
            "The company plans to deploy these funds to expand its international sales force."
        ),
        "expected_hallucinations": [
            {
                "type": "unsupported_number",
                "detected_in_draft": "$450 million",
                "actual_in_source": "$45 million"
            },
            {
                "type": "unsupported_number",
                "detected_in_draft": "$2.5 billion",
                "actual_in_source": "$250 million"
            }
        ]
    },
    {
        "id": "hal-quote-02",
        "title": "Fabricated Executive Quotation",
        "ground_truth_sources": {
            "src-real-02": (
                "CloudTech released version 2.0 with enhanced Kubernetes orchestration capabilities. "
                "The update includes multi-cluster networking."
            )
        },
        "test_draft": (
            "CloudTech version 2.0 is now live. CEO Sarah Jenkins announced: 'This breakthrough marks the definitive end of legacy cloud providers forever.' "
            "The update delivers automated multi-cluster networking."
        ),
        "expected_hallucinations": [
            {
                "type": "fabricated_quote",
                "quote": "This breakthrough marks the definitive end of legacy cloud providers forever.",
                "reason": "Quotation does not appear anywhere in source text."
            }
        ]
    },
    {
        "id": "hal-ref-03",
        "title": "Invented Source ID Reference",
        "ground_truth_sources": {
            "src-001": "OpenAI announced GPT-4o with multimodal audio capabilities."
        },
        "test_draft": (
            "The new multimodal capabilities were unveiled on Monday [Source: src-999-phantom]. "
            "Real-time voice processing latency dropped to 232 milliseconds."
        ),
        "valid_source_ids": ["src-001"],
        "expected_hallucinations": [
            {
                "type": "invented_source_reference",
                "invalid_id": "src-999-phantom"
            }
        ]
    },
    {
        "id": "hal-attrib-04",
        "title": "Misattributed Technical Benchmark",
        "ground_truth_sources": {
            "src-google": "Google DeepMind published Gemini 1.5 Pro benchmark results showing a 1M token context window.",
            "src-anthropic": "Anthropic released Claude 3.5 Sonnet showing 92% on HumanEval coding tasks."
        },
        "test_draft": (
            "According to Google DeepMind [src-google], their team achieved a 92% score on HumanEval coding tasks."
        ),
        "expected_hallucinations": [
            {
                "type": "misattribution",
                "claim": "92% on HumanEval",
                "attributed_to": "src-google",
                "actual_source": "src-anthropic"
            }
        ]
    }
]

