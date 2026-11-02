# AI Editorial Workspace — Final Presentation & Demo Script

**Presenter:** Mubashir Hussain  
**Role:** Forward Deployed Engineer (FDE) Intern Candidate  
**Target Duration:** 5 to 7 Minutes  
**Publication:** *This Week in AI*  

---

## 1. Introduction (0:00 – 0:45)
- **Screen:** Homepage / Login (`http://localhost:5173/login`)
- **Action:** Introduce the problem and log in to the platform.
- **Speaking Notes:**
  > *"Hello everyone. Today I am presenting the AI Editorial Workspace, a specialized full-stack platform built for the senior editorial desk at This Week in AI. Technical media organizations face two critical failure modes: first, unverified AI marketing PR and benchmark claims being accepted by standard LLMs without citation links; second, technical drafts becoming bloated with passive voice and filler words while generic rewriters flatten authorial voice. The AI Editorial Workspace enforces an evidence-grounded, non-destructive editorial pipeline."*

---

## 2. Main Dashboard & Architecture (0:45 – 1:30)
- **Screen:** Dashboard (`/dashboard`)
- **Action:** Point out live connection pill, metrics, and user profile widget in top-right navbar.
- **Speaking Notes:**
  > *"Here on the Dashboard, our live connection indicator confirms backend health via `/api/v1/health`. The system displays active investigations, verified claims, and drafts in real time. Under the hood, this is a React 18 TypeScript SPA communicating with an asynchronous FastAPI backend and SQLAlchemy 2.0 managing 34 relational tables with connection pooling."*

---

## 3. Research Assistant & Epistemic Triangulation (1:30 – 3:00)
- **Screen:** Research Assistant (`/research`)
- **Action:** Select project "Datacenter Scaling 2026", ingest 3 primary sources (DeepSeek-R1, OpenAI o1, Meta Llama 3), demonstrate SSRF rejection on `127.0.0.1`, click "Generate Research Brief".
- **Speaking Notes:**
  > *"In the Research Assistant, we ingest three heterogeneous sources. Notice our SSRF security guardrail: before making an HTTP request, our backend resolves hostnames at the socket level. If an attacker passes an internal IP or AWS metadata `169.254.169.254`, it is rejected immediately. Once extracted, the engine separates claims into Verified Facts, Editorial Analysis, and Speculation, each linked to a verbatim quote and immutable `source_id`."*

---

## 4. Writing Assistant & Deterministic Audits (3:00 – 4:30)
- **Screen:** Writing Assistant (`/writing`)
- **Action:** Load sample draft, click "Audit Quality", review suggestion cards, accept two suggestions, click "Compare Original vs Revised".
- **Speaking Notes:**
  > *"In the Writing Assistant, we audit draft quality across 6 deterministic checks in under 15ms without calling an expensive LLM. Readability is scored mathematically using the Flesch Reading Ease formula. When I click 'Accept' on a rewrite, our safe replacement algorithm modifies only the target sentence in `revised_content`, while `original_content` remains permanently immutable in the database."*

---

## 5. Editorial Output & Source Citations (4:30 – 5:30)
- **Screen:** Editorial Studio (`/editorial`)
- **Action:** Select brief, generate 300–500 word newsletter article, review inline citations `[1]`, `[2]`, export to Markdown and HTML5.
- **Speaking Notes:**
  > *"In the Editorial Studio, we generate a 300–500-word newsletter edition strictly adhering to the style guide. Every fact embeds an inline citation `[1]`, `[2]` linking directly to verified references in the footer. One-click export provides clean Markdown, Plain Text, or semantic HTML5 with styled superscript citations and XSS entity escaping."*

---

## 6. Engineering Reliability & Conclusion (5:30 – 6:30)
- **Screen:** Settings (`/settings`) & Terminal
- **Action:** Show `/health/ready` probe, AES-128 key masking, and Docker Compose configuration.
- **Speaking Notes:**
  > *"From an engineering perspective, this workspace is production-hardened: 104 passed tests, 0 failed, multi-stage Docker containerization running as unprivileged `appuser:10001`, and an intelligent AI router with an offline deterministic fallback that guarantees zero crashes if external cloud APIs fail. Thank you, and I look forward to your questions."*

