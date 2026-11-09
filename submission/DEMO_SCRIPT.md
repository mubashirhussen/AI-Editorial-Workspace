# Presenter Walkthrough Guide: 7–10 Minute Live Demonstration

**Project:** AI Editorial Workspace  
**Presenter:** Mubashir Hussen (Forward Deployed Engineer Candidate)  
**Evaluator Audience:** Technical Assessment Committee & Engineering Mentors  
**Target Time:** 8 Minutes (Target Range: 7–10 Minutes)  

---

## 1. Quick Setup & Start Commands

```powershell
# In terminal 1: Start backend & ensure clean demo database
python backend/scripts/seed_demo_environment.py --reset
backend\venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000

# In terminal 2: Start frontend dev server
npm --prefix frontend run dev
```
**Access:** Open `http://localhost:5173` in Google Chrome or Microsoft Edge.  
**Login:** `demo_editor@thisweekin.ai` / `DemoEditor2026!`

---

## 2. Five-Act Demonstration Narrative

```
[ Act 1: 00:00 - 01:00 ] ──── The Enterprise Problem: Unverifiable AI Generation
[ Act 2: 01:00 - 02:00 ] ──── Executive Workspace Dashboard & Multi-Tenant Topology
[ Act 3: 02:00 - 05:00 ] ──── Research Assistant: SSRF Ingestion & Factual Brief Synthesis
[ Act 4: 05:00 - 08:00 ] ──── Writing Assistant: 9 Deterministic Checks & Version Diffs
[ Act 5: 08:00 - 10:00 ] ──── Reliability Center: Fallbacks, Token Telemetry & Q&A
```

---

### Act 1: The Problem (0:00 – 1:00)
- **Screen:** Login Page (`/auth`) -> Dashboard (`/dashboard`).
- **Narrative:**
  - Standard chatbots make statements without grounding, creating legal and factual exposure for publishers.
  - The AI Editorial Workspace flips this: **No claim without evidence, no publication without a deterministic quality audit**.

---

### Act 2: Workspace Dashboard & Organization Topology (1:00 – 2:00)
- **Screen:** `/dashboard`.
- **Key Points to Highlight:**
  - Multi-tenant tenant switcher showing `This Week in AI — Editorial Desk`.
  - The 4 KPI cards: Active Projects, Verified Sources, Quality Score (84/100), and Real-Time Backend Health (Green `Online` status).
  - Transition to the active project: `Autonomous AI Reasoning & Factual Grounding`.

---

### Act 3: Research Assistant (2:00 – 5:00)
- **Screen:** `/research`.
- **Actions:**
  1. Inspect the 3 pre-ingested sources: DeepSeek-R1, Anthropic MCP Specification, Attention Paper.
  2. Explain the **SSRF Guardrail**: How the backend resolves DNS and checks IP CIDRs before fetching external URLs.
  3. Explore the **Research Brief**:
     - **Evidence Alignment:** Cross-source correlation.
     - **Facts vs. Speculation:** Empirical findings flagged separately from market hype.
     - **Knowledge Graph:** Entity relationship topology.

---

### Act 4: Writing Assistant & Editorial Studio (5:00 – 8:00)
- **Screen:** `/writing` -> `/editorial`.
- **Actions:**
  1. Open draft: `Why Enterprise AI Demands Verified Citations Over Fluent Prose`.
  2. Click **Audit Quality**: Show the 9 deterministic checks running locally.
  3. Show the real-time scores: Flesch Reading Ease (68.4), Grade Level (9.1), Sentence Length.
  4. Click **Highlight Issues**: Demonstrate inline visual annotations of stylistic flaws.
  5. Click **Compare Original vs Revised**: Walk through the character-level semantic diff.
  6. Navigate to `/editorial` and show the final approved edition with inline citation anchors `[SRC-001]`, `[SRC-002]`.

---

### Act 5: Reliability Center & Technical Defense (8:00 – 10:00)
- **Screen:** `/observability` (or `/settings`).
- **Key Points to Highlight:**
  - Token consumption tracking (Prompt vs. Completion tokens).
  - Request tracing via `X-Request-ID` across every client request.
  - **Graceful Fallback Resilience:** Explain that if external LLM APIs fail, the built-in deterministic heuristic engine takes over with zero downtime.
  - Conclude and invite technical questions from the evaluators.

