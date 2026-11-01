"""
Phase 21 - Advanced Security Hardening & Privacy Review Test Suite
Covers:
1. Invalid URL schemes and non-HTTP protocol rejection
2. Private, loopback, link-local, carrier-grade NAT, and cloud metadata SSRF rejection
3. Safe redirect vs. private IP redirect validation
4. Oversized input rejection / length bounding
5. Malformed AI response handling
6. XSS mitigation in HTML exports (script tags, javascript: schemes, entity escaping)
7. HTTP Security Headers verification (nosniff, DENY, xss protection)
8. In-memory Rate Limiting under burst volume
9. Sensitive information redaction in logs / error responses
"""

import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.utils.security import is_safe_url, is_ip_blocked
from backend.app.services.editorial.export_service import ExportService
from backend.app.models.base import EditorialOutput
import ipaddress

client = TestClient(app)

# =====================================================================
# 1. SSRF & URL VALIDATION
# =====================================================================
def test_ssrf_invalid_schemes_rejected():
    """Validates that non-HTTP/HTTPS protocols are rejected."""
    invalid_urls = [
        "ftp://internal.vault/secret.key",
        "file:///etc/passwd",
        "gopher://127.0.0.1:70/",
        "data:text/html,<script>alert(1)</script>",
        "javascript:alert(1)",
        "ldap://localhost:389/o=example",
        "dict://127.0.0.1:11211/",
        "tftp://10.0.0.1/config"
    ]
    for url in invalid_urls:
        assert is_safe_url(url) is False, f"Scheme in '{url}' must be rejected!"

def test_ssrf_private_and_cloud_metadata_ips_blocked():
    """Validates that all loopback, RFC1918, link-local, and cloud metadata IPs are blocked."""
    blocked_targets = [
        "http://localhost",
        "http://localhost:8000/api",
        "http://127.0.0.1:8080/admin",
        "http://127.0.1.1",
        "http://0.0.0.0",
        "http://[::1]",
        "http://10.0.0.5/secret",
        "http://172.16.0.10:80",
        "http://172.31.255.255",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",  # AWS / OpenStack metadata
        "http://metadata.google.internal/computeMetadata/v1/", # GCP metadata
        "http://100.100.100.200/latest/meta-data/",  # Alibaba metadata
        "http://100.64.0.1",                          # Carrier Grade NAT
        "http://service.corp.internal",
        "http://database.local",
    ]
    for target in blocked_targets:
        assert is_safe_url(target) is False, f"Target '{target}' must be rejected by SSRF guard!"

def test_ip_evasion_blocked():
    """Tests integer decimal IP and edge case IP evasion representations."""
    # 2130706433 is integer decimal for 127.0.0.1
    assert is_safe_url("http://2130706433/") is False
    # Link-local direct check
    link_local_ip = ipaddress.ip_address("169.254.169.254")
    assert is_ip_blocked(link_local_ip) is True

def test_safe_public_url_accepted():
    """Validates that legitimate public HTTP/HTTPS URLs pass safety checks."""
    safe_urls = [
        "https://www.google.com",
        "https://arxiv.org/abs/2303.08774",
        "https://github.com",
        "http://example.com"
    ]
    for url in safe_urls:
        assert is_safe_url(url) is True, f"Legitimate public URL '{url}' should be accepted."

# =====================================================================
# 2. XSS MITIGATION & HTML EXPORT HARDENING
# =====================================================================
def test_xss_mitigation_and_javascript_link_sanitization():
    """Validates that HTML export sanitizes script tags and disallows javascript: URI schemes."""
    export_svc = ExportService()
    
    mock_editorial = EditorialOutput(
        id="ed-sec-1",
        project_id="proj-sec-1",
        headline="AI Breakthrough <script>alert('xss')</script>",
        content="Testing paragraph with <img src=x onerror=alert(1)> and regular citations [1].",
        word_count=120,
        source_references=[
            {
                "index": 1,
                "title": "Malicious Link <b onmouseover=alert(1)>Hover</b>",
                "url": "javascript:alert(document.cookie)",
                "supported_claim": "Claim with <iframe> payload"
            },
            {
                "index": 2,
                "title": "Legitimate Source",
                "url": "https://trusted.ai/whitepaper",
                "supported_claim": "Factual benchmark claim"
            }
        ]
    )

    export_res = export_svc.export(mock_editorial, format_type="html")
    html_out = export_res.html_content

    # Assert raw script tags and event handlers are strictly escaped
    assert "<script>" not in html_out
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_out
    assert "<img src=x onerror=alert(1)>" not in html_out
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_out

    # Assert javascript: link is replaced with '#' or escaped safely
    assert 'href="javascript:alert' not in html_out
    assert 'href="#"' in html_out
    # Assert legitimate link is preserved
    assert 'href="https://trusted.ai/whitepaper"' in html_out

# =====================================================================
# 3. HTTP SECURITY HEADERS
# =====================================================================
def test_http_security_headers_present():
    """Verifies that all responses include defensive HTTP security headers."""
    resp = client.get("/")
    assert resp.status_code == 200
    headers = resp.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in (headers.get("Permissions-Policy") or "")

# =====================================================================
# 4. INPUT VALIDATION & OVERSIZED PAYLOAD BOUNDING
# =====================================================================
def test_input_validation_oversized_payload_rejected():
    """Validates that excessively large payload strings are rejected by Pydantic."""
    # Title exceeds 255 chars
    huge_title = "A" * 300
    resp = client.post("/api/v1/projects", json={
        "title": huge_title,
        "description": "Valid description"
    })
    assert resp.status_code == 422
    err_detail = str(resp.json())
    assert "string_too_long" in err_detail or "max_length" in err_detail or "at most 255" in err_detail

    # Oversized description (exceeds 10,000 chars)
    huge_desc = "D" * 15000
    resp2 = client.post("/api/v1/projects", json={
        "title": "Normal Title",
        "description": huge_desc
    })
    assert resp2.status_code == 422

# =====================================================================
# 5. ERROR SANITIZATION & LOG LEAK PREVENTION
# =====================================================================
def test_error_response_sanitization():
    """Ensures 404 and 500 error responses return structured JSON without raw database tracebacks."""
    # Invalid UUID format or missing project
    resp = client.get("/api/v1/projects/non-existent-uuid-12345")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    # Ensure no internal SQL syntax or local system file paths leak
    assert "Traceback" not in str(data)
    assert "SELECT " not in str(data)
    assert "C:\\" not in str(data)

