# AI Editorial Workspace — 5–7 Minute Technical Demonstration Script

**System:** AI Editorial Workspace  
**Assignment:** Forward Deployed Engineer (FDE) Intern Assignment  
**Publication Target:** *This Week in AI*  
**Presenter:** Mubashir Hussain  
**Format:** Live Technical Walkthrough & Architecture Defense  
**Total Target Time:** 5 to 7 Minutes  

---

## Timeline & Scene Overview

```
0:00 ── 0:45 : Problem & Product Introduction
0:45 ── 1:30 : Application Architecture & Dashboard
1:30 ── 2:45 : Research Assistant (3 Sources, SSRF & Triangulation)
2:45 ── 4:00 : Writing Assistant & Deterministic Hemingway Audits
4:00 ── 5:00 : Surgical Non-Destructive Rewrites & Version Comparison
5:00 ── 6:00 : Editorial Studio, Numerical Citations & XSS Sanitization
6:00 ── 7:00 : SRE Observability, Reliability Defense & Roadmap
```

---

## Step-by-Step Demonstration Playbook

### Step 1: Problem & Product Introduction (0:00 – 0:45)

- **Screen to Open:** Homepage / Login Screen ([http://localhost:5173/login](http://localhost:5173/login) or [http://localhost](http://localhost))
- **Action to Perform:** Present the core editorial challenge; log in using standard credentials.
- **Expected Result:** Instant transition into the authenticated Workspace Dashboard with live "Backend connected" green status pill and user profile in top-right navbar.
- **Important Technical Point to Explain:**
  > "Technical media publications face two critical failure modes: **The Epistemic Dilution Problem** (frontier labs packaging speculative roadmaps as empirical facts, leading to ungrounded LLM hallucinations), and **The Style & Jargon Bloat Problem** (drafts saturated with run-on sentences >25 words, passive voice, and redundant filler). The AI Editorial Workspace enforces an evidence-first, non-destructive editorial pipeline."

---

### Step 2: Application Architecture & Dashboard (0:45 – 1:30)

- **Screen to Open:** Dashboard (`/dashboard`)
- **Action to Perform:** Highlight real-time metric cards (Active Investigations, Total Sources, Verified Claims, Drafts, Readability Index) and workspace profile badge.
- **Expected Result:** Live database counts populated via `GET /api/v1/dashboard/metrics`; status indicator shows active connection and database readiness.
- **Important Technical Point to Explain:**
  > "The architecture pairs a React 18 / TypeScript SPA with a FastAPI ASGI backend, backed by SQLAlchemy 2.0 with connection pooling and 34 relational tables. Every incoming request is stamped with an `X-Request-ID` correlation header tracked through an in-memory latency ring buffer."

---

### Step 3: Research Assistant & Multi-Source Triangulation (1:30 – 2:45)

- **Screen to Open:** Research Assistant (`/research`)
- **Action to Perform:**
  1. Select project: `"Datacenter Scaling 2026"`.
  2. Ingest 3 heterogeneous sources:
     - Source 1: DeepSeek-R1 Technical Report (Web URL / Paste Text)
     - Source 2: OpenAI o1 Test-Time Compute Paper
     - Source 3: Meta Llama 3 Infrastructure Blog
  3. Attempt ingestion of private IP `http://127.0.0.1:8000/internal` to show SSRF defense.
  4. Click **"Generate Research Brief"**.
- **Expected Result:**
  - SSRF test is rejected with HTTP 400 Bad Request ("Target URL resolves to a protected or private IP address").
  - Primary sources extract with author, publication date, and word count.
  - Epistemic Engine separates claims into **Verified Facts**, **Editorial Analysis**, and **Speculation**, linked to verbatim quotes.
  - Generates 10-section brief and 3 distinct newsletter angles.
- **Important Technical Point to Explain:**
  > "Our extraction pipeline uses Trafilatura with BeautifulSoup4 fallback and socket-level DNS pre-flight checking. Notice that each claim retains an immutable `source_id` link. If a client-rendered SPA blocks scraping, the UI provides an immediate inline 'Paste Text' fallback."

---

### Step 4: Writing Assistant & Deterministic Hemingway Audits (2:45 – 4:00)

- **Screen to Open:** Writing Assistant (`/writing`)
- **Action to Perform:** Load sample draft `"Production Reasoning Architecture Review"`, containing 121 words, 4 sentences, passive voice, and filler words. Click **"Audit Quality"**.
- **Expected Result:**
  - Readability Index displays: **"Very Difficult"** (Flesch Reading Ease: 0.0 / 100, Average Sentence Length: 30.2 words).
  - Flags 6 filler phrases, 1 passive construction, 3 jargon phrases, and 3 long sentences.
  - Each suggestion displays the original snippet, exact explanation, and proposed concise rewrite.
- **Important Technical Point to Explain:**
  > "Zero LLM calls are made for writing analysis. All 6 Hemingway checks run locally via deterministic Python AST and regex heuristics in under 15ms. This eliminates LLM latency, cost, and hallucination during style auditing."

---

### Step 5: Surgical Non-Destructive Rewrites & Version Comparison (4:00 – 5:00)

- **Screen to Open:** Writing Assistant (`/writing`) $\rightarrow$ Comparison Modal
- **Action to Perform:**
  1. Click **"Accept"** on `"In order to"` $\rightarrow$ `"To"`.
  2. Click **"Accept"** on `"Due to the fact that"` $\rightarrow$ `"Because"`.
  3. Click **"Compare Original vs Revised"**.
- **Expected Result:**
  - Real-time recalculation of Flesch Reading Ease jumps to accessible readability.
  - The side-by-side comparison modal highlights deletions in red and additions in green.
  - `original_content` remains permanently immutable in the database.
- **Important Technical Point to Explain:**
  > "Our replacement algorithm uses sentence-boundary substring slicing. Accepting an editorial rewrite modifies only the target sentence in `revised_content`, completely protecting adjacent citations and surrounding copy from accidental corruption."

---

### Step 6: Editorial Studio, Numerical Citations & Multi-Format Export (5:00 – 6:00)

- **Screen to Open:** Editorial Studio (`/editorial`)
- **Action to Perform:** Select brief, generate 300–500 word newsletter article, review inline citations `[1]`, `[2]`, and export to Markdown, Plain Text, and HTML5.
- **Expected Result:**
  - Produces structured publication-ready newsletter (Headline, Context, Analysis, Implications, References).
  - All facts have corresponding numbered citations `[1]`, `[2]` linking to the references footer.
  - One-click copy formats Markdown, Plain Text, and HTML with styled superscript citations and XSS entity escaping.
- **Important Technical Point to Explain:**
  > "The output strictly adheres to the 300–500 word length invariant. In the HTML5 export, all dynamic content is entity-escaped using Python's `html.escape`, preventing stored XSS while preserving rich superscript markup for newsletter readers."

---

### Step 7: SRE Observability, Reliability Defense & Roadmap (6:00 – 7:00)

- **Screen to Open:** Settings / Telemetry Screen (`/settings`) & Terminal
- **Action to Perform:** Show `/health/ready` probe, AES-128 key masking (`••••••••1234`), and Docker Compose setup.
- **Expected Result:**
  - Status shows 100% database connectivity, zero unhandled exceptions, and active providers.
  - Docker Compose demonstrates multi-container orchestration with PostgreSQL 15, FastAPI, and Nginx.
- **Important Technical Point to Explain:**
  > "Production readiness is verified: 104 passed tests, 0 failed, 0 skipped. In Docker, backend runs as an unprivileged non-root user `appuser:10001`. Automated database backups run via `backup_db.py` with SHA-256 verification."

---

## 8. Fallback Demonstration Plan (Zero-Dependency Offline Mode)

If live internet connectivity drops or upstream AI API providers experience outages during the demo:

1. **Activate Deterministic Fallback Mode:**
   - In `Settings`, clear the API key or set `OPENAI_API_KEY=""`.
   - The backend Intelligent AI Router automatically routes all requests to the **Deterministic Rule Engine**.
2. **Deterministic Research Synthesis:**
   - The offline engine synthesizes the 10-section brief using extracted source key sentences, entity frequencies, and heuristic templates.
3. **Deterministic Editorial Drafting:**
   - The offline drafting engine generates the 300–500 word newsletter article adhering to formulaic templates, complete with numbered citations `[1]`, `[2]`.
4. **Key Talking Point:**
   > "This demonstrates our zero-failure resilience architecture: the application never crashes or presents a blank screen when upstream cloud providers fail. The editorial desk can continue publishing even in an air-gapped or offline environment."
