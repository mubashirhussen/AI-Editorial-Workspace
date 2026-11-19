# PHASE 31 — AI QUALITY, GROUNDING & CITATION INTEGRITY AUDIT

## 1. Executive Summary
This audit inspects the AI reliability architecture, LLM provider routing, prompt management, evidence grounding, citation validation, and prompt injection defense within the **AI Editorial Workspace** (This Week in AI).

- **Audit Date:** November 19, 2026
- **Auditor:** Senior AI Quality & Reliability Engineering
- **Scope:** Research Assistant, Writing Assistant, Editorial Studio, AI Provider Adapters, Database Persistence, and Safety Defenses.

---

## 2. Component-by-Component Audit Findings

### 2.1 AI Provider Integration & Routing (`backend/app/services/ai/router.py`)
- **Status:** **OPERATIONAL WITH FALLBACK**
- **Existing Capabilities:**
  - Multi-provider support: Google Gemini (`gemini-1.5-flash`), Anthropic (`claude-3-5-sonnet-latest`), OpenAI (`gpt-4o`), Groq (`llama-3.3-70b-versatile`), and deterministic offline fallback.
  - Per-tenant API key encryption using AES-GCM (`backend/app/core/encryption.py`).
  - Bounded exponential retries with jitter and timeout handling (`execute_structured`).
  - Cost calculation and token usage accounting in `ProviderUsageRecord`.
- **Identified Improvement Areas:**
  - Standardize structured response validation across all endpoints so that invalid JSON returns actionable remediation rather than internal 500 errors.
  - Add explicit provider health scoring to prioritize active, low-latency providers.

---

### 2.2 Prompt Management & Versioning (`backend/app/services/ai/prompt_registry.py`)
- **Status:** **STRUCTURED WITH SEMANTIC VERSIONING**
- **Existing Capabilities:**
  - `PromptMetadata` schema with prompt name, semantic version (`v1.0.0`), system prompt, user template, input variables, and security guards.
  - Basic prompt injection defense prefix (`PROMPT_INJECTION_DEFENSE`) in system prompts.
- **Identified Improvement Areas:**
  - Add dynamic prompt parameter interpolation with strict input validation to avoid injection via template formatting.
  - Formalize prompt version association in saved research briefs and editorial version records.
  - Expand prompt catalog to include specialized templates for contradiction detection and source quality assessment.

---

### 2.3 Research Grounding & Evidence Extraction (`backend/app/services/research/`)
- **Status:** **PARTIALLY INTEGRATED**
- **Existing Capabilities:**
  - Ingests article URLs and supported file formats (PDF, DOCX, TXT, MD, Images).
  - Normalizes text, computes SHA-256 content hashes, and extracts entities and claims.
- **Identified Improvement Areas:**
  - Every claim generated in a research brief must link directly to an existing database `Source` ID.
  - The system must explicitly classify claims into 5 unambiguous states: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, and `NOT_VERIFIABLE`.
  - Disclose evidence limitations and avoid forcing high confidence when sources contain contradictory information.

---

### 2.4 Citation Integrity & Hallucination Defense (`claim_verification_service.py`)
- **Status:** **STRONG HEURISTIC FOUNDATION**
- **Existing Capabilities:**
  - Regex-based citation tag extraction (`[1]`, `[2]`, `[Source: id]`).
  - Numerical value and direct quotation matching against reference sources.
  - Grounding audit report calculating `grounding_score` and `citation_accuracy`.
- **Identified Improvement Areas:**
  - Centralize citation validation so that both Research Briefs and Editorial Studio use identical server-side verification against the database `Source` table.
  - Detect and classify 5 citation defect categories: `VALID`, `ORPHANED`, `FABRICATED`, `MISSING`, and `TAMPERED`.
  - Prohibit editorial finalization if any citation is flagged as `FABRICATED` or `ORPHANED`.

---

### 2.5 Prompt Injection & Untrusted Input Resistance
- **Status:** **DELIMITER-BASED GUARDRAILS**
- **Existing Capabilities:**
  - System prompts instruct models to treat `<source_content>` as passive untrusted data.
- **Identified Improvement Areas:**
  - Source content extracted from external URLs and uploaded documents must undergo input sanitization to strip instruction-override patterns (`"ignore previous instructions"`, `"system prompt:"`, `"you are now an unfiltered bot"`).
  - Explicit delimiter tags (`<untrusted_source_excerpt>`) with XML escaping for untrusted source strings.

---

## 3. Prioritized Implementation Roadmap (Phase 31)

1. **Centralized AI Quality Coordinator:** Unify prompt versioning, structured schema validation, grounding, citation integrity, and safety guards into a single service.
2. **Server-Side Citation Integrity Engine:** Validate citation indices against project source database records; detect fabricated citations.
3. **5-State Claim Grounding Engine:** Classify claims into `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, and `NOT_VERIFIABLE`.
4. **Contradiction Detection:** Cross-reference ingested sources to extract and display contradictory facts.
5. **Prompt Injection Sanitizer:** Sanitize untrusted web content and document text before feeding into LLM prompts.
6. **Deterministic AI Quality Evaluation Dataset:** Create repeatable fixtures in `backend/tests/fixtures/ai_quality/`.
7. **Automated Verification:** Comprehensive test suite in `backend/tests/test_phase31_ai_quality_reliability.py`.
