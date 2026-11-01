"""
Phase 22 - AI Evaluation, Accuracy & Quality Benchmarking Test Suite
Verifies:
1. Research Assistant evaluation suite (20 test cases, coverage, injection resistance)
2. Writing Assistant evaluation suite (8 test cases, Precision, Recall, F1, Preservation)
3. Editorial Studio evaluation suite (300-500 words, citation validity, rubric)
4. Hallucination detection suite (unsupported numbers, fabricated quotes, misattributions)
5. Structured JSON and Markdown report artifact generation
"""

import os
import json
import pytest
from backend.app.evaluation.runners.runner import EvaluationRunner, REPORTS_DIR

@pytest.mark.asyncio
async def test_phase22_research_assistant_evaluation():
    """Validates that all 20 research evaluation scenarios run and achieve target entity coverage."""
    runner = EvaluationRunner(mode="offline")
    result = await runner.run_research_suite()
    
    assert result["suite"] == "research"
    assert result["total_cases"] >= 20
    assert result["passed_cases"] >= 18
    assert result["pass_rate"] >= 0.90
    assert result["aggregate_metrics"]["average_entity_coverage"] >= 0.85
    assert result["aggregate_metrics"]["prompt_injection_resistance_rate"] == 1.0

def test_phase22_writing_assistant_evaluation():
    """Validates that writing quality checks achieve target Precision, Recall, and F1."""
    runner = EvaluationRunner(mode="offline")
    result = runner.run_writing_suite()
    
    assert result["suite"] == "writing"
    assert result["total_cases"] >= 8
    assert result["passed_cases"] == result["total_cases"]
    assert result["pass_rate"] == 1.0
    assert result["aggregate_metrics"]["macro_f1"] >= 0.90
    assert result["aggregate_metrics"]["average_original_preservation_rate"] == 1.0

@pytest.mark.asyncio
async def test_phase22_editorial_studio_evaluation():
    """Validates word count compliance (300-500 words) and qualitative rubric averages."""
    runner = EvaluationRunner(mode="offline")
    result = await runner.run_editorial_suite()
    
    assert result["suite"] == "editorial"
    assert result["total_cases"] >= 2
    assert result["passed_cases"] == result["total_cases"]
    assert result["aggregate_metrics"]["word_count_compliance_rate"] == 1.0
    assert result["aggregate_metrics"]["average_qualitative_rubric_score"] >= 4.0

def test_phase22_hallucination_evaluation():
    """Validates detection recall on unsupported figures, fake quotes, and misattributions."""
    runner = EvaluationRunner(mode="offline")
    result = runner.run_hallucination_suite()
    
    assert result["suite"] == "hallucination"
    assert result["total_cases"] >= 4
    assert result["passed_cases"] == result["total_cases"]
    assert result["aggregate_metrics"]["hallucination_detection_recall"] == 1.0

@pytest.mark.asyncio
async def test_phase22_full_run_and_report_generation():
    """Ensures full runner executes and generates valid JSON and Markdown reports."""
    runner = EvaluationRunner(mode="offline")
    summary = await runner.run_all()
    
    assert summary["total_tests"] >= 34
    assert summary["passed_tests"] == summary["total_tests"]
    assert summary["overall_pass_rate"] == 1.0

    json_path = os.path.join(REPORTS_DIR, "evaluation_report.json")
    md_path = os.path.join(REPORTS_DIR, "evaluation_report.md")

    assert os.path.exists(json_path)
    assert os.path.exists(md_path)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["total_tests"] == summary["total_tests"]
        assert "suites" in data

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "# AI Evaluation & Benchmark Quality Report" in content
        assert "Research Assistant Results" in content
        assert "Writing Assistant Results" in content

