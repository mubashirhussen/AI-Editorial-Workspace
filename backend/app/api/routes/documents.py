from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_active_organization
from backend.app.models.base import User, Organization, ResearchProject, EditorialVersion
from backend.app.schemas.version import (
    EditorialVersionResponse,
    VersionComparisonResponse,
    RestoreVersionRequest,
    RestoreVersionResponse
)
from backend.app.services.version_control.version_service import version_service

router = APIRouter(prefix="/documents", tags=["Version Control"])

def _verify_tenant_access(
    db: Session,
    document_type: str,
    document_id: str,
    active_org: Organization
) -> None:
    doc, org_id, _, _ = version_service.resolve_document(db, document_type, document_id)
    if org_id and active_org and org_id != active_org.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{document_type} '{document_id}' not found in active workspace."
        )

@router.get(
    "/{document_type}/{document_id}/versions",
    response_model=List[EditorialVersionResponse],
    summary="List all version snapshots for a document"
)
def list_document_versions(
    document_type: str,
    document_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    _verify_tenant_access(db, document_type, document_id, active_org)
    return version_service.list_versions(db, document_type, document_id, limit=limit)

@router.get(
    "/{document_type}/{document_id}/versions/{version_id}",
    response_model=EditorialVersionResponse,
    summary="Get a specific document version snapshot"
)
def get_document_version(
    document_type: str,
    document_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    _verify_tenant_access(db, document_type, document_id, active_org)
    return version_service.get_version(db, document_type, document_id, version_id)

@router.get(
    "/{document_type}/{document_id}/compare",
    response_model=VersionComparisonResponse,
    summary="Compare any two versions of a document"
)
def compare_document_versions(
    document_type: str,
    document_id: str,
    from_version: Optional[str] = Query(None, description="Starting version ID or version number"),
    to_version: Optional[str] = Query(None, description="Target version ID or version number"),
    from_: Optional[str] = Query(None, alias="from", description="Alias for from_version"),
    to: Optional[str] = Query(None, alias="to", description="Alias for to_version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    _verify_tenant_access(db, document_type, document_id, active_org)
    
    start_ref = from_version or from_
    end_ref = to_version or to
    if not start_ref or not end_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'from_version' (or 'from') and 'to_version' (or 'to') query parameters are required."
        )

    return version_service.compare_versions(db, document_type, document_id, start_ref, end_ref)

@router.post(
    "/{document_type}/{document_id}/restore/{version_id}",
    response_model=RestoreVersionResponse,
    summary="Restore a previous document version without losing history"
)
def restore_document_version(
    document_type: str,
    document_id: str,
    version_id: str,
    payload: Optional[RestoreVersionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_org: Organization = Depends(get_active_organization)
):
    _verify_tenant_access(db, document_type, document_id, active_org)

    target_ver = version_service.get_version(db, document_type, document_id, version_id)
    note = payload.note if payload else None

    new_version, new_content = version_service.restore_version(
        db=db,
        document_type=document_type,
        document_id=document_id,
        version_ref=version_id,
        user_id=current_user.id if current_user else None,
        note=note
    )

    return RestoreVersionResponse(
        success=True,
        message=f"Successfully restored document from version {target_ver.version_number}. Created new version {new_version.version_number}.",
        document_type=document_type.upper(),
        document_id=document_id,
        restored_from_version=target_ver.version_number,
        new_version=new_version,
        updated_content=new_content
    )
