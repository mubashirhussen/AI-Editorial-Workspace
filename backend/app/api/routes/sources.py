from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.base import Source, User, ResearchProject
from backend.app.schemas.source import SourceCreate, SourceUpdate, SourceResponse, SourceListResponse, SourceAnalysisSchema
from backend.app.schemas.auth import OrgPermission
from backend.app.services.research_service import research_service
from backend.app.api.deps import get_current_user
from backend.app.api.v1.endpoints.projects import check_project_tenant_access
from backend.app.services.research.document_extractor import extract_from_bytes
from backend.app.services.analytics_service import analytics_service

router = APIRouter(tags=['Sources'])

@router.post("/research/projects/{project_id}/sources/upload", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Upload source document to research project")
@router.post("/projects/{project_id}/sources/upload", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Upload source document alias")
async def upload_project_source_file(
    project_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Multi-modal document and image ingestion (PDF, Word docx, Text, Markdown, Image OCR)."""
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.ADD_SOURCES)

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    extracted = extract_from_bytes(content_bytes, file.filename or "uploaded_document", file.content_type)
    if not extracted.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=extracted.get("error", "Failed to extract content from file."))

    source_title = title.strip() if title and title.strip() else extracted["title"]
    source = Source(
        project_id=project_id,
        title=source_title,
        url=None,
        original_url=None,
        source_type=extracted.get("source_type", "TEXT"),
        raw_content=extracted["content"],
        extracted_content=extracted["content"],
        extraction_status="completed",
        summary=extracted["content"][:280] if extracted.get("content") else None
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.post("/sources/{source_id}/upload", response_model=SourceResponse, summary="Reupload file to source")
async def reupload_source_file(
    source_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Re-verifies an existing source by uploading a document or image file."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    extracted = extract_from_bytes(content_bytes, file.filename or "uploaded_document", file.content_type)
    if not extracted.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=extracted.get("error", "Failed to extract content."))

    source.source_type = extracted.get("source_type", "TEXT")
    source.raw_content = extracted["content"]
    source.extracted_content = extracted["content"]
    source.extraction_status = "completed"
    source.error_message = None
    source.summary = extracted["content"][:280] if extracted.get("content") else None

    db.commit()
    db.refresh(source)
    return source

@router.post("/research/projects/{project_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Add URL or text source to project")
@router.post("/projects/{project_id}/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED, summary="Add source to project alias")
async def add_source(
    project_id: str,
    data: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Adds a web URL or pasted text source to an active investigation project."""
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.ADD_SOURCES)
    source = await research_service.add_source(db, project_id, data)
    status_label = "success" if getattr(source, "extraction_status", "") != "failed" else "failed"
    org_id = getattr(project, "organization_id", None)
    if status_label == "success":
        analytics_service.track_event(db, org_id, "source_processed", metadata={"status": "success"})
    else:
        analytics_service.track_event(db, org_id, "workflow_failed", metadata={"category": "source_extraction"})
    return source

@router.get("/research/projects/{project_id}/sources", response_model=List[SourceResponse], summary="List sources for project")
@router.get("/projects/{project_id}/sources", response_model=List[SourceResponse], summary="List sources for project alias")
def list_project_sources(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all ingested sources and extraction status for a project."""
    project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.VIEW_CONTENT)
    sources = db.query(Source).filter(Source.project_id == project_id).order_by(Source.created_at.asc()).offset(skip).limit(limit).all()
    return sources

@router.get("/sources/{source_id}", response_model=SourceResponse, summary="Get source by ID")
def get_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves source metadata and extracted body content."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.VIEW_CONTENT)
    return source

@router.put("/sources/{source_id}", response_model=SourceResponse, summary="Update source content")
def update_source(
    source_id: str,
    data: SourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates source title or manually corrects extracted text content."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)

    if data.title and data.title.strip():
        source.title = data.title.strip()

    content = data.text_content or data.raw_content
    if content and content.strip():
        cleaned = content.strip()
        source.raw_content = cleaned
        source.extracted_content = cleaned
        source.extraction_status = "completed"
        source.error_message = None
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            source.summary = lines[0][:280]

    db.commit()
    db.refresh(source)
    return source

@router.delete("/sources/{source_id}", summary="Delete source")
def delete_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a source and cascades to its extracted claims and evidence."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if source.project:
        check_project_tenant_access(db, source.project, current_user, OrgPermission.ADD_SOURCES)
    db.delete(source)
    db.commit()
    return {"success": True, "message": "Source removed successfully."}

@router.post("/sources/{source_id}/extract", response_model=SourceResponse, summary="Trigger source extraction")
async def extract_source_content(source_id: str, db: Session = Depends(get_db)):
    """Triggers automated extraction and metadata parsing for a URL source."""
    source = await research_service.extract_source(db, source_id)
    return source

@router.post("/sources/{source_id}/analyze", summary="Trigger source analysis")
async def analyze_source(source_id: str, db: Session = Depends(get_db)):
    """Executes single-source claim and evidence extraction."""
    analysis = await research_service.analyze_single_source(db, source_id)
    return {"success": True, "analysis_id": analysis.id}

@router.get("/sources/{source_id}/analysis", summary="Get source analysis")
def get_source_analysis(source_id: str, db: Session = Depends(get_db)):
    """Retrieves verified claims and analysis breakdown for a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source with ID '{source_id}' not found.")
    if not source.analyses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source analysis not found.")
    return source.analyses
