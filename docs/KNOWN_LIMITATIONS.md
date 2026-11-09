# Known Limitations & Operational Boundaries

**System:** AI Editorial Workspace  
**Document Classification:** System Architecture & Operational Boundary Specification  
**Version:** 1.0.0 (Release Candidate)  
**Date:** November 2026  

---

## 1. Overview

The AI Editorial Workspace is designed to deliver robust, traceable, and evidence-grounded editorial workflows. To maintain predictable reliability, prevent unbounded resource consumption, and ensure high availability, certain functional and technical boundaries are intentionally established.

This document details all known limitations, operational thresholds, and the technical rationale for each.

---

## 2. AI Intelligence & Provider Fallbacks

### 2.1 Deterministic Fallback Pipeline
- **Boundary:** When external LLM provider keys (`GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`) are not supplied or external providers experience outages/rate-limiting, the workspace engages an internal deterministic heuristic engine (`backend/app/services/ai_router.py`).
- **Limitation:**
  - Research briefs generated under deterministic fallback utilize NLP sentence extraction, TF-IDF ranking, and extractive summarization rather than generative synthesis.
  - Tone adjustments and headline variants will follow rule-based pattern transformations.
- **Operational Guidance:** For production-grade generative synthesis, supply at least one valid LLM provider key in `.env` or configure dynamic credentials via the **Workspace Settings** screen.

### 2.2 Token Window & Context Truncation
- **Boundary:** Source documents processed into research briefs are constrained to a maximum of **100,000 characters** per source before chunking.
- **Limitation:** Ingestion of books or encyclopedic volumes (>200 pages) will truncate trailing sections unless pre-split into distinct focused source documents.

---

## 3. Ingestion & Content Extraction

### 3.1 Document File Types & Upload Limits
- **Supported Formats:** PDF (`.pdf`), Microsoft Word (`.docx`), Plain Text (`.txt`, `.md`).
- **File Size Limit:** Maximum **15 MB** per individual file upload.
- **Limitation:**
  - Scanned PDFs containing pure image scans without an embedded OCR text layer will extract empty or partial text. (Full optical character recognition requires Tesseract OCR engine, planned for v1.1).
  - Password-protected or encrypted PDF/DOCX files will fail validation with HTTP 422 Unprocessable Entity.

### 3.2 URL Scraping & SSRF Protection
- **Boundary:** Web scraping is protected by an SSRF (Server-Side Request Forgery) firewall that blocks loopback (`127.0.0.1`, `localhost`), link-local (`169.254.169.254`), and RFC 1918 private IP subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- **Limitation:** Paywalled content or websites requiring interactive JavaScript execution (SPA without prerendering) may yield partial text when fetched via standard HTTP GET.

---

## 4. Concurrency & Collaborative Editing

### 4.1 Document Versioning & Optimistic Locking
- **Architecture:** The writing assistant uses revision timestamps and auto-versioning snapshots.
- **Limitation:** Simultaneous real-time multi-cursor collaborative editing (like Google Docs or Figma multiplayer) is not implemented in v1.0. If two editors update the same draft concurrently, the last saved version persists while prior revisions remain retrievable via the **Version History** panel. Full CRDT (Conflict-free Replicated Data Types) is scheduled for v2.0.

### 4.2 SQLite vs. PostgreSQL Concurrency
- **Development Profile (SQLite):** Suitable for single-user local evaluation and automated testing. High-frequency concurrent writes may encounter `sqlite3.OperationalError: database is locked`.
- **Production Profile (PostgreSQL 15):** Solves concurrency lock contention via row-level locking (`FOR UPDATE`) and connection pooling (`QueuePool`, pool size 20, max overflow 10). Always deploy with PostgreSQL for multi-user production environments.

---

## 5. Telemetry & Observability Boundaries

### 5.1 Real-Time Telemetry Sampling
- **Boundary:** AI latency, token usage, and claim verification telemetry records are persisted to the database synchronously within the request lifecycle.
- **Limitation:** Under high burst traffic (>1,000 concurrent AI requests/sec), synchronous telemetry writes may introduce up to 5ms of database I/O latency. For ultra-high-scale installations, an asynchronous Redis queue with batch Celery ingestion should be enabled.

---

## 6. Frontend & Browser Support

### 6.1 Supported Environments
- **Modern Evergreen Browsers:** Google Chrome >= 100, Mozilla Firefox >= 100, Apple Safari >= 15, Microsoft Edge >= 100.
- **Unsupported:** Internet Explorer 11, legacy mobile browsers lacking Web Crypto API or CSS Grid.

---

## 7. Roadmap & Future Enhancements

| Feature | Target Version | Scope |
| :--- | :--- | :--- |
| **Multiplayer CRDT Collaboration** | v1.2.0 | Real-time concurrent typing with presence indicators |
| **Native OCR Pipeline** | v1.1.0 | Tesseract/DocTR integration for scanned PDFs |
| **Vector Database Embeddings** | v1.1.0 | pgvector / Qdrant semantic retrieval for research libraries |
| **OAuth2 / SAML SSO** | v1.2.0 | Enterprise Okta, Google Workspace, and Azure AD integration |

