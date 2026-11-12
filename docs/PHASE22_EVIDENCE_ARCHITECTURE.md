# Phase 22 — Evidence Grounding & Traceability Architecture

**Target Application:** AI Editorial Workspace  
**Module:** Research Synthesis & Epistemic Grounding Engine  
**Version:** Phase 22 Enterprise Release  
**Status:** Validated & Deployed  

---

## 1. Overview & Core Philosophy

In professional editorial publishing and intelligence synthesis, automated AI summaries cannot be trusted without empirical proof. Unsubstantiated claims, hallucinated data, and benchmark drift undermine editorial authority.

The AI Editorial Workspace enforces an **Epistemic Grounding Architecture** (inspired by classical source attribution principles like the *Isnad* methodology and modern Retrieval-Augmented Verification):

> **Core Axiom:** *No factual assertion is admitted into an editorial brief without explicit mapping to extracted source passages, direct quotation verification, and an assigned epistemic status.*

---

## 2. Epistemic Classification Taxonomy

Every assertion synthesized by the engine is evaluated against all available primary source texts and categorized into one of five mutually exclusive epistemic states:

| Status Code | Epistemic Definition | Verification Requirement | Visual Indicator |
| :--- | :--- | :--- | :--- |
| **`SUPPORTED`** | Direct, unambiguous corroboration in one or more authoritative ingested sources. | Verbatim quote or high semantic cosine similarity ($\ge 0.85$) with matching facts, metrics, and entities. | Emerald Badge (`#10B981`) |
| **`PARTIALLY_SUPPORTED`** | Conceptually aligned with source statements, but missing exact numerical metrics or specific named details. | Core premise corroborated, but specific extrapolation requires qualification or disclaimer. | Sky Blue Badge (`#0EA5E9`) |
| **`UNSUPPORTED`** | No corroborating passage or quote discovered across any ingested source text. | Identified as unverified generative extrapolation or unbacked model intuition. | Amber Badge (`#F59E0B`) |
| **`CONTRADICTED`** | Source passage explicitly negates, disputes, or contradicts the synthesized claim. | Direct textual conflict (e.g. source reports a 12% gain, but claim asserts a 45% gain or decline). | Rose / Red Badge (`#EF4444`) |
| **`NOT_VERIFIABLE`** | Normative, subjective, or future speculative assertion incapable of empirical source proof. | Statement of opinion, recommendation, or long-term industry prognosis. | Slate Gray Badge (`#64748B`) |

---

## 3. Grounding & Verification Pipeline

```
     [ Ingested Source Passages ]
                  |
    +-------------v-------------+
    | Chunking & Passage Index  |
    | - Sliding window chunks   |
    | - Entity & metric tagging |
    +-------------+-------------+
                  |
    +-------------v-------------+
    | Candidate Claim Extraction|
    | - Executive summary claims|
    | - Key findings statements |
    +-------------+-------------+
                  |
    +-------------v-------------+
    | Passage-to-Claim Matching |
    | - Semantic embedding sim  |
    | - Verbatim substring test |
    | - Entity overlap scoring  |
    +-------------+-------------+
                  |
         +--------+--------+
         |                 |
  [ Direct Match ]  [ Semantic Only ]  [ Negation / Conflict ]
         |                 |                     |
     SUPPORTED     PARTIALLY_SUPPORTED      CONTRADICTED
```

### 3.1 Verification Steps
1. **Passage Chunking:** Extracted texts are segmented into sentences and paragraphs (100–300 words) with source ID and positional offsets.
2. **Claim Decomposition:** The synthesizer decomposes summary points and findings into discrete proposition atoms (e.g., *Subject + Predicate + Object/Metric*).
3. **Evidence Retrieval:** Candidate passages are ranked by semantic relevance, keyword overlap, and named entity matches.
4. **Epistemic Classification:** An automated classifier examines premise entailment, detecting neutral, supportive, or contradictory relations.
5. **Confidence Scoring:** Generates a calibrated confidence score between `0.00` and `1.00`.

---

## 4. Evidence Map Data Schema

Each research brief maintains an immutable `evidence` list serializable to JSON and database storage:

```json
{
  "id": "ev-8f2a1b",
  "claim": "Verifiable citation density improves grounding fidelity by 44%.",
  "source_id": "src-phase22-1",
  "source_title": "DeepSeek-R1 Technical Report",
  "source_url": "https://arxiv.org/abs/2501.12948",
  "quote": "We observe a 44% relative gain in factual consistency benchmarks with verifiable reasoning chains.",
  "verification_status": "SUPPORTED",
  "confidence_score": 0.96,
  "paragraph_index": 3
}
```

---

## 5. Editorial User Interface Integration

The frontend exposes the Evidence Architecture directly to the human researcher in `ResearchPage.tsx`:
1. **Dedicated Tab (`Evidence Alignment`):** Displays all audited assertions with live status filter pills (`ALL`, `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `NOT_VERIFIABLE`).
2. **Audit Card:** Each card displays:
   - Evaluated Claim
   - Status Badge with color-coded styling
   - Authoritative Source Link and Title
   - Verbatim Blockquote highlighting supporting/contradicting text
   - Numeric Confidence Score (%)
3. **Contradiction Alerting:** If a brief contains `CONTRADICTED` claims, an alert warning surfaces to caution the editorial desk prior to article drafting.

---

## 6. Test Evidence & Verification

- Tested via `backend/tests/test_phase22_research_assistant.py::test_phase22_brief_synthesis_and_evidence_traceability`
  - Validates source claim generation, verbatim quote alignment, and status classification.
- Tested via Playwright E2E `frontend/e2e/research-workflow.spec.ts`
  - Validates evidence tab navigation, filter pill rendering, and claim verification display.

