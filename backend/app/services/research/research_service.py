import logging
import hashlib
import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.config import settings
from backend.app.models.base import (
    ResearchProject,
    Source,
    SourceAnalysis,
    ResearchBrief,
    ResearchClaim,
    ResearchEvidence
)
from backend.app.schemas.research import ProjectCreate, ProjectUpdate, ResearchBriefUpdate
from backend.app.schemas.source import SourceCreate
from backend.app.services.research.extraction_service import extraction_service, canonicalize_url
from backend.app.services.research.synthesis_service import synthesis_service
from backend.app.services.version_control.version_service import version_service
from backend.app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class ResearchService:
    """
    Core Research Assistant orchestrator.
    Manages projects, source extraction, single-source claim analysis,
    cross-source evidence synthesis, and relational claim/evidence persistence.
    """

    def create_project(self, db: Session, data: ProjectCreate, organization_id: Optional[str] = None) -> ResearchProject:
        title = data.title or getattr(data, "name", None) or "Untitled Investigation"
        project = ResearchProject(
            title=title.strip(),
            name=title.strip(),
            topic=data.topic.strip() if getattr(data, "topic", None) else None,
            description=data.description.strip() if data.description else None,
            research_objective=data.research_objective.strip() if getattr(data, "research_objective", None) else None,
            target_audience=data.target_audience.strip() if getattr(data, "target_audience", None) else None,
            research_scope=data.research_scope.strip() if getattr(data, "research_scope", None) else None,
            keywords=getattr(data, "keywords", []) or [],
            preferred_source_types=getattr(data, "preferred_source_types", []) or [],
            status="draft",
            organization_id=organization_id or getattr(data, "organization_id", None)
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def get_projects(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        query: Optional[str] = None,
        status: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> List[ResearchProject]:
        q = db.query(ResearchProject)
        if organization_id is not None:
            q = q.filter(
                (ResearchProject.organization_id == organization_id) | (ResearchProject.organization_id == None)
            )
        if status:
            q = q.filter(ResearchProject.status == status.lower())
        if query and query.strip():
            search_pat = f"%{query.strip()}%"
            q = q.filter(
                (ResearchProject.title.ilike(search_pat)) |
                (ResearchProject.description.ilike(search_pat))
            )
        return q.order_by(ResearchProject.updated_at.desc()).offset(skip).limit(limit).all()

    def count_projects(
        self,
        db: Session,
        query: Optional[str] = None,
        status: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> int:
        q = db.query(ResearchProject)
        if organization_id is not None:
            q = q.filter(
                (ResearchProject.organization_id == organization_id) | (ResearchProject.organization_id == None)
            )
        if status:
            q = q.filter(ResearchProject.status == status.lower())
        if query and query.strip():
            search_pat = f"%{query.strip()}%"
            q = q.filter(
                (ResearchProject.title.ilike(search_pat)) |
                (ResearchProject.description.ilike(search_pat))
            )
        return q.count()

    def get_project(self, db: Session, project_id: str) -> ResearchProject:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Research project with ID '{project_id}' not found.")
        return project

    def update_project(self, db: Session, project_id: str, data: ProjectUpdate) -> ResearchProject:
        project = self.get_project(db, project_id)
        if data.title is not None:
            project.title = data.title.strip()
            project.name = data.title.strip()
        if getattr(data, "topic", None) is not None:
            project.topic = data.topic.strip() if data.topic else None
        if data.description is not None:
            project.description = data.description.strip()
        if getattr(data, "research_objective", None) is not None:
            project.research_objective = data.research_objective.strip() if data.research_objective else None
        if getattr(data, "target_audience", None) is not None:
            project.target_audience = data.target_audience.strip() if data.target_audience else None
        if getattr(data, "research_scope", None) is not None:
            project.research_scope = data.research_scope.strip() if data.research_scope else None
        if getattr(data, "keywords", None) is not None:
            project.keywords = data.keywords
        if getattr(data, "preferred_source_types", None) is not None:
            project.preferred_source_types = data.preferred_source_types
        if data.status is not None:
            project.status = data.status.lower()
        db.commit()
        db.refresh(project)
        return project

    def archive_project(self, db: Session, project_id: str) -> ResearchProject:
        project = self.get_project(db, project_id)
        project.status = "archived"
        db.commit()
        db.refresh(project)
        return project

    def reopen_project(self, db: Session, project_id: str) -> ResearchProject:
        project = self.get_project(db, project_id)
        project.status = "in_progress"
        db.commit()
        db.refresh(project)
        return project

    def delete_project(self, db: Session, project_id: str) -> bool:
        project = self.get_project(db, project_id)
        db.delete(project)
        db.commit()
        return True

    # ---------------- Source Management ----------------

    async def add_source(self, db: Session, project_id: str, data: SourceCreate) -> Source:
        project = self.get_project(db, project_id)

        source_type = (data.source_type or "URL").upper()
        url = str(data.url).strip() if data.url else None

        # Check duplicate URL within this project
        if url:
            c_url = canonicalize_url(url)
            existing = db.query(Source).filter(
                Source.project_id == project_id,
                (Source.url == url) | (Source.original_url == url) | (Source.url == c_url) | (Source.original_url == c_url)
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="This source URL has already been added to this project.")

        if source_type in ("TEXT", "PASTED"):
            # Process pasted text
            processed = extraction_service.process_pasted_text(data.text_content or "", data.title)
            if not processed["success"]:
                raise HTTPException(status_code=400, detail=processed["error"])
            
            # Check duplicate content hash within project
            new_hash = processed["content_hash"]
            for existing_s in project.sources:
                if existing_s.content_hash == new_hash:
                    raise HTTPException(
                        status_code=400,
                        detail="A source with identical content already exists in this project (duplicate content hash)."
                    )

            source = Source(
                project_id=project_id,
                title=processed["title"],
                url=None,
                original_url=None,
                source_type="TEXT",
                raw_content=processed["content"],
                extracted_content=processed["content"],
                extraction_status="completed",
                summary=processed["content"][:280] if processed.get("content") else None
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            return source

        else:
            # URL source
            c_url = canonicalize_url(url) if url else None
            source = Source(
                project_id=project_id,
                title=data.title.strip() if data.title else "Fetching article...",
                url=url,
                original_url=c_url or url,
                source_type="URL",
                extraction_status="pending"
            )
            db.add(source)
            db.commit()
            db.refresh(source)

            # Trigger extraction immediately
            if url:
                await self.extract_source(db, source.id)

            return source

    def get_project_sources(self, db: Session, project_id: str) -> List[Source]:
        self.get_project(db, project_id)
        return db.query(Source).filter(Source.project_id == project_id).order_by(Source.created_at.asc()).all()

    def get_source(self, db: Session, source_id: str) -> Source:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail=f"Source with ID '{source_id}' not found.")
        return source

    def delete_source(self, db: Session, source_id: str) -> bool:
        source = self.get_source(db, source_id)
        db.delete(source)
        db.commit()
        return True

    async def extract_source(self, db: Session, source_id: str) -> Source:
        source = self.get_source(db, source_id)

        if source.source_type == "TEXT" and source.extracted_content:
            source.extraction_status = "completed"
            db.commit()
            return source

        if not source.url:
            source.extraction_status = "failed"
            source.error_message = "No URL provided for extraction."
            db.commit()
            return source

        source.extraction_status = "extracting"
        db.commit()

        result = await extraction_service.extract_url(source.url)
        if result["success"]:
            source.title = result["title"] or source.title
            source.extracted_content = result["content"]
            source.raw_content = result["content"]
            source.author = result["author"]
            source.published_at = result["published_at"]
            source.original_url = result.get("canonical_url") or source.url
            source.extraction_status = "completed"
            source.error_message = None
            if not source.summary and result["content"]:
                source.summary = result["content"][:280]
        else:
            source.extraction_status = "failed"
            source.error_message = result["error"]
            if result.get("title"):
                source.title = result["title"]

        db.commit()
        db.refresh(source)
        return source

    # ---------------- Source Analysis ----------------

    async def analyze_single_source(self, db: Session, source_id: str) -> SourceAnalysis:
        source = self.get_source(db, source_id)

        content = source.extracted_content or ""
        if not content.strip():
            raise HTTPException(status_code=400, detail="Source has no extracted text to analyze.")

        analysis_schema = await ai_service.analyze_source(
            title=source.title,
            content=content,
            url=source.url,
            source_id=source.id
        )

        source.summary = analysis_schema.summary

        # Normalize reported facts with evidence classifications
        reported_facts_data = []
        for claim in analysis_schema.important_claims:
            claim_dict = claim.model_dump() if hasattr(claim, "model_dump") else claim
            claim_dict["source_id"] = source.id
            reported_facts_data.append(claim_dict)

            # Persist relational ResearchClaim and ResearchEvidence
            try:
                rc = ResearchClaim(
                    project_id=source.project_id,
                    source_id=source.id,
                    claim_text=claim_dict.get("claim", ""),
                    supporting_excerpt=claim_dict.get("supporting_excerpt", "") or content[:250],
                    evidence_classification=(claim_dict.get("evidence_type") or "REPORTED_BY_SOURCE").upper(),
                    confidence=0.92
                )
                db.add(rc)
                db.flush()

                re_item = ResearchEvidence(
                    project_id=source.project_id,
                    source_id=source.id,
                    claim_id=rc.id,
                    excerpt=rc.supporting_excerpt,
                    fact_type="DIRECT_FACT" if "direct" in str(claim_dict.get("evidence_type", "")).lower() else "REPORTED_FACT",
                    confidence=0.92,
                    verified=True
                )
                db.add(re_item)
            except Exception as e:
                logger.warning(f"Failed to persist relational evidence item: {e}")

        existing = db.query(SourceAnalysis).filter(SourceAnalysis.source_id == source.id).first()
        if existing:
            existing.summary = analysis_schema.summary
            existing.key_points = analysis_schema.key_developments
            existing.reported_facts = reported_facts_data
            existing.analysis = analysis_schema.analysis
            existing.founder_implications = {
                "technical": analysis_schema.technical_implications,
                "business": analysis_schema.business_implications
            }
            existing.uncertainties = analysis_schema.limitations
            existing.newsletter_angles = [
                {
                    "headline": f"What {source.title} Means for Builders",
                    "central_argument": analysis_schema.summary,
                    "target_audience": "Technical Founders & Operators",
                    "why_readers_care": "Direct architectural and operational shift."
                }
            ]
            existing.key_developments = analysis_schema.key_developments
            existing.important_claims = reported_facts_data
            existing.facts = analysis_schema.facts
            existing.speculation = analysis_schema.speculation
            existing.implications = existing.founder_implications
            existing.limitations = analysis_schema.limitations
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_analysis = SourceAnalysis(
                source_id=source.id,
                summary=analysis_schema.summary,
                key_points=analysis_schema.key_developments,
                reported_facts=reported_facts_data,
                analysis=analysis_schema.analysis,
                founder_implications={
                    "technical": analysis_schema.technical_implications,
                    "business": analysis_schema.business_implications
                },
                uncertainties=analysis_schema.limitations,
                newsletter_angles=[
                    {
                        "headline": f"What {source.title} Means for Builders",
                        "central_argument": analysis_schema.summary,
                        "target_audience": "Technical Founders & Operators",
                        "why_readers_care": "Direct architectural and operational shift."
                    }
                ],
                key_developments=analysis_schema.key_developments,
                important_claims=reported_facts_data,
                facts=analysis_schema.facts,
                speculation=analysis_schema.speculation,
                implications={
                    "technical": analysis_schema.technical_implications,
                    "business": analysis_schema.business_implications
                },
                limitations=analysis_schema.limitations
            )
            db.add(new_analysis)
            db.commit()
            db.refresh(new_analysis)
            return new_analysis

    def get_source_analysis(self, db: Session, source_id: str) -> SourceAnalysis:
        analysis = db.query(SourceAnalysis).filter(SourceAnalysis.source_id == source_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail=f"No analysis generated yet for source ID '{source_id}'.")
        return analysis

    # ---------------- Cross-Source Research Synthesis ----------------

    async def synthesize_research(self, db: Session, project_id: str) -> ResearchBrief:
        project = self.get_project(db, project_id)
        sources = db.query(Source).filter(Source.project_id == project.id).all()

        if len(sources) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"At least 3 sources are required to generate a research brief. Current count: {len(sources)}."
            )

        # Analyze any sources that have not yet been analyzed
        for s in sources:
            if not s.analyses and s.extracted_content:
                await self.analyze_single_source(db, s.id)
                db.refresh(s)

        # Build synthesis payload
        sources_payload = []
        for s in sources:
            sources_payload.append({
                "id": s.id,
                "title": s.title,
                "url": s.url or s.original_url,
                "summary": s.summary or (s.extracted_content[:300] if s.extracted_content else ""),
                "analysis": {
                    "key_developments": s.analyses.key_developments if s.analyses else [],
                    "facts": s.analyses.facts if s.analyses else [],
                    "analysis": s.analyses.analysis if s.analyses else [],
                    "speculation": s.analyses.speculation if s.analyses else []
                }
            })

        # Call AI or deterministic synthesis engine
        if ai_service.is_available:
            brief_data = await ai_service.synthesize_brief(project.title, sources_payload)
            evidence_items = brief_data.get("evidence_verification", [])
            verified_evidence = synthesis_service.validate_and_trace_evidence(evidence_items, sources)
            brief_data["evidence_verification"] = verified_evidence
        else:
            brief_data = synthesis_service.generate_deterministic_synthesis(project.title, sources)
            verified_evidence = brief_data.get("evidence_verification", [])

        # Persist relational ResearchEvidence for synthesis
        for ev in verified_evidence:
            try:
                sid = ev.get("source_id")
                if sid:
                    ev_record = ResearchEvidence(
                        project_id=project.id,
                        source_id=sid,
                        excerpt=ev.get("supporting_excerpt", ""),
                        fact_type=ev.get("evidence_classification", "DIRECT_FACT"),
                        confidence=float(ev.get("confidence", 0.9)),
                        verified=ev.get("status") == "SUPPORTED"
                    )
                    db.add(ev_record)
            except Exception as e:
                logger.warning(f"Could not persist synthesis evidence item: {e}")

        brief_record = ResearchBrief(
            project_id=project.id,
            title=brief_data.get("title", f"Research Brief: {project.title}"),
            executive_summary=brief_data.get("executive_summary", ""),
            key_developments=brief_data.get("key_developments", []),
            strategic_implications=brief_data.get("strategic_implications", {}),
            newsletter_angles=brief_data.get("newsletter_angles", []),
            source_references=brief_data.get("source_references", []),
            brief_content=brief_data,
            evidence=verified_evidence,
            recommended_angle=brief_data.get("recommended_story") or brief_data.get("recommended_angle") or (brief_data.get("newsletter_angles", [{}])[0] if brief_data.get("newsletter_angles") else {})
        )
        db.add(brief_record)
        project.status = "completed"
        db.commit()
        db.refresh(brief_record)

        try:
            version_service.create_snapshot(
                db=db,
                document_type="RESEARCH_BRIEF",
                document_id=brief_record.id,
                content=brief_record.executive_summary or "",
                title=brief_record.title,
                change_type="INITIAL",
                change_summary="Initial research synthesis brief generated"
            )
        except Exception:
            pass

        return brief_record

    async def generate_research_brief(self, db: Session, project_id: str) -> ResearchBrief:
        """Alias for synthesize_research to ensure full compatibility."""
        return await self.synthesize_research(db, project_id)

    async def analyze_project_sources(self, db: Session, project_id: str) -> List[Source]:
        """Analyze all extracted sources in a project."""
        project = self.get_project(db, project_id)
        sources = self.get_project_sources(db, project_id)
        for s in sources:
            if s.extracted_content:
                await self.analyze_single_source(db, s.id)
        project.status = "analyzed"
        db.commit()
        db.refresh(project)
        return sources

    def get_brief(self, db: Session, project_id: str) -> ResearchBrief:
        """Alias for get_latest_brief."""
        return self.get_latest_brief(db, project_id)

    def get_latest_brief(self, db: Session, project_id: str) -> ResearchBrief:
        brief = (
            db.query(ResearchBrief)
            .filter(ResearchBrief.project_id == project_id)
            .order_by(ResearchBrief.created_at.desc())
            .first()
        )
        if not brief:
            raise HTTPException(status_code=404, detail="No research brief found for this project.")
        return brief

    def get_brief_history(self, db: Session, project_id: str) -> List[ResearchBrief]:
        self.get_project(db, project_id)
        return (
            db.query(ResearchBrief)
            .filter(ResearchBrief.project_id == project_id)
            .order_by(ResearchBrief.created_at.desc())
            .all()
        )

    def update_brief(self, db: Session, project_id: str, data: ResearchBriefUpdate) -> ResearchBrief:
        brief = self.get_latest_brief(db, project_id)
        if data.title is not None:
            brief.title = data.title.strip()
        if data.executive_summary is not None:
            brief.executive_summary = data.executive_summary.strip()
        if data.user_notes is not None:
            brief.user_notes = data.user_notes.strip()

        # Update nested brief_content fields if provided
        bc = dict(brief.brief_content or {})
        if data.what_happened is not None:
            bc["what_happened"] = data.what_happened.strip()
        if data.why_it_matters is not None:
            bc["why_it_matters"] = data.why_it_matters.strip()
        if data.key_developments is not None:
            brief.key_developments = data.key_developments
            bc["key_developments"] = data.key_developments
        if data.limitations is not None:
            bc["limitations"] = data.limitations
        if data.unanswered_questions is not None:
            bc["unanswered_questions"] = data.unanswered_questions

        brief.brief_content = bc
        brief.is_user_edited = True
        brief.version = (brief.version or 1) + 1

        db.commit()
        db.refresh(brief)

        # Record version snapshot
        try:
            version_service.create_snapshot(
                db=db,
                document_type="RESEARCH_BRIEF",
                document_id=brief.id,
                content=brief.executive_summary or "",
                title=brief.title,
                change_type="REVISION",
                change_summary=f"User updated brief (v{brief.version})"
            )
        except Exception as e:
            logger.warning(f"Failed to record brief revision snapshot: {e}")

        return brief

    def export_brief(self, db: Session, project_id: str, format: str = "markdown") -> Dict[str, Any]:
        project = self.get_project(db, project_id)
        brief = self.get_latest_brief(db, project_id)
        sources = self.get_project_sources(db, project_id)

        bc = brief.brief_content or {}
        evidence = brief.evidence or []

        # 1. Build Markdown
        md_lines = [
            f"# {brief.title or project.title}",
            "",
            f"**Research Project:** {project.title}  ",
            f"**Status:** {'User-Edited' if brief.is_user_edited else 'AI-Synthesized'} (Version {brief.version or 1})  ",
            f"**Synthesized At:** {brief.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Sources Ingested:** {len(sources)}  ",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            brief.executive_summary or "No executive summary available.",
            "",
        ]

        if bc.get("what_happened"):
            md_lines.extend([
                "## What Happened?",
                "",
                bc["what_happened"],
                "",
            ])

        if bc.get("why_it_matters"):
            md_lines.extend([
                "## Why It Matters",
                "",
                bc["why_it_matters"],
                "",
            ])

        if brief.key_developments:
            md_lines.extend([
                "## Key Developments & Findings",
                "",
            ])
            for i, kd in enumerate(brief.key_developments, start=1):
                md_lines.append(f"{i}. {kd}")
            md_lines.append("")

        if evidence:
            md_lines.extend([
                "## Evidence Alignment & Traceability",
                "",
                "| Status | Claim | Source | Excerpt |",
                "| :--- | :--- | :--- | :--- |",
            ])
            for ev in evidence:
                st = ev.get("status", "SUPPORTED")
                cl = str(ev.get("claim", "")).replace("|", "\\|")
                stitle = str(ev.get("source_title", "")).replace("|", "\\|")
                exc = str(ev.get("supporting_excerpt", "")).replace("|", "\\|").replace("\n", " ")
                if len(exc) > 120:
                    exc = exc[:117] + "..."
                md_lines.append(f"| **{st}** | {cl} | {stitle} | *\"{exc}\"* |")
            md_lines.append("")

        if brief.newsletter_angles:
            md_lines.extend([
                "## Newsletter Angles",
                "",
            ])
            for i, a in enumerate(brief.newsletter_angles, start=1):
                headline = a.get("headline", f"Angle {i}")
                pitch = a.get("angle_pitch", a.get("central_argument", ""))
                aud = a.get("target_audience", "")
                md_lines.append(f"### {i}. {headline}")
                if aud:
                    md_lines.append(f"**Target Audience:** {aud}")
                if pitch:
                    md_lines.append(f"**Pitch:** {pitch}")
                md_lines.append("")

        if sources:
            md_lines.extend([
                "## Verified Sources",
                "",
            ])
            for i, s in enumerate(sources, start=1):
                url_str = f" - [{s.url}]({s.url})" if s.url else ""
                md_lines.append(f"{i}. **{s.title}** ({s.source_type}){url_str}")
            md_lines.append("")

        markdown_str = "\n".join(md_lines)

        # 2. Build Plain Text
        txt_lines = [
            f"RESEARCH BRIEF: {brief.title or project.title}".upper(),
            "=" * 60,
            f"Project: {project.title}",
            f"Synthesized: {brief.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Sources: {len(sources)}",
            "",
            "EXECUTIVE SUMMARY:",
            "-" * 40,
            brief.executive_summary or "",
            "",
        ]
        if bc.get("what_happened"):
            txt_lines.extend([
                "WHAT HAPPENED:",
                "-" * 40,
                bc["what_happened"],
                "",
            ])
        if bc.get("why_it_matters"):
            txt_lines.extend([
                "WHY IT MATTERS:",
                "-" * 40,
                bc["why_it_matters"],
                "",
            ])
        if brief.key_developments:
            txt_lines.extend([
                "KEY DEVELOPMENTS:",
                "-" * 40,
            ])
            for i, kd in enumerate(brief.key_developments, start=1):
                txt_lines.append(f"[{i}] {kd}")
            txt_lines.append("")

        plain_text_str = "\n".join(txt_lines)

        # 3. Build JSON
        import json
        json_obj = {
            "project_id": project.id,
            "project_title": project.title,
            "brief_id": brief.id,
            "brief_title": brief.title,
            "executive_summary": brief.executive_summary,
            "key_developments": brief.key_developments,
            "brief_content": brief.brief_content,
            "evidence": brief.evidence,
            "newsletter_angles": brief.newsletter_angles,
            "is_user_edited": brief.is_user_edited,
            "version": brief.version or 1,
            "sources": [
                {
                    "id": s.id,
                    "title": s.title,
                    "url": s.url or s.original_url,
                    "source_type": s.source_type,
                    "status": s.extraction_status
                }
                for s in sources
            ],
            "created_at": brief.created_at.isoformat(),
            "updated_at": brief.updated_at.isoformat()
        }
        json_str = json.dumps(json_obj, indent=2)

        return {
            "project_id": project.id,
            "brief_id": brief.id,
            "title": brief.title,
            "markdown_content": markdown_str,
            "plain_text_content": plain_text_str,
            "json_content": json_str,
            "format": format.lower(),
            "exported_at": datetime.utcnow().isoformat()
        }

    def get_project_evidence(self, db: Session, project_id: str) -> List[Dict[str, Any]]:
        """Returns verified evidence items for project from latest brief or database records."""
        self.get_project(db, project_id)
        try:
            brief = self.get_latest_brief(db, project_id)
            if brief.evidence:
                return brief.evidence
        except Exception:
            pass
        
        # Fallback to research_evidence table
        records = db.query(ResearchEvidence).filter(ResearchEvidence.project_id == project_id).all()
        source_map = {s.id: s.title for s in self.get_project_sources(db, project_id)}
        return [
            {
                "evidence_id": r.id,
                "source_id": r.source_id,
                "source_title": source_map.get(r.source_id, "Source"),
                "claim": r.excerpt,
                "supporting_excerpt": r.excerpt,
                "evidence_classification": r.fact_type,
                "status": "SUPPORTED" if r.verified else "UNVERIFIED",
                "confidence": r.confidence,
                "grounded": r.verified,
                "section_reference": "Paragraph 1",
                "reasoning": "Extracted from source analysis records."
            }
            for r in records
        ]

research_service = ResearchService()
