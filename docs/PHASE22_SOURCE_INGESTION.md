# Phase 22 — Source Ingestion Architecture & SSRF Defense Specification

**Target Application:** AI Editorial Workspace  
**Module:** Research Assistant — Source Ingestion Pipeline  
**Version:** Phase 22 Enterprise Release  
**Status:** Validated & Deployed  

---

## 1. Overview & Architectural Goals

The Source Ingestion Engine serves as the primary intake mechanism for the AI Editorial Workspace. It is responsible for ingesting multi-modal intelligence artifacts—including web URLs, academic research papers (PDF), corporate briefs (DOCX), and markdown/plain text documents—and extracting structured text content while rigorously defending against Server-Side Request Forgery (SSRF), Denial of Service (DoS), and malicious payload execution.

```
                      +-----------------------------+
                      |   Source Ingestion Input    |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
      [ Web URL Ingestion ]                       [ Document Upload ]
               |                                           |
    +----------v-----------+                    +----------v-----------+
    |   SSRF Defense Loop   |                    | Magic Byte Validation|
    | - Scheme check       |                    | - PDF (%PDF-)        |
    | - DNS IP resolution  |                    | - DOCX (PK\x03\x04)  |
    | - RFC 1918 filter    |                    | - Max 10MB cap       |
    | - Cloud metadata blk |                    | - Executable reject  |
    +----------+-----------+                    +----------+-----------+
               | (Redirect re-validation)                  |
    +----------v-----------+                    +----------v-----------+
    | Trafilatura / BS4    |                    | pypdf / python-docx  |
    | Extraction Engine    |                    | Extraction Pipeline  |
    +----------+-----------+                    +----------+-----------+
               |                                           |
               +---------------------+---------------------+
                                     |
                      +--------------v--------------+
                      | Normalized Text + Metadata  |
                      | - Word count, Domain, Hash  |
                      | - Epistemic Chunking        |
                      +-----------------------------+
```

---

## 2. Server-Side Request Forgery (SSRF) Defense

To prevent arbitrary internal network port scanning, container metadata extraction, or cloud credential exfiltration (e.g. AWS IMDSv1/v2, GCP metadata, Azure instance metadata), URL ingestion is governed by multi-tier validation:

### 2.1 Enforced Rules & Blocked Subnets
1. **Allowed Schemes:** `http://` and `https://` only. Schemes like `file://`, `gopher://`, `ftp://`, `ldap://`, or `dict://` are immediately rejected with `400 Bad Request`.
2. **Blocked Loopback & Local Addresses:**
   - `127.0.0.0/8` (e.g., `127.0.0.1`, `localhost`)
   - `::1` and `0.0.0.0`
3. **Blocked Private & Carrier-Grade Networks (RFC 1918 & RFC 6598):**
   - `10.0.0.0/8`
   - `172.16.0.0/12`
   - `192.168.0.0/16`
   - `100.64.0.0/10`
4. **Blocked Link-Local & Cloud Metadata Subnets:**
   - `169.254.0.0/16` (including `169.254.169.254`)
   - `fe80::/10`
   - Hostnames: `metadata.google.internal`, `instance-data`
5. **DNS Re-Validation & Rebinding Defense:**
   - Hostnames are resolved to IPv4/IPv6 addresses using `socket.getaddrinfo`.
   - Every resolved IP is checked against `ipaddress.ip_network.is_private`, `is_loopback`, `is_link_local`, `is_reserved`, and `is_multicast`.
   - When HTTP client follows redirects, redirect targets are re-evaluated through the same SSRF gate.

### 2.2 Extraction Pipeline
- Primary extractor: `trafilatura` (extracts main article body without boilerplate ads, navigation bars, or footers).
- Fallback extractor: `BeautifulSoup4` with heuristic paragraph extraction.
- Strict request timeout: 15 seconds connection, 20 seconds read timeout.

---

## 3. Document Ingestion & Signature Verification

Document uploads are handled via `POST /api/v1/research/projects/{id}/sources/upload`. Security guardrails include:

### 3.1 Magic Bytes / File Signature Verification
File extension alone is untrusted. The service reads the leading 2048 bytes of the uploaded payload to verify authentic file magic bytes:
- **PDF Documents:** Must start with `%PDF-` signature. Rejects corrupted headers or renamed executables.
- **Word Documents (.docx):** Must begin with the ZIP archive header `PK\x03\x04` and contain valid XML part manifests.
- **Plain Text / Markdown:** Decoded using UTF-8 with `errors='replace'`. Any binary null bytes (`\x00`) in non-binary text streams result in rejection.

### 3.2 Size & Resource Limits
- **Max File Size:** 10 MB (`10,485,760 bytes`). Oversized files return `413 Request Entity Too Large`.
- **Extension Blocklist:** `.exe`, `.dll`, `.bin`, `.sh`, `.bat`, `.cmd`, `.msi`, `.jar`, `.vbs`, `.ps1` are explicitly blocked.
- **Page Extraction Cap:** For PDFs, extraction processes up to 100 pages to avoid decompression bombs.

---

## 4. Source Management & State Model

Every ingested source transitions through a deterministic state machine:

```
[ PENDING ] ---> [ EXTRACTING ] ---> [ COMPLETED ]
                      |
                      +------------> [ FAILED ] ---> [ RETRYING ] ---> [ COMPLETED ]
```

- **Extraction Statuses:** `pending`, `extracting`, `completed`, `failed`.
- **Source Types:** `url`, `pdf`, `docx`, `text`, `manual`.
- **Retry Mechanism:** `POST /api/v1/research/sources/{source_id}/retry` re-executes extraction with fallback parsers and records extraction duration and failure diagnostics.
- **Curation Metadata:** Supports user notes (`why_saved`), editorial tags, author, publication date, and word count.

---

## 5. Verification & Test Evidence

All ingestion capabilities are covered in the automated test suite:
- `backend/tests/test_phase22_research_assistant.py::test_phase22_ssrf_prevention`
  - Validates rejection of `http://127.0.0.1:8000`, `http://localhost/admin`, `http://169.254.169.254/latest/meta-data`, and private RFC 1918 IPs.
- `backend/tests/test_phase22_research_assistant.py::test_phase22_document_extractor_and_signature_checks`
  - Validates valid PDF, corrupted PDF header rejection, valid DOCX, invalid binary signature rejection, and oversized upload rejection.

