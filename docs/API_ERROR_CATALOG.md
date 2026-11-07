# API Error Catalog & Handling Specification

This catalog documents all standardized error codes, HTTP status mappings, response envelope schemas, and handling protocols implemented in the **AI Editorial Workspace**.

---

## 1. Standardized Error Response Structure

All client error ($4xx$) and server error ($5xx$) responses conform to the following unified JSON contract:

```json
{
  "success": false,
  "message": "Human-readable diagnostic message explaining the cause of the error.",
  "error": {
    "code": "STANDARDIZED_ERROR_CODE",
    "details": null
  },
  "detail": "Backward-compatible string or validation error list",
  "request_id": "c1f7a8e2-4b3d-4e91-8d2a-1f8a7e3b5d92",
  "error_category": "STANDARDIZED_ERROR_CODE"
}
```

Every response also includes the correlating tracing header:
```http
X-Request-ID: c1f7a8e2-4b3d-4e91-8d2a-1f8a7e3b5d92
```

---

## 2. Error Code Catalog & Mappings

| HTTP Status | Error Code | Category | Cause / Description | Client Remediation |
| :---: | :--- | :--- | :--- | :--- |
| **400** | `BAD_REQUEST` | Validation / Logic | Malformed request parameters, invalid query logic, or violation of domain rules (e.g., fewer than 3 sources for brief synthesis). | Inspect `message` and adjust request parameters accordingly. |
| **401** | `UNAUTHORIZED` | Authentication | Missing Bearer token, expired JWT, signature failure, or revoked token. | Redirect to login, obtain fresh credentials, or call `/api/v1/auth/refresh`. |
| **403** | `FORBIDDEN` | Authorization | User authenticated but lacks required role permission (e.g. `VIEWER` attempting `EDIT_DRAFTS` or `DELETE`). | Request elevated permissions or switch to an authorized organization. |
| **404** | `NOT_FOUND` | Resource Lookup | Target resource does not exist, was soft-deleted, or belongs to another organization (cross-tenant masking). | Verify UUID or verify active organization context header. |
| **409** | `DATABASE_INTEGRITY_ERROR` | Conflict | Database unique constraint violation (duplicate email or membership) or foreign-key collision. | Provide unique attributes or resolve dependency order. |
| **409** | `RESOURCE_CONFLICT` | Domain Conflict | State transition conflict or version mismatch. | Refresh resource state and re-attempt operation. |
| **422** | `VALIDATION_ERROR` | Pydantic Schema | Input payload violates typing, bounds (`min_length`, `max_length`), or missing required fields. | Review `error.details` for field-level error locations. |
| **429** | `RATE_LIMIT_EXCEEDED` | Rate Limiting | Client exceeded permitted request threshold (180 requests/min). | Check `Retry-After` header and back off before retrying. |
| **500** | `INTERNAL_SERVER_ERROR` | Server Crash | Unhandled server exception. Diagnostics logged with `request_id`; stack traces sanitized from client. | Contact support with `request_id` for correlation. |
| **502** | `AI_PROVIDER_ERROR` | Upstream AI Service | Upstream LLM provider API timed out or responded with a fatal network failure. Workspace automatically attempts fallback. | Re-try operation or review integration provider keys. |

---

## 3. Client Exception Handling Protocols (Frontend React Integration)

The React frontend (`frontend/src/services/api.ts`) includes centralized Axios response interceptors:
* **Session Expiration**: On HTTP 401, clears `access_token` and dispatches `session-expired` custom event.
* **Request Correlation**: Extracts `X-Request-ID` from response headers for display in developer diagnostics and toast notifications.
* **Validation Normalization**: Unpacks Pydantic validation errors (`loc`, `msg`) into user-friendly inline form notifications.
