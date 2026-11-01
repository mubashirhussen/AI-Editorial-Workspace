"""
Performance & Scalability Benchmark Suite
Measures actual API response times and database throughput on realistic datasets:
- 10 Research Projects
- 100 Sources
- 50 Writing Drafts
- 200 Writing Suggestions
- 30 Editorial Outputs
"""

import os
import sys
import time
import statistics
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Force test configuration
os.environ["ENVIRONMENT"] = "test"
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./benchmark_perf_baseline.db"
os.environ["OPENAI_API_KEY"] = ""

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.models.base import (
    ResearchProject,
    Source,
    SourceAnalysis,
    ResearchBrief,
    WritingDraft,
    WritingSuggestion,
    EditorialOutput
)

client = TestClient(app)

def setup_benchmark_dataset():
    """Populates realistic database volume."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        projects = []
        for i in range(10):
            p = ResearchProject(
                title=f"AI Infrastructure Benchmark Project {i+1}",
                description=f"Automated benchmark project evaluation {i+1}",
                status="active"
            )
            db.add(p)
            projects.append(p)
        db.commit()
        for p in projects:
            db.refresh(p)

        # 100 Sources (10 per project) with analyses
        sources = []
        for p in projects:
            for s_idx in range(10):
                s = Source(
                    project_id=p.id,
                    title=f"Source {s_idx+1} for Project {p.title}",
                    url=f"https://benchmark.domain/source-{p.id[:8]}-{s_idx}",
                    source_type="article",
                    extracted_content=f"Detailed hardware benchmark evidence {s_idx}. Latency reduced by 35% on TPU clusters.",
                    extraction_status="COMPLETED"
                )
                db.add(s)
                sources.append(s)
        db.commit()
        for s in sources:
            db.refresh(s)

        # Add SourceAnalysis for each source
        for s in sources:
            sa = SourceAnalysis(
                source_id=s.id,
                summary="Technical analysis of hardware performance",
                key_points=["Latency reduction", "Throughput gain"],
                reported_facts=["35% latency drop verified on TPU v5e."],
                analysis=["Modular design allows better thermal dissipation."],
                founder_implications={"action": "Consider TPU for inference pipelines"},
                uncertainties=["Early yields are uncertain"],
                newsletter_angles=["Why hardware co-design matters"],
                key_developments=["Cluster scaling"],
                important_claims=["35% reduction"],
                facts=["35% latency drop"],
                speculation=["Expected 2x gains by 2027"],
                implications={"arch": "co-design"},
                limitations=[]
            )
            db.add(sa)

        # Brief for each project
        briefs = []
        for p in projects:
            b = ResearchBrief(
                project_id=p.id,
                title=f"Synthesized Brief for {p.title}",
                executive_summary="Hardware improvements show steady latency drops across model sizes.",
                key_developments=["TPU cluster scaling"],
                strategic_implications={"market": "Compute economics shift toward energy efficiency."},
                newsletter_angles=[{
                    "angle": "Energy is the new compute bottleneck",
                    "target_audience": "Founders and Operators",
                    "why_it_matters": "Datacenter power caps dictate scaling limit."
                }],
                source_references=[{"source_title": "TPU Benchmark", "url": "https://benchmark.domain"}],
                brief_content={
                    "what_happened": "Capex surged as models expanded.",
                    "why_it_matters": "Operators must optimize per-watt efficiency.",
                    "predictions": "Hyperscalers will deploy micro-nuclear colocations."
                },
                evidence=[{"fact": "35% latency drop", "source_title": "TPU Benchmark"}],
                recommended_angle={"angle": "Energy efficiency"}
            )
            db.add(b)
            briefs.append(b)

        # 50 Drafts (5 per project) with 200 suggestions (4 per draft)
        drafts = []
        for p in projects:
            for d_idx in range(5):
                d = WritingDraft(
                    project_id=p.id,
                    title=f"Newsletter Draft {d_idx+1} for {p.title}",
                    original_content="In order to understand the hardware bottleneck, models were trained by researchers.",
                    revised_content="To understand the hardware bottleneck, researchers trained models.",
                    word_count=52,
                    readability_score=71.2,
                    status="in_review"
                )
                db.add(d)
                drafts.append(d)
        db.commit()
        for d in drafts:
            db.refresh(d)

        # 200 Suggestions (4 per draft)
        for d in drafts:
            for sug_idx in range(4):
                sug = WritingSuggestion(
                    draft_id=d.id,
                    category="filler" if sug_idx % 2 == 0 else "passive_voice",
                    original_text="In order to" if sug_idx % 2 == 0 else "models were trained",
                    suggested_rewrite="To" if sug_idx % 2 == 0 else "researchers trained models",
                    explanation="Clarity rewrite",
                    severity="medium",
                    status="pending" if sug_idx < 2 else "accepted"
                )
                db.add(sug)

        # 30 Editorial outputs (3 per project)
        for p in projects:
            for ed_idx in range(3):
                ed = EditorialOutput(
                    project_id=p.id,
                    headline=f"The Future of Compute Cluster Scaling {ed_idx+1}",
                    content="Hyperscalers are investing over $120B in AI infrastructure [SemiAnalysis]. However, power grids are reaching capacity.",
                    word_count=360,
                    source_references=[{"source_title": "SemiAnalysis", "url": None}],
                    status="published"
                )
                db.add(ed)

        db.commit()
        return len(projects), len(sources), len(drafts), 200, 30
    finally:
        db.close()

def run_benchmarks(iterations: int = 20) -> Dict[str, Any]:
    results = {}

    # 1. Dashboard Load Time (GET /api/v1/research/dashboard/stats)
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/research/dashboard/stats")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
    results["dashboard_stats_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # 2. Project List Retrieval (GET /api/v1/research/projects)
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/research/projects?skip=0&limit=50")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
    results["project_listing_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # Get sample project ID & source ID
    db = SessionLocal()
    sample_proj_id = db.query(ResearchProject).first().id
    sample_source_id = db.query(Source).first().id
    sample_draft_id = db.query(WritingDraft).first().id
    sample_brief_id = db.query(ResearchBrief).first().id
    db.close()

    # 3. Single Project Retrieval with sources
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.get(f"/api/v1/research/projects/{sample_proj_id}")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
    results["single_project_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # 4. Source Retrieval & Analysis (GET /api/v1/sources/{id}/analysis)
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.get(f"/api/v1/sources/{sample_source_id}/analysis")
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
    results["source_analysis_retrieval_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # 5. Draft Analysis (POST /api/v1/writing/analyze)
    sample_text = (
        "In order to understand the paradigm shift, engineers must carefully evaluate memory bandwidth limitations. "
        "The model was trained by researchers using distributed gradient accumulation across sixteen clusters."
    )
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.post("/api/v1/writing/analyze", json={
            "text": sample_text,
            "title": "Benchmark Draft"
        })
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 200
    results["draft_analysis_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # 6. Editorial Generation (POST /api/v1/editorial/generate)
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        resp = client.post("/api/v1/editorial/generate", json={
            "project_id": sample_proj_id,
            "research_brief_id": sample_brief_id,
            "audience": "founders, builders, and operators",
            "tone": "Newsletter-style",
            "min_words": 300,
            "max_words": 500
        })
        latencies.append((time.perf_counter() - t0) * 1000)
        assert resp.status_code == 201
    results["editorial_generation_ms"] = {
        "mean": statistics.mean(latencies),
        "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        "min": min(latencies),
        "max": max(latencies)
    }

    # 7. Concurrent Request Burst (20 parallel requests to dashboard stats)
    def fetch_dashboard():
        t = time.perf_counter()
        r = client.get("/api/v1/research/dashboard/stats")
        return (time.perf_counter() - t) * 1000, r.status_code

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_dashboard) for _ in range(20)]
        concurrent_times = [f.result()[0] for f in futures]
        status_codes = [f.result()[1] for f in futures]
    
    assert all(code == 200 for code in status_codes)
    results["concurrent_burst_20_ms"] = {
        "mean": statistics.mean(concurrent_times),
        "p95": sorted(concurrent_times)[int(len(concurrent_times) * 0.95)],
        "min": min(concurrent_times),
        "max": max(concurrent_times)
    }

    return results

if __name__ == "__main__":
    n_p, n_s, n_d, n_sug, n_ed = setup_benchmark_dataset()
    print(f"Dataset Seeded: {n_p} Projects, {n_s} Sources, {n_d} Drafts, {n_sug} Suggestions, {n_ed} Editorials.")
    res = run_benchmarks(20)
    import json
    print("--- BENCHMARK RESULTS JSON ---")
    print(json.dumps(res, indent=2))
