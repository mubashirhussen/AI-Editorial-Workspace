"""
Writing Assistant Evaluation Dataset.
Contains curated prose samples with ground-truth labels for:
- Long sentences (>25 words)
- Passive voice constructions
- Filler and wordy phrases
- Corporate and tech jargon
- Repeated expressions
- Complex/dense paragraphs
- Clean control prose (zero expected defects)
"""

from typing import List, Dict, Any

WRITING_EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "write-long-01",
        "title": "Unbounded Compound Sentence",
        "category": "long_sentence",
        "text": (
            "Because the engineering team failed to anticipate the surge in consumer demand during the annual holiday promotional period, "
            "the distributed caching cluster experienced catastrophic memory pressure, which subsequently caused widespread database connection timeouts across all regional clusters, "
            "ultimately forcing the operations team to manually restart fifty individual production nodes in the middle of the night."
        ),
        "expected_issues": {
            "long_sentences": 1,
            "passive_voice": 0,
            "filler_phrases": 0,
            "jargon": 0
        }
    },
    {
        "id": "write-passive-01",
        "title": "Repeated Passive Voice Constructions",
        "category": "passive_voice",
        "text": (
            "The architectural guidelines were developed by the staff engineers before implementation. "
            "Subsequently, the deployment scripts were executed by the automated runner, and multiple anomalies were observed by the team."
        ),
        "expected_issues": {
            "long_sentences": 0,
            "passive_voice": 3,  # were developed, were executed, were observed
            "filler_phrases": 0,
            "jargon": 0
        }
    },
    {
        "id": "write-filler-01",
        "title": "Verbose and Redundant Filler Phrases",
        "category": "filler",
        "text": (
            "In order to successfully deploy the update, it is important to note that engineers must conduct an audit. "
            "At the end of the day, our goal is to basically eliminate database downtime."
        ),
        "expected_issues": {
            "long_sentences": 0,
            "passive_voice": 0,
            "filler_phrases": 4,  # in order to, it is important to note that, at the end of the day, basically
            "jargon": 0
        }
    },
    {
        "id": "write-jargon-01",
        "title": "Corporate Buzzwords and Silicon Valley Jargon",
        "category": "jargon",
        "text": (
            "We must create synergy across teams to execute a paradigm shift in our ecosystem. "
            "We should leverage our infrastructure to drive growth."
        ),
        "expected_issues": {
            "long_sentences": 0,
            "passive_voice": 0,
            "filler_phrases": 0,
            "jargon": 5  # synergy, paradigm shift, ecosystem, leverage, infrastructure
        }
    },
    {
        "id": "write-repeated-01",
        "title": "Consecutive Repeated Sentence Openers",
        "category": "repetition",
        "text": (
            "Engineers discovered memory leaks in the caching layer during peak traffic. "
            "Engineers restarted fifty servers to prevent system outages. "
            "Engineers refactored the connection pool after sunrise."
        ),
        "expected_issues": {
            "repeated_expressions": 2  # Sentences 2 and 3 repeat 'Engineers'
        }
    },
    {
        "id": "write-complex-01",
        "title": "Dense Complex Paragraph",
        "category": "complexity",
        "text": (
            "The distributed storage system underwent extensive benchmarking across twenty availability zones yesterday afternoon. "
            "Network latency fluctuated considerably during cross-region replication tests conducted under synthetic workloads. "
            "Storage controllers experienced intermittent buffer overflow conditions when processing concurrent write transactions. "
            "Operations personnel deployed hotfix packages to mitigate packet retransmission overhead across the spine switches. "
            "Database reliability metrics gradually normalized once the revised throttling policies took effect."
        ),
        "expected_issues": {
            "complex_paragraphs": 1  # 5 sentences in a single paragraph triggers complexity check
        }
    },
    {
        "id": "write-concise-01",
        "title": "Redundant Wordy Phrases",
        "category": "filler",
        "text": (
            "The cluster has the ability to scale nodes automatically due to the fact that demand fluctuates. "
            "Needless to say, it is very important."
        ),
        "expected_issues": {
            "filler_phrases": 4  # has the ability to, due to the fact that, needless to say, very
        }
    },
    {
        "id": "write-clean-control",
        "title": "Clean High-Quality Technical Prose (Control Case)",
        "category": "control",
        "text": (
            "Nvidia shipped thirty thousand Blackwell GPUs to cloud customers this quarter. "
            "Datacenter revenue grew by twelve percent compared to last month. "
            "Engineers reported stable cluster performance during initial training runs."
        ),
        "expected_issues": {
            "long_sentences": 0,
            "passive_voice": 0,
            "filler_phrases": 0,
            "jargon": 0
        }
    }
]
