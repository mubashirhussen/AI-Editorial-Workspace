# PHASE 38 — INSIGHT RULES SPECIFICATION
## Deterministic Pattern Detection Rules & Evidence Grounding Reference

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Production Frontend:** `https://ai-editorial-workspace-blue.vercel.app/`  
**Branch:** `feat/phase38-ai-product-intelligence`  
**Author:** Senior AI Engineer & Forward Deployed Engineer  
**Date:** November 2026  
**Status:** Certified & Implemented

---

## 1. Rule Engine Architecture

The AI Product Intelligence rules engine operates deterministically over aggregated first-party telemetry events stored in the `analytics_events` table. Rather than delegating critical workflow diagnostics to unstructured LLM queries, all patterns are detected through formal statistical rules.

### Rule Evaluation Pipeline:
1. **Data Quality Gate:** The rule engine verifies that the organization has $\ge 3$ telemetry events within the lookback window (default 30 days) and that telemetry freshness is $\le 72$ hours.
2. **Event Filtering & Aggregation:** Events are filtered by `organization_id` and grouped by workflow type (`research`, `writing`, `editorial`, `project`).
3. **Threshold Evaluation:** Each registered rule evaluates its quantitative condition against aggregated metrics.
4. **Evidence Grounding:** When a condition fires, a structured evidence dictionary is computed containing exact counts, timestamps, and percentages.
5. **Deduplication:** Repeated insights for identical patterns update their confidence scores and evidence rather than cluttering the user's dashboard with duplicates.

---

## 2. Comprehensive Rules Inventory

### Rule 1: High Research Source Processing Failure Rate (`high_source_processing_failure`)
- **Category:** `research`
- **Severity:** `CRITICAL` if failure rate $\ge 40\%$, else `HIGH`
- **Trigger Condition:**
  $$\text{Failed Sources} > 0 \quad \text{AND} \quad \frac{\text{Failed Sources}}{\text{Total Sources}} \ge 0.20$$
- **Evidence Structure:**
  ```json
  {
    "total_sources_attempted": 12,
    "failed_sources_count": 4,
    "failure_rate_percent": 33.3,
    "threshold_percent": 20.0,
    "sample_period_days": 30
  }
  ```
- **Generated Insight Title:** "Elevated Failure Rate in Research Source Ingestion"
- **Generated Description:** "Source processing failure rate reached 33.3% across 12 ingestion attempts. Network timeouts and unhandled paywalls represent the primary failure vector."
- **Confidence Derivation:**
  $$\text{Confidence} = \min\left(0.60 + \frac{\text{Total Sources}}{50} \times 0.35, 0.95\right)$$

---

### Rule 2: Slow Editorial Generation Latency (`slow_editorial_generation`)
- **Category:** `editorial`
- **Severity:** `HIGH` if avg duration $\ge 50\text{s}$, else `MEDIUM`
- **Trigger Condition:**
  $$\text{Avg Editorial Duration (ms)} \ge 35,000 \quad \text{AND} \quad \text{Editorial Count} \ge 2$$
- **Evidence Structure:**
  ```json
  {
    "total_editorial_generations": 8,
    "avg_duration_seconds": 42.6,
    "max_duration_seconds": 68.1,
    "threshold_seconds": 35.0,
    "p90_duration_seconds": 58.4
  }
  ```
- **Generated Insight Title:** "High Editorial Generation Latency Detected"
- **Generated Description:** "Average editorial generation latency is 42.6 seconds, exceeding the 35.0 second operational SLA. Token output generation and large prompt templates are compounding delay."
- **Confidence Derivation:**
  $$\text{Confidence} = \min\left(0.65 + \frac{\text{Editorial Count}}{20} \times 0.30, 0.95\right)$$

---

### Rule 3: Writing Suggestion Rejection Friction (`high_suggestion_rejection_rate`)
- **Category:** `writing`
- **Severity:** `MEDIUM`
- **Trigger Condition:**
  $$\frac{\text{Rejected Suggestions}}{\text{Total Suggestions Evaluated}} \ge 0.30 \quad \text{AND} \quad \text{Total Evaluated} \ge 3$$
- **Evidence Structure:**
  ```json
  {
    "accepted_suggestions": 4,
    "rejected_suggestions": 6,
    "rejection_rate_percent": 60.0,
    "threshold_percent": 30.0
  }
  ```
- **Generated Insight Title:** "Elevated AI Writing Suggestion Rejection"
- **Generated Description:** "Users rejected 60.0% of suggested writing edits, indicating misaligned stylistic preferences or excessive suggestion frequency."
- **Confidence Derivation:**
  $$\text{Confidence} = \min\left(0.55 + \frac{\text{Total Evaluated}}{20} \times 0.35, 0.90\right)$$

---

### Rule 4: Research-to-Draft Conversion Drop-Off (`low_research_to_draft_conversion`)
- **Category:** `workflow_optimization`
- **Severity:** `HIGH`
- **Trigger Condition:**
  $$\text{Briefs Generated} \ge 2 \quad \text{AND} \quad \frac{\text{Drafts Created}}{\text{Briefs Generated}} < 0.35$$
- **Evidence Structure:**
  ```json
  {
    "briefs_completed": 5,
    "drafts_created": 1,
    "conversion_rate_percent": 20.0,
    "expected_baseline_percent": 35.0
  }
  ```
- **Generated Insight Title:** "Low Research Brief to Draft Conversion Gap"
- **Generated Description:** "Only 20.0% of completed research briefs progress into article drafts. Users experience cognitive fatigue transitioning between research synthesis and drafting."
- **Confidence Derivation:**
  $$\text{Confidence} = \min\left(0.60 + \frac{\text{Briefs Completed}}{15} \times 0.30, 0.90\right)$$

---

### Rule 5: Repetitive Research Queries Underutilizing Cache (`cache_underutilization`)
- **Category:** `performance`
- **Severity:** `MEDIUM`
- **Trigger Condition:**
  $$\text{Identical Source Domains} \ge 3 \quad \text{AND} \quad \text{Cache Hit Rate} < 0.15$$
- **Evidence Structure:**
  ```json
  {
    "repeated_queries_count": 7,
    "cache_hit_rate_percent": 5.0,
    "potential_latency_savings_seconds": 18.5
  }
  ```
- **Generated Insight Title:** "Underutilized Source Caching in Research Ingestion"
- **Generated Description:** "Repeated ingestion of identical sources caused unnecessary LLM re-extraction and redundant network requests."
- **Confidence Derivation:**
  $$\text{Confidence} = 0.80$$

---

## 3. Conflict Resolution & Edge Cases

1. **Zero Events:** The rule engine short-circuits immediately with a clean `INSUFFICIENT_DATA` status; zero phantom insights or alerts are emitted.
2. **Conflicting Trends:** If source failure rate is high but recent events in the last 2 hours show 100% success, the confidence score is dynamically decayed by $0.20$ to reflect recent stabilization.
3. **Multi-Tenant Boundary:** Rule evaluation queries enforce `organization_id == active_tenant`. No cross-tenant event aggregation occurs under any circumstances.
