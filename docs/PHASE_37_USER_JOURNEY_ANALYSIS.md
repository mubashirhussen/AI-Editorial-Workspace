# Phase 37: User Journey Intelligence & Workflow Bottleneck Analysis

**Project:** AI Editorial Workspace — This Week in AI  
**Focus:** Quantitative Analysis of User Progression Across Research, Writing, and Editorial Pipelines  
**Audience:** Product Engineering, UX Researchers, Forward Deployed Engineers  

---

## 1. Editorial Workflow Lifecycle Architecture

The AI Editorial Workspace supports three decoupled yet interconnected editorial journeys:

```
  ┌──────────────────────────────────────────────────────────┐
  │ 1. RESEARCH JOURNEY (Knowledge Ingestion)                │
  │ Project ──► Sources Ingested ──► Brief Synthesized       │
  └─────────────────────────────┬────────────────────────────┘
                                │ (Brief & Sources)
                                ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 2. WRITING JOURNEY (Drafting & Quality Enforcement)      │
  │ Draft Init ──► AI Rewrite ──► Style Audit ──► Draft Saved│
  └─────────────────────────────┬────────────────────────────┘
                                │ (Verified Draft)
                                ▼
  ┌──────────────────────────────────────────────────────────┐
  │ 3. EDITORIAL JOURNEY (Studio & Peer Review Governance)   │
  │ Studio Opened ──► Edition Generated ──► Approved ──► Export
  └──────────────────────────────────────────────────────────┘
```

---

## 2. Quantitative Journey Analysis

### 2.1 Research Knowledge Ingestion Journey
- **Milestone 1 — Source Addition (`research_source_added`):**
  - Measures the entry point of an investigation.
  - Typical sources: PDF whitepapers, arXiv publications, technical URLs.
- **Milestone 2 — Extraction & SSRF Verification (`research_source_processing_completed`):**
  - Measures backend ingestion success.
  - **Identified Bottleneck / Friction Point:** Malformed web pages or slow network sockets. When extraction fails, the pipeline transitions to `research_source_processing_failed` with `EXTRACTION_FAILURE` error code.
- **Milestone 3 — Research Brief Synthesis (`research_brief_generation_completed`):**
  - Measures AI extraction of claims, separation of facts from speculation, and citation mapping.
  - Target SLA: < 15 seconds.
- **Milestone 4 — Export / Transition (`research_brief_exported`):**
  - Measures utilization of the brief either as an export or forwarded into drafting.

### 2.2 Assisted Composition Journey
- **Milestone 1 — Draft Creation (`writing_draft_created`):**
  - User starts drafting directly or uses the research brief as an outline.
- **Milestone 2 — Writing Assistance Requested (`writing_assistance_requested`):**
  - Editor highlights prose or requests style checks against publication tone rules.
- **Milestone 3 — Suggestion Acceptance / Polish (`writing_assistance_completed`):**
  - In-process Deterministic Linguistic Auditor checks readability (Flesch Reading Ease), passive voice ratios, and word count.
- **Milestone 4 — Draft Completion & Save (`writing_draft_saved`):**
  - Version snapshots recorded with character-level diffs.

### 2.3 Editorial Studio & Publication Journey
- **Milestone 1 — Studio Opened (`editorial_workspace_opened`):**
  - Editorial desk selects verified research project and draft.
- **Milestone 2 — Edition Bundling (`editorial_generation_completed`):**
  - AI synthesizes publication-ready newsletter draft with strict source citations.
- **Milestone 3 — Peer Review & Comment Resolution (`editorial_review_completed`):**
  - Human editor conducts peer review; leaves section-specific comments.
- **Milestone 4 — Approval Gate (`editorial_approved`):**
  - Enforces `APPROVE_EDITORIALS` permission. Enforces self-approval guard (authors cannot approve their own drafts without independent peer review).
- **Milestone 5 — Finalization & Syndication (`editorial_finalized` / `editorial_exported`):**
  - Edition is sealed and exported in Markdown, TXT, HTML5, or JSON.

---

## 3. Product Friction & Abandonment Detection

### Definition of Abandonment vs Failure
- **Workflow Failure (`workflow_failed`):** Confirmed unrecoverable error emitted by backend (e.g. database constraint error, SSRF block, AI provider outage).
- **Workflow Abandonment (`workflow_abandoned`):** A workflow initiated (`status = "started"`) that has no subsequent milestone event recorded within a 2-hour sliding window.
- **Bottleneck Identification:** The system calculates drop-off counts between consecutive funnel stages. When drop-off exceeds 25% of stage entrants, `AnalyticsService.get_workflows()` flags that specific step as an active bottleneck requiring UX or reliability intervention.
