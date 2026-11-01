from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import Source, ResearchProject
from backend.app.schemas.source import SourceCreate
from backend.app.services.extraction_service import extraction_service

class SourceService:
    @staticmethod
    async def add_source(db: Session, project_id: str, data: SourceCreate) -> Source:
        # Verify project exists
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Research project not found")

        # Duplicate URL check
        if data.url:
            existing = db.query(Source).filter(
                Source.project_id == project_id,
                Source.url == data.url.strip()
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="This source URL has already been added to this project.")

        source = Source(
            project_id=project_id,
            title=data.title.strip() if data.title else ("Pasted Source" if data.source_type == "text" else "Processing URL..."),
            url=data.url.strip() if data.url else None,
            source_type=data.source_type,
            extracted_content=data.text_content.strip() if data.text_content else None,
            extraction_status="completed" if data.source_type == "text" and data.text_content else "pending"
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        if source.source_type == "url" and source.url:
            await SourceService.extract_source(db, source.id)

        return source

    @staticmethod
    def get_sources_by_project(db: Session, project_id: str) -> List[Source]:
        return db.query(Source).filter(Source.project_id == project_id).order_by(Source.created_at.asc()).all()

    @staticmethod
    def get_source(db: Session, source_id: str) -> Source:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source

    @staticmethod
    def delete_source(db: Session, source_id: str) -> bool:
        source = SourceService.get_source(db, source_id)
        db.delete(source)
        db.commit()
        return True

    @staticmethod
    async def extract_source(db: Session, source_id: str) -> Source:
        source = SourceService.get_source(db, source_id)

        if source.source_type != "url" or not source.url:
            source.extraction_status = "completed"
            db.commit()
            return source

        source.extraction_status = "extracting"
        db.commit()

        result = await extraction_service.extract_url(source.url)
        if result["success"]:
            source.title = result["title"] or source.title
            source.extracted_content = result["content"]
            source.author = result["author"]
            source.published_at = result["published_at"]
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

source_service = SourceService()

