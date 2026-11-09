# Known Architectural Boundaries, Trade-offs & Engineering Roadmap

**Project:** AI Editorial Workspace  
**Document Type:** Technical Debt Ledger & Future Systems Roadmap  
**Author:** Forward Deployed Engineer  
**Status:** **DOCUMENTED ARCHITECTURAL BOUNDARIES**  

---

## 1. Context & Architectural Philosophy

Engineering production software involves making conscious trade-offs between delivery velocity, operational complexity, and resource constraints. In accordance with Forward Deployed Engineering best practices, this document transparently catalogs the known architectural boundaries of the current implementation and outlines the planned enterprise roadmap.

---

## 2. Technical Boundaries & Planned Enterprise Enhancements

### 1. Ingestion Pipeline: In-Process vs. Distributed Task Queue
- **Current Architecture:** Document parsing (text extraction, regex cleaning, URL fetching) is handled asynchronously within the FastAPI event loop via `asyncio.to_thread` and `httpx.AsyncClient`.
- **Trade-off:** This eliminates external infrastructure dependencies (like Redis or RabbitMQ) during local development and single-node container deployment, simplifying zero-configuration setups. However, ingesting hundreds of concurrent 50MB PDF whitepapers could lead to CPU starvation of the main ASGI loop.
- **Enterprise Roadmap:** Transition heavy document ingestion tasks to a distributed task queue (Celery or ARQ backed by Redis) with dedicated worker nodes and AWS S3 storage buckets.

### 2. Semantic Search & Vector Embeddings: In-Process vs. Dedicated Vector Database
- **Current Architecture:** Source document chunking and claim correlation utilize lightweight in-process vector representations and exact keyword/regex indexing stored as JSON structures in relational tables.
- **Trade-off:** Keeps the database footprint compact and eliminates external vector service latency and licensing fees. For corpora under 1,000 documents per project, retrieval latency is sub-10ms.
- **Enterprise Roadmap:** Integrate `pgvector` for PostgreSQL or a managed vector engine (Qdrant / Milvus) when project document collections scale beyond 100,000 pages.

### 3. Collaborative Writing: Version Snapshotting vs. Operational Transforms / CRDTs
- **Current Architecture:** Draft revisions are managed via explicit version snapshots (`EditorialVersion`), capturing immutable character-level diffs, authors, and timestamps upon saving.
- **Trade-off:** Ideal for asynchronous, multi-stage editorial workflows (e.g., Writer -> Editor -> Publisher) and guarantees a simple, auditable transaction log without concurrent conflict bugs. However, it does not support Google Docs-style simultaneous multi-cursor typing.
- **Enterprise Roadmap:** Implement a WebSocket layer backed by Yjs or Automerge CRDTs for real-time collaborative concurrent typing.

### 4. PDF OCR & Unstructured Document Parsing
- **Current Architecture:** The PDF extractor utilizes `pypdf` to parse standard text-based PDF documents and technical papers.
- **Trade-off:** Extremely fast (< 100ms per paper) and requires zero native C++ binaries. However, scanned documents containing images of text rather than selectable fonts will extract empty text strings.
- **Enterprise Roadmap:** Integrate Tesseract OCR or cloud vision APIs (Google Cloud Document AI) with graceful fallback to standard text extraction when selectable fonts are detected.

### 5. Multi-Region High-Availability & Database Replication
- **Current Architecture:** Operates with high performance on local SQLite (with WAL mode and busy timeout enabled) or single-instance PostgreSQL via SQLAlchemy.
- **Trade-off:** Perfect for developer setup and single-tenant enterprise deployments. Does not currently include multi-region active-active read replica routing.
- **Enterprise Roadmap:** Configure AWS Aurora PostgreSQL with multi-AZ replication and read-replica connection pooling via PgBouncer.

