import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import ResearchProject, Source, SourceAnalysis, ResearchBrief
from backend.app.schemas.research import ProjectCreate, ProjectUpdate
from backend.app.schemas.source import SourceCreate
from backend.app.services.research.extraction_service import extraction_service
from backend.app.services.research.synthesis_service import synthesis_service
from backend.app.services.version_control.version_service import version_service
from backend.app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

class ResearchService:
    """
    Core Research Assistant orchestrator.
    Manages projects, source extraction, single-source claim analysis,
    and cross-source evidence synthesis.
    """

    def create_project(self, db: Session, data: ProjectCreate) -> ResearchProject:
        title = data.title or getattr(data, "name", None) or "Untitled Investigation"
        project = ResearchProject(
            title=title.strip(),
            name=title.strip(),
            description=data.description.strip() if data.description else None,
            status="draft"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def get_projects(self, db: Session, skip: int = 0, limit: int = 50) -> List[ResearchProject]:
        return db.query(ResearchProject).order_by(ResearchProject.created_at.desc()).offset(skip).limit(limit).all()

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
        if data.description is not None:
            project.description = data.description.strip()
        if data.status is not None:
            project.status = data.status
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
            existing = db.query(Source).filter(
                Source.project_id == project_id,
                Source.url == url
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="This source URL has already been added to this project.")

        if source_type in ("TEXT", "PASTED"):
            # Process pasted text
            processed = extraction_service.process_pasted_text(data.text_content or "", data.title)
            if not processed["success"]:
                raise HTTPException(status_code=400, detail=processed["error"])
            
            source = Source(
                project_id=project_id,
                title=processed["title"],
                url=None,
                original_url=None,
                source_type="TEXT",
                raw_content=processed["content"],
                extracted_content=processed["content"],
                extraction_status="completed"
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            return source

        else:
            # URL source
            source = Source(
                project_id=project_id,
                title=data.title.strip() if data.title else "Fetching article...",
                url=url,
                original_url=url,
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
            source.original_url = result["canonical_url"]
            source.extraction_status = "completed"
            source.error_message = None
        else:
            source.extraction_status = "failed"
            source.error_message = result["error"]
            if result["title"]:
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
            # Retain legacy fields
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
            # Enforce evidence traceability
            evidence_items = brief_data.get("evidence_verification", [])
            verified_evidence = synthesis_service.validate_and_trace_evidence(evidence_items, sources)
            brief_data["evidence_verification"] = verified_evidence
        else:
            brief_data = synthesis_service.generate_deterministic_synthesis(project.title, sources)

        brief_record = ResearchBrief(
            project_id=project.id,
            title=brief_data.get("title", f"Research Brief: {project.title}"),
            executive_summary=brief_data.get("executive_summary", ""),
            key_developments=brief_data.get("key_developments", []),
            strategic_implications=brief_data.get("strategic_implications", {}),
            newsletter_angles=brief_data.get("newsletter_angles", []),
            source_references=brief_data.get("source_references", []),
            brief_content=brief_data,
            evidence=brief_data.get("evidence_verification", []),
            recommended_angle=brief_data.get("recommended_story") or brief_data.get("recommended_angle") or (brief_data.get("newsletter_angles", [{}])[0] if brief_data.get("newsletter_angles") else {})
        )
        db.add(brief_record)
        project.status = "COMPLETED"
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

research_service = ResearchService()
