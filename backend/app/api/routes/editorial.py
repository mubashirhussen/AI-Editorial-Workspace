from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException, Response
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.editorial import (
    EditorialGenerateRequest,
    EditorialUpdateRequest,
    EditorialCreateRequest,
    EditorialResponse,
    EditorialExportResponse,
    HeadlineGenerateRequest,
    HeadlineGenerateResponse
)
from backend.app.services.editorial.editorial_service import editorial_service
from backend.app.services.editorial.headline_service import headline_service

router = APIRouter(prefix="/editorial", tags=["Editorial Studio"])

@router.post("/headlines", response_model=HeadlineGenerateResponse, status_code=status.HTTP_200_OK)
async def generate_headlines(req: HeadlineGenerateRequest, db: Session = Depends(get_db)):
    """Generate at least five non-clickbait editorial headline options with audience rationale."""
    return await headline_service.generate_headlines(db, req)

@router.post("/generate", response_model=EditorialResponse, status_code=status.HTTP_201_CREATED)
async def generate_editorial(req: EditorialGenerateRequest, db: Session = Depends(get_db)):
    """Generate a 300-500 word publication-ready newsletter draft from research brief and sources."""
    return await editorial_service.generate_editorial(db, req)

@router.post("", response_model=EditorialResponse, status_code=status.HTTP_201_CREATED)
def create_editorial(req: EditorialCreateRequest, db: Session = Depends(get_db)):
    """Directly persist an editorial output."""
    return editorial_service.create_editorial(db, req)

@router.get("", response_model=List[EditorialResponse])
def list_editorials(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db)
):
    """List all saved editorial outputs."""
    return editorial_service.list_editorials(db, project_id=project_id)

@router.get("/{editorial_id}", response_model=EditorialResponse)
def get_editorial(editorial_id: str, db: Session = Depends(get_db)):
    """Retrieve saved editorial output by ID."""
    return editorial_service.get_editorial(db, editorial_id)

@router.put("/{editorial_id}", response_model=EditorialResponse)
def update_editorial(editorial_id: str, data: EditorialUpdateRequest, db: Session = Depends(get_db)):
    """Update editorial headline, content, or publication status."""
    return editorial_service.update_editorial(db, editorial_id, data)

@router.delete("/{editorial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_editorial(editorial_id: str, db: Session = Depends(get_db)):
    """Delete an editorial output."""
    editorial_service.delete_editorial(db, editorial_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{editorial_id}/export", response_model=EditorialExportResponse)
def export_editorial(
    editorial_id: str, 
    format: str = Query("markdown", pattern="^(markdown|txt|html)$"),
    db: Session = Depends(get_db)
):
    """Export editorial into Markdown, TXT, or semantic HTML5."""
    return editorial_service.export_editorial(db, editorial_id, format_type=format)
