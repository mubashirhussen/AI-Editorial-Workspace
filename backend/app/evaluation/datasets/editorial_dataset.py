"""
Editorial Studio Evaluation Dataset.
Provides structured scenarios with project briefs, multiple sources, and reference criteria:
- Word count compliance target (300-500 words)
- Headline relevance criteria
- Required structural sections
- Ground-truth source citations and quotes
"""

from typing import List, Dict, Any

EDITORIAL_EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "edit-scenario-01",
        "title": "Open Weights vs Closed Labs Strategic Shift",
        "project_title": "The Strategic Rise of Frontier Open Weights",
        "brief_data": {
            "key_takeaways": [
                "Llama 3.1 405B rivals closed models like GPT-4o and Claude 3.5 Sonnet on core benchmarks.",
                "Meta's updated license permits commercial distillation of smaller models from 405B outputs.",
                "Enterprise developers are shifting compute budgets from hosted API tokens to self-hosted vLLM clusters."
            ],
            "newsletter_angles": [
                {
                    "angle": "Why Open Weights Win the Enterprise Compute War",
                    "target_audience": "CTOs and AI Infrastructure Engineers",
                    "why_it_matters": "Distillation allows teams to run specialized 8B models at 1/100th API costs."
                }
            ],
            "claims_to_verify": [
                "Llama 3.1 405B was trained on 15 trillion tokens using 16,000 H100 GPUs."
            ]
        },
        "sources": [
            {
                "id": "src-llama-405b",
                "source_id": "src-llama-405b",
                "title": "Meta Research Announcement",
                "url": "https://ai.meta.com/blog/llama-3-1",
                "content": (
                    "Meta announced Llama 3.1 405B, trained on over 15 trillion tokens using a cluster of 16,000 H100 GPUs. "
                    "The model features an expanded 128k context window and competitive benchmarks against top proprietary models. "
                    "Meta updated its community license to allow model outputs to be used for fine-tuning and distilling other models."
                )
            },
            {
                "id": "src-enterprise-shift",
                "source_id": "src-enterprise-shift",
                "title": "SemiAnalysis Infrastructure Report",
                "url": "https://semianalysis.example.com/open-weights-economics",
                "content": (
                    "Enterprises running high-volume batch workloads report that distilling frontier open-weight models into 8B and 70B variants "
                    "reduces inference operational expenditures by up to 85% compared to proprietary API endpoints. "
                    "Open weights allow strict data residency compliance inside private VPC enclaves."
                )
            }
        ],
        "expected_word_count_min": 300,
        "expected_word_count_max": 500,
        "required_sections": ["Headline", "Analysis", "Founder", "Citations"],
        "valid_source_ids": ["src-llama-405b", "src-enterprise-shift"],
        "key_factual_quotes": [
            "trained on over 15 trillion tokens using a cluster of 16,000 H100 GPUs",
            "reduces inference operational expenditures by up to 85%"
        ]
    },
    {
        "id": "edit-scenario-02",
        "title": "Autonomous Coding Agents & Software Engineering Shifts",
        "project_title": "From Copilots to Autonomous Software Workspaces",
        "brief_data": {
            "key_takeaways": [
                "Agentic coding environments now plan, edit multi-file repositories, and run tests in isolated containers.",
                "Early developer benchmarks show 40% reduction in time-to-PR for routine bugfixes and refactoring.",
                "Engineering leaders face challenges auditing AI-authored PRs and preventing semantic drift."
            ],
            "newsletter_angles": [
                {
                    "angle": "The Post-Copilot Era: Why Multi-File Agentic Workspaces Change Engineering Velocity",
                    "target_audience": "Engineering Leaders and Startup Founders",
                    "why_it_matters": "Autonomous code synthesis shifts the developer role from typing syntax to reviewing architecture."
                }
            ],
            "claims_to_verify": [
                "GitHub Copilot Workspace operates on full repository specifications rather than single-file completions."
            ]
        },
        "sources": [
            {
                "id": "src-agentic-dev",
                "source_id": "src-agentic-dev",
                "title": "GitHub Next Technical Report",
                "url": "https://github.blog/next/agentic-workspace",
                "content": (
                    "Copilot Workspace allows engineers to initiate work from an issue description. "
                    "The system generates a human-editable natural language plan, proposes edits across multiple repository files simultaneously, "
                    "and validates code changes by executing automated build tests inside browser-based WebAssembly containers."
                )
            },
            {
                "id": "src-velocity-study",
                "source_id": "src-velocity-study",
                "title": "DevOps Productivity Benchmark 2024",
                "url": "https://devops-metrics.example.com/2024-report",
                "content": (
                    "A study across 1,200 software teams revealed that multi-file autonomous agents reduced turnaround time for bugfix pull requests by 38%, "
                    "while increasing overall code review duration by 15% due to larger diff footprints."
                )
            }
        ],
        "expected_word_count_min": 300,
        "expected_word_count_max": 500,
        "required_sections": ["Headline", "Analysis", "Founder", "Citations"],
        "valid_source_ids": ["src-agentic-dev", "src-velocity-study"],
        "key_factual_quotes": [
            "proposes edits across multiple repository files simultaneously",
            "reduced turnaround time for bugfix pull requests by 38%"
        ]
    }
]

