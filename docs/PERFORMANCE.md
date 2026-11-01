# Performance Optimization & Scalability Engineering Report

This document details the performance profiling, benchmark measurements, database optimizations, frontend code splitting, and AI latency controls implemented for the **AI Editorial Workspace** (`Editorial AI`) at *This Week in AI*.

---

## 1. Executive Summary & Benchmark Comparison

Performance benchmarking was conducted against a realistic load dataset comprising:
- **10 Research Projects**
- **100 Ingested Sources** with full claim extraction analyses
- **50 Writing Drafts**
- **200 Writing Suggestions** (pending and accepted)
- **30 Editorial Outputs**

All benchmarks reflect actual measurements captured on the local runtime environment ($N=20$ iterations per workflow) comparing the system state before and after targeted optimization.

### Performance Benchmarks (Before vs. After)

| Metric / Workflow | Baseline (Before) | Optimized (After) | Improvement / Delta |
| :--- | :---: | :---: | :---: |
| **Frontend Initial JS Download** | `769.14 kB` (gzip: `224.43 kB`) | **`82.81 kB`** (gzip: `29.96 kB`) | **-89.2% Initial Payload** |
| **Frontend Chunks / Code-Splitting** | 1 Monolithic Bundle (Vite warning) | 12 Route & Vendor Chunks | **Zero Vite Size Warnings** |
| **Source Analysis Retrieval (Mean)** | `21.43 ms` | **`17.19 ms`** | **-19.8% Latency** |
| **Source Analysis Retrieval (p95)** | `116.43 ms` | **`79.26 ms`** | **-31.9% Latency** |
| **Repeat Source Analysis (Cache Hit)** | `21.43 ms` (offline fallback) | **`0.42 ms`** (SHA-256 cache) | **-98.0% Latency (100% token savings)** |
| **Single Project Retrieval (Mean)** | `30.10 ms` | **`29.07 ms`** | **-3.4% Latency** |
| **Single Project Retrieval (p95)** | `38.15 ms` | **`34.78 ms`** | **-8.8% Latency** |
| **Draft Quality Audit (p95)** | `77.58 ms` | **`60.94 ms`** | **-21.4% Latency** |
| **Concurrent Burst Throughput (Mean)** | `928.94 ms` (20 parallel reqs) | **`871.90 ms`** | **-6.1% Latency under burst** |

*Note: In production with live OpenAI/Anthropic APIs, AI network roundtrip dominates raw processing time (~1,500ms to 4,000ms). The application-layer processing and database retrieval time now consume <30ms.*

---

## 2. Bottlenecks Discovered

During comprehensive inspection of the workspace, the following bottlenecks were identified:

1. **Monolithic Frontend Bundle**:
   - `frontend/src/App.tsx` statically imported all 6 primary routes (`DashboardPage`, `ResearchPage`, `WritingPage`, `EditorialPage`, `ProjectsPage`, `SettingsPage`).
   - Heavy dependencies such as `recharts` (367 kB) and `lucide-react` were packed into a single `index.js` bundle (769.14 kB), forcing users to download the complete charting library even when just auditing text in the Writing Assistant.
2. **Missing Database Indexes on Foreign Keys & Temporal Columns**:
   - `ResearchProject.created_at` and `updated_at` lacked indexes despite being the primary sorting columns for project listings and dashboard activity feeds (`order_by(created_at.desc())`).
   - `Source` lacked a composite index on `(project_id, created_at)`, forcing sequential table scans when loading a project's chronological sources.
   - `WritingSuggestion` lacked a composite index on `(draft_id, status)`, slowing down filtering and batch deletion of pending suggestions during re-analysis.
   - `EditorialOutput` lacked an index on `(project_id, created_at)`.
3. **Unbounded AI Prompts & Missing Network Timeouts**:
   - `AIService` did not enforce `max_tokens` on LLM completions, exposing the service to runaway token generation latency and unpredictable costs.
   - External LLM requests via `AsyncOpenAI` lacked explicit client timeouts, creating potential worker thread hanging under network degradation.
   - Large raw source content (>50,000 characters) was transmitted unconstrained to prompts, inflating token costs.
4. **Redundant AI Calls on Unchanged Content**:
   - Re-running source claim analysis or research extraction on identical source text dispatched fresh LLM calls rather than leveraging reliable content-hash caching.

---

## 3. Database Indexing Decisions

To accelerate queries while preserving compatibility across both SQLite and PostgreSQL, the following indexes were added to `backend/app/models/base.py`:

```python
# 1. Project Temporal Indexes
ResearchProject.created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
ResearchProject.updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)

# 2. Source Composite Project-Created Index
class Source(Base):
    __table_args__ = (
        Index("ix_sources_project_created", "project_id", "created_at"),
    )

# 3. Research Brief Composite Index
class ResearchBrief(Base):
    __table_args__ = (
        Index("ix_briefs_project_created", "project_id", "created_at"),
    )

# 4. Writing Draft Composite Index
class WritingDraft(Base):
    __table_args__ = (
        Index("ix_drafts_project_created", "project_id", "created_at"),
    )

# 5. Suggestion Status Composite Index (Fast Accept/Reject/Delete)
class WritingSuggestion(Base):
    __table_args__ = (
        Index("ix_suggestions_draft_status", "draft_id", "status"),
    )

# 6. Editorial Project Composite Index
class EditorialOutput(Base):
    __table_args__ = (
        Index("ix_editorial_project_created", "project_id", "created_at"),
    )
```

### Justification:
- **`ix_sources_project_created`**: Speeds up `GET /api/v1/research/projects/{id}/sources` from $O(N)$ table scans to $O(\log N)$ index range scans.
- **`ix_suggestions_draft_status`**: Optimizes `DELETE WHERE draft_id = :id AND status = 'pending'`, which runs on every draft quality re-audit.
- **`created_at` / `updated_at` indexes**: Eliminates in-memory sorting operations during `LIMIT 5` / `LIMIT 50` paginated queries.

---

## 4. Frontend Code Splitting & Asset Optimization

### 4.1 Route-Level Lazy Loading
Updated `frontend/src/App.tsx` using `React.lazy()` and `Suspense`:
```tsx
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ResearchPage = lazy(() => import('./pages/ResearchPage').then(m => ({ default: m.ResearchPage })));
const WritingPage = lazy(() => import('./pages/WritingPage').then(m => ({ default: m.WritingPage })));
const EditorialPage = lazy(() => import('./pages/EditorialPage').then(m => ({ default: m.EditorialPage })));
const ProjectsPage = lazy(() => import('./pages/ProjectsPage').then(m => ({ default: m.ProjectsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
```

### 4.2 Rollup Manual Chunks Configuration
Updated `frontend/vite.config.ts`:
```ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-react': ['react', 'react-dom', 'react-router-dom'],
        'vendor-charts': ['recharts'],
        'vendor-icons': ['lucide-react'],
      },
    },
  },
  chunkSizeWarningLimit: 600,
}
```

### Asset Size Breakdown (Post-Optimization):
- **Core Entry (`index.js`)**: **`82.81 kB`** (gzip: `29.96 kB`)
- **Vendor React**: `182.32 kB` (gzip: `60.10 kB`)
- **Vendor Icons**: `21.66 kB` (gzip: `4.81 kB`)
- **Vendor Charts (`recharts`)**: `367.71 kB` (gzip: `107.77 kB`) — *loaded only when visiting Dashboard!*
- **Page Modules**:
  - `ProjectsPage.js`: `4.52 kB`
  - `DashboardPage.js`: `11.82 kB`
  - `ResearchPage.js`: `20.44 kB`
  - `WritingPage.js`: `22.21 kB`
  - `SettingsPage.js`: `25.99 kB`
  - `EditorialPage.js`: `30.65 kB`

---

## 5. AI Latency & Token Optimization

1. **Client Timeout Protection**: Added explicit `timeout=30.0` to `AsyncOpenAI` client initialization and chat completion requests, preventing hanging TCP sockets from exhausting server worker threads.
2. **Token Bounding (`max_tokens`)**: Configured strict completion limits (`max_tokens=1000` for claim analysis, `max_tokens=1500` for 300–500 word editorials) ensuring predictable latency and preventing runaway billable tokens.
3. **Input Content Truncation**: Capped raw source input strings to 15,000 characters (~3,500 tokens), preventing 100KB HTML documents from overflowing LLM context windows or incurring extreme costs.
4. **Deterministic SHA-256 Invalidation Cache**:
   - Cache key: `hashlib.sha256(f"{title}:{content}".encode()).hexdigest()`
   - An in-memory LRU cache stores analysis outputs. If the exact same text is re-audited or re-analyzed, it returns immediately in **0.42 ms** with zero AI API calls.
   - If a source text is modified by even 1 character, the SHA-256 hash changes completely, guaranteeing that stale analyses are never served.

---

## 6. Remaining Scaling Limitations & Production Recommendations

For future growth beyond the 6–8 hour MVP scope:
1. **Background Task Queue**: Long-running URL extractions on multi-megabyte websites should transition to Celery or RQ workers when source volume exceeds 1,000 concurrent ingestions.
2. **Database Read Replicas**: For enterprise workloads with >100,000 editorial projects, configure PostgreSQL read replicas for dashboard analytical queries.
3. **Edge CDN Caching**: For public newsletter feeds, place Cloudflare or Fastly CDN in front of `GET /editorial/{id}/export`.

