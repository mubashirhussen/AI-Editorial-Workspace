"""
CLI Entrypoint for AI Quality Benchmarking and Evaluation.
Usage:
    python -m backend.app.evaluation.run --suite research
    python -m backend.app.evaluation.run --suite writing
    python -m backend.app.evaluation.run --suite editorial
    python -m backend.app.evaluation.run --suite hallucination
    python -m backend.app.evaluation.run --suite all
    python -m backend.app.evaluation.run --mode offline (default) or --mode live
"""

import sys
import os
import argparse
import asyncio
import json

# Ensure parent directory and workspace root are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
workspace_root = os.path.abspath(os.path.join(backend_dir, ".."))
for p in [workspace_root, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.app.evaluation.runners.runner import EvaluationRunner
except ImportError:
    from app.evaluation.runners.runner import EvaluationRunner

async def main():
    parser = argparse.ArgumentParser(description="AI Editorial Workspace Benchmark & Evaluation Runner")
    parser.add_argument(
        "--suite",
        choices=["research", "writing", "editorial", "hallucination", "all"],
        default="all",
        help="Evaluation suite to execute (default: all)"
    )
    parser.add_argument(
        "--mode",
        choices=["offline", "live"],
        default="offline",
        help="Execution mode: 'offline' (deterministic fast mock) or 'live' (invokes external LLM)"
    )
    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"  AI Editorial Workspace Benchmark Runner")
    print(f"  Suite: {args.suite.upper()} | Mode: {args.mode.upper()}")
    print(f"=======================================================\n")

    runner = EvaluationRunner(mode=args.mode)

    if args.suite == "research":
        res = await runner.run_research_suite()
        print(f"Research Suite: {res['passed_cases']} / {res['total_cases']} Passed ({res['pass_rate']*100:.1f}%) in {res['duration_seconds']}s")
        print(f"Aggregate Entity Coverage: {res['aggregate_metrics']['average_entity_coverage']*100:.1f}%")
    elif args.suite == "writing":
        res = runner.run_writing_suite()
        print(f"Writing Suite: {res['passed_cases']} / {res['total_cases']} Passed ({res['pass_rate']*100:.1f}%) in {res['duration_seconds']}s")
        print(f"Macro F1 Score: {res['aggregate_metrics']['macro_f1']*100:.1f}% | Preservation: {res['aggregate_metrics']['average_original_preservation_rate']*100:.1f}%")
    elif args.suite == "editorial":
        res = await runner.run_editorial_suite()
        print(f"Editorial Suite: {res['passed_cases']} / {res['total_cases']} Passed ({res['pass_rate']*100:.1f}%) in {res['duration_seconds']}s")
        print(f"Word Count Compliance: {res['aggregate_metrics']['word_count_compliance_rate']*100:.1f}% | Rubric: {res['aggregate_metrics']['average_qualitative_rubric_score']} / 5.0")
    elif args.suite == "hallucination":
        res = runner.run_hallucination_suite()
        print(f"Hallucination Suite: {res['passed_cases']} / {res['total_cases']} Passed ({res['pass_rate']*100:.1f}%) in {res['duration_seconds']}s")
        print(f"Detection Recall: {res['aggregate_metrics']['hallucination_detection_recall']*100:.1f}%")
    else:
        summary = await runner.run_all()
        print(f"\nCompleted Full Evaluation Suite in {summary['total_duration_seconds']}s")
        print(f"Overall Result: {summary['passed_tests']} / {summary['total_tests']} Passed ({summary['overall_pass_rate']*100:.1f}%)\n")
        print("Reports generated:")
        print("  - backend/app/evaluation/reports/evaluation_report.json")
        print("  - backend/app/evaluation/reports/evaluation_report.md")

if __name__ == "__main__":
    asyncio.run(main())
