# Phase 23 — Writing Quality Analysis & Readability Architecture

## 1. Overview

Phase 23 establishes a clear architectural and visual segregation between:
1. **Deterministic Linguistic & Structural Metrics**: Computed instantly on the client or server without AI model inference.
2. **AI-Powered Quality Diagnostics & Readability Linters**: Heuristic and model-evaluated style compliance, passive voice detection, and research grounding verification.

---

## 2. Segregated Metrics Architecture

```mermaid
graph LR
    subgraph Deterministic Engine
        A["Word Count"]
        B["Character Count"]
        C["Sentence Count"]
        D["Paragraph Count"]
        E["Average Sentence Length"]
        F["Estimated Reading Time"]
        G["Flesch Reading Ease Formula"]
    end

    subgraph AI & Linter Diagnostics
        H["Passive Voice Detector"]
        I["Filler Word Linter"]
        J["Subordinate Clause Analyzer"]
        K["Jargon & Slang Detector"]
        L["Repetition & Tautology Check"]
        M["Factual Grounding Audit (ISNAD)"]
    end

    Deterministic Engine --> UI["Top Metric Bar (Zero Latency)"]
    AI & Linter Diagnostics --> Sidebar["Sidebar Review Panel & Linter Overlay"]
```

---

## 3. Deterministic Linguistic Metrics

Computed in real-time (`useMemo` via `analyzeText`):
- **Word Count**: Regex-delimited tokenization (`/\s+/`).
- **Character Count**: Raw Unicode character count.
- **Sentence Count**: Sentence boundary detection (`/[.!?]+/`).
- **Paragraph Count**: Block separation detection (`/\n\s*\n/`).
- **Average Sentence Length**: Ratio of words to sentences ($\frac{\text{Words}}{\text{Sentences}}$). Flagged as warning if $> 25.0$.
- **Reading Time**: Calculated based on standard 200 words-per-minute comprehension speed.
- **Flesch Reading Ease Formula**:
  $$\text{Score} = 206.835 - (1.015 \times \text{ASL}) - (84.6 \times \text{ASW})$$
  - $\ge 60$: Standard / Conversational cadence.
  - $< 60$: Academic / Complex cadence.

---

## 4. AI & Linter Diagnostic Linters

Accessible via the **Sidebar Review Panel** and the **Interactive Linter Highlight**:
1. **Long Sentences**: Flagged when a single statement exceeds 30 words or contains 3+ comma splices.
2. **Passive Voice**: Identifies constructions like `"models were evaluated by the team"` and proposes active transformations (`"the team evaluated models"`).
3. **Filler Phrases**: Targets verbose qualifiers (`in order to`, `due to the fact that`, `at the end of the day`) and offers one-word drop-in replacements (`to`, `because`, `ultimately`).
4. **Technical Jargon**: Flags obscure terminology lacking explanatory context.
5. **Repetition**: Flags identical consecutive words or tautologies (`absolutely essential`, `future plans`).
6. **Sentence Complexity**: Evaluates cognitive load of dense technical statements.

---

## 5. Research Grounding & Claim Verification (ISNAD)

Clicking **Verify Grounding** evaluates the active draft against connected research project sources:
- **Grounded Claims**: Factual statements verified against indexed retrieval chunks.
- **Inferred Claims**: General deductions consistent with the source corpus.
- **Unsupported Claims**: Flagged statements lacking empirical backing, accompanied by editorial warnings.
- **Contradictory Claims**: Statements directly refuting documented evidence.
