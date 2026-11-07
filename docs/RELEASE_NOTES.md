# AI Editorial Workspace — Release Notes & Version History

**Current Version:** 1.0.0 (Production Release — FDE Intern Milestone)  
**Release Date:** November 2026  
**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  

---

## 1. Release Highlights (v1.0.0)

### 🔬 Module A: Research Assistant & Source Intelligence
- **Multi-Source Parallel Ingestion:** Ingest $\ge 3$ research sources simultaneously via URL or direct text paste.
- **SSRF Defense Network Guard:** Pre-flight DNS resolution strictly blocking private IP ranges (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`) and cloud metadata endpoints (`169.254.169.254`).
- **Epistemic Triangulation:** Automated sorting of raw document claims into **Verified Facts**, **Editorial Analysis**, and **Speculation**.
- **10-Section Research Brief Synthesis:** Generates structured research dossiers with verified citations.

### ✍️ Module B: Writing Assistant & Editorial Studio
- **Inverted Pyramid Drafting:** Synthesizes 300–500 word newsletter drafts leading with core analytical conclusions.
- **Hemingway 6-Check Auditor:** Real-time deterministic analysis of sentence length (>25 words), passive voice, filler phrases, technical jargon, repetition, and Flesch Reading Ease score.
- **Surgical Non-Destructive Rewriting:** Rewrites target sentence boundaries without modifying surrounding copy or corrupting citation tags.
- **Selection-Level Transformations:** Floating toolbar for targeted paragraph rewriting (*Make Punchy*, *Simplify*, *Shorten*, *Expand*).
- **Draft Versioning & Rollback:** Immutable timestamped snapshots with visual side-by-side diff comparisons.

### 🛡️ Multi-Tenant Governance & Security
- **Role-Based Access Control (RBAC):** Strict boundaries across 5 roles: `OWNER`, `ADMIN`, `EDITOR`, `REVIEWER`, `VIEWER`.
- **Row-Level Organization Isolation:** Tenant queries scoped by `organization_id` to guarantee zero cross-tenant data leakage.
- **Cryptographic Security:** Argon2 password hashing and stateless HS256 JWT tokens.

### 📊 AI Reliability, Hallucination Auditing & Observability
- **Multi-Provider AI Router:** Standardized adapters for **Groq LPU**, **OpenAI GPT-4o**, **Anthropic Claude 3.5**, **Google Gemini 1.5 Pro**, and a zero-dependency **Deterministic Fallback Engine**.
- **5-Tier Claim Grounding:** Color-coded verification hierarchy (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`).
- **Citation Integrity Checks:** Automated resolution auditing for `[1]`, `[2]`, `[Source: id]` markers.
- **Live Token Cost Accounting:** Real-time calculation of expenditure in `$USD` using live provider pricing schedules.
- **34-Case Evaluation Benchmark:** Full offline evaluation suite with continuous CI/CD verification.

---

## 2. Bug Fixes & Refinements in this Release

1. **Multi-URL Ingestion Fix:** Resolved an issue where single-line inputs stripped newline characters when pasting multiple URLs. Replaced with multi-line textarea and added "Quick Load 3 Sample URLs" helper.
2. **Project Dropdown State Sync:** Fixed a state timing issue where existing projects failed to auto-bind to the active workspace on page load.
3. **Cloudflare 403 Graceful Handling:** Replaced hard 500 crashes on bot-protected domains with informative amber toasts and instant "Paste Text" tab switching.
4. **Deterministic Fallback Resolution:** Short-circuited provider checks to ensure deterministic offline execution whenever offline mode or fallback is requested.
5. **Alembic Test Synchronization:** Updated database integrity tests to dynamically validate progressive migrations through revision `7a2c3d4e5f6a`.

---

## 3. Database Migration Instructions

To upgrade existing database schemas to this release:
```powershell
alembic -c backend/alembic.ini upgrade head
```
Head revision: `7a2c3d4e5f6a`

