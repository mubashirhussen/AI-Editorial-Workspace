import pytest

def test_health_check(client):
    # Test Root
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    root_data = root_resp.json()
    assert root_data["application"] == "AI Editorial Workspace"
    assert root_data["status"] == "running"
    assert root_data["version"] == "1.0.0"

    # Test Health Endpoint with Database check
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "ai_engine" in data

def test_project_lifecycle(client):
    # 1. Create project
    create_resp = client.post("/api/v1/research/projects", json={
        "title": "State of Agentic Workflows 2026",
        "description": "Analyzing frontier models and agent orchestration frameworks."
    })
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]
    assert project_id is not None

    # 2. Get project
    get_resp = client.get(f"/api/v1/research/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "State of Agentic Workflows 2026"

    # 3. Add 3 sources (pasted text)
    sources_data = [
        {
            "title": "Frontier AI Benchmark Report",
            "source_type": "text",
            "text_content": "Frontier AI systems announced a 45% increase in multi-hop reasoning accuracy. However, latency metrics rose by 12% across distributed inference clusters."
        },
        {
            "title": "Enterprise Agent Adoption Survey",
            "source_type": "text",
            "text_content": "A survey of 500 enterprise CTOs revealed that 68% have deployed retrieval-augmented generation systems in production, while 40% are actively evaluating autonomous agents."
        },
        {
            "title": "Hardware Infrastructure Analysis",
            "source_type": "text",
            "text_content": "Data center power constraints are expected to limit accelerator scaling. Analysts predict specialized quantization will become mandatory for cost-effective edge deployment."
        }
    ]

    for s in sources_data:
        s_resp = client.post(f"/api/v1/research/projects/{project_id}/sources", json=s)
        assert s_resp.status_code == 201

    # 4. Check duplicate prevention
    dup_resp = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "title": "Duplicate URL test",
        "url": "https://example.com/source-one",
        "source_type": "url"
    })
    # If added again, should fail
    dup_resp_2 = client.post(f"/api/v1/research/projects/{project_id}/sources", json={
        "title": "Duplicate URL test 2",
        "url": "https://example.com/source-one",
        "source_type": "url"
    })
    assert dup_resp_2.status_code == 400

    # 5. Generate Brief
    brief_resp = client.post(f"/api/v1/research/projects/{project_id}/generate-brief")
    assert brief_resp.status_code == 200
    brief_data = brief_resp.json()
    assert "executive_summary" in brief_data
    assert len(brief_data["newsletter_angles"]) >= 3
    assert "recommended_angle" in brief_data

def test_ssrf_protection():
    from backend.app.utils.security import is_safe_url
    assert is_safe_url("http://127.0.0.1:8000") is False
    assert is_safe_url("http://localhost:3000") is False
    assert is_safe_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_url("http://192.168.1.1/admin") is False
    assert is_safe_url("ftp://example.com") is False

