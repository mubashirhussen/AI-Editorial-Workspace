# Phase 37: Product Metrics Definitions & Calculation Methodology

**Project:** AI Editorial Workspace — This Week in AI  
**Document:** Mathematical Definitions of Core Product KPIs  
**Author:** Forward Deployed Engineer & Senior Product Analyst  

---

## 1. Executive Summary

This document establishes the exact mathematical formulas, denominators, data sources, and edge-case handling rules for all product metrics reported in the **AI Editorial Workspace** Analytics Dashboard. Every metric is derived strictly from durable database records (`analytics_events`, `research_projects`, `sources`, `writing_drafts`, `editorial_outputs`, `user_feedbacks`), with zero fabrication or mock values.

---

## 2. Executive Product Metrics

### 2.1 Active Users (Pseudonymous)
- **Definition:** The number of unique, pseudorandomized user identifiers (`user_pseudonym`) that generated at least one validated analytics event within the selected lookback window ($T$).
- **Formula:**
  $$\text{Active Users} = \left| \{ \text{user\_pseudonym} \mid \text{event} \in E_T \land \text{user\_pseudonym} \neq \text{null} \} \right|$$
- **Edge Cases:** If an organization has created projects but users have opted out of tracking, the metric floors to at least 1 to reflect confirmed organizational activity.

### 2.2 Active Sessions
- **Definition:** The count of unique client session tokens (`session_id`) recorded across user interactions within the reporting window.
- **Formula:**
  $$\text{Active Sessions} = \left| \{ \text{session\_id} \mid \text{event} \in E_T \land \text{session\_id} \neq \text{null} \} \right|$$

### 2.3 Projects Created
- **Definition:** Authoritative count of primary investigation records created in `research_projects` table for the tenant within time window $T$.
- **Formula:**
  $$\text{Projects Created} = \text{COUNT}(\text{ResearchProject.id}) \quad \text{where} \quad \text{created\_at} \ge (t_{\text{now}} - T) \land \text{organization\_id} = \text{org\_id}$$

### 2.4 Workflow Completion Rate
- **Definition:** Percentage of initiated multi-step editorial workflows that reached a validated terminal state (`completed`).
- **Formula:**
  $$\text{Completion Rate} = \frac{\sum \text{Workflows}_{\text{completed}}}{\max\left(\sum \text{Workflows}_{\text{started}}, \sum \text{Workflows}_{\text{completed}}, 1\right)} \times 100\%$$
- **Incomplete Handling:** Started workflows that have neither completed nor failed within the timeout window are tracked as in-progress or abandoned, preventing inflation of completion rates.

### 2.5 AI Reliability / Success Rate
- **Definition:** Proportion of AI provider operations (brief generation, writing assistance, editorial bundling) that concluded successfully without timeouts, HTTP 500s, or unhandled exceptions.
- **Formula:**
  $$\text{AI Success Rate} = \frac{\text{AI Ops}_{\text{completed}}}{\text{AI Ops}_{\text{completed}} + \text{AI Ops}_{\text{failed}}} \times 100\%$$
- **Edge Cases:** If zero AI operations occurred during the period, the metric displays 100.0% (healthy baseline).

### 2.6 Average Workflow Latency ($\text{Duration}_{\text{avg}}$)
- **Definition:** Arithmetic mean of elapsed execution time in milliseconds across all completed workflow events where `duration_ms` is recorded.
- **Formula:**
  $$\text{Duration}_{\text{avg}} = \frac{1}{N} \sum_{i=1}^{N} \text{duration\_ms}_i$$

---

## 3. User Journey Funnel Progression

### 3.1 Research Knowledge Ingestion Funnel
The Research pipeline consists of 4 sequential milestones:
1. **Source Added ($S_1$):** `research_source_added`
2. **Source Ingested ($S_2$):** `research_source_processing_completed`
3. **Brief Synthesized ($S_3$):** `research_brief_generation_completed`
4. **Brief Exported ($S_4$):** `research_brief_exported`

- **Step Conversion Rate:**
  $$\text{CR}_k = \frac{\text{Count}(S_k)}{\max(\text{Count}(S_{k-1}), 1)} \times 100\% \quad (\text{with } \text{CR}_1 = 100\%)$$
- **Drop-off Count:**
  $$\text{DropOff}_k = \max(0, \text{Count}(S_{k-1}) - \text{Count}(S_k))$$
- **End-to-End Funnel Conversion:**
  $$\text{E2E Conversion} = \frac{\text{Count}(S_4)}{\max(\text{Count}(S_1), 1)} \times 100\%$$

### 3.2 Assisted Composition & Polish Funnel
1. **Draft Initiated ($W_1$):** `writing_draft_created`
2. **AI Assist Triggered ($W_2$):** `writing_assistance_requested`
3. **Prose Improved ($W_3$):** `writing_assistance_completed`
4. **Draft Exported ($W_4$):** `writing_draft_exported`

### 3.3 Editorial Studio Publication Funnel
1. **Studio Opened ($E_1$):** `editorial_workspace_opened`
2. **Edition Generated ($E_2$):** `editorial_generation_completed`
3. **Peer Reviewed ($E_3$):** `editorial_review_completed`
4. **Edition Approved ($E_4$):** `editorial_approved`
5. **Edition Published ($E_5$):** `editorial_exported`

---

## 4. Feature Adoption & Reliability Matrix

Each module is measured on 3 primary axes:
1. **Invocations:** Total count of events tagged to the module.
2. **Success Rate:** $\frac{\text{Successes}}{\text{Total Invocations}} \times 100\%$.
3. **Average Latency:** Average processing duration in milliseconds for operations reporting `duration_ms`.

Monitored modules:
- Research Ingestion & Analysis
- Research Brief Generator
- Writing Assistant & Drafting
- Deterministic Linguistic Auditor
- Editorial Studio Bundler
- Editorial Review & Governance
- Multi-Tenant Project Hub
- In-App User Feedback
