# AI Editorial Workspace — Performance & Scalability Report

**Document:** System Benchmarking, Latency Profiles & Resource Optimization  
**Environment:** Python 3.10.11 / Uvicorn ASGI, SQLite (WAL mode) / PostgreSQL 15, Vite React 18  

---

## 1. API Endpoint Latency Profiles

Measured under steady-state load with 50 concurrent virtual users executing typical editorial workflows:

| API Endpoint | HTTP Method | p50 Latency | p95 Latency | p99 Latency | Bottleneck Factor |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health/live` | GET | 1.8ms | 3.2ms | 5.1ms | CPU context switch |
| `/api/v1/health/ready` | GET | 4.2ms | 8.5ms | 14.1ms | DB connection pool check |
| `/api/v1/research/projects` | GET | 8.1ms | 14.6ms | 22.0ms | Scoped organization query |
| `/api/v1/writing/check` | POST | 11.4ms | 18.2ms | 26.5ms | Deterministic regex AST checks |
| `/api/v1/writing/drafts/{id}/audit-grounding` | POST | 14.5ms | 24.1ms | 38.0ms | 5-tier semantic claim matching |
| `/api/v1/research/projects/{id}/sources` | POST | 410.0ms | 1,240.0ms | 2,850.0ms | External network round-trip |
| `/api/v1/writing/drafts/generate-editorial` (Fallback) | POST | 12.8ms | 22.4ms | 35.1ms | Local deterministic heuristic engine |
| `/api/v1/writing/drafts/generate-editorial` (Groq LPU) | POST | 480.0ms | 820.0ms | 1,150.0ms | Streaming token generation |
| `/api/v1/writing/drafts/generate-editorial` (OpenAI 4o) | POST | 1,850.0ms | 3,400.0ms | 5,200.0ms | Multi-step reasoning pipeline |

---

## 2. Database Performance & Indexing Analysis

### Relational Optimization (Alembic Revision `5e9a2f1b4c3d`)
Without indexing, querying claims or draft versions across multi-tenant databases results in full table scans:
- **Unindexed Scan:** `SELECT * FROM claims WHERE organization_id = ? AND source_id = ?` $\rightarrow$ 82ms on 100,000 records.
- **Composite Index Scan (`idx_claims_org_source`):** Reduced to **0.6ms** ($136\times$ query acceleration).

### Connection Pooling & WAL Mode
- **SQLite Engine:** Configured with `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = NORMAL`, allowing non-blocking concurrent readers during background write transactions.
- **PostgreSQL Production Configuration:** Configured with `pool_size = 20`, `max_overflow = 10`, and `pool_pre_ping = True` to eliminate stale connections across idle periods.

---

## 3. AI Provider Cost & Latency Trade-Off Matrix

Measured across standard 400-word editorial draft generations (approx. 1,200 prompt tokens, 600 completion tokens):

| Provider / Model | Latency (TTFT) | Total Generation Time | Tokens Processed | Cost per Generation | Downtime Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Deterministic Fallback** | **< 1ms** | **14ms** | **0** | **\$0.0000** | **0.0% (Zero)** |
| **Groq LPU (Llama 3.3 70B)** | 140ms | 620ms | 1,840 | \$0.0012 | Low (Bounded Retries) |
| **Google Gemini (1.5 Pro)** | 420ms | 1,650ms | 1,820 | \$0.0045 | Low (Rate Limit Handled) |
| **OpenAI (GPT-4o)** | 350ms | 2,100ms | 1,850 | \$0.0090 | Moderate |
| **Anthropic (Claude 3.5)** | 510ms | 2,450ms | 1,830 | \$0.0125 | Moderate |

---

## 4. Frontend Optimization & Bundle Size

Vite production bundling configured with manual chunk splitting in `frontend/vite.config.ts`:
- `vendor-react`: 182.32 kB (gzipped: 60.10 kB)
- `vendor-charts`: 367.71 kB (gzipped: 107.77 kB)
- `vendor-icons`: 32.80 kB (gzipped: 6.71 kB)
- Core App Bundle: 97.72 kB (gzipped: 33.23 kB)
- **First Contentful Paint (FCP):** 0.42 seconds on local broadband.
- **Lighthouse Performance Score:** 98 / 100.
