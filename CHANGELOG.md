# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-09 - Final Assessment & Production Handover

### Added
- **Evidence-Driven Defect Closure & Verification (Phase 17):**
  - Current implementation status audit (`PHASE17_CURRENT_IMPLEMENTATION_STATUS.md`).
  - Prioritized defect register with root cause analyses (`PHASE17_DEFECT_REGISTER.md`).
  - Final execution report and defect closure sign-off (`PHASE17_FINAL_EXECUTION_REPORT.md`).
  - Submission documentation suite: `API_DOCUMENTATION.md`, `DATABASE_ARCHITECTURE_AUDIT.md`, `SECURITY_AUDIT.md`, and `FINAL_IMPLEMENTATION_STATUS.md`.
- **User Acceptance Testing & Independent QA (Phase 15):**
  - Automated UAT suite (`backend/tests/test_phase15_uat_validation.py`) executing Scenarios A, B, and C.
  - End-to-end requirements traceability matrix (`docs/PHASE15_REQUIREMENTS_TRACEABILITY.md`).
  - User acceptance test report auditing modules A through H (`docs/PHASE15_USER_ACCEPTANCE_TEST_REPORT.md`).
  - Empirical data validation report (`docs/PHASE15_DATA_VALIDATION_REPORT.md`).
  - 9-scenario AI quality & factual grounding evaluation (`docs/PHASE15_AI_QUALITY_EVALUATION.md`).
  - Consolidated defect register with 10 closed defects (`docs/PHASE15_DEFECT_REGISTER.md`).
  - Forward Deployed Engineer 15-competency assessment rubric (`docs/FDE_ASSESSMENT_EVALUATION.md`).
  - Root-level submission artifacts: `PRODUCT_NOTE.md`, `TECHNICAL_ARCHITECTURE.md`, `ENGINEERING_DECISIONS.md`, `TEST_REPORT.md`, `SAMPLE_EDITORIAL.md`, and `DEMO_SCRIPT.md`.
- **Production Architecture & Deployment (Phase 14):**
  - Multi-stage Docker configuration with non-root security contexts (`UID 10001`).
  - Production Docker Compose stack (`docker-compose.prod.yml`) featuring 3-tier architecture with Nginx reverse proxy.
  - Complete operations guides: `DEPLOYMENT_GUIDE.md`, `ROLLBACK_GUIDE.md`, and `KNOWN_LIMITATIONS.md`.
  - Comprehensive operational readiness reports: `PHASE14_PRODUCTION_READINESS_AUDIT.md`, `PRODUCTION_DATABASE_DEPLOYMENT.md`, `CI_CD_PIPELINE.md`, `PRODUCTION_SECURITY_REVIEW.md`, and `PHASE14_PERFORMANCE_REPORT.md`.
- **System Integration & End-to-End Testing (Phase 13):**
  - Master E2E integration test suite (`backend/tests/test_phase13_master_integration.py`) verifying 7 continuous editorial workflows.
  - Verification of 208 backend unit/integration tests with 100% pass rate.
  - 34 offline AI benchmark test cases covering factual grounding, tone fidelity, and citation accuracy.
  - Live API connection recovery and health monitoring across all frontend screens.
- **AI Reliability & Observability (Phase 11–12):**
  - Interactive benchmark test runner with live pass/fail score distribution and latency breakdown.
  - Dynatrace and Splunk-style Real User Monitoring (RUM) and GenAI quality telemetry metrics.
  - Single and batch claim verification engine with confidence scoring and evidence attribution.

### Changed
- **Alembic Database Engine:**
  - Standardized root `alembic.ini` and normalized migration URL loading to prioritize `DATABASE_URL` with auto-migration from `postgres://` to `postgresql://`.
  - Reconciled schema head to revision `7a2c3d4e5f6a` covering all 34 relational database tables.
  - Enforced production startup bypass of `Base.metadata.create_all()` to ensure deterministic DDL evolution through migrations only.
- **Security & Secret Decoupling:**
  - Cryptographically decoupled JWT `SECRET_KEY` from Fernet dynamic provider `ENCRYPTION_KEY`.
  - Added strict Pydantic startup validation enforcing minimum 32-character entropy on critical secret keys in production environments.
  - Hardened SSRF defense filtering IPv4/IPv6 private ranges and cloud metadata endpoints.

---

## [0.9.0] - 2026-11-08 - System Hardening & Integration

### Added
- Writing Assistant revision diff engine and version history tracking.
- Editorial Studio publication pipeline converting research briefs into structured newsletter editions.
- PDF and DOCX document ingestion with text extraction safeguards.

### Fixed
- "Backend unavailable" status banner handling and automatic reconnection polling in the frontend.
- Writing audit score synchronization between backend analysis and frontend score meters.

---

## [0.5.0] - 2026-11-06 - Core Capabilities & AI Routing

### Added
- Research Assistant with multi-source ingestion (URL, file, pasted text).
- Deterministic heuristic AI fallback pipeline for offline operation without API keys.
- Multi-provider AI router supporting Groq, OpenAI, Anthropic, and Gemini.

---

## [0.1.0] - 2026-11-04 - Initial Foundation

### Added
- Project initialization with FastAPI backend and React/TypeScript frontend.
- Relational schema modeling with SQLAlchemy and Alembic.
- Core UI layouts and navigation scaffolding.

