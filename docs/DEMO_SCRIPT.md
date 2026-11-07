# AI Editorial Workspace — Live Product Demonstration Playbook

**Target Audience:** Technical Hiring Manager & Lead Editorial Engineers  
**Role:** Forward Deployed Engineer (FDE) Intern Assessment Handover  
**System:** AI Editorial Workspace  
**Presenter:** Mubashir Hussain  
**Format:** Live Technical Walkthrough & Architecture Defense  
**Total Target Time:** 5 to 7 Minutes  
**Branch:** `docs/phase10-final-assessment-handover`

---

## 1. Demo Schedule & Timing Breakdown

| Segment | Duration | Screen / Feature | Key Objective |
| :--- | :---: | :--- | :--- |
| **1. Problem Statement** | 0:45 | Dashboard / Slides | Establish the dual pain points: hallucination vs. cognitive bloat. |
| **2. Research Assistant** | 2:00 | `/research` (Local Library) | Demonstrate multi-source ingestion, SSRF protection, and chunk inspection. |
| **3. Evidence Triangulation**| 1:00 | Research Brief & Claims | Show 5-tier claim verification and Facts vs. Speculation sorting. |
| **4. Writing Assistant** | 2:00 | `/writing` (Notalx + Afforai) | Show templates, Afforai citation manager, inline linter, and rewrite cards. |
| **5. Observability & SRE** | 1:00 | `/observability` (APM/RUM) | Present Splunk RUM, Instana APM metrics, token cost, and offline fallback. |
| **Total Target Time** | **6:45** | | |

---

## 2. Step-by-Step Live Walkthrough Playbook

### Segment 1: Introduction & Problem Context (0:00 – 0:45)
- **Screen:** Open browser at `http://localhost:5173/` (Dashboard Overview).
- **What to Say:**
  > *"Welcome everyone. In technical media, newsletter publishing, and developer relations, content quality cannot be compromised by factual errors. Editorial teams face two major dilemmas today: first, reading dozens of technical papers and cross-referencing vendor claims takes 10+ hours per article. Second, generic LLMs hallucinate plausible statistics, sever citation provenance, and flatten technical cadence into bland corporate jargon.*
  >
  > *Today, I'm excited to demonstrate the AI Editorial Workspace: an evidence-grounded platform engineered specifically for technical journalists. It guarantees 100% citation traceability, deterministic style auditing, and enterprise-grade multi-tenant security."*
- **Expected Result:** Clean dashboard displaying active projects, recent drafts, and system health status.
- **Fallback:** If local server isn't running, run `npm --prefix frontend run dev` and `uvicorn backend.app.main:app --port 8000`.

---

### Segment 2: Research Assistant & Local Library Ingestion (0:45 – 2:45)
- **Screen:** Navigate to `/research` by clicking **Research Assistant** in the sidebar.
- **Action 1 (Project Setup):** Click the project dropdown, select or create project: `Frontier Reasoning & Open Weights`.
- **Action 2 (Local Library View):** Click the **"Local Library"** button in the header.
- **What to Say:**
  > *"Here is our Local Library hub. In the header, we see real-time telemetry: 409 indexed sources, over 24,000 retrieval chunks across 11 formats. On the left, we can filter by Research Paper, Document, or Web URL, and toggle pinned sources.*
  >
  > *When we inspect a research paper like 'Attention Is All You Need', notice how the system extracts the structural Outline, isolates verified Key Claims, captures curation metadata including AI enrichment model provenance, and allows granular inspection of indexed 150-word retrieval chunks with character offsets."*
- **Action 3 (Demonstrate Ingestion & SSRF Protection):** Close the Local Library modal. In the **Ingest Source Material** box, type a malicious cloud metadata endpoint: `http://169.254.169.254/latest/meta-data/` and click Submit.
- **What to Say:**
  > *"Because this platform ingests untrusted user URLs, security is paramount. Notice that when I attempt to input an AWS metadata endpoint or loopback IP, the request is immediately intercepted by our backend SSRF guardrail, preventing internal infrastructure probing."*
- **Expected Result:** Toast notification: `"URL resolves to a protected or private IP address (SSRF Guardrail Triggered)"`.
- **Action 4 (Load Verified Research):** Click **"Quick Load 3 Sample URLs"** (DeepMind Gemini, LLMs Wikipedia, ArXiv Transformer) and click **"Add Sources"**.
- **Expected Result:** Sources appear with green checkmarks, word counts, and cryptographic SHA-256 fingerprints.

---

### Segment 3: Evidence Triangulation & Brief Synthesis (2:45 – 3:45)
- **Screen:** In `/research`, click **"Generate Brief"** (or switch to the **Evidence Alignment** tab).
- **What to Say:**
  > *"Now we execute cross-source synthesis. Rather than blindly trusting text, the engine executes epistemic triangulation. It extracts key claims and assigns each a 5-tier verification verdict: SUPPORTED, PARTIALLY_SUPPORTED, or UNSUPPORTED.*
  >
  > *Notice the 'Facts vs Speculation' tab: empirical benchmarks like DeepSeek's 79.8% AIME score are cataloged as Verified Facts, while ungrounded claims like 'pure RL will solve all software engineering in 12 months' are flagged as Unsupported Speculation."*
- **Expected Result:** 10-section research brief loads with verified inline source pills `[1]`, `[2]`.
- **Fallback:** If external API times out, the `DeterministicFallbackAdapter` automatically generates the structured brief in <50ms.

---

### Segment 4: Writing Assistant, Afforai Cite & Hemingway Linters (3:45 – 5:45)
- **Screen:** Navigate to `/writing` in the sidebar.
- **Action 1 (Notalx Quick Templates):** Click **"Let's Write"** in the top action bar. Select **"Weekly AI newsletter"**.
- **What to Say:**
  > *"Moving to the Writing Assistant. For rapid drafting, editors can open our Notalx-style template drawer and load pre-structured frameworks—from weekly newsletters to technical explainers."*
- **Action 2 (Afforai Cite Extension):** Click **"Afforai Cite"** in the top action bar. Search for `Garcia`, check two citations, and click **"Insert Selected Citations"**.
- **What to Say:**
  > *"To eliminate citation syntax errors, we built the Afforai Cite Extension. Writers search connected project references, select multiple sources, and insert formatted citation anchors directly into the text with one click. In the side panel, writers can rephrase complex technical paragraphs with real-time research grounding."*
- **Action 3 (Inline Readability Linter & Highlighting):** Toggle **"Highlight issues"** in the editor.
- **What to Say:**
  > *"Notice how the prose is dynamically highlighted in real-time: purple for hard-to-read sentences over 25 words, blue for passive voice, and amber for technical jargon. When I click a purple highlight, a tooltip popover appears with a single-click 'Simplify' button that non-destructively rewrites only that bounded sentence span, preserving the surrounding text and citations."*
- **Action 4 (Article Improvements Panel):** Point to the right sidebar score bar (*Overall score: Good (72/100)*).
- **What to Say:**
  > *"On the right, our Article Improvements panel tracks overall quality across SEO, Readability, and Tone. Each flagged issue has a dedicated Rewrite card powered by our backend style intelligence engine."*
- **Expected Result:** Sentence is replaced with a punchy, active phrasing; Flesch score jumps from 42 to 65.

---

### Segment 5: Observability, DevSecOps & Production Reliability (5:45 – 6:45)
- **Screen:** Navigate to `/observability` in the sidebar.
- **What to Say:**
  > *"Finally, let's examine enterprise observability and production readiness. On this page, we mirror Splunk RUM and Instana APM telemetry. We track real-user Core Web Vitals with LCP under 2.5 seconds, client JavaScript errors, latency distributions—including P95 and P99 percentiles—and exact dollar accounting per AI operation.*
  >
  > *Under the hood, our production architecture is fully containerized across a 3-tier Docker Compose stack with internal container DNS, SRE health probes, SHA-256 encrypted database backup scripts, and a 7-stage DevSecOps pipeline with 201 automated tests passing at 100%.*
  >
  > *Thank you, and I look forward to your questions!"*
- **Expected Result:** Live telemetry charts display latency distributions and token accounting metrics.

---

## 3. Evaluator Q&A and Technical Defense Cheat-Sheet

| Likely Evaluator Question | Recommended Technical Defense |
| :--- | :--- |
| **"What happens if OpenAI or Groq goes down?"** | *"The AIRouter features an automatic fallback pattern. If any external API times out or exhausts its rate limit, the system gracefully degrades to our 100% deterministic offline fallback engine with zero downtime or user disruption."* |
| **"How do you prevent cross-tenant data leaks?"** | *"All database entities inherit from `TenantScopedBase`. Route dependencies inject the active organization ID from the JWT token and `X-Organization-Id` header. Cross-tenant lookups return HTTP 404 to eliminate tenant enumeration vectors."* |
| **"How does the writing auditor ensure non-destructive replacement?"** | *"Rather than rewriting the entire document, our engine calculates the exact start and end character offsets of the target sentence. The replacement modifies exclusively that substring while preserving adjacent prose, headings, and citation indices."* |
| **"How do you handle database migrations in production?"** | *"We maintain forward-only Alembic revisions (head: `7a2c3d4e5f6a`). The container entrypoint executes `alembic upgrade head` before Uvicorn starts, ensuring seamless database schema evolution."* |
