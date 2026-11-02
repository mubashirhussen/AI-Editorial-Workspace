# Forward Deployed Engineer (FDE) Scenario-Based Troubleshooting Playbook

This guide prepares engineers for customer-facing technical triage, incident response, and field engineering challenges.

---

## Scenario 1: A customer reports that research summaries are inaccurate or hallucinating facts.

- **How to Investigate:**
  1. Retrieve the `project_id`, `brief_id`, and `X-Request-ID` from the customer.
  2. Inspect the database records for `SourceAnalysis` and `Claim` associated with that project.
  3. Compare the generated summary claims against the verbatim `quote_excerpt` fields in the database.
- **What Questions to Ask:**
  - *"Which specific bullet point or claim in the research brief contradicts the source material?"*
  - *"Can you provide the URL or text of the primary source you ingested?"*
  - *"Was this generated using an external AI provider key or the deterministic rule engine?"*
- **How to Reproduce:**
  Create a test project in staging using the customer's identical primary sources and execute `POST /api/v1/research/projects/{id}/synthesize`.
- **Root Cause Identification:**
  Verify if the LLM hallucinated during synthesis or if the initial extraction scraper captured boilerplate/cookie text instead of the article body.
- **How to Implement a Solution:**
  Tighten the XML `<source_data>` prompt fences, increase few-shot grounding instructions, and lower temperature to `0.1` for synthesis.
- **How to Validate the Fix:**
  Run `pytest backend/tests/test_phase22_ai_evaluation.py` to confirm citation accuracy scores exceed 95%.
- **Customer Communication:**
  > *"Thank you for flagging this discrepancy. We investigated the brief and found that the source article contained conversational commentary that was interpreted too broadly by the model. We have updated our synthesis grounding filters to enforce stricter verbatim quote verification and re-generated your brief accurately."*

---

## Scenario 2: An AI provider changes its API response format or deprecates an endpoint.

- **How to Investigate:**
  1. Check application logs for HTTP 400 or HTTP 422 errors from the provider's adapter in `backend/app/services/ai/adapters/`.
  2. Inspect provider release notes and deprecation notices.
- **What Questions to Ask:**
  - *"Did the provider alter the JSON schema, model name, or authentication header requirement?"*
- **How to Reproduce:**
  Run the adapter unit test `pytest backend/tests/test_phase5_ai_integration.py` against the provider's live endpoint.
- **Root Cause Identification:**
  Identify specific field renames (e.g. `response.choices[0].message.content` vs `response.content[0].text`).
- **How to Implement a Solution:**
  Update the provider adapter class to deserialize both old and new response formats. Ensure the fallback engine catches unexpected payload schemas.
- **How to Validate the Fix:**
  Execute integration tests with mock responses reflecting the new API schema.
- **Customer Communication:**
  > *"We detected an upstream API schema update from the provider. Our intelligent fallback engine prevented downtime by servicing requests deterministically, and we have deployed a patch updating the adapter to the provider's new API version."*

---

## Scenario 3: A customer cannot connect their external AI API key.

- **How to Investigate:**
  1. Check server logs for decryption or validation failures on `POST /api/v1/integrations/verify`.
  2. Verify that the customer's key has not expired and has active billing credits on the provider console.
- **What Questions to Ask:**
  - *"Which provider key are you adding (OpenAI, Anthropic, Gemini, Groq)?"*
  - *"Does this key have organization-level permissions for chat completion models?"*
  - *"Are there IP whitelisting restrictions configured on your provider API dashboard?"*
- **How to Reproduce:**
  Test the key using a minimal curl test or the `/api/v1/integrations/verify` endpoint.
- **Root Cause Identification:**
  Common causes: account has $0 balance, copy-paste included trailing whitespace, or key lacks permissions for the specified model.
- **How to Implement a Solution:**
  Sanitize key inputs (strip leading/trailing whitespace), return clear diagnostic errors (e.g. "Quota Exceeded" or "Invalid Secret Key" rather than generic 500).
- **How to Validate the Fix:**
  Verify that `POST /api/v1/integrations/verify` returns HTTP 200 with masked key preview.
- **Customer Communication:**
  > *"We verified the connection attempt. The provider returned an authentication failure indicating that this API key currently has an expired billing quota. Please check your billing balance in the provider console or generate a fresh key with chat completion permissions."*

---

## Scenario 4: The application works locally but fails in production.

- **How to Investigate:**
  1. Inspect production container logs (`docker logs editorial-backend`).
  2. Test health probes `/health/live` and `/health/ready`.
  3. Verify environment variables in the production environment.
- **What Questions to Ask:**
  - *"Is the PostgreSQL database container healthy and accepting connections on port 5432?"*
  - *"Did database migrations execute (`alembic upgrade head`) on deployment?"*
  - *"Are CORS origins correctly configured for the production frontend domain?"*
- **How to Reproduce:**
  Spin up a clean production Docker Compose instance using `.env.example` in an isolated staging environment.
- **Root Cause Identification:**
  Often missing `SECRET_KEY`, unapplied database migrations, or CORS origin mismatches rejecting frontend Axios calls.
- **How to Implement a Solution:**
  Ensure entrypoint executes `alembic upgrade head` before starting Uvicorn, and pass `ALLOWED_ORIGINS` matching the production domain.
- **How to Validate the Fix:**
  Confirm `GET /health/ready` returns HTTP 200 `{"status": "ready", "database": "connected"}`.
- **Customer Communication:**
  > *"The issue was identified as an unapplied schema migration during container startup. We have automated migration execution in the container entrypoint, and the service is now fully operational."*

---

## Scenario 5: Research processing and source extraction take too long.

- **How to Investigate:**
  1. Inspect `ObservabilityMiddleware` latency logs for `/api/v1/sources/extract`.
  2. Check individual HTTP request durations to external target sites.
- **What Questions to Ask:**
  - *"Which URLs specifically trigger the latency spike?"*
  - *"Are the target websites applying rate-limiting or slow tarpitting to scrapers?"*
- **How to Reproduce:**
  Measure extraction latency for the target URLs using `time.perf_counter()`.
- **Root Cause Identification:**
  HTTP client hanging on slow external servers waiting for timeouts.
- **How to Implement a Solution:**
  Enforce strict 10–12 second socket timeouts in `httpx.AsyncClient` and execute source extractions concurrently via `asyncio.gather()`.
- **How to Validate the Fix:**
  Confirm multi-source extraction completes in $< 15\text{ seconds}$ total.
- **Customer Communication:**
  > *"We discovered that several remote websites were throttling automated connections. We have implemented parallel asynchronous extraction and strict connection timeouts to keep total brief generation under 15 seconds."*

---

## Scenario 6: Users report that writing suggestions are incorrect or overly aggressive.

- **How to Investigate:**
  1. Inspect the flagged draft in the database.
  2. Review the specific suggestions generated by `writing_analysis_service.py`.
- **What Questions to Ask:**
  - *"Which specific suggestion was inappropriate for your article's voice?"*
  - *"Did the suggestion misidentify technical domain terminology as jargon?"*
- **How to Reproduce:**
  Paste the customer's draft into `/api/v1/writing/analyze` and inspect the returned suggestion list.
- **Root Cause Identification:**
  Overly aggressive regex patterns flagging legitimate technical terms (e.g. "RAG" or "embeddings") as jargon.
- **How to Implement a Solution:**
  Add a customizable publication terminology whitelist and allow users to reject suggestions without impacting the rest of the draft.
- **How to Validate the Fix:**
  Run `pytest backend/tests/test_writing_analysis.py` to confirm precision and recall.
- **Customer Communication:**
  > *"We appreciate your feedback. We have added your custom technical terms to the publication whitelist so our auditor recognizes them as standard executive vocabulary."*

---

## Scenario 7: The database contains inconsistent records or orphaned claims.

- **How to Investigate:**
  1. Run diagnostic queries to find claims where `source_id` does not exist in `sources`.
  2. Check if transactions failed mid-execution.
- **What Questions to Ask:**
  - *"Were sources deleted while brief synthesis was actively running?"*
- **How to Reproduce:**
  Attempt deleting a source while its brief is generating.
- **Root Cause Identification:**
  Missing foreign key cascade constraints or uncommitted transactions.
- **How to Implement a Solution:**
  Add `ondelete="CASCADE"` to foreign key relationships in SQLAlchemy models and wrap multi-step operations in single database transactions.
- **How to Validate the Fix:**
  Confirm that deleting a source automatically cleans up all associated claims without orphan records.
- **Customer Communication:**
  > *"We resolved the database inconsistency by enforcing automated cascade cleanups. All orphaned claims have been reconciled, and data integrity is verified."*

---

## Scenario 8: Multiple organizations must use the same platform securely.

- **How to Investigate:**
  1. Inspect the `organization_id` column across all tables.
  2. Check query filters in repository and service methods.
- **What Questions to Ask:**
  - *"Can an authenticated user from Organization A access projects from Organization B by guessing UUIDs?"*
- **How to Reproduce:**
  Run `pytest backend/tests/test_phase24_multi_tenancy.py`.
- **Root Cause Identification:**
  Querying `db.query(ResearchProject).filter(ResearchProject.id == project_id)` without checking `organization_id`.
- **How to Implement a Solution:**
  Enforce tenant scoping on all CRUD operations: `filter(ResearchProject.organization_id == current_user.organization_id)`.
- **How to Validate the Fix:**
  Verify cross-tenant requests return HTTP 403 Forbidden or 404 Not Found.
- **Customer Communication:**
  > *"We have verified that strict organization-level data isolation is enforced across all endpoints. Cross-tenant access is cryptographically blocked by our JWT authorization layer."*

---

## Scenario 9: An external website blocks automated article extraction (Cloudflare / 403 Forbidden).

- **How to Investigate:**
  1. Inspect extraction logs for HTTP 403 Forbidden or captcha challenge pages.
  2. Check User-Agent and header configuration.
- **What Questions to Ask:**
  - *"Does this website require subscriber authentication or CAPTCHA verification?"*
- **How to Reproduce:**
  Attempt `extraction_service.extract_content_from_url(url)` on the target domain.
- **Root Cause Identification:**
  Target web server uses Cloudflare bot management or Cloudflare Turnstile that blocks automated HTTP requests.
- **How to Implement a Solution:**
  Configure standard browser User-Agent headers (`Mozilla/5.0...`). If still blocked, present the user with the instant **"Paste Text"** fallback modal in the UI.
- **How to Validate the Fix:**
  Verify that when extraction fails, the UI card displays `"Extraction failed - Paste Text"`, allowing the user to paste copy and proceed to full verification.
- **Customer Communication:**
  > *"Some technical publications employ bot-protection that blocks automated HTTP scrapers. In those cases, you can click 'Paste Text' on the source card to paste the article text directly. The system immediately verifies it and includes it in your research brief."*

---

## Scenario 10: The customer requests a feature that conflicts with the core architecture.

- **How to Investigate:**
  1. Understand the underlying business goal behind the request.
  2. Evaluate architectural impacts on security, scalability, and code integrity.
- **What Questions to Ask:**
  - *"What specific editorial bottleneck are you attempting to solve with this feature?"*
  - *"How would this impact our existing non-destructive draft preservation model?"*
- **Root Cause Identification:**
  The customer may request full-document automated AI re-writing, which conflicts with our core principle of preserving authorial voice and non-destructive sentence-level editing.
- **How to Implement a Solution:**
  Propose an architecturally sound alternative: allow batch acceptance of suggestions or custom style profiles rather than opaque full-text regeneration.
- **How to Validate the Fix:**
  Walk through a prototype demonstrating that the alternative solves their velocity need without destroying baseline traceability.
- **Customer Communication:**
  > *"We understand your goal of accelerating newsletter production. Rather than completely replacing the draft with generic AI copy—which risks flattening your publication's authoritative voice and hallucinating claims—we have enabled batch suggestion acceptance and custom publication style presets. This cuts your editing time in half while preserving 100% source attribution."*

