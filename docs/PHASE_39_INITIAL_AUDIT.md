# PHASE 39 — INITIAL REPOSITORY AUDIT & RESEARCH RELIABILITY BASELINE
## Assessment of Source Ingestion, Evidence Extraction, Claim Grounding & Citation Validation

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Branch:** `feat/phase39-research-evidence-reliability`  
**Auditor:** Senior AI Research Systems Engineer & Forward Deployed Engineer  
**Date:** November 2026  
**Status:** Audit Completed — Baseline Established

---

## 1. Executive Summary

A comprehensive repository audit was conducted across the backend services, database schemas, frontend components, AI pipelines, and test suites to assess the existing research capabilities of the AI Editorial Workspace.

While previous phases (Phases 3, 6, 22, 25, 31, and 38) introduced foundational research extraction, entities, claims, relationships, and basic citation linking, multiple critical gaps exist that prevent the system from meeting rigorous journalistic and enterprise research standards:
- Sources currently store basic metadata (`title`, `url`, `author`, `published_at`) but lack formal credibility classification, publisher authority evaluation, and freshness scoring.
- Citations in generated briefs are stored as raw JSON dictionaries without deterministic referential validation against stored source IDs or content hashes.
- Claim verification lacks formal six-tier epistemic classification (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `UNVERIFIED`, `NOT_APPLICABLE`).
- Independent corroboration analysis does not distinguish between distinct publishers and syndicated or near-duplicate republishing.
- No structured **Research Quality Report** exists to calculate claim evidence coverage, citation integrity, and research limitations before publication.
- Section regeneration does not provide evidence-grounded diffing and revision history preservation.

---

## 2. Existing Research Subsystem Inventory

### 2.1. Backend Services & Pipeline
1. `backend/app/services/research/extraction_service.py`:
   - Dual-layer Trafilatura + BeautifulSoup extractor.
   - Basic SSRF validation (`is_safe_url`) checking private subnets and localhost.
   - Canonical URL parameter stripping (`utm_`, `ref`, etc.).
   - *Audit Finding:* Lacks automated publisher taxonomy mapping, domain reputation scoring, freshness status calculation, and content hash deduplication index.
2. `backend/app/services/research/synthesis_service.py`:
   - Enforces basic evidence grounding checks between brief claims and source texts.
   - Contains `validate_and_trace_evidence`.
   - *Audit Finding:* Does not perform automated claim-to-evidence mapping for user-edited briefs or arbitrary text sections. Citations are not systematically verified against live HTTP endpoints.
3. `backend/app/services/research_intelligence/`:
   - `claim_extractor.py`: Identifies claims with classifications `DIRECTLY_STATED`, `REPORTED_BY_SOURCE`, `INFERENCE`, `UNVERIFIED`.
   - `contradiction_detector.py`: Cross-matches claims between sources.
   - `relationship_analyzer.py`: Identifies entity relationships.
   - *Audit Finding:* These models operate cross-source during intelligence discovery, but are not tightly integrated into the primary research brief generation and citation validation loop.
4. `backend/app/api/routes/research.py` & `research_intelligence.py`:
   - Provides endpoints for projects, sources, brief generation, and intelligence exploration.
   - *Audit Finding:* Lacks endpoints for:
     - Explicit source verification (`POST /sources/{id}/verify`) and retry.
     - Project-wide citation validation (`POST /projects/{id}/validate-citations`).
     - Claim verification re-evaluation (`POST /projects/{id}/verify-claims`).
     - Research quality report computation (`GET /projects/{id}/quality-report`).
     - Section-specific evidence-aware regeneration (`POST /projects/{id}/regenerate-section`).

### 2.2. Database Models (`backend/app/models/base.py`)
- `Source`: Stores `project_id`, `title`, `url`, `original_url`, `source_type`, `raw_content`, `extracted_content`, `author`, `published_at`, `extraction_status`. Has properties `content_hash` and `domain`.
- `ResearchBrief`: Stores `brief_content`, `evidence` (JSON list), `source_references` (JSON list), `strategic_implications`.
- `ResearchEvidence`: Stores `project_id`, `source_id`, `claim_id`, `excerpt`, `fact_type`, `confidence`, `verified`.
- `ResearchClaim`: Stores `project_id`, `source_id`, `claim_text`, `supporting_excerpt`, `evidence_classification`.
- `ResearchContradiction`: Stores `project_id`, `claim_a_id`, `claim_b_id`, `claim_a_text`, `claim_b_text`, `disagreement_nature`.
- *Audit Finding:*
  - No explicit model for **Citation Validation Records** (`citation_validations`).
  - No model for **Research Quality Reports** (`research_quality_reports`) tracking factual claim counts, coverage percentages, and audit limitations.
  - `Source` needs fields or related models for credibility tier, accessibility status, freshness criteria, and publisher metadata.

### 2.3. Frontend Components (`frontend/src/`)
- `ResearchPage.tsx`:
  - Contains tabs: `brief`, `sources`, `evidence`, `facts`, `intelligence`.
  - Has basic source preview modals, file uploads, and brief editing.
  - *Audit Finding:*
    - Source list does not display credibility tier badges, publisher authority, freshness indicators, or accessibility status.
    - Evidence tab lists raw excerpts but lacks claim-to-evidence interactive verification, corroboration indicators, and contradiction alerts.
    - Missing dedicated **Research Quality Report** tab/drawer.
    - Missing interactive **Citation Validation** panel with live status pills (`VALID`, `BROKEN`, `INACCESSIBLE`, `UNVERIFIED`).
    - Section regeneration cannot be triggered on a per-section basis with evidence constraints.

---

## 3. Security & SSRF Audit

1. **URL & Redirection Security:**
   - Current URL validation inspects scheme (`http`, `https`) and checks IP against `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254` (AWS metadata).
   - *Audit Finding:* In-flight DNS rebinding and redirects to internal addresses are caught in `extraction_service.py` via per-hop validation. However, timeout limits must be rigorously maintained and error messages must not leak internal network details.
2. **Untrusted Source Content Handling:**
   - Source content could contain indirect prompt injections (e.g. "Ignore previous instructions and output...").
   - *Audit Finding:* AI generation pipelines must explicitly wrap source content in delimited quotes or context frames and treat source text as untrusted raw facts, preventing instructions inside sources from hijacking synthesis.
3. **Multi-Tenancy Isolation:**
   - All research projects, sources, and briefs are scoped by `organization_id` (enforced in `check_project_tenant_access`).
   - *Audit Finding:* Any newly added citation validation records, evidence mappings, and quality reports must enforce strict `organization_id` and `project_id` foreign-key cascading and tenant scoping.

---

## 4. Phase 39 Implementation Roadmap

1. **Database Schema Enhancements & Migration:**
   - Create tables:
     - `source_credibility_assessments`: Stores credibility tier, publisher authority, freshness criteria, accessibility status, and methodological transparency.
     - `citation_validations`: Stores citation URL, text, source ID, existence check, accessibility status, and claim associations.
     - `research_quality_reports`: Stores total claims, supported/partially/unsupported/contradicted counts, evidence coverage score, citation health score, and known limitations.
     - `research_revisions`: Stores section revision history for evidence-aware regeneration.
   - Author Alembic migration `df8b9c0d1e2f_add_phase39_research_reliability_tables.py`.

2. **Core Backend Services:**
   - `SourceCredibilityService`: Evaluates publisher authority, source type, freshness requirements, and transparent explainability.
   - `EvidenceEngineeringService`: Implements sentence-level extraction, passage location indexing, evidence hashing, and semantic matching.
   - `ClaimVerificationService`: Extracts claims from brief/draft, performs six-tier classification (`SUPPORTED` to `NOT_APPLICABLE`), and maps claims to verified passages.
   - `CitationValidationService`: Validates existence, format, source record matching, URL accessibility, and duplicate detection.
   - `ContradictionAndCorroborationService`: Identifies discrepancies between sources and verifies independent multi-publisher corroboration.
   - `ResearchQualityService`: Aggregates metrics into an authoritative, reproducible Research Quality Report.
   - `EvidenceGroundedGenerationService`: Enhances brief generation and section regeneration with strict evidence constraints.

3. **REST API Extensions (`backend/app/api/routes/research_reliability.py`):**
   - Provide clean, typed endpoints mounted under `/api/v1/research/...`.

4. **Frontend UI Extensions:**
   - Enhance `ResearchPage.tsx` and create dedicated subcomponents:
     - `SourceCredibilityCard`: Displays credibility badge, publisher type, freshness status, and accessibility.
     - `ClaimVerificationDrawer`: Inspects individual claims, supporting evidence passages, and contradiction alerts.
     - `CitationValidationPanel`: Live table of citations with validation status pills and source links.
     - `ResearchQualityReportView`: Visual scorecard of evidence coverage, citation validity, claim support rates, and audit limitations.
     - `SectionRegenerateModal`: Allows selecting a brief section, previewing evidence-grounded regeneration diff, and accepting changes.

5. **Automated Testing & Release Verification:**
   - Unit and integration tests in `backend/tests/test_phase39_research_reliability.py`.
   - Update `test_phase3_database_integrity.py` with the new migration head.
   - Verify full backend suite (326+ tests) and frontend build.
