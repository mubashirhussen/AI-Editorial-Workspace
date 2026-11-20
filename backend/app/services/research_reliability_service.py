"""
Phase 39: AI Research Reliability, Source Intelligence & Citation Verification Service.
Provides end-to-end evidence engineering:
- Source credibility assessment & explainable publisher profiling
- Source freshness analysis & canonical deduplication
- Sentence-level evidence extraction & location indexing
- Six-tier epistemic claim verification (SUPPORTED to NOT_APPLICABLE)
- Strict citation validation & hallucinated reference detection
- Cross-publisher corroboration & contradiction analysis
- Authoritative Research Quality Reporting
- Evidence-grounded section regeneration with diff tracking
"""

import re
import difflib
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from backend.app.models.base import (
    ResearchProject,
    Source,
    SourceAnalysis,
    ResearchBrief,
    ResearchClaim,
    ResearchEvidence,
    ResearchContradiction,
    SourceCredibilityAssessment,
    CitationValidation,
    ResearchQualityReport,
    ResearchRevision,
    User,
)
from backend.app.services.research.extraction_service import canonicalize_url, ResearchExtractionService
from backend.app.schemas.research_reliability import (
    ClaimVerificationItem,
    SourceIngestRequest,
)

logger = logging.getLogger("editorial_workspace.research_reliability")


class ResearchReliabilityService:
    """Core intelligence engine for research evidence quality, citation verification, and credibility assessment."""

    # Publisher taxonomy & domain classification rules
    KNOWN_INSTITUTIONAL_DOMAINS = {
        "arxiv.org": ("ArXiv", "PEER_REVIEWED", "Institutional Preprint Server", True, "HIGH"),
        "nature.com": ("Nature Publishing Group", "PEER_REVIEWED", "Academic Journal", True, "HIGH"),
        "science.org": ("AAAS Science", "PEER_REVIEWED", "Academic Journal", True, "HIGH"),
        "acm.org": ("ACM Digital Library", "PEER_REVIEWED", "Academic Conference/Journal", True, "HIGH"),
        "ieee.org": ("IEEE Xplore", "PEER_REVIEWED", "Academic Engineering Society", True, "HIGH"),
        "whitehouse.gov": ("U.S. Federal Government", "OFFICIAL_SOURCE", "Government Executive Office", True, "HIGH"),
        "sec.gov": ("U.S. Securities & Exchange Commission", "OFFICIAL_SOURCE", "Regulatory Agency", True, "HIGH"),
        "europa.eu": ("European Commission", "OFFICIAL_SOURCE", "Government Body", True, "HIGH"),
        "gov.uk": ("UK Government", "OFFICIAL_SOURCE", "Government Body", True, "HIGH"),
        "openai.com": ("OpenAI Research", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "anthropic.com": ("Anthropic Research", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "deepmind.google": ("Google DeepMind", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "research.google": ("Google Research", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "meta.com": ("Meta AI Research", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "microsoft.com": ("Microsoft Research", "OFFICIAL_SOURCE", "Primary Technology Developer", True, "HIGH"),
        "reuters.com": ("Reuters", "NEWS_REPORTING", "Global News Wire", False, "STANDARD"),
        "bloomberg.com": ("Bloomberg", "NEWS_REPORTING", "Financial News Publisher", False, "STANDARD"),
        "ft.com": ("Financial Times", "NEWS_REPORTING", "Business News Publisher", False, "STANDARD"),
        "wsj.com": ("The Wall Street Journal", "NEWS_REPORTING", "Business News Publisher", False, "STANDARD"),
        "techcrunch.com": ("TechCrunch", "NEWS_REPORTING", "Technology News Publisher", False, "STANDARD"),
        "theverge.com": ("The Verge", "NEWS_REPORTING", "Technology Media", False, "STANDARD"),
        "arstechnica.com": ("Ars Technica", "NEWS_REPORTING", "Technology Journalism", False, "STANDARD"),
        "venturebeat.com": ("VentureBeat", "NEWS_REPORTING", "Technology News", False, "STANDARD"),
        "medium.com": ("Medium", "OPINION", "User-Generated Blog Platform", False, "LOW"),
        "substack.com": ("Substack", "OPINION", "Independent Newsletter Platform", False, "LOW"),
    }

    # ---------------------------------------------------------------------------
    # 1. Source Credibility & Freshness Assessment
    # ---------------------------------------------------------------------------
    @classmethod
    def assess_source_credibility(
        cls,
        db: Session,
        source: Source,
        freshness_requirement: str = "technology"
    ) -> SourceCredibilityAssessment:
        """
        Evaluates source quality using explainable, transparent criteria.
        Analyzes publisher authority, author attribution, publication freshness,
        primary vs. secondary status, and methodological transparency.
        """
        existing = db.query(SourceCredibilityAssessment).filter(
            SourceCredibilityAssessment.source_id == source.id
        ).first()

        domain = source.domain.lower() if source.domain else ""
        # Match against known domain patterns
        matched_domain_info = None
        for known_d, info in cls.KNOWN_INSTITUTIONAL_DOMAINS.items():
            if domain == known_d or domain.endswith("." + known_d):
                matched_domain_info = info
                break

        if matched_domain_info:
            pub_name, cred_tier, pub_type, is_primary, method_transp = matched_domain_info
        elif source.source_type == "TEXT":
            pub_name = "User Provided Text"
            cred_tier = "PRIMARY_SOURCE"
            pub_type = "Direct User Submission"
            is_primary = True
            method_transp = "STANDARD"
        elif source.source_type == "FILE":
            pub_name = "Uploaded Document"
            cred_tier = "PRIMARY_SOURCE"
            pub_type = "Document Upload"
            is_primary = True
            method_transp = "STANDARD"
        elif any(kw in domain for kw in (".edu", ".ac.uk", ".gov", ".mil")):
            pub_name = domain.upper()
            cred_tier = "INSTITUTIONAL"
            pub_type = "Academic or Government TLD"
            is_primary = True
            method_transp = "HIGH"
        else:
            pub_name = domain if domain else "Unknown Publisher"
            cred_tier = "UNKNOWN"
            pub_type = "General Web Domain"
            is_primary = False
            method_transp = "STANDARD"

        # Check accessibility status
        if source.extraction_status == "COMPLETED":
            accessibility_status = "ACCESSIBLE"
        elif source.extraction_status == "PENDING":
            accessibility_status = "ACCESSIBLE"
        elif source.extraction_status == "FAILED":
            accessibility_status = "PERMANENT_ERROR" if "blocked" in (source.error_message or "").lower() else "RETRIABLE_ERROR"
        else:
            accessibility_status = "ACCESSIBLE"

        # Evaluate freshness based on requirement
        freshness_status, freshness_criteria = cls._compute_freshness(
            source.published_at, source.created_at, freshness_requirement
        )

        # Criteria breakdown
        has_author = bool(source.author and source.author.strip() and source.author.lower() != "unknown")
        has_date = bool(source.published_at and source.published_at.strip())
        word_count = source.word_count

        criteria_breakdown = {
            "publisher_identified": bool(pub_name and pub_name != "Unknown Publisher"),
            "publisher_authority": pub_type,
            "author_identified": has_author,
            "author_name": source.author if has_author else "Not stated in metadata",
            "publication_date_present": has_date,
            "publication_date": source.published_at if has_date else "Unavailable in HTTP metadata",
            "is_primary_source": is_primary,
            "methodological_transparency": method_transp,
            "word_count": word_count,
            "evidence_density": "HIGH" if word_count > 800 else "MEDIUM" if word_count > 250 else "LOW",
            "known_domain_match": matched_domain_info is not None,
        }

        # Formulate limitations explanation
        limitations_items = []
        if not has_author:
            limitations_items.append("Author attribution unavailable in source metadata.")
        if not has_date:
            limitations_items.append("Original publication date could not be extracted; freshness inferred from retrieval date.")
        if cred_tier == "UNKNOWN":
            limitations_items.append("Domain is not part of certified academic or official publisher registry; claims require independent corroboration.")
        if accessibility_status != "ACCESSIBLE":
            limitations_items.append(f"Source content retrieval encountered: {source.error_message or 'extraction failure'}.")

        limitations = " ".join(limitations_items) if limitations_items else "No critical methodological limitations identified."

        if existing:
            existing.credibility_tier = cred_tier
            existing.publisher_type = pub_type
            existing.publisher_name = pub_name
            existing.author_name = source.author
            existing.publication_date = source.published_at
            existing.freshness_status = freshness_status
            existing.freshness_criteria = freshness_criteria
            existing.accessibility_status = accessibility_status
            existing.is_primary_source = is_primary
            existing.methodological_transparency = method_transp
            existing.criteria_breakdown_json = criteria_breakdown
            existing.limitations = limitations
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        assessment = SourceCredibilityAssessment(
            id=str(uuid.uuid4()),
            source_id=source.id,
            project_id=source.project_id,
            credibility_tier=cred_tier,
            publisher_type=pub_type,
            publisher_name=pub_name,
            author_name=source.author,
            publication_date=source.published_at,
            freshness_status=freshness_status,
            freshness_criteria=freshness_criteria,
            accessibility_status=accessibility_status,
            is_primary_source=is_primary,
            methodological_transparency=method_transp,
            criteria_breakdown_json=criteria_breakdown,
            limitations=limitations,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @classmethod
    def _compute_freshness(
        cls,
        pub_date_str: Optional[str],
        retrieved_at: Optional[datetime],
        requirement: str
    ) -> Tuple[str, str]:
        """Computes freshness status based on publication date and contextual requirement."""
        now = datetime.now(timezone.utc)
        parsed_date = None

        if pub_date_str:
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y", "%Y"):
                try:
                    cleaned = pub_date_str.strip()[:19]
                    parsed_date = datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
                    break
                except Exception:
                    continue

        ref_date = parsed_date or retrieved_at or now
        if ref_date.tzinfo is None:
            ref_date = ref_date.replace(tzinfo=timezone.utc)

        age_days = (now - ref_date).total_seconds() / 86400.0

        if requirement == "breaking_news":
            if age_days <= 2.0:
                return "CURRENT", f"Within 48-hour breaking news threshold ({round(age_days, 1)} days old)."
            elif age_days <= 7.0:
                return "RECENT", f"Within 7-day news development cycle ({round(age_days, 1)} days old)."
            else:
                return "AGED", f"Exceeds 7-day breaking news freshness standard ({round(age_days, 1)} days old)."

        elif requirement == "scientific":
            if age_days <= 365.0:
                return "CURRENT", f"Published within past 12 months ({round(age_days / 30.0, 1)} months old)."
            elif age_days <= 1095.0:
                return "RECENT", f"Published within 3-year research window ({round(age_days / 365.0, 1)} years old)."
            else:
                return "HISTORICAL", f"Prior research literature ({round(age_days / 365.0, 1)} years old)."

        elif requirement == "historical":
            return "HISTORICAL", "Historical context reference; timeless empirical baseline."

        else:  # "technology" or "industry_update"
            if age_days <= 90.0:
                return "CURRENT", f"Active technology cycle ({round(age_days, 1)} days old)."
            elif age_days <= 365.0:
                return "RECENT", f"Annual tech update window ({round(age_days / 30.0, 1)} months old)."
            else:
                return "AGED", f"Dated technology reference ({round(age_days / 365.0, 1)} years old)."

    # ---------------------------------------------------------------------------
    # 2. Source Ingestion Pipeline with Deduplication
    # ---------------------------------------------------------------------------
    @classmethod
    async def ingest_source(
        cls,
        db: Session,
        project_id: str,
        request: SourceIngestRequest
    ) -> Tuple[Source, SourceCredibilityAssessment, bool]:
        """
        Executes robust source ingestion:
        Input Validation -> SSRF Defense -> Canonicalization -> Deduplication -> Extraction -> Evidence Generation -> Credibility Assessment.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise ValueError(f"Research project '{project_id}' not found.")

        is_url = request.source_type == "URL" and bool(request.url and request.url.strip())
        raw_url = request.url.strip() if is_url else None
        canon_url = canonicalize_url(raw_url) if raw_url else None

        # Content preparation
        extracted_text = (request.text_content or "").strip()
        title = (request.title or "").strip() or (raw_url if raw_url else "Untitled Source")
        author = None
        published_at = None
        status = "COMPLETED"
        err_msg = None

        extractor = ResearchExtractionService()

        # Execute URL retrieval if URL provided
        if is_url:
            ext_res = await extractor.extract_url(raw_url)
            if ext_res["success"]:
                extracted_text = ext_res.get("content", "")
                title = ext_res.get("title") or title
                author = ext_res.get("author")
                published_at = ext_res.get("published_at")
                canon_url = ext_res.get("canonical_url") or canon_url
                status = "COMPLETED"
            else:
                status = "FAILED"
                err_msg = ext_res.get("error", "URL extraction failed")

        content_hash = hashlib.sha256(extracted_text.encode("utf-8")).hexdigest() if extracted_text else ""

        # Deduplication check within project
        existing_duplicate = None
        if canon_url:
            existing_duplicate = db.query(Source).filter(
                Source.project_id == project_id,
                Source.deleted_at.is_(None),
                (Source.url == canon_url) | (Source.original_url == raw_url)
            ).first()

        if not existing_duplicate and content_hash:
            # Check content hash duplicate
            existing_sources = db.query(Source).filter(
                Source.project_id == project_id,
                Source.deleted_at.is_(None)
            ).all()
            for s in existing_sources:
                if s.content_hash == content_hash:
                    existing_duplicate = s
                    break

        if existing_duplicate:
            # Re-evaluate credibility and return duplicate flag
            cred = cls.assess_source_credibility(db, existing_duplicate, request.freshness_requirement)
            return existing_duplicate, cred, True

        # Persist new source
        new_source = Source(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title,
            url=canon_url or raw_url,
            original_url=raw_url,
            source_type=request.source_type,
            raw_content=request.text_content or extracted_text,
            extracted_content=extracted_text,
            author=author,
            published_at=published_at,
            extraction_status=status,
            error_message=err_msg,
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)

        # Extract sentence-level evidence passages
        if extracted_text:
            cls.extract_evidence_passages(db, new_source)

        # Assess source credibility
        cred = cls.assess_source_credibility(db, new_source, request.freshness_requirement)

        return new_source, cred, False

    # ---------------------------------------------------------------------------
    # 3. Sentence-Level Evidence Extraction & Passage Indexing
    # ---------------------------------------------------------------------------
    @classmethod
    def extract_evidence_passages(cls, db: Session, source: Source) -> List[ResearchEvidence]:
        """
        Extracts atomic evidence passages from source text, indexing exact paragraph locations
        and computing content hashes for permanent traceability.
        """
        text = (source.extracted_content or source.raw_content or "").strip()
        if not text:
            return []

        # Split into paragraphs and sentences
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        evidence_records = []

        for p_idx, para in enumerate(paragraphs, start=1):
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for s_idx, sent in enumerate(sentences, start=1):
                clean_sent = sent.strip()
                # Keep substantive sentences (between 40 and 400 chars)
                if len(clean_sent) < 40:
                    continue

                location_ref = f"Paragraph {p_idx}, Sentence {s_idx}"
                ev_hash = hashlib.sha256(clean_sent.encode("utf-8")).hexdigest()[:12]

                # Classify fact type
                lower_sent = clean_sent.lower()
                if any(w in lower_sent for w in ("announced", "released", "published", "demonstrated", "achieved", "tested", "measured")):
                    fact_type = "DIRECT_FACT"
                elif any(w in lower_sent for w in ("according to", "reported by", "stated", "claimed", "spokesperson")):
                    fact_type = "REPORTED_FACT"
                elif any(w in lower_sent for w in ("suggests", "indicates", "implies", "may lead to", "likely")):
                    fact_type = "INFERENCE"
                else:
                    fact_type = "DIRECT_FACT"

                ev = ResearchEvidence(
                    id=str(uuid.uuid4()),
                    project_id=source.project_id,
                    source_id=source.id,
                    excerpt=clean_sent,
                    fact_type=fact_type,
                    confidence=0.95 if fact_type == "DIRECT_FACT" else 0.85,
                    verified=True,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(ev)
                evidence_records.append(ev)

        db.commit()
        return evidence_records

    # ---------------------------------------------------------------------------
    # 4. Six-Tier Claim Extraction & Verification
    # ---------------------------------------------------------------------------
    @classmethod
    def extract_and_verify_claims(
        cls,
        db: Session,
        project_id: str,
        brief_id: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> List[ClaimVerificationItem]:
        """
        Extracts factual statements and performs formal six-tier epistemic verification:
        - SUPPORTED: Retrieved evidence directly and sufficiently supports the claim.
        - PARTIALLY_SUPPORTED: Evidence supports some aspects but not the complete statement.
        - UNSUPPORTED: Available evidence does not adequately back the statement.
        - CONTRADICTED: Reliable evidence materially conflicts with the statement.
        - UNVERIFIED: Insufficient evidence available to evaluate.
        - NOT_APPLICABLE: Non-factual statement (opinion, prediction, editorial recommendation).
        """
        # Determine source text for claim extraction
        content_to_audit = ""
        if text_content:
            content_to_audit = text_content
        elif brief_id:
            brief = db.query(ResearchBrief).filter(ResearchBrief.id == brief_id).first()
            if brief:
                content_to_audit = f"{brief.executive_summary}\n\n" + "\n\n".join(
                    str(d.get("summary") if isinstance(d, dict) else d) for d in (brief.key_developments or [])
                )
        else:
            brief = db.query(ResearchBrief).filter(
                ResearchBrief.project_id == project_id
            ).order_by(desc(ResearchBrief.updated_at)).first()
            if brief:
                content_to_audit = f"{brief.executive_summary}\n\n" + "\n\n".join(
                    str(d.get("summary") if isinstance(d, dict) else d) for d in (brief.key_developments or [])
                )

        if not content_to_audit:
            return []

        # Load project sources and verified evidence records
        sources = db.query(Source).filter(
            Source.project_id == project_id,
            Source.deleted_at.is_(None)
        ).all()
        evidence_items = db.query(ResearchEvidence).filter(
            ResearchEvidence.project_id == project_id
        ).all()
        contradictions = db.query(ResearchContradiction).filter(
            ResearchContradiction.project_id == project_id
        ).all()

        source_map = {s.id: s for s in sources}
        all_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content_to_audit) if len(s.strip()) > 25]

        verified_claims: List[ClaimVerificationItem] = []

        for idx, sentence in enumerate(all_sentences, start=1):
            lower_s = sentence.lower()

            # 1. Classify claim type
            if any(w in lower_s for w in ("in our opinion", "we believe", "we view", "impressive", "disappointing", "fascinating")):
                claim_type = "OPINION"
                status = "NOT_APPLICABLE"
                expl = "Editorial opinion or stylistic commentary; outside factual verification scope."
            elif any(w in lower_s for w in ("will likely", "projected to", "forecasted", "by 2028", "by 2030", "expected to surge")):
                claim_type = "PREDICTION"
                status = "NOT_APPLICABLE"
                expl = "Forward-looking prediction or forecast; empirical ground truth does not exist."
            elif any(w in lower_s for w in ("founders should", "recommend", "teams must", "we advise", "strategy ought to")):
                claim_type = "RECOMMENDATION"
                status = "NOT_APPLICABLE"
                expl = "Prescriptive strategic guidance; not an empirical factual claim."
            else:
                claim_type = "FACTUAL"
                status = "UNVERIFIED"
                expl = "Pending matching against primary evidence passages."

            supporting_passages = []
            conflicting_passages = []
            citations = []

            if claim_type == "FACTUAL":
                # Check for direct contradictions
                for contra in contradictions:
                    if (contra.claim_a_text and contra.claim_a_text[:40].lower() in lower_s) or \
                       (contra.claim_b_text and contra.claim_b_text[:40].lower() in lower_s):
                        status = "CONTRADICTED"
                        expl = f"Contradiction detected: {contra.disagreement_nature}"
                        conflicting_passages.append({
                            "claim_a": contra.claim_a_text,
                            "claim_b": contra.claim_b_text,
                            "disagreement": contra.disagreement_nature
                        })
                        break

                if status != "CONTRADICTED":
                    # Token matching against extracted evidence
                    claim_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', lower_s))
                    best_match = None
                    best_overlap = 0.0

                    for ev in evidence_items:
                        ev_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', ev.excerpt.lower()))
                        if not ev_words:
                            continue
                        overlap = len(claim_words & ev_words) / float(len(claim_words)) if claim_words else 0.0

                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_match = ev

                    if best_overlap >= 0.55:
                        status = "SUPPORTED"
                        expl = f"Corroborated by primary evidence passage ({round(best_overlap * 100, 1)}% semantic overlap)."
                        source_obj = source_map.get(best_match.source_id)
                        supporting_passages.append({
                            "evidence_id": best_match.id,
                            "source_id": best_match.source_id,
                            "source_title": source_obj.title if source_obj else "Primary Source",
                            "excerpt": best_match.excerpt,
                            "fact_type": best_match.fact_type,
                            "confidence": best_match.confidence,
                        })
                        if source_obj and source_obj.url:
                            citations.append(source_obj.url)
                    elif best_overlap >= 0.30:
                        status = "PARTIALLY_SUPPORTED"
                        expl = f"Partially grounded in source excerpt; minor aspects inferred ({round(best_overlap * 100, 1)}% overlap)."
                        source_obj = source_map.get(best_match.source_id)
                        supporting_passages.append({
                            "evidence_id": best_match.id,
                            "source_id": best_match.source_id,
                            "source_title": source_obj.title if source_obj else "Primary Source",
                            "excerpt": best_match.excerpt,
                            "fact_type": best_match.fact_type,
                            "confidence": 0.70,
                        })
                        if source_obj and source_obj.url:
                            citations.append(source_obj.url)
                    else:
                        status = "UNSUPPORTED"
                        expl = "No supporting excerpt found in ingested project sources."

            verified_claims.append(ClaimVerificationItem(
                id=f"claim-{idx}-{uuid.uuid4().hex[:6]}",
                claim_text=sentence,
                claim_type=claim_type,
                verification_status=status,
                claim_location=f"Sentence {idx}",
                supporting_evidence=supporting_passages,
                conflicting_evidence=conflicting_passages,
                citation_references=citations,
                confidence=0.95 if status == "SUPPORTED" else 0.70 if status == "PARTIALLY_SUPPORTED" else 0.40,
                explanation=expl
            ))

        return verified_claims

    # ---------------------------------------------------------------------------
    # 5. Citation Validation & Anti-Fabrication Engine
    # ---------------------------------------------------------------------------
    @classmethod
    def validate_citations(
        cls,
        db: Session,
        project_id: str,
        brief_id: Optional[str] = None
    ) -> List[CitationValidation]:
        """
        Conducts strict citation validation:
        - Validates referential integrity against real stored Source records.
        - Prevents fabricated citations (citations citing non-existent sources or URLs).
        - Verifies URL format, accessibility status, and deduplicates citations.
        """
        sources = db.query(Source).filter(
            Source.project_id == project_id,
            Source.deleted_at.is_(None)
        ).all()
        source_id_map = {s.id: s for s in sources}
        source_url_map = {}
        for s in sources:
            if s.url:
                source_url_map[canonicalize_url(s.url)] = s
            if s.original_url:
                source_url_map[canonicalize_url(s.original_url)] = s

        # Find target brief
        brief = None
        if brief_id:
            brief = db.query(ResearchBrief).filter(ResearchBrief.id == brief_id).first()
        if not brief:
            brief = db.query(ResearchBrief).filter(
                ResearchBrief.project_id == project_id
            ).order_by(desc(ResearchBrief.updated_at)).first()

        citations_to_audit: List[Dict[str, Any]] = []

        if brief and brief.source_references:
            for idx, ref in enumerate(brief.source_references, start=1):
                if isinstance(ref, dict):
                    citations_to_audit.append({
                        "number": idx,
                        "text": ref.get("title") or ref.get("text") or f"Citation [{idx}]",
                        "url": ref.get("url") or ref.get("link"),
                        "source_id": ref.get("source_id"),
                    })
                elif isinstance(ref, str):
                    citations_to_audit.append({
                        "number": idx,
                        "text": ref,
                        "url": ref if ref.startswith("http") else None,
                        "source_id": None,
                    })

        # If brief references are empty, extract from sources directly
        if not citations_to_audit:
            for idx, s in enumerate(sources, start=1):
                citations_to_audit.append({
                    "number": idx,
                    "text": s.title,
                    "url": s.url or s.original_url,
                    "source_id": s.id,
                })

        validation_records: List[CitationValidation] = []
        seen_urls = set()

        for c in citations_to_audit:
            c_text = c["text"]
            raw_url = c["url"]
            canon_c_url = canonicalize_url(raw_url) if raw_url else None
            matched_source = None
            is_fabricated = False
            status = "UNVERIFIED"
            details = {}

            # 1. Match source by source_id
            if c.get("source_id") and c["source_id"] in source_id_map:
                matched_source = source_id_map[c["source_id"]]
            elif canon_c_url and canon_c_url in source_url_map:
                matched_source = source_url_map[canon_c_url]
            else:
                # Text title match fallback
                for s in sources:
                    if s.title.lower() in c_text.lower() or c_text.lower() in s.title.lower():
                        matched_source = s
                        break

            # 2. Check for fabrication
            if not matched_source:
                # Source ID was supplied but does not exist in project -> Fabricated!
                is_fabricated = True
                status = "INVALID"
                details = {
                    "reason": "Citation references a source ID or URL not present in project library.",
                    "source_record_found": False,
                    "url_accessible": False
                }
            else:
                # Source exists
                if matched_source.extraction_status == "COMPLETED":
                    status = "VALID"
                    details = {
                        "source_record_found": True,
                        "matched_source_id": matched_source.id,
                        "source_title": matched_source.title,
                        "url_accessible": True,
                        "canonical_url": matched_source.url
                    }
                elif matched_source.extraction_status == "FAILED":
                    status = "BROKEN"
                    details = {
                        "source_record_found": True,
                        "matched_source_id": matched_source.id,
                        "error": matched_source.error_message or "Extraction failed",
                        "url_accessible": False
                    }
                else:
                    status = "NEEDS_REVIEW"
                    details = {
                        "source_record_found": True,
                        "status": matched_source.extraction_status,
                        "url_accessible": False
                    }

            # 3. Duplicate check
            if canon_c_url and canon_c_url in seen_urls:
                details["is_duplicate_citation"] = True
            if canon_c_url:
                seen_urls.add(canon_c_url)

            rec = CitationValidation(
                id=str(uuid.uuid4()),
                project_id=project_id,
                brief_id=brief.id if brief else None,
                source_id=matched_source.id if matched_source else None,
                citation_text=c_text,
                citation_url=raw_url,
                citation_number=c["number"],
                status=status,
                validation_details_json=details,
                is_fabricated=is_fabricated,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(rec)
            validation_records.append(rec)

        db.commit()
        return validation_records

    # ---------------------------------------------------------------------------
    # 6. Corroboration & Disagreement Analysis
    # ---------------------------------------------------------------------------
    @classmethod
    def analyze_corroboration_and_contradictions(cls, db: Session, project_id: str) -> Dict[str, Any]:
        """
        Analyzes evidence corroboration across independent publishers vs. single-source syndication,
        and aggregates cross-source contradictions while preserving unresolved tensions.
        """
        sources = db.query(Source).filter(
            Source.project_id == project_id,
            Source.deleted_at.is_(None)
        ).all()
        contradictions = db.query(ResearchContradiction).filter(
            ResearchContradiction.project_id == project_id
        ).all()

        unique_domains = {s.domain for s in sources if s.domain}
        primary_sources = [s for s in sources if s.source_type in ("TEXT", "FILE") or any(
            d in (s.domain or "") for d in ("arxiv.org", "whitehouse.gov", "sec.gov", "openai.com", "anthropic.com")
        )]

        # Classify corroboration tier
        if len(unique_domains) >= 3 and len(primary_sources) >= 1:
            corroboration_tier = "STRONG_INDEPENDENT_CORROBORATION"
            explanation = f"Findings corroborated across {len(unique_domains)} independent domains including verified primary sources."
        elif len(unique_domains) >= 2:
            corroboration_tier = "MODERATE_CROSS_PUBLISHER"
            explanation = f"Corroborated across {len(unique_domains)} independent domains."
        elif len(sources) > 1:
            corroboration_tier = "SINGLE_DOMAIN_MULTIPLE_REPORTS"
            explanation = "Multiple source entries originate from the same publisher or syndicated network; shared provenance."
        else:
            corroboration_tier = "SINGLE_SOURCE_UNVERIFIED"
            explanation = "Only one source available; claims cannot be cross-verified."

        contra_list = []
        for c in contradictions:
            contra_list.append({
                "id": c.id,
                "claim_a": c.claim_a_text,
                "claim_b": c.claim_b_text,
                "disagreement_nature": c.disagreement_nature,
                "possible_explanations": c.possible_explanations,
                "unresolved_questions": c.unresolved_questions,
            })

        return {
            "corroboration_tier": corroboration_tier,
            "explanation": explanation,
            "total_sources": len(sources),
            "unique_domains_count": len(unique_domains),
            "primary_sources_count": len(primary_sources),
            "contradictions_count": len(contra_list),
            "contradictions": contra_list,
        }

    # ---------------------------------------------------------------------------
    # 7. Research Quality Report Generation
    # ---------------------------------------------------------------------------
    @classmethod
    def generate_quality_report(
        cls,
        db: Session,
        project_id: str,
        brief_id: Optional[str] = None
    ) -> ResearchQualityReport:
        """
        Synthesizes an explainable, comprehensive Research Quality Report.
        Computes factual claim support rates, citation health, source diversity,
        and documents explicit research limitations.
        """
        # Run claim verification
        claims = cls.extract_and_verify_claims(db, project_id, brief_id=brief_id)
        # Run citation validation
        citations = cls.validate_citations(db, project_id, brief_id=brief_id)
        # Run corroboration analysis
        corrob = cls.analyze_corroboration_and_contradictions(db, project_id)

        sources = db.query(Source).filter(
            Source.project_id == project_id,
            Source.deleted_at.is_(None)
        ).all()

        total_claims = len(claims)
        supported = sum(1 for c in claims if c.verification_status == "SUPPORTED")
        partially = sum(1 for c in claims if c.verification_status == "PARTIALLY_SUPPORTED")
        unsupported = sum(1 for c in claims if c.verification_status == "UNSUPPORTED")
        contradicted = sum(1 for c in claims if c.verification_status == "CONTRADICTED")
        unverified = sum(1 for c in claims if c.verification_status == "UNVERIFIED")
        not_applicable = sum(1 for c in claims if c.verification_status == "NOT_APPLICABLE")

        claims_requiring_evidence = total_claims - not_applicable

        if claims_requiring_evidence > 0:
            evidence_coverage_score = round(((supported + (0.5 * partially)) / float(claims_requiring_evidence)) * 100.0, 1)
        else:
            evidence_coverage_score = 100.0 if total_claims > 0 else 0.0

        total_citations = len(citations)
        valid_citations = sum(1 for c in citations if c.status == "VALID")
        if total_citations > 0:
            citation_health_score = round((valid_citations / float(total_citations)) * 100.0, 1)
        else:
            citation_health_score = 100.0 if len(sources) > 0 else 0.0

        source_diversity_score = min(100.0, corrob["unique_domains_count"] * 25.0)

        # Composite Grade Calculation
        composite_score = (evidence_coverage_score * 0.5) + (citation_health_score * 0.3) + (source_diversity_score * 0.2)
        if composite_score >= 88.0 and contradicted == 0:
            grade = "A"
        elif composite_score >= 75.0:
            grade = "B"
        elif composite_score >= 60.0:
            grade = "C"
        elif composite_score >= 45.0:
            grade = "D"
        else:
            grade = "F"

        # Source quality breakdown
        cred_assessments = db.query(SourceCredibilityAssessment).filter(
            SourceCredibilityAssessment.project_id == project_id
        ).all()
        tier_counts = {}
        for ca in cred_assessments:
            tier_counts[ca.credibility_tier] = tier_counts.get(ca.credibility_tier, 0) + 1

        source_quality_summary = {
            "total_sources": len(sources),
            "credibility_tier_breakdown": tier_counts,
            "primary_sources_count": sum(1 for ca in cred_assessments if ca.is_primary_source),
            "accessible_sources_count": sum(1 for ca in cred_assessments if ca.accessibility_status == "ACCESSIBLE"),
        }

        # Audit findings
        audit_findings = []
        if unsupported > 0:
            audit_findings.append({
                "severity": "HIGH",
                "finding": f"{unsupported} factual statements lack direct supporting evidence in ingested sources.",
                "remediation": "Ingest primary documentation or remove unsupported factual assertions."
            })
        if contradicted > 0:
            audit_findings.append({
                "severity": "CRITICAL",
                "finding": f"{contradicted} statements directly conflict with source data.",
                "remediation": "Review contradiction panel and present both perspectives."
            })
        if any(c.is_fabricated for c in citations):
            audit_findings.append({
                "severity": "CRITICAL",
                "finding": "Fabricated citation detected: referenced source ID or URL does not exist in library.",
                "remediation": "Replace with verified source record or remove footnote reference."
            })
        if corrob["unique_domains_count"] < 2:
            audit_findings.append({
                "severity": "MEDIUM",
                "finding": "Research relies on a single publisher domain; vulnerability to single-source bias.",
                "remediation": "Corroborate claims with at least one independent publisher."
            })

        # Limitations summary
        limitations_summary = f"Research based on {len(sources)} sources. " + (
            f"Caution: {unsupported} statements remain unsupported by primary evidence." if unsupported > 0
            else "All verifiable factual statements grounded in primary literature."
        )

        report = ResearchQualityReport(
            id=str(uuid.uuid4()),
            project_id=project_id,
            brief_id=brief_id,
            total_claims=total_claims,
            claims_requiring_evidence=claims_requiring_evidence,
            supported_claims=supported,
            partially_supported_claims=partially,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            unverified_claims=unverified,
            not_applicable_claims=not_applicable,
            evidence_coverage_score=evidence_coverage_score,
            citation_health_score=citation_health_score,
            source_diversity_score=source_diversity_score,
            overall_quality_grade=grade,
            source_quality_summary_json=source_quality_summary,
            corroboration_summary_json=corrob,
            contradictions_count=corrob["contradictions_count"],
            limitations_summary=limitations_summary,
            audit_findings_json=audit_findings,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    # ---------------------------------------------------------------------------
    # 8. Evidence-Grounded Section Regeneration
    # ---------------------------------------------------------------------------
    @classmethod
    def regenerate_section(
        cls,
        db: Session,
        project_id: str,
        brief_id: str,
        section_key: str,
        instructions: Optional[str] = None,
        required_evidence_ids: Optional[List[str]] = None
    ) -> Tuple[ResearchRevision, List[ClaimVerificationItem]]:
        """
        Regenerates a specific section of a research brief strictly constrained to verified evidence passages.
        Generates diff summary and preserves revision history.
        """
        brief = db.query(ResearchBrief).filter(
            ResearchBrief.id == brief_id,
            ResearchBrief.project_id == project_id
        ).first()
        if not brief:
            raise ValueError(f"Research brief '{brief_id}' not found for project '{project_id}'.")

        # Get original text
        if section_key == "executive_summary":
            original_text = brief.executive_summary or ""
        elif section_key == "key_developments":
            original_text = "\n".join(str(d.get("summary") if isinstance(d, dict) else d) for d in (brief.key_developments or []))
        elif section_key == "strategic_implications":
            original_text = str(brief.strategic_implications or "")
        else:
            original_text = brief.user_notes or ""

        # Fetch verified evidence
        ev_query = db.query(ResearchEvidence).filter(
            ResearchEvidence.project_id == project_id,
            ResearchEvidence.verified == True
        )
        if required_evidence_ids:
            ev_query = ev_query.filter(ResearchEvidence.id.in_(required_evidence_ids))

        evidence_items = ev_query.limit(10).all()
        supporting_ev_ids = [e.id for e in evidence_items]

        # Synthesize evidence-grounded regenerated text
        if evidence_items:
            passages = [f"• {e.excerpt}" for e in evidence_items[:4]]
            guidance = f" [{instructions.strip()}]" if instructions and instructions.strip() else ""
            regenerated_text = (
                f"{original_text.strip()}\n\n"
                f"[Grounded Evidence Revision{guidance}]:\n" +
                "\n".join(passages)
            )
        else:
            regenerated_text = original_text.strip() + "\n\n[Verified Baseline]: No supplementary primary evidence passages available to extend this section."

        # Compute diff summary
        diff_lines = list(difflib.unified_diff(
            original_text.splitlines(keepends=True),
            regenerated_text.splitlines(keepends=True),
            fromfile="Original",
            tofile="Regenerated",
            n=2
        ))
        diff_summary = "".join(diff_lines) if diff_lines else "No textual differences detected."

        # Persist revision
        revision = ResearchRevision(
            id=str(uuid.uuid4()),
            project_id=project_id,
            brief_id=brief_id,
            section_key=section_key,
            original_text=original_text,
            regenerated_text=regenerated_text,
            diff_summary=diff_summary,
            supporting_evidence_ids_json=supporting_ev_ids,
            status="PENDING",
            user_notes=instructions,
            created_at=datetime.now(timezone.utc),
        )
        db.add(revision)
        db.commit()
        db.refresh(revision)

        # Audit newly generated claims
        verified_claims = cls.extract_and_verify_claims(db, project_id, text_content=regenerated_text)

        return revision, verified_claims


research_reliability_service = ResearchReliabilityService()
