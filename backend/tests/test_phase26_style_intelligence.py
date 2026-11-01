import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app
from backend.app.core.database import get_db
from backend.app.models.base import EditorialStyleProfile, WritingDraft, WritingSuggestion
from backend.app.services.style_intelligence.tone_detector import ToneDetector
from backend.app.services.style_intelligence.terminology_checker import TerminologyChecker
from backend.app.services.style_intelligence.consistency_checker import ConsistencyChecker
from backend.app.services.style_intelligence.style_scorer import StyleScorer
from backend.app.services.style_intelligence.style_analyzer import style_analyzer

client = TestClient(app)

def test_tone_detector_promotional_hype_and_informal():
    detector = ToneDetector()
    text = (
        "This revolutionary model is an unrivaled game-changer that skyrocketed industry expectations. "
        "We are gonna deploy tons of accelerators tomorrow."
    )
    result = detector.analyze_tone(text)

    assert result["promotional_count"] >= 3
    assert result["informal_count"] >= 2
    assert "Promotional" in result["detected_tone"]
    assert len(result["suggestions"]) >= 5

    # Check that a suggestion provides an objective rewrite
    hype_sug = next(s for s in result["suggestions"] if s["category"] == "style_promotional_hype")
    assert hype_sug["suggested_rewrite"] != hype_sug["original_text"]

def test_terminology_checker_and_avoided_words():
    checker = TerminologyChecker()
    preferred_terms = {
        "AI chip": "AI accelerator",
        "running the model": "inference"
    }
    words_to_avoid = ["delve", "paradigm shift", "pivotal"]

    text = "We will delve into why running the model on an AI chip triggers a pivotal paradigm shift."
    result = checker.check_terminology(text, preferred_terms, words_to_avoid)

    assert result["terminology_deviations_count"] == 2
    assert result["avoided_words_count"] >= 2
    assert len(result["suggestions"]) >= 4

    # Verify suggested terminology substitution
    chip_sug = next(s for s in result["suggestions"] if "AI accelerator" in s["suggested_rewrite"])
    assert "AI accelerator" in chip_sug["suggested_rewrite"]

def test_consistency_checker_sentence_length_and_acronyms():
    checker = ConsistencyChecker()
    # Sentence with 30 words (exceeding 25)
    long_sentence = (
        "Hyperscale datacenter operators are dramatically scaling compute clusters across multiple regional grid "
        "interconnects while simultaneously retrofitting their existing liquid cooling facilities to support next generation "
        "two phase micro nuclear accelerators worldwide."
    )
    text = f"{long_sentence} We will test the Gpu performance."

    result = checker.check_consistency(text, max_sentence_length=25)

    assert result["length_violations_count"] == 1
    assert result["acronym_deviations_count"] == 1

    length_sug = next(s for s in result["suggestions"] if s["category"] == "style_sentence_length")
    assert "exceeding the publication maximum limit" in length_sug["explanation"]

    acronym_sug = next(s for s in result["suggestions"] if s["category"] == "style_consistency")
    assert "GPU" in acronym_sug["suggested_rewrite"]

def test_style_scorer_multidimensional():
    scorer = StyleScorer()
    # High compliance case
    score, metrics, qualitative = scorer.compute_score(
        text="Founders deploy compute clusters with high efficiency.",
        target_flesch_score=65.0,
        length_violations=0,
        total_sentences=1,
        terminology_deviations=0,
        avoided_words=0,
        promotional_count=0,
        informal_count=0
    )
    assert score >= 85.0
    assert "Strong adherence" in qualitative

    # Poor compliance case
    low_score, low_metrics, low_qual = scorer.compute_score(
        text="Game-changer revolutionary hype gonna delve paradigm shift.",
        target_flesch_score=65.0,
        length_violations=2,
        total_sentences=2,
        terminology_deviations=3,
        avoided_words=3,
        promotional_count=3,
        informal_count=2
    )
    assert low_score < 50.0

def test_style_profile_crud_and_tenant_isolation():
    unique_suffix = int(time.time() * 1000)

    # 1. Register Tenant A
    user_a = client.post("/api/v1/auth/register", json={
        "email": f"style_a_{unique_suffix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Style Alpha",
        "organization_name": "Org Alpha Style"
    }).json()
    token_a = user_a["access_token"]
    org_a_id = user_a["organization"]["id"]

    # 2. Register Tenant B
    user_b = client.post("/api/v1/auth/register", json={
        "email": f"style_b_{unique_suffix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Style Beta",
        "organization_name": "Org Beta Style"
    }).json()
    token_b = user_b["access_token"]
    org_b_id = user_b["organization"]["id"]

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_a_id}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}

    # 3. Create Custom Style Profile in Tenant A
    profile_payload = {
        "name": "Alpha Deep Tech Voice",
        "publication_name": "Alpha AI Review",
        "tone": "Rigorous, empirical, no-hype",
        "target_audience": "Systems Architects & Founders",
        "max_sentence_length": 22,
        "preferred_sentence_length": 16,
        "max_paragraph_length": 60,
        "target_flesch_score": 60.0,
        "preferred_terminology": {
            "AI chip": "accelerator ASIC"
        },
        "words_to_avoid": [
            "game-changer",
            "revolutionary",
            "delve"
        ],
        "is_default": True
    }

    create_res = client.post("/api/v1/styles", headers=headers_a, json=profile_payload)
    assert create_res.status_code == 201, create_res.text
    profile_a = create_res.json()
    profile_a_id = profile_a["id"]
    assert profile_a["name"] == "Alpha Deep Tech Voice"
    assert profile_a["is_default"] is True

    # 4. List Style Profiles for Tenant A
    list_res = client.get("/api/v1/styles", headers=headers_a)
    assert list_res.status_code == 200
    profiles = list_res.json()
    assert any(p["id"] == profile_a_id for p in profiles)

    # 5. Tenant B attempts to access Tenant A's private profile -> 404 Not Found
    res_b_attempt = client.get(f"/api/v1/styles/{profile_a_id}", headers=headers_b)
    assert res_b_attempt.status_code == 404

    # 6. Update Profile in Tenant A
    update_res = client.put(
        f"/api/v1/styles/{profile_a_id}",
        headers=headers_a,
        json={"max_sentence_length": 20}
    )
    assert update_res.status_code == 200
    assert update_res.json()["max_sentence_length"] == 20

    # 7. Delete Profile in Tenant A
    del_res = client.delete(f"/api/v1/styles/{profile_a_id}", headers=headers_a)
    assert del_res.status_code == 204

def test_style_check_on_writing_draft_and_non_destructive_accept():
    unique_suffix = int(time.time() * 1000)
    user = client.post("/api/v1/auth/register", json={
        "email": f"writer_{unique_suffix}@editorial.ai",
        "password": "Password123!",
        "full_name": "Writer One",
        "organization_name": "Writing Lab"
    }).json()
    token = user["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": user["organization"]["id"]}

    # Create a draft with style violations: hype phrase + non-preferred terminology
    original_text = (
        "This revolutionary AI chip delivers unprecedented throughput. "
        "Founders should avoid running the model on legacy hardware."
    )
    draft_res = client.post(
        "/api/v1/writing/drafts",
        headers=headers,
        json={
            "title": "Hardware Scaling 2026",
            "original_content": original_text,
            "revised_content": original_text
        }
    )
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # Trigger Style Check
    check_res = client.post(
        f"/api/v1/writing/drafts/{draft_id}/style-check",
        headers=headers,
        json={}
    )
    assert check_res.status_code == 200, check_res.text
    check_data = check_res.json()
    assert check_data["style_score"] < 100.0
    assert len(check_data["suggestions"]) >= 2
    assert check_data["avoided_words_count"] >= 1 or check_data["terminology_deviations_count"] >= 1

    # Grab first style suggestion
    first_sug = check_data["suggestions"][0]
    sug_id = first_sug["id"]
    assert sug_id is not None

    # Accept the suggestion
    accept_res = client.post(
        f"/api/v1/writing/drafts/{draft_id}/suggestions/{sug_id}/accept",
        headers=headers
    )
    assert accept_res.status_code == 200
    accept_data = accept_res.json()

    # Crucial Verification: revised_content changed, original_content preserved 100%
    assert accept_data["success"] is True
    assert accept_data["revised_content"] != original_text

    # Verify on draft record
    updated_draft = client.get(f"/api/v1/writing/drafts/{draft_id}", headers=headers).json()
    assert updated_draft["original_content"] == original_text
    assert updated_draft["revised_content"] != original_text
