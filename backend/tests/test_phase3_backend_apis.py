import io
import pytest
from PIL import Image
from backend.app.models.base import ResearchProject, Source, WritingDraft, User, Organization


def test_dashboard_endpoints(client, db_session):
    """Test all dashboard and analytics aggregation APIs."""
    # Overview
    res = client.get("/api/v1/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "recent_projects" in data
    assert "recent_drafts" in data
    assert data["metrics"]["total_projects"] >= 0

    # Activity
    res = client.get("/api/v1/dashboard/activity")
    assert res.status_code == 200
    assert "activities" in res.json()

    # Research Analytics
    res = client.get("/api/v1/dashboard/research-analytics")
    assert res.status_code == 200
    res_data = res.json()
    assert "total_sources" in res_data
    assert "verification_rate" in res_data

    # Writing Analytics
    res = client.get("/api/v1/dashboard/writing-analytics")
    assert res.status_code == 200
    wr_data = res.json()
    assert "total_drafts" in wr_data

    # Usage
    res = client.get("/api/v1/dashboard/usage")
    assert res.status_code == 200
    usage = res.json()
    assert "api_calls" in usage
    assert "rate_limit_quota" in usage


def test_integrations_management(client):
    """Test AI provider integrations, health checks, and connection lifecycle."""
    # List available providers
    res = client.get("/api/v1/integrations/providers")
    assert res.status_code == 200
    providers = res.json()
    provider_ids = [p["id"] for p in providers]
    assert "openai" in provider_ids
    assert "google_gemini" in provider_ids
    assert "anthropic" in provider_ids

    # Health check
    res = client.get("/api/v1/integrations/health")
    assert res.status_code == 200
    health = res.json()
    assert "status" in health
    assert "providers" in health

    # Create connection
    payload = {
        "provider": "openai",
        "name": "Production OpenAI Key",
        "api_key": "sk-proj-test1234567890abcdef1234567890",
        "is_default": True
    }
    res = client.post("/api/v1/integrations/connections", json=payload)
    assert res.status_code == 201
    conn = res.json()
    assert conn["provider"] == "openai"
    assert "masked_key" in conn
    assert not conn["masked_key"].startswith("sk-proj-test1234567890")  # Masked securely
    conn_id = conn["id"]

    # Validate connection
    res = client.post(f"/api/v1/integrations/connections/{conn_id}/validate")
    assert res.status_code == 200
    val_data = res.json()
    assert val_data["status"] in ("valid", "connected")

    # List connections
    res = client.get("/api/v1/integrations/connections")
    assert res.status_code == 200
    conns = res.json()
    assert any(c["id"] == conn_id for c in conns)

    # Delete connection
    res = client.delete(f"/api/v1/integrations/connections/{conn_id}")
    assert res.status_code == 200


def test_multimodal_document_upload_and_extraction(client, db_session):
    """Test multi-modal file ingestion for text and images into research sources."""
    # Create project first
    project = ResearchProject(
        id="proj-phase3-test",
        title="Multi-modal Ingestion Project",
        status="active"
    )
    db_session.add(project)
    db_session.commit()

    # 1. Plaintext / Markdown document upload
    sample_text = (
        "# High-Throughput Transformer Inference\n\n"
        "Batch scheduling and kernel fusion reduce end-to-end inference latency by 42%. "
        "Speculative decoding delivers a 2.5x speedup across 70B parameter models without degradation."
    )
    file_bytes = io.BytesIO(sample_text.encode("utf-8"))
    files = {"file": ("inference_paper.md", file_bytes, "text/markdown")}
    res = client.post(
        f"/api/v1/research/projects/{project.id}/sources/upload",
        files=files,
        data={"title": "Inference Latency Whitepaper"}
    )
    assert res.status_code == 201
    src_data = res.json()
    assert src_data["title"] == "Inference Latency Whitepaper"
    assert src_data["extraction_status"] == "completed"
    assert "inference latency" in src_data["extracted_content"]
    source_id = src_data["id"]

    # 2. Image upload and extraction
    img_buf = io.BytesIO()
    img = Image.new("RGB", (400, 200), color=(73, 109, 137))
    img.save(img_buf, format="PNG")
    img_buf.seek(0)
    img_files = {"file": ("architecture_chart.png", img_buf, "image/png")}
    res = client.post(
        f"/api/v1/research/projects/{project.id}/sources/upload",
        files=img_files,
        data={"title": "Architecture Chart Diagram"}
    )
    assert res.status_code == 201
    img_src = res.json()
    assert img_src["extraction_status"] == "completed"
    assert img_src["title"] == "Architecture Chart Diagram"

    # 3. Re-upload / retry on existing source
    reupload_text = "Updated technical analysis verifying liquid cooling benchmarks for clusters."
    re_buf = io.BytesIO(reupload_text.encode("utf-8"))
    re_files = {"file": ("updated_cooling.txt", re_buf, "text/plain")}
    res = client.post(
        f"/api/v1/sources/{source_id}/upload",
        files=re_files
    )
    assert res.status_code == 200
    re_data = res.json()
    assert re_data["extraction_status"] == "completed"
    assert "liquid cooling benchmarks" in re_data["extracted_content"]


def test_research_lifecycle_endpoints(client, db_session):
    """Test PATCH project, GET sources, and GET results."""
    project = ResearchProject(
        id="proj-lifecycle-test",
        title="Original Title",
        status="active"
    )
    db_session.add(project)
    db_session.commit()

    # Patch project
    res = client.patch(
        f"/api/v1/research/projects/{project.id}",
        json={"title": "Updated Research Lifecycle Project", "description": "Phase 3 Verified"}
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Research Lifecycle Project"

    # Get sources
    res = client.get(f"/api/v1/research/projects/{project.id}/sources")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Get results
    res = client.get(f"/api/v1/research/projects/{project.id}/results")
    assert res.status_code == 200
    results = res.json()
    assert "project" in results
    assert "sources" in results
    assert "ready_for_editorial" in results


def test_writing_lifecycle_and_versions(client, db_session):
    """Test PATCH draft, rewrite, and version history."""
    draft = WritingDraft(
        id="draft-phase3-test",
        title="Initial Draft Review",
        original_content="In order to understand reasoning models, many tests were conducted.",
        revised_content="In order to understand reasoning models, many tests were conducted.",
        status="draft"
    )
    db_session.add(draft)
    db_session.commit()

    # Patch draft content
    res = client.patch(
        f"/api/v1/writing/drafts/{draft.id}",
        json={"title": "Updated Draft Title", "content": "Modern reasoning architectures deliver deterministic performance."}
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Draft Title"

    # Rewrite draft
    res = client.post(
        f"/api/v1/writing/drafts/{draft.id}/rewrite",
        json={"instructions": "Make it punchy and executive-friendly", "tone": "authoritative"}
    )
    assert res.status_code == 200
    assert "revised_content" in res.json()

    # Check version history
    res = client.get(f"/api/v1/writing/drafts/{draft.id}/versions")
    assert res.status_code == 200
    versions = res.json()
    assert isinstance(versions, list)
    assert len(versions) >= 1
