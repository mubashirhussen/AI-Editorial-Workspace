from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException, Response
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.base import User, ResearchProject, EditorialOutput, OrganizationMembership
from backend.app.schemas.auth import OrgPermission
from backend.app.api.deps import get_current_user
from backend.app.api.v1.endpoints.projects import check_project_tenant_access
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
async def generate_headlines(
    req: HeadlineGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate at least five non-clickbait editorial headline options with audience rationale."""
    project = db.query(ResearchProject).filter(ResearchProject.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{req.project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.VIEW_CONTENT)
    return await headline_service.generate_headlines(db, req)

@router.post("/generate", response_model=EditorialResponse, status_code=status.HTTP_201_CREATED)
async def generate_editorial(
    req: EditorialGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a 300-500 word publication-ready newsletter draft from research brief and sources."""
    project = db.query(ResearchProject).filter(ResearchProject.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{req.project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.CREATE_PROJECTS)
    return await editorial_service.generate_editorial(db, req)

@router.post("", response_model=EditorialResponse, status_code=status.HTTP_201_CREATED)
def create_editorial(
    req: EditorialCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Directly persist an editorial output."""
    project = db.query(ResearchProject).filter(ResearchProject.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{req.project_id}' not found.")
    check_project_tenant_access(db, project, current_user, OrgPermission.EDIT_DRAFTS)
    return editorial_service.create_editorial(db, req)

@router.get("", response_model=List[EditorialResponse])
def list_editorials(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List saved editorial outputs with tenant isolation."""
    if project_id:
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            return []
        check_project_tenant_access(db, project, current_user, OrgPermission.VIEW_CONTENT)
        return editorial_service.list_editorials(db, project_id=project_id)

    # Multi-tenant scoping when no specific project_id requested
    user_memberships = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == current_user.id
    ).all()
    user_org_ids = [m.organization_id for m in user_memberships]

    if user_org_ids:
        return (
            db.query(EditorialOutput)
            .join(ResearchProject, EditorialOutput.project_id == ResearchProject.id)
            .filter(ResearchProject.organization_id.in_(user_org_ids))
            .order_by(EditorialOutput.created_at.desc())
            .all()
        )

    return editorial_service.list_editorials(db, project_id=None)

@router.get("/{editorial_id}", response_model=EditorialResponse)
def get_editorial(
    editorial_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve saved editorial output by ID with tenant verification."""
    editorial = editorial_service.get_editorial(db, editorial_id)
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.VIEW_CONTENT)
    return editorial

@router.put("/{editorial_id}", response_model=EditorialResponse)
def update_editorial(
    editorial_id: str,
    data: EditorialUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update editorial headline, content, or publication status."""
    editorial = editorial_service.get_editorial(db, editorial_id)
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.EDIT_DRAFTS)
    return editorial_service.update_editorial(db, editorial_id, data)

@router.delete("/{editorial_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_editorial(
    editorial_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an editorial output."""
    editorial = editorial_service.get_editorial(db, editorial_id)
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.EDIT_DRAFTS)
    editorial_service.delete_editorial(db, editorial_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{editorial_id}/export", response_model=EditorialExportResponse)
def export_editorial(
    editorial_id: str,
    format: str = Query("markdown", pattern="^(markdown|txt|html|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export editorial into Markdown, TXT, semantic HTML5, or structured JSON."""
    editorial = editorial_service.get_editorial(db, editorial_id)
    if editorial.project:
        check_project_tenant_access(db, editorial.project, current_user, OrgPermission.VIEW_CONTENT)
    return editorial_service.export_editorial(db, editorial_id, format_type=format)
