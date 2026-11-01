from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.crud import project as crud_project
from backend.app.models.base import ResearchProject, User, Organization, OrganizationMembership
from backend.app.schemas.research import ProjectCreate, ProjectUpdate, ProjectResponse
from backend.app.schemas.auth import OrgPermission, has_permission
from backend.app.api.deps import get_current_user, get_active_organization, require_permission

router = APIRouter(tags=["Projects"])

def check_project_tenant_access(
    db: Session,
    project: ResearchProject,
    user: User,
    required_permission: Optional[OrgPermission] = None
) -> Optional[OrganizationMembership]:
    """Ensures the user belongs to the project's organization and holds the required permission."""
    if not project.organization_id:
        return None  # Unassigned legacy project

    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == project.organization_id,
        OrganizationMembership.user_id == user.id
    ).first()

    if not membership:
        # Return 404 to prevent cross-tenant project existence disclosure
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project.id}' not found."
        )

    if required_permission and not has_permission(membership.role, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{membership.role}' lacks permission '{required_permission.value}' for this project's workspace."
        )

    return membership


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    org: Organization = Depends(require_permission(OrgPermission.CREATE_PROJECTS)),
    db: Session = Depends(get_db)
):
    """Create a new research project strictly bound to the active organization."""
    return crud_project.create_project(db, payload, organization_id=org.id)


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    org: Organization = Depends(require_permission(OrgPermission.VIEW_CONTENT)),
    db: Session = Depends(get_db)
):
    """List all projects isolated to the active organization."""
    return crud_project.get_projects(db, skip=skip, limit=limit, organization_id=org.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project by ID, verifying tenant membership."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.VIEW_CONTENT)
    return proj


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project metadata or status (enforcing tenant authorization)."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.EDIT_DRAFTS)
    return crud_project.update_project(db, proj, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a research project and associated resources (requires Admin or Owner)."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")

    check_project_tenant_access(db, proj, current_user, OrgPermission.MANAGE_ORG_LIMITED)
    crud_project.delete_project(db, project_id)
    return None


# Research Synthesis & Briefs
@router.post("/{project_id}/research/synthesize")
async def synthesize_project_research(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synthesize cross-source research brief from at least 3 analyzed sources."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.CREATE_PROJECTS)

    from backend.app.services.research import research_service
    brief = await research_service.synthesize_research(db, project_id)
    return {
        "id": brief.id,
        "project_id": brief.project_id,
        "title": brief.title,
        "executive_summary": brief.executive_summary,
        "key_developments": brief.key_developments,
        "strategic_implications": brief.strategic_implications,
        "evidence": brief.evidence,
        "newsletter_angles": brief.newsletter_angles,
        "source_references": brief.source_references,
        "brief_content": brief.brief_content,
        "created_at": brief.created_at
    }


@router.get("/{project_id}/research/brief")
def get_project_brief(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve the latest synthesized research brief for a project."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.VIEW_CONTENT)
    
    from backend.app.services.research import research_service
    return research_service.get_latest_brief(db, project_id)


@router.get("/{project_id}/research/history")
def get_project_brief_history(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve history of all synthesized research briefs for a project."""
    proj = crud_project.get_project_by_id(db, project_id)
    if not proj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project with ID '{project_id}' not found.")
    
    check_project_tenant_access(db, proj, current_user, OrgPermission.VIEW_CONTENT)
    
    from backend.app.services.research import research_service
    return research_service.get_brief_history(db, project_id)
