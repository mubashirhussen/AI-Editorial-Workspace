# PHASE 32 — PRODUCT DEMONSTRATION WALKTHROUGH
## Complete 24-Step End-to-End Live Product Demonstration Guide

**Project:** AI Editorial Workspace — *This Week in AI*  
**Evaluation Role:** Forward Deployed Engineer (FDE) Intern Assessment  
**Production URL:** https://ai-editorial-workspace-blue.vercel.app/  
**Local URL:** `http://localhost:5173` (Frontend) | `http://localhost:8000` (Backend API)  
**Date:** 2026-11-19  

---

## 1. Demonstration Overview & Preparation

This walkthrough demonstrates the real, working AI Editorial Workspace across its full lifecycle: transforming raw technical announcements into evidence-grounded research briefs, executing deterministic linguistic audits in the Writing Assistant, and synthesizing citation-anchored, approved editions in the Editorial Studio.

### Prerequisites & Environment Setup
- **Node.js:** v18.0.0 or higher
- **Python:** v3.10 or higher
- **Local Database:** SQLite (default for instant reproducibility) or PostgreSQL 15
- **Test Credentials:**
  - **Email:** `demo@thisweekin.ai`
  - **Password:** `Password123!`
  - *(Alternatively, register a new account on `/register` or utilize dev mode credentials).*

---

## 2. Step-by-Step 24-Step Demonstration Workflow

### Step 1: Authentication & Workspace Session
1. Navigate to `/login`.
2. Enter email `demo@thisweekin.ai` and password `Password123!`.
3. Click **Sign In**.
4. **Expected Outcome:** User is redirected to `/dashboard` with session token stored and multi-tenant organization context active.

### Step 2: Open Dashboard & Review Live Telemetry
1. Inspect the 4 core metric cards: Total Projects, Ingested Sources, Drafts Analyzed, Editorial Outputs.
2. Observe the **Editorial Lifecycle & Review Status** panel displaying pending human sign-offs.
3. **Expected Outcome:** Metrics are queried dynamically from `/api/dashboard/stats` reflecting real workspace records.

### Step 3: Initialize Investigation Project
1. Click **New Project** or navigate to `/projects`.
2. In the modal, enter:
   - **Title:** `DeepSeek-R1 & Test-Time Compute Reasoning Revolution`
   - **Scope:** `Investigating open-weights reasoning architectures and inference economics.`
3. Click **Create Project**.
4. **Expected Outcome:** Project is persisted with a UUID; user is routed to `/research?projectId=<UUID>`.

### Step 4: Open Research Assistant
1. Verify breadcrumb displays `Workspace / Research Assistant / DeepSeek-R1 & Test-Time Compute...`.
2. Notice the empty state inviting source ingestion.

### Step 5: Add Primary Sources
1. In the **Add Source Material** panel, input the following technical sources:
   - **Source 1 (URL):** `https://github.com/deepseek-ai/DeepSeek-R1` (Title: *DeepSeek-R1 Technical Report*)
   - **Source 2 (URL):** `https://openai.com/index/learning-to-reason-with-llms/` (Title: *OpenAI o1 Reasoning Scaling Laws*)
   - **Source 3 (Text / File):** Paste technical excerpt on Meta Llama 3 dense pre-training.
2. Click **Add to Investigation**.

### Step 6: Ingest & Extract Source Materials
1. Click **Ingest & Extract All Sources**.
2. **Expected Outcome:** Extraction pipeline triggers Trafilatura text extraction, normalizes prose, verifies SSRF safety, and calculates content hashes. Source status badges update to `EXTRACTED` with green checkmarks.

### Step 7: Generate Research Analysis
1. Click **Run Multi-Source Analysis**.
2. **Expected Outcome:** The synthesis engine scans across all sources, extracts key developments, and identifies strategic industry implications with bracketed citation markers `[1]`, `[2]`.

### Step 8: Generate Structured Research Brief
1. Click **Generate Research Brief**.
2. Review generated brief containing:
   - Executive Summary
   - Key Empirical Developments
   - Strategic Implications
   - Potential Newsletter Angles
3. Click **Edit Brief** to make quick refinements, then click **Save Brief Snapshot**.

### Step 9: Inspect Claims & Citations
1. Open the **Evidence & Claim Grounding** tab.
2. Observe discrete 5-state claim classifications:
   - Verified statistics (e.g. *79.8% pass@1 on AIME 2024*) marked `SUPPORTED`.
   - General market projections marked `NOT_VERIFIABLE` with `requires_evidence=False`.
3. Check for any cross-source contradictions flagged between sources.

### Step 10: Open Writing Assistant
1. In the sidebar or top navigation, click **Writing Assistant** (`/writing`).
2. Notice the split-pane layout: Editor on left, Real-Time Linguistic Auditor on right.

### Step 11: Create a Writing Draft
1. Click **New Draft** or edit the active draft.
2. Set Title: `The Open Reasoning Shift: Inference Economics for Founders`.
3. Paste or draft introductory paragraphs analyzing test-time compute.

### Step 12: Generate AI Writing Suggestions
1. Highlight an elongated or passive sentence in the editor.
2. Click the floating or toolbar AI menu $\to$ select **Improve Clarity** or **Simplify Language**.
3. **Expected Outcome:** A non-destructive diff preview appears showing original vs rewritten text with an explanation.

### Step 13: Apply Writing Suggestion
1. Click **Accept Suggestion** (or press shortcut).
2. **Expected Outcome:** The editor text updates in place; autosave status indicates `SAVING` $\to$ `SAVED` within 500ms.

### Step 14: Review Writing Quality & Readability Metrics
1. Inspect the **Linguistic Auditor** panel:
   - **Flesch Reading Ease:** Target $\ge 60$ (Standard / Plain English).
   - **Flesch-Kincaid Grade Level:** Target Grade 8–10.
   - **Hard-to-read sentence counter:** Real-time highlights on sentences exceeding 25 words.
   - **Passive voice ratio:** Target $< 10\%$.

### Step 15: Open Editorial Studio
1. Navigate to **Editorial Studio** (`/editorial`).
2. Notice the project selector: select `DeepSeek-R1 & Test-Time Compute Reasoning Revolution`.

### Step 16: Select Research Brief & Angle
1. The studio automatically loads the linked research brief.
2. In the **Select Newsletter Angle** dropdown, choose:
   - *Angle 1: The Open-Weights Frontier: How Distilled Reasoning Commoditizes Closed APIs*.

### Step 17: Generate Full Editorial Edition
1. Set Target Word Count: `300–500 words`.
2. Set Audience: `Founders, builders, and operators`.
3. Set Tone: `Authoritative, analytical, hook-driven`.
4. Click **Generate Editorial Draft**.
5. **Expected Outcome:** Structured edition is generated with headline, subtitle, body paragraphs, and embedded citation tags `[1]`, `[2]`.

### Step 18: Edit the Editorial in Editorial Studio
1. Review the generated edition in the editor pane.
2. Make inline copy adjustments, add subheadings, or refine phrasing.
3. Observe the live word counter updating dynamically.

### Step 19: Review Quality & Grounding Audit
1. Switch view mode to **Quality Audit & Review**.
2. Inspect the **Grounding Audit Report**:
   - Total claims identified.
   - Grounding score (e.g. $95\%+$).
   - Citation accuracy ($100\%$ valid citations referencing active sources).
   - Absence of fabricated or tampered citation tags.

### Step 20: Inspect Citations & Evidence Traceability
1. Click on inline citation `[1]`.
2. The **Source References** drawer highlights the exact source excerpt and author metadata.

### Step 21: Editorial Review & Peer Sign-Off
1. Switch to the **Review & Approval** tab.
2. Add an editorial review comment: `"Grounded empirical analysis with verified benchmarks. Approved for publication."`
3. If signed in as an authorized editor, select decision **APPROVED**.
4. *(Note: The system strictly prevents self-approval if the reviewer is the draft author, enforcing editorial governance).*

### Step 22: Finalize Editorial
1. Click **Finalize Edition**.
2. **Expected Outcome:** Draft status transitions to `FINALIZED`; editing is locked to preserve version integrity.

### Step 23: Multi-Format Export
1. Click **Export Edition**.
2. Select desired format:
   - **HTML:** Standalone publication-ready HTML with responsive styling, serif typography, and citation footnotes.
   - **Markdown:** Clean markdown for newsletter platforms (Substack, Beehiiv, Ghost).
   - **Plain Text:** Plaintext wire format.
3. Click **Download File** (or **Copy to Clipboard**).

### Step 24: Verify Exported File
1. Open the downloaded `.html` or `.md` file.
2. Verify:
   - Headline and executive summary are intact.
   - All citations `[1]`, `[2]` are correctly anchored.
   - Clean, validated markup without broken entities.

---

## 3. Failure Recovery & Fallback Demonstration

If external LLM providers (Groq, OpenAI, Anthropic, Gemini) experience network latency or rate-limiting:
- The **AIRouter** automatically switches to the built-in deterministic offline fallback engine (`FallbackAdapter`).
- Generation completes with zero user-visible exceptions.
- Telemetry captures the fallback event under `/observability` for auditability.
