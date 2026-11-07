# PHASE 8 — INITIAL AI ARCHITECTURE AUDIT REPORT
**Project:** AI Editorial Workspace  
**Date:** 2026-11-07  
**Auditor:** Senior AI Engineer, LLM Evaluation Specialist & AI Platform Architect  
**Branch:** `feature/ai-reliability-observability`  

---

## 1. Executive Summary

This audit evaluates the reliability, hallucination risks, model provider failovers, citation integrity, prompt versioning, and observability of the **AI Editorial Workspace**.

The workspace currently features functional research brief synthesis and editorial draft generation backed by an OpenAI/Groq API client with deterministic fallback logic and an initial 34-case offline evaluation runner. However, to operate as an enterprise-grade, dependable newsroom platform, several key gaps in **claim verification granularity**, **centralized provider abstraction**, **bounded retry policies**, **persistent token/cost observability**, and **prompt version governance** must be resolved.

---

## 2. Component-by-Component Architecture Audit

### 2.1 AI Provider Integrations & Model Configuration
- **Current State:** `backend/app/services/ai_service.py` initializes an `AsyncOpenAI` client targeting either Groq (`openai/gpt-oss-20b` / `llama-3.3-70b-versatile`) or OpenAI (`gpt-4o-mini`).
- **Deficiencies Identified:**
  - Tight coupling to OpenAI-compatible SDKs without discrete provider adapter interfaces for Anthropic Claude or Google Gemini.
  - Retries rely on ad-hoc or SDK defaults rather than explicit, bounded exponential backoff policies with jitter.
  - Missing normalized error envelopes for transient provider outages (e.g., distinguishing rate limits `429` from context window overflow `400` or gateway timeouts `504`).
  - No dynamic cost computation tracking tokens against current provider pricing tables.

### 2.2 Hallucination & Evidence Grounding Pipeline
- **Current State:** 
  - `writing_service.py` contains basic regex sentence extraction and term-overlap checking against project sources.
  - `backend/app/evaluation/evaluators/hallucination_evaluator.py` contains offline number verification, quote verification, and source ID matching.
- **Deficiencies Identified:**
  - Production APIs lack a unified 5-state claim classification (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`).
  - Contradiction detection is not exposed in real-time writing endpoints.
  - Claims lacking statistical evidence or verifiable attribution do not offer structured remediation suggestions for editors.

### 2.3 Citation Integrity & Evidence Traceability
- **Current State:** In-text references use citations like `[1]`, `[2]`, or `[Source: title]`.
- **Deficiencies Identified:**
  - Citations are not automatically cross-referenced against the active project's database source registry on save or update.
  - If a user deletes a source from an investigation, orphaned citations in existing drafts are not flagged.
  - Missing automated check for claims containing precise numbers or quotes that lack an attached citation token.

### 2.4 Prompt Engineering & Version Governance
- **Current State:** Prompts for source analysis, synthesis, newsletter drafting, and selection rewriting are hardcoded multi-line strings scattered across `ai_service.py` and `synthesis_service.py`.
- **Deficiencies Identified:**
  - Zero prompt version tracking: generation records cannot identify which prompt variation produced an output.
  - System prompts and user instructions are mixed together without explicit boundaries.
  - External scraped text is directly interpolated into prompts without defensive delimiters (`<source_content>...</source_content>`), presenting prompt injection vulnerabilities from adversarial web pages.

### 2.5 Token Usage, Cost & Observability
- **Current State:** `monitoring_service.py` holds volatile, in-memory counters (`cumulative_tokens`, `recent_events`).
- **Deficiencies Identified:**
  - In-memory metrics are lost on application restart.
  - Metrics are global rather than partitioned by multi-tenant `organization_id`.
  - No per-operation cost calculation in USD.
  - Lack of authorized REST endpoints for administrative telemetry inspection and latency percentiles (P50, P95, P99).

---

## 3. High-Priority Remediations Plan for Phase 8

| Domain | Required Implementation |
|---|---|
| **Centralized Provider Abstraction** | Build `AIProvider` base class with concrete adapters for Groq, OpenAI, Anthropic, Gemini, and Deterministic Fallback. Include explicit timeouts (15–45s) and bounded exponential retries. |
| **Grounding & Hallucination Engine** | Implement `ClaimVerificationService` with 5-tier classification (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`) and numeric/quote integrity checks. |
| **Citation Integrity Validator** | Implement `CitationValidator` verifying that every citation token points to a completed source in the database, with flags for missing or orphaned citations. |
| **Prompt Version Registry** | Create `PromptRegistry` with semantic versioning (`v1.0.0`), prompt metadata, injection defense guards, and prompt regression verification. |
| **Persistent Observability & Cost Tracking** | Introduce SQLAlchemy `AIOperationLog` table with Alembic migration. Track tokens, latency, status, provider, prompt version, and estimated cost per organization. |
| **Observability API & UI** | Add `/api/v1/observability/ai-metrics` and `/api/v1/observability/operations` endpoints. Extend Settings UI with live health, cost analytics, and claim verification telemetry. |
| **Automated Testing Suite** | Comprehensive pytest suite (`test_phase8_ai_reliability.py`) asserting 100% pass rate across provider adapters, hallucination detection, citation integrity, and cost accounting. |

