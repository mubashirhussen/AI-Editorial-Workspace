import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

class TestApiStandardizationAndReliability:
    """Comprehensive test suite verifying Phase 4 Backend API Standardization & Reliability."""

    @pytest.fixture(autouse=True)
    def setup_authenticated_session(self):
        """Creates and logs in an editor user to obtain a valid JWT."""
        self.email = f"editor_phase4_{os.urandom(4).hex()}@editorial.ai"
        self.password = "SecureTestPassword123!"
        self.full_name = "Phase 4 Architect"
        self.org_name = "API Standardization Guild"

        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "full_name": self.full_name,
                "organization_name": self.org_name
            }
        )
        assert reg_resp.status_code in (200, 201)
        data = reg_resp.json()
        self.token = data.get("access_token")
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}
        yield

    # 1. Standardized Error Response Envelope
    def test_standardized_error_response_on_validation_failure(self):
        """Verify 422 errors return standardized error structure and request correlation id."""
        # Intentionally missing required 'title' in project creation
        resp = client.post(
            "/api/v1/research/projects",
            json={"description": "Invalid payload missing title"},
            headers=self.auth_headers
        )
        assert resp.status_code == 422
        body = resp.json()

        # Check standardized fields
        assert body.get("success") is False
        assert "validation" in body.get("message", "").lower()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert isinstance(body["error"]["details"], list)
        assert "request_id" in body
        assert "X-Request-ID" in resp.headers

    def test_standardized_error_response_on_404_not_found(self):
        """Verify 404 resource errors conform to the standardized error schema."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(
            f"/api/v1/research/projects/{fake_id}",
            headers=self.auth_headers
        )
        assert resp.status_code == 404
        body = resp.json()

        assert body.get("success") is False
        assert body.get("error", {}).get("code") == "HTTP_404"
        assert f"Research project with ID '{fake_id}' not found." in body["message"]
        assert "X-Request-ID" in resp.headers

    # 2. Authentication & Authorization Standardized Guards
    def test_unauthenticated_request_rejected_with_401(self, monkeypatch):
        """Verify that endpoints requiring authentication strictly return HTTP 401 when anonymous dev is disabled."""
        monkeypatch.setattr(settings, "ALLOW_ANONYMOUS_DEV", False)
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        body = resp.json()
        assert body.get("success") is False
        assert "detail" in body or "error" in body

    def test_invalid_token_rejected_with_401(self):
        """Verify that malformed JWT tokens strictly return HTTP 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token.here"}
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body.get("success") is False

    # 3. HTTP Status Codes & RESTful Semantics
    def test_http_methods_and_status_codes_for_research_projects(self):
        """Verify POST yields 201, GET yields 200, PUT yields 200, DELETE yields 200."""
        # POST -> 201
        create_resp = client.post(
            "/api/v1/research/projects",
            json={"title": "Phase 4 Project Semantics", "description": "Verification of HTTP codes"},
            headers=self.auth_headers
        )
        assert create_resp.status_code == 201
        proj = create_resp.json()
        proj_id = proj["id"]
        assert proj["title"] == "Phase 4 Project Semantics"

        # GET -> 200
        get_resp = client.get(
            f"/api/v1/research/projects/{proj_id}",
            headers=self.auth_headers
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == proj_id

        # PUT -> 200
        update_resp = client.put(
            f"/api/v1/research/projects/{proj_id}",
            json={"title": "Phase 4 Project Semantics (Updated)"},
            headers=self.auth_headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["title"] == "Phase 4 Project Semantics (Updated)"

        # DELETE -> 200
        delete_resp = client.delete(
            f"/api/v1/research/projects/{proj_id}",
            headers=self.auth_headers
        )
        assert delete_resp.status_code == 200

    # 4. Writing Assistant API Consolidation
    def test_writing_assistant_complete_lifecycle(self):
        """Verify unified writing router: create draft, update, retrieve metrics, and analyze."""
        # 1. Create Draft
        draft_resp = client.post(
            "/api/v1/writing/drafts",
            json={
                "title": "Phase 4 Editorial Standardization",
                "content": "This is a high quality editorial draft demonstrating API consistency and robustness."
            },
            headers=self.auth_headers
        )
        assert draft_resp.status_code in (200, 201)
        draft = draft_resp.json()
        draft_id = draft["id"]

        # 2. Get Draft
        get_draft = client.get(
            f"/api/v1/writing/drafts/{draft_id}",
            headers=self.auth_headers
        )
        assert get_draft.status_code == 200
        assert get_draft.json()["id"] == draft_id

        # 3. Retrieve Metrics
        metrics_resp = client.get(
            f"/api/v1/writing/drafts/{draft_id}/metrics",
            headers=self.auth_headers
        )
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()
        assert "word_count" in metrics
        assert metrics["word_count"] > 0

        # 4. Update / Patch Draft
        patch_resp = client.patch(
            f"/api/v1/writing/drafts/{draft_id}",
            json={"content": "Updated content with additional analytical depth and standardized responses."},
            headers=self.auth_headers
        )
        assert patch_resp.status_code == 200

        # 5. List Versions
        ver_resp = client.get(
            f"/api/v1/writing/drafts/{draft_id}/versions",
            headers=self.auth_headers
        )
        assert ver_resp.status_code == 200
        assert isinstance(ver_resp.json(), list)

    # 5. Zero Duplicate Operation IDs in OpenAPI Specification
    def test_openapi_schema_has_zero_duplicate_operations(self):
        """Verify OpenAPI contract has no duplicate operation IDs across routes."""
        schema = app.openapi()
        assert "paths" in schema

        operation_ids = {}
        duplicates = []

        for path, methods in schema["paths"].items():
            for method, spec in methods.items():
                if method.lower() in ("get", "post", "put", "patch", "delete", "options", "head"):
                    op_id = spec.get("operationId")
                    if op_id:
                        if op_id in operation_ids:
                            duplicates.append((op_id, path, operation_ids[op_id]))
                        else:
                            operation_ids[op_id] = path

        assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate Operation IDs in OpenAPI schema: {duplicates}"

    # 6. Pagination & Query Parameter Limits
    def test_pagination_query_parameters_validation(self):
        """Verify skip and limit query parameter validation on standardized list endpoints."""
        # Limit > 100 should trigger a 422 validation error
        resp = client.get(
            "/api/v1/projects?limit=500",
            headers=self.auth_headers
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
