# PHASE 39 — EVIDENCE QUALITY ENGINEERING SPECIFICATION
## Passage Extraction, Epistemic Claim Grounding & Contradiction Analysis

**Repository:** `https://github.com/mubashirhussen/AI-Editorial-Workspace`  
**Production Frontend:** `https://ai-editorial-workspace-blue.vercel.app/`  
**Branch:** `feat/phase39-research-evidence-reliability`  
**Author:** Senior AI Research Systems Engineer & Forward Deployed Engineer  
**Date:** November 2026  
**Status:** Certified & Implemented

---

## 1. Evidence Extraction Methodology

The evidence engineering pipeline converts unstructured raw HTML and document text into structured, queryable, and verifiable evidence passages.

```
Source Ingestion
      │
      ▼
Text Normalization (strip noise, HTML tags, excess whitespace)
      │
      ▼
Paragraph Segmentation (\n\n boundary splitting)
      │
      ▼
Sentence Boundary Detection (regex punctuation split)
      │
      ▼
Substantive Filtering (40 <= length <= 400 characters)
      │
      ▼
Location Indexing ("Paragraph {X}, Sentence {Y}")
      │
      ▼
Fact Type Classification (DIRECT_FACT, REPORTED_FACT, INFERENCE)
      │
      ▼
SHA-256 Passage Hashing (12-char fingerprint)
      │
      ▼
Database Persistence (`research_evidence` Table)
```

### Fact Type Definitions:
- **`DIRECT_FACT`**: Empirical statements describing verifiable actions, results, or physical architectures (e.g., *"Training was completed using 2,048 H800 GPUs over 55 days"*). Initial confidence: $0.95$.
- **`REPORTED_FACT`**: Secondhand reporting or statements attributed to third parties (e.g., *"According to spokespersons, the initiative commenced in March"*). Initial confidence: $0.85$.
- **`INFERENCE`**: Logical deductions derived from primary facts (e.g., *"This suggests memory bandwidth was the primary scaling bottleneck"*). Initial confidence: $0.70$.

---

## 2. Six-Tier Claim Verification Taxonomy

Every extracted claim from research briefs, drafts, or user documents is evaluated against the project's evidence corpus and categorized into one of six distinct epistemic states:

| Status | Epistemic Definition | Mathematical / Linguistic Threshold | User Action |
|---|---|---|---|
| **`SUPPORTED`** | Direct, unambiguous backing passage found in ingested primary source. | Semantic token overlap $\ge 55\%$ | Certified for publication. |
| **`PARTIALLY_SUPPORTED`** | Core claim is grounded, but minor numerical or contextual aspects are inferred. | Semantic token overlap $30\% \le \text{Overlap} < 55\%$ | Editorial note recommended. |
| **`UNSUPPORTED`** | No corroborating passage exists anywhere in ingested sources. | Semantic token overlap $< 30\%$ | Flagged in Quality Report; must be removed or proven. |
| **`CONTRADICTED`** | Reliable source evidence materially conflicts with statement figures, dates, or assertions. | Directly matches registered cross-source discrepancy | Mandatory presentation of both perspectives. |
| **`UNVERIFIED`** | Claim requires external evidence not yet available in the project library. | Insufficient source volume in project | Ingest supplementary primary sources. |
| **`NOT_APPLICABLE`** | Non-verifiable statement: opinion, future prediction, or strategic recommendation. | Explicit linguistic markers (*in our view, predicted to, founders should*) | Retained as editorial commentary without citation burden. |

---

## 3. Semantic Claim-to-Evidence Matching Algorithm

The matching algorithm extracts significant content lemmas (filtering punctuation, common stopwords, and words under 4 characters):

$$\text{Overlap Score} = \frac{|W_{\text{claim}} \cap W_{\text{evidence}}|}{|W_{\text{claim}}|}$$

Where:
- $W_{\text{claim}}$ is the set of significant words in the candidate assertion.
- $W_{\text{evidence}}$ is the set of significant words in the candidate passage excerpt.

When $\text{Overlap Score} \ge 0.55$, the claim is classified as `SUPPORTED`, and the supporting evidence excerpt is attached alongside the source's title and URL.

---

## 4. Contradiction Detection & Disagreement Preservation

When two sources report conflicting information (e.g. differing benchmark scores, release timelines, or financial valuations):
- The system **never** uses an LLM to arbitrarily pick a "winner."
- Both assertions are preserved side-by-side in `research_contradictions`.
- The nature of the disagreement (`disagreement_nature`), plausible explanations (`possible_explanations`), and unresolved questions are presented directly in the Research Reliability panel.

This ensures journalistic neutrality and protects researchers from presenting disputed numbers as consensus facts.
