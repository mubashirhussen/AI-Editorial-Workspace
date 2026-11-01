"""
Evaluation Suite Runner.
Orchestrates test execution across:
- Research Assistant Suite (20 test cases)
- Writing Assistant Suite (8 test cases)
- Editorial Studio Suite (2 comprehensive scenarios)
- Hallucination & Traceability Suite (4 adversarial scenarios)
Generates structured JSON and Markdown summary reports.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.app.evaluation.datasets.research_dataset import RESEARCH_EVALUATION_DATASET
    from backend.app.evaluation.datasets.writing_dataset import WRITING_EVALUATION_DATASET
    from backend.app.evaluation.datasets.editorial_dataset import EDITORIAL_EVALUATION_DATASET
    from backend.app.evaluation.datasets.hallucination_dataset import HALLUCINATION_EVALUATION_DATASET

    from backend.app.evaluation.evaluators.research_evaluator import ResearchEvaluator
    from backend.app.evaluation.evaluators.writing_evaluator import WritingEvaluator
    from backend.app.evaluation.evaluators.editorial_evaluator import EditorialEvaluator
    from backend.app.evaluation.evaluators.hallucination_evaluator import HallucinationEvaluator
except ImportError:
    from app.evaluation.datasets.research_dataset import RESEARCH_EVALUATION_DATASET
    from app.evaluation.datasets.writing_dataset import WRITING_EVALUATION_DATASET
    from app.evaluation.datasets.editorial_dataset import EDITORIAL_EVALUATION_DATASET
    from app.evaluation.datasets.hallucination_dataset import HALLUCINATION_EVALUATION_DATASET

    from app.evaluation.evaluators.research_evaluator import ResearchEvaluator
    from app.evaluation.evaluators.writing_evaluator import WritingEvaluator
    from app.evaluation.evaluators.editorial_evaluator import EditorialEvaluator
    from app.evaluation.evaluators.hallucination_evaluator import HallucinationEvaluator

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")

class EvaluationRunner:
    def __init__(self, mode: str = "offline"):
        self.mode = mode
        self.research_evaluator = ResearchEvaluator()
        self.writing_evaluator = WritingEvaluator()
        self.editorial_evaluator = EditorialEvaluator()
        self.hallucination_evaluator = HallucinationEvaluator()
        os.makedirs(REPORTS_DIR, exist_ok=True)

    async def run_research_suite(self) -> Dict[str, Any]:
        results = []
        start_t = time.perf_counter()
        for case in RESEARCH_EVALUATION_DATASET:
            res = await self.research_evaluator.evaluate_test_case(case, mode=self.mode)
            results.append(res)
        duration_s = time.perf_counter() - start_t

        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        pass_rate = round(passed_count / total_count, 4) if total_count else 0.0

        # Aggregate metrics
        avg_coverage = sum(r["metrics"]["entity_coverage_rate"] for r in results) / total_count
        injection_resisted = sum(1 for r in results if r["metrics"]["prompt_injection_resisted"])

        return {
            "suite": "research",
            "mode": self.mode,
            "total_cases": total_count,
            "passed_cases": passed_count,
            "pass_rate": pass_rate,
            "duration_seconds": round(duration_s, 2),
            "aggregate_metrics": {
                "average_entity_coverage": round(avg_coverage, 4),
                "prompt_injection_resistance_rate": round(injection_resisted / total_count, 4)
            },
            "cases": results
        }

    def run_writing_suite(self) -> Dict[str, Any]:
        results = []
        start_t = time.perf_counter()
        for case in WRITING_EVALUATION_DATASET:
            res = self.writing_evaluator.evaluate_test_case(case)
            results.append(res)
        duration_s = time.perf_counter() - start_t

        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        pass_rate = round(passed_count / total_count, 4) if total_count else 0.0

        avg_prec = sum(r["metrics"]["precision"] for r in results) / total_count
        avg_rec = sum(r["metrics"]["recall"] for r in results) / total_count
        avg_f1 = sum(r["metrics"]["f1"] for r in results) / total_count
        avg_preservation = sum(r["metrics"]["original_preservation_rate"] for r in results) / total_count

        return {
            "suite": "writing",
            "mode": self.mode,
            "total_cases": total_count,
            "passed_cases": passed_count,
            "pass_rate": pass_rate,
            "duration_seconds": round(duration_s, 2),
            "aggregate_metrics": {
                "macro_precision": round(avg_prec, 4),
                "macro_recall": round(avg_rec, 4),
                "macro_f1": round(avg_f1, 4),
                "average_original_preservation_rate": round(avg_preservation, 4)
            },
            "cases": results
        }

    async def run_editorial_suite(self) -> Dict[str, Any]:
        results = []
        start_t = time.perf_counter()
        for case in EDITORIAL_EVALUATION_DATASET:
            res = await self.editorial_evaluator.evaluate_test_case(case, mode=self.mode)
            results.append(res)
        duration_s = time.perf_counter() - start_t

        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        pass_rate = round(passed_count / total_count, 4) if total_count else 0.0

        wc_compliance_rate = sum(1 for r in results if r["metrics"]["word_count_compliant"]) / total_count
        avg_source_validity = sum(r["metrics"]["source_validity_rate"] for r in results) / total_count
        avg_rubric = sum(r["metrics"]["rubric_average"] for r in results) / total_count

        return {
            "suite": "editorial",
            "mode": self.mode,
            "total_cases": total_count,
            "passed_cases": passed_count,
            "pass_rate": pass_rate,
            "duration_seconds": round(duration_s, 2),
            "aggregate_metrics": {
                "word_count_compliance_rate": round(wc_compliance_rate, 4),
                "average_source_validity_rate": round(avg_source_validity, 4),
                "average_qualitative_rubric_score": round(avg_rubric, 2)
            },
            "cases": results
        }

    def run_hallucination_suite(self) -> Dict[str, Any]:
        results = []
        start_t = time.perf_counter()
        for case in HALLUCINATION_EVALUATION_DATASET:
            res = self.hallucination_evaluator.evaluate_test_case(case)
            results.append(res)
        duration_s = time.perf_counter() - start_t

        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        pass_rate = round(passed_count / total_count, 4) if total_count else 0.0

        avg_recall = sum(r["metrics"]["detection_recall"] for r in results) / total_count

        return {
            "suite": "hallucination",
            "mode": self.mode,
            "total_cases": total_count,
            "passed_cases": passed_count,
            "pass_rate": pass_rate,
            "duration_seconds": round(duration_s, 2),
            "aggregate_metrics": {
                "hallucination_detection_recall": round(avg_recall, 4)
            },
            "cases": results
        }

    async def run_all(self) -> Dict[str, Any]:
        overall_start = time.perf_counter()
        research_res = await self.run_research_suite()
        writing_res = self.run_writing_suite()
        editorial_res = await self.run_editorial_suite()
        hallucination_res = self.run_hallucination_suite()
        total_duration = time.perf_counter() - overall_start

        total_tests = (
            research_res["total_cases"] +
            writing_res["total_cases"] +
            editorial_res["total_cases"] +
            hallucination_res["total_cases"]
        )
        passed_tests = (
            research_res["passed_cases"] +
            writing_res["passed_cases"] +
            editorial_res["passed_cases"] +
            hallucination_res["passed_cases"]
        )
        overall_pass_rate = round(passed_tests / total_tests, 4) if total_tests else 0.0

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "total_duration_seconds": round(total_duration, 2),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "overall_pass_rate": overall_pass_rate,
            "suites": {
                "research": research_res,
                "writing": writing_res,
                "editorial": editorial_res,
                "hallucination": hallucination_res
            }
        }

        # Save JSON Report
        json_path = os.path.join(REPORTS_DIR, "evaluation_report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        # Generate and Save Markdown Report
        md_content = self.generate_markdown_report(summary)
        md_path = os.path.join(REPORTS_DIR, "evaluation_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return summary

    def generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        s = summary["suites"]
        lines = [
            "# AI Evaluation & Benchmark Quality Report",
            f"\n**Execution Mode:** `{summary['mode']}`  ",
            f"**Timestamp (UTC):** `{summary['timestamp']}`  ",
            f"**Total Duration:** `{summary['total_duration_seconds']}s`  ",
            f"**Overall Result:** **{summary['passed_tests']} / {summary['total_tests']} Passed ({round(summary['overall_pass_rate'] * 100, 1)}%)**\n",
            "---",
            "## 1. Executive Suite Summary\n",
            "| Suite | Total Cases | Passed Cases | Pass Rate | Key Quality Metric | Result |",
            "| :--- | :---: | :---: | :---: | :--- | :---: |",
            f"| **Research Assistant** | {s['research']['total_cases']} | {s['research']['passed_cases']} | {round(s['research']['pass_rate']*100, 1)}% | Entity Coverage | {round(s['research']['aggregate_metrics']['average_entity_coverage']*100, 1)}% |",
            f"| **Writing Assistant** | {s['writing']['total_cases']} | {s['writing']['passed_cases']} | {round(s['writing']['pass_rate']*100, 1)}% | Macro F1 Score | {round(s['writing']['aggregate_metrics']['macro_f1']*100, 1)}% |",
            f"| **Editorial Studio** | {s['editorial']['total_cases']} | {s['editorial']['passed_cases']} | {round(s['editorial']['pass_rate']*100, 1)}% | Word Count Compliance | {round(s['editorial']['aggregate_metrics']['word_count_compliance_rate']*100, 1)}% |",
            f"| **Hallucination & Traceability** | {s['hallucination']['total_cases']} | {s['hallucination']['passed_cases']} | {round(s['hallucination']['pass_rate']*100, 1)}% | Hallucination Recall | {round(s['hallucination']['aggregate_metrics']['hallucination_detection_recall']*100, 1)}% |\n",
            "---",
            "## 2. Research Assistant Results (20 Scenarios)\n",
            "| Case ID | Category | Status | Entity Coverage | Injection Resisted | Uncertainties Flagged |",
            "| :--- | :--- | :---: | :---: | :---: | :---: |"
        ]

        for c in s["research"]["cases"]:
            status_badge = "✅ PASS" if c["passed"] else "❌ FAIL"
            cov = f"{round(c['metrics']['entity_coverage_rate'] * 100, 1)}%"
            inj = "YES" if c["metrics"]["prompt_injection_resisted"] else "NO"
            unc = "YES" if c["metrics"]["uncertainty_identified"] else "N/A"
            lines.append(f"| `{c['case_id']}` | {c['category']} | {status_badge} | {cov} | {inj} | {unc} |")

        lines.extend([
            "\n---",
            "## 3. Writing Assistant Results (8 Prose Checks)\n",
            "| Case ID | Defect Category | Status | Precision | Recall | F1 | Preservation |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
        ])

        for c in s["writing"]["cases"]:
            status_badge = "✅ PASS" if c["passed"] else "❌ FAIL"
            prec = f"{round(c['metrics']['precision'] * 100, 1)}%"
            rec = f"{round(c['metrics']['recall'] * 100, 1)}%"
            f1 = f"{round(c['metrics']['f1'] * 100, 1)}%"
            pres = f"{round(c['metrics']['original_preservation_rate'] * 100, 1)}%"
            lines.append(f"| `{c['case_id']}` | `{c['category']}` | {status_badge} | {prec} | {rec} | {f1} | {pres} |")

        lines.extend([
            "\n---",
            "## 4. Editorial Studio Results\n",
            "| Case ID | Scenario | Status | Words | Word Count Compliant | Source Validity | Rubric (1-5) |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
        ])

        for c in s["editorial"]["cases"]:
            status_badge = "✅ PASS" if c["passed"] else "❌ FAIL"
            wc = c["metrics"]["word_count"]
            wc_comp = "YES" if c["metrics"]["word_count_compliant"] else "NO"
            sv = f"{round(c['metrics']['source_validity_rate'] * 100, 1)}%"
            rubric = f"{c['metrics']['rubric_average']} / 5.0"
            lines.append(f"| `{c['case_id']}` | {c['title']} | {status_badge} | {wc} | {wc_comp} | {sv} | {rubric} |")

        lines.extend([
            "\n---",
            "## 5. Hallucination & Grounding Audit\n",
            "| Case ID | Attack / Stress Scenario | Status | Recall | Grounding Violations Detected |",
            "| :--- | :--- | :---: | :---: | :--- |"
        ])

        for c in s["hallucination"]["cases"]:
            status_badge = "✅ PASS" if c["passed"] else "❌ FAIL"
            rec = f"{round(c['metrics']['detection_recall'] * 100, 1)}%"
            categories = ", ".join(c["metrics"]["detected_categories"]) or "None"
            lines.append(f"| `{c['case_id']}` | {c['title']} | {status_badge} | {rec} | `{categories}` |")

        return "\n".join(lines)
