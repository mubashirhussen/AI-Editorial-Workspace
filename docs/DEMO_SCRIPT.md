# AI Editorial Workspace — Live Product Demonstration Playbook

**System:** AI Editorial Workspace  
**Assignment:** Forward Deployed Engineer (FDE) Intern Assessment  
**Publication:** *This Week in AI*  
**Presenter:** Mubashir Hussain  
**Format:** Live Technical Walkthrough & Architecture Defense  
**Total Target Time:** 7 to 10 Minutes  

---

## Demonstration Overview

```
========================================================================================
Demo Segment          Focus Area                                      Key Capabilities
========================================================================================
DEMO 1: Research      Source Ingestion & Evidence Triangulation       SSRF defense, Trafilatura extraction,
(3.5 Minutes)                                                         Facts vs Analysis vs Speculation,
                                                                      10-section structured brief synthesis.
----------------------------------------------------------------------------------------
DEMO 2: Writing       Editorial Studio & Quality Intelligence         Inverted pyramid generation, Hemingway
(3.5 Minutes)                                                         6-check style audit, selection-level
                                                                      rewrites, version history & rollbacks.
----------------------------------------------------------------------------------------
DEMO 3: Reliability   Fault-Tolerance, Grounding & Observability     Deterministic offline fallback, 5-tier
(3.0 Minutes)                                                         claim verification, multi-tenant RBAC,
                                                                      token cost ($USD) & benchmark runner.
========================================================================================
```

---

## DEMO 1: Research Assistant — Multi-Source Ingestion & Evidence Triangulation

### Objective
Demonstrate how an editor ingests raw, heterogeneous AI announcements and converts them into a structured, evidence-backed research brief.

### Step-by-Step Execution:
1. **Navigate to Research Assistant:**
   - Open browser at `http://localhost:5173/research` (or click **Research Assistant** in sidebar).
   - Verify green connection pill in header shows `Backend connected`.
2. **Select or Create an Investigation:**
   - Click the project dropdown in the top right.
   - Click **"+ New"**, enter title: `Frontier LLM Reasoning & Test-Time Compute`, and click OK.
3. **Ingest Credible Research Sources:**
   - In the **Ingest Source Material** card, ensure **Web URL** tab is selected.
   - Click the button **"Quick Load 3 Sample URLs"** (or paste 3 URLs):
     ```
     https://deepmind.google/technologies/gemini/
     https://en.wikipedia.org/wiki/Large_language_model
     https://arxiv.org/abs/1706.03762
     ```
   - Click **"+ Add 3 Sources to Investigation"**.
   - *Observation:* Status toast indicates parallel extraction. All 3 sources appear under **Verified Sources** with word counts, timestamps, and domain badges.
4. **Demonstrate SSRF Protection:**
   - Enter malicious target URL: `http://169.254.169.254/latest/meta-data/` or `http://127.0.0.1:8000/api/v1/auth/me`.
   - Click **"+ Add Source to Investigation"**.
   - *Observation:* Request is immediately blocked with a security alert: `"URL resolves to a protected or private IP address (SSRF Guardrail Triggered)"`.
5. **Inspect Epistemic Triangulation (Facts vs. Analysis vs. Speculation):**
   - Click the tab **Facts vs Analysis vs Speculation**.
   - *Observation:* Verified Facts (empirical figures, benchmark scores), Editorial Analysis (interpretations), and Speculation (unsupported roadmaps) are categorized with direct citation links.
6. **Generate 10-Section Research Brief:**
   - Click the top button **"Generate Brief (3/3 Sources)"**.
   - *Observation:* The workspace synthesizes Sections A through J: Executive Summary, Architectural Breakthroughs, Comparative Trade-Offs, and Editorial Angles.

---

## DEMO 2: Writing Assistant — Editorial Intelligence & Non-Destructive Quality Auditing

### Objective
Demonstrate how the workspace transforms a research brief into an authoritative, publication-ready article while enforcing high-impact readability.

### Step-by-Step Execution:
1. **Navigate to Writing Assistant:**
   - Click **Writing Assistant** in the sidebar (`http://localhost:5173/writing`).
2. **Configure Editorial Audience & Tone:**
   - Select target audience: `Senior Engineers & Founders`.
   - Select editorial tone: `Authoritative & Analytical`.
   - Click **"Generate Editorial Draft"**.
   - *Observation:* A 350-word article is synthesized following the **inverted pyramid structure**, leading with core conclusions and embedding verifiable citations `[1]`, `[2]`.
3. **Run Interactive Hemingway Quality Audit:**
   - Click the button **"Audit Style & Readability"**.
   - *Observation:* The right-hand panel displays the 6 Hemingway checks:
     - Sentence Length (>25 words)
     - Passive Voice constructions
     - Wordy Filler phrases (`in order to` $\rightarrow$ `to`)
     - Technical Jargon abbreviations
     - Repetitive sentence starters
     - Exact Flesch Reading Ease score
4. **Perform Surgical Non-Destructive Rewriting:**
   - Under Filler Phrases, click **"Accept"** on a suggestion.
   - *Observation:* Only the target sentence boundary is updated in `revised_content`. Surrounding sentences and citations remain intact. Readability score updates immediately.
5. **Selection-Level Targeted Transformation:**
   - Highlight any sentence or paragraph in the rich editor.
   - Click the floating toolbar option **"Make Punchy"** or **"Simplify"**.
   - *Observation:* The transformation generates an inline diff preview showing removals in red and additions in green. Click **"Apply"** to accept.
6. **Version Snapshots & Safe Rollback:**
   - Click **"Version History"** in the editor toolbar.
   - *Observation:* View previous timestamped snapshots (`v1`, `v2`, `v3`). Select `v1` and click **"Restore Snapshot"** to demonstrate non-destructive rollback.
7. **Multi-Format Export:**
   - Click **"Export"** in the top right.
   - Choose between **Markdown (.md)**, **Plain Text (.txt)**, or **Sanitized HTML5 (.html)** with escaped entities and styled citation pills.

---

## DEMO 3: Reliability, Grounding, Multi-Tenancy & Observability

### Objective
Prove that the application is fault-tolerant, hallucination-resistant, strictly multi-tenant, and measurable.

### Step-by-Step Execution:
1. **Demonstrate AI Provider Failure & Deterministic Fallback:**
   - Open **Settings** (`/settings`) $\rightarrow$ **AI Engine & LLM**.
   - Observe that even when no paid API keys are configured, the system displays:
     `Failover Security: Deterministic Fallback Active (0% Downtime Guarantee)`.
   - Execute a draft generation or claim audit—it succeeds in under 20ms using local deterministic NLP heuristics.
2. **Demonstrate 5-Tier Evidence Grounding & Hallucination Auditing:**
   - In Writing Assistant, click **"Audit Research Grounding"**.
   - *Observation:* Sentences are color-coded:
     - 🟢 `SUPPORTED`: Overlaps with source document excerpts.
     - 🟡 `PARTIALLY_SUPPORTED`: Missing nuance.
     - 🔴 `UNSUPPORTED`: Contains ungrounded numerical figures.
     - 🟣 `CONTRADICTED`: Asserts opposite claims (e.g. "latency increased" vs source "latency decreased").
3. **Demonstrate Multi-Tenant Access Governance:**
   - Open **Workspace Management** (`/organization`).
   - Show active organization (`Personal Workspace`) and user role (`OWNER`).
   - Invite a new member as `VIEWER`.
   - Log in as the `VIEWER`—verify that the "Generate Brief" and "Edit Draft" buttons are strictly disabled and return HTTP 403 if invoked directly.
4. **Inspect Observability & Token Cost Dashboard:**
   - Open **Settings** $\rightarrow$ **Observability & SRE**.
   - *Observation:* Live telemetry cards show:
     - Total AI Operations
     - Success Rate (100%)
     - Total Tokens Processed (Prompt vs. Completion)
     - Estimated Cost ($USD) calculated from real provider schedules
5. **Run the 34-Case Benchmark Suite from UI:**
   - In the Observability tab, click **"Run 34-Case Evaluation Benchmark"**.
   - *Observation:* The modal runs all 34 evaluation cases across Research, Writing, Style, and Hallucination recall, displaying a **100% Pass Rate** badge.
