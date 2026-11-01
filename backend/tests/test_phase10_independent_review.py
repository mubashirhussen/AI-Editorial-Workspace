import pytest
from backend.app.services.writing import writing_analyzer, metrics_service
from backend.app.utils.text_processing import replace_text_safely, calculate_reading_ease, split_into_sentences
from backend.app.utils.security import is_safe_url
from backend.app.services.editorial.export_service import export_service
from backend.app.models.base import EditorialOutput, ResearchProject, ResearchBrief, WritingDraft

def test_edge_case_empty_and_whitespace_writing_analysis():
    # Empty string
    res_empty = writing_analyzer.analyze_text("")
    assert res_empty.metrics.word_count == 0
    assert res_empty.metrics.sentence_count == 0
    assert len(res_empty.issues) == 0

    # Whitespace only
    res_ws = writing_analyzer.analyze_text("    \n\t   ")
    assert res_ws.metrics.word_count == 0
    assert len(res_ws.issues) == 0

    # Punctuation only
    res_punct = writing_analyzer.analyze_text("... ??? !!!")
    assert res_punct.metrics.word_count == 0
    assert len(res_punct.issues) == 0

def test_edge_case_stale_suggestion_rejection_and_safe_replacement():
    doc = "The engineering team published a new benchmark report."
    
    # 1. Target present once
    new_doc, ok, err = replace_text_safely(doc, "engineering team", "research group")
    assert ok is True
    assert err is None
    assert "research group published" in new_doc

    # 2. Target not present (stale suggestion scenario)
    new_doc2, ok2, err2 = replace_text_safely(new_doc, "engineering team", "another group")
    assert ok2 is False
    assert err2 is not None
    assert new_doc2 == new_doc # unchanged

    # 3. Empty target
    _, ok3, err3 = replace_text_safely(doc, "", "replacement")
    assert ok3 is False

def test_xss_mitigation_export_service():
    # Construct an editorial with potential XSS attack payloads
    malicious_headline = 'AI Update <script>alert("XSS")</script>'
    malicious_content = 'This is a test paragraph with <img src=x onerror=alert(1)> and a citation [1].\n\n## Subhead <script>stealCookies()</script>'
    malicious_refs = [
        {
            "index": 1,
            "title": 'Malicious Title <b onmouseover="alert(1)">Click</b>',
            "url": 'javascript:alert(1)',
            "supported_claim": '<script>bad()</script>'
        }
    ]

    ed = EditorialOutput(
        headline=malicious_headline,
        content=malicious_content,
        word_count=25,
        source_references=malicious_refs
    )

    html_out = export_service.build_html(ed)
    
    # Assert raw script tags and onerror handlers are completely entity-escaped
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "stealCookies" in html_out and "<script>stealCookies()" not in html_out
    assert "<img src=x" not in html_out
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_out
    assert '<b onmouseover="alert(1)">' not in html_out
    # Check citation is styled
    assert '<sup class="citation">[1]</sup>' in html_out

def test_ssrf_strict_blocking_vectors():
    blocked_urls = [
        "http://127.0.0.1:8000/api",
        "http://localhost:5173",
        "http://0.0.0.0:80",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "ftp://example.com/file.txt",
        "file:///etc/passwd",
        "http://10.0.0.1/admin",
        "http://172.16.0.1/status",
        "http://192.168.1.1/config"
    ]

    for u in blocked_urls:
        assert is_safe_url(u) is False, f"URL '{u}' should be strictly blocked by SSRF defense!"

def test_cross_project_isolation(client, db_session):
    # Create Project 1 and Brief 1
    p1 = ResearchProject(title="Project Alpha", name="Project Alpha", status="draft")
    db_session.add(p1)
    db_session.commit()
    db_session.refresh(p1)

    b1 = ResearchBrief(
        project_id=p1.id, 
        title="Brief Alpha",
        executive_summary="Executive summary for project Alpha test brief."
    )
    db_session.add(b1)
    db_session.commit()
    db_session.refresh(b1)

    # Create Project 2
    p2 = ResearchProject(title="Project Beta", name="Project Beta", status="draft")
    db_session.add(p2)
    db_session.commit()
    db_session.refresh(p2)

    # Attempt to generate editorial for Project 2 using Project 1's brief
    res = client.post("/api/v1/editorial/generate", json={
        "project_id": p2.id,
        "research_brief_id": b1.id
    })
    # Must reject with 400 Bad Request
    assert res.status_code == 400
    assert "Cross-project research brief rejected" in res.json()["detail"]
