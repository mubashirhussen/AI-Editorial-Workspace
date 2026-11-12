from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.app.core.database import get_db
from backend.app.schemas.writing import (
    WritingAnalysisRequest,
    WritingAnalysisResponse,
    WritingMetrics,
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftCompareResponse,
    DraftGenerateRequest,
    DraftGenerateResponse,
    SelectionRewriteRequest,
    SelectionRewriteResponse,
    ResearchGroundingAuditResponse,
    DraftExportResponse
)
from backend.app.schemas.style import (
    StyleCheckRequest,
    StyleCheckResponse
)
from backend.app.schemas.version import VersionResponse, VersionRestoreResponse
from backend.app.services.writing_service import writing_service
from backend.app.services.style_intelligence.style_analyzer import style_analyzer
from backend.app.services.version_control.version_service import version_service
from backend.app.schemas.auth import OrgPermission, has_permission
from backend.app.services.writing import writing_analyzer, metrics_service, suggestion_service
from backend.app.services.analytics_service import analytics_service
from backend.app.models.base import WritingDraft, WritingSuggestion, ResearchProject, EditorialStyleProfile, User, Organization, OrganizationMembership
from backend.app.api.deps import get_current_user, get_active_organization

router = APIRouter(prefix="/writing", tags=["Writing Assistant"])

def check_draft_tenant_access(
    db: Session,
    draft: WritingDraft,
    user: Optional[User],
    required_permission: Optional[OrgPermission] = None
) -> Optional[OrganizationMembership]:
    """Ensures the user belongs to the draft's organization and holds the required permission."""
    if not draft.organization_id:
        return None  # Unassigned legacy draft
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == draft.organization_id,
        OrganizationMembership.user_id == user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Writing draft with ID '{draft.id}' not found."
        )

    if required_permission and not has_permission(membership.role, required_permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{membership.role}' lacks permission '{required_permission.value}' for this draft."
        )
    return membership

@router.post("/analyze", response_model=WritingAnalysisResponse, summary="Analyze writing text")
async def analyze_writing(req: WritingAnalysisRequest, db: Session = Depends(get_db)):
    """Executes writing quality, readability, and structural analysis on provided text."""
    return await writing_service.analyze_and_store(db, req)

@router.post("/drafts", response_model=DraftResponse, status_code=status.HTTP_201_CREATED, summary="Create a new draft")
def create_draft(
    data: DraftCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization)
):
    """Creates a new writing draft and records an initial version snapshot."""
    org_id = org.id if org else None
    user_id = current_user.id if current_user else None
    draft = writing_service.create_draft(db, data, organization_id=org_id, user_id=user_id)
    analytics_service.track_event(db, org_id, "draft_created")
    return draft

@router.post("/drafts/generate", response_model=DraftGenerateResponse, status_code=status.HTTP_201_CREATED, summary="AI Generate editorial draft from research")
@router.post("/generate", response_model=DraftGenerateResponse, status_code=status.HTTP_201_CREATED, summary="AI Generate editorial draft from research alias")
async def generate_draft(
    req: DraftGenerateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    org: Optional[Organization] = Depends(get_active_organization)
):
    """
    Synthesizes a full, evidence-grounded editorial draft based on a research brief or topic.
    Preserves source citations and factual traceability.
    """
    org_id = org.id if org else None
    user_id = current_user.id if current_user else None
    res = await writing_service.generate_editorial_draft(db, req, organization_id=org_id, user_id=user_id)
    analytics_service.track_event(db, org_id, "draft_created", metadata={"status": "success"})
    return res

@router.post("/drafts/{draft_id}/duplicate", response_model=DraftResponse, status_code=status.HTTP_201_CREATED, summary="Duplicate draft")
def duplicate_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Clones an existing writing draft non-destructively."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    user_id = current_user.id if current_user else None
    return writing_service.duplicate_draft(db, draft_id, user_id=user_id)

@router.post("/rewrite-selection", response_model=SelectionRewriteResponse, summary="Rewrite selected text span")
@router.post("/drafts/{draft_id}/rewrite-selection", response_model=SelectionRewriteResponse, summary="Rewrite selected text span in draft")
async def rewrite_selection_span(
    req: SelectionRewriteRequest,
    draft_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Applies surgical AI or deterministic rewriting to a highlighted text selection.
    Preserves inline citations [1], [2] and surrounding context strictly.
    """
    if draft_id and not req.draft_id:
        req.draft_id = draft_id
    res = await writing_service.rewrite_selection(db, req)
    op_name = getattr(req.operation, "value", str(req.operation)) if hasattr(req, "operation") else "rewrite"
    analytics_service.track_event(db, None, "writing_improved", metadata={"category": op_name})
    return res

@router.get("/drafts/{draft_id}/grounding-audit", response_model=ResearchGroundingAuditResponse, summary="Audit factual grounding against research")
@router.post("/drafts/{draft_id}/grounding-audit", response_model=ResearchGroundingAuditResponse, summary="Audit factual grounding against research alias")
def audit_grounding(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Cross-references claims in the draft against connected research brief evidence and sources.
    Reports grounded, inferred, unsupported, and contradictory statements.
    """
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.VIEW_CONTENT)
    return writing_service.audit_research_grounding(db, draft_id)

@router.get("/drafts/{draft_id}/export", summary="Export draft to Markdown, Text, Word, or HTML")
def export_draft_document(
    draft_id: str,
    format: str = Query("markdown", description="Format: markdown, txt, docx, html"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Exports the latest revised draft to publication-ready formats.
    Preserves headings, formatting, citations, and metadata.
    """
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.VIEW_CONTENT)
    file_bytes, filename, mime_type = writing_service.export_draft(db, draft_id, format)
    analytics_service.track_event(db, getattr(draft, "organization_id", None), "export_executed", metadata={"format": format})
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/drafts", response_model=List[DraftResponse], summary="List writing drafts")
def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("updated_at", description="Field to sort by: updated_at, created_at, title"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db),
    org: Optional[Organization] = Depends(get_active_organization)
):
    """Retrieves paginated writing drafts scoped to user organization with sorting and filters."""
    org_id = org.id if org else None
    return writing_service.get_drafts(
        db,
        organization_id=org_id,
        project_id=project_id,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )

@router.get("/drafts/{draft_id}", response_model=DraftResponse, summary="Get draft by ID")
def get_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Retrieves full writing draft details including revised and original content."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.VIEW_CONTENT)
    return draft

@router.put("/drafts/{draft_id}", response_model=DraftResponse, summary="Update draft content")
def update_draft(
    draft_id: str,
    data: DraftUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Updates draft text, title, or status, creating a version snapshot if revised."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    user_id = current_user.id if current_user else None
    return writing_service.update_draft(db, draft_id, data, user_id=user_id)

@router.patch("/drafts/{draft_id}", response_model=DraftResponse, summary="Patch draft fields")
def patch_draft(
    draft_id: str,
    data: DraftUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Partially updates draft content, metadata, or status with automatic snapshot."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    user_id = current_user.id if current_user else None
    updated = writing_service.update_draft(db, draft_id, data, user_id=user_id)
    content = updated.revised_content or updated.original_content or ""
    try:
        version_service.create_snapshot(
            db,
            document_type="WRITING_DRAFT",
            document_id=draft_id,
            content=content,
            title=updated.title,
            change_type="MANUAL_EDIT",
            change_summary="Draft updated via API",
            user_id=user_id,
            force=True
        )
    except Exception:
        pass
    return updated

@router.post("/drafts/{draft_id}/archive", response_model=DraftResponse, summary="Archive draft")
def archive_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Archives a writing draft non-destructively."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    user_id = current_user.id if current_user else None
    return writing_service.archive_draft(db, draft_id, user_id=user_id)

@router.post("/drafts/{draft_id}/reopen", response_model=DraftResponse, summary="Reopen draft")
def reopen_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Reopens an archived writing draft."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    user_id = current_user.id if current_user else None
    return writing_service.reopen_draft(db, draft_id, user_id=user_id)

@router.delete("/drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete draft")
def delete_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Deletes a writing draft and its associated suggestions."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.EDIT_DRAFTS)
    writing_service.delete_draft(db, draft_id)
    return None

# --- Draft Analysis Endpoints ---

@router.post("/drafts/{draft_id}/analyze", response_model=WritingAnalysisResponse, summary="Run analysis on draft")
def analyze_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Analyzes an existing draft's text for readability and generates actionable rewrite suggestions."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.VIEW_CONTENT)
    content = draft.revised_content or draft.original_content or ""
    
    # Clean previous pending suggestions
    db.query(WritingSuggestion).filter(
        WritingSuggestion.draft_id == draft.id,
        WritingSuggestion.status.in_(["pending", "PENDING"])
    ).delete()
    db.commit()

    analysis = writing_analyzer.analyze_text(content, draft_id=draft.id)
    for issue in analysis.issues:
        sugg = WritingSuggestion(
            id=issue.id,
            draft_id=draft.id,
            category=issue.category,
            severity=issue.severity,
            original_text=issue.original_text,
            suggested_text=issue.suggested_rewrite,
            suggested_rewrite=issue.suggested_rewrite,
            explanation=issue.explanation,
            reason=issue.reason or "",
            confidence=issue.confidence,
            status="PENDING"
        )
        db.add(sugg)

    draft.status = "ANALYZED"
    draft.readability_score = analysis.metrics.readability_score
    db.commit()
    db.refresh(draft)
    return analysis

@router.get("/drafts/{draft_id}/analysis", response_model=WritingAnalysisResponse, summary="Get cached draft analysis")
def get_draft_analysis(draft_id: str, db: Session = Depends(get_db)):
    """Retrieves current analysis feedback and issues for a draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    return writing_analyzer.analyze_text(content, draft_id=draft.id)

@router.get("/drafts/{draft_id}/metrics", response_model=WritingMetrics, summary="Get draft writing metrics")
def get_draft_metrics(draft_id: str, db: Session = Depends(get_db)):
    """Calculates live writing metrics (word count, reading time, readability) for a draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    return metrics_service.calculate_metrics(content)

# --- Suggestions Management ---

@router.get("/drafts/{draft_id}/suggestions", summary="List draft suggestions")
def get_draft_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """Returns all suggestions generated for a writing draft."""
    writing_service.get_draft(db, draft_id)
    return db.query(WritingSuggestion).filter(WritingSuggestion.draft_id == draft_id).all()

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/accept", summary="Accept suggestion in draft")
def accept_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Applies a specific suggested rewrite to the draft content."""
    return writing_service.accept_suggestion(db, draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/{suggestion_id}/reject", summary="Reject suggestion in draft")
def reject_suggestion(draft_id: str, suggestion_id: str, db: Session = Depends(get_db)):
    """Marks a suggestion as rejected without altering draft content."""
    return writing_service.reject_suggestion(db, draft_id, suggestion_id)

@router.post("/suggestions/{suggestion_id}/accept", summary="Accept suggestion direct")
def accept_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Accepts a suggestion using its global ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return writing_service.accept_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/suggestions/{suggestion_id}/reject", summary="Reject suggestion direct")
def reject_suggestion_direct(suggestion_id: str, db: Session = Depends(get_db)):
    """Rejects a suggestion using its global ID."""
    sugg = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
    if not sugg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Suggestion with ID '{suggestion_id}' not found.")
    return writing_service.reject_suggestion(db, sugg.draft_id, suggestion_id)

@router.post("/drafts/{draft_id}/suggestions/accept-all", summary="Accept all suggestions")
@router.post("/drafts/{draft_id}/accept-all", summary="Accept all suggestions alias")
def accept_all_suggestions(draft_id: str, db: Session = Depends(get_db)):
    """Accepts and applies all pending suggestions for the specified draft."""
    return writing_service.accept_all_suggestions(db, draft_id)

@router.get("/drafts/{draft_id}/compare", response_model=DraftCompareResponse, summary="Compare draft with baseline")
def compare_draft(draft_id: str, db: Session = Depends(get_db)):
    """Compares the current revised draft against its baseline original content."""
    return writing_service.compare_draft(db, draft_id)

@router.post("/drafts/{draft_id}/rewrite", summary="Request AI draft rewrite")
def request_draft_rewrite(draft_id: str, db: Session = Depends(get_db)):
    """Generates AI rewrite suggestions for the full draft."""
    draft = writing_service.get_draft(db, draft_id)
    content = draft.revised_content or draft.original_content or ""
    analysis = writing_analyzer.analyze_text(content, draft_id=draft.id)
    return {
        "draft_id": draft_id,
        "metrics": analysis.metrics.model_dump() if hasattr(analysis.metrics, "model_dump") else analysis.metrics.dict(),
        "issues_count": len(analysis.issues),
        "issues": [i.model_dump() if hasattr(i, "model_dump") else i.dict() for i in analysis.issues],
        "revised_content": content
    }

# --- Version History & Restoration ---

@router.get("/drafts/{draft_id}/versions", response_model=List[VersionResponse], summary="List draft version snapshots")
def get_draft_versions(draft_id: str, db: Session = Depends(get_db)):
    """Returns chronological snapshot versions for this draft."""
    writing_service.get_draft(db, draft_id)
    return version_service.list_versions(db, "WRITING_DRAFT", draft_id)

@router.post("/drafts/{draft_id}/restore/{version_id}", response_model=VersionRestoreResponse, summary="Restore draft snapshot")
def restore_draft_version(draft_id: str, version_id: str, db: Session = Depends(get_db)):
    """Restores a previous draft snapshot non-destructively as a new head version."""
    writing_service.get_draft(db, draft_id)
    version = version_service.get_version(db, "WRITING_DRAFT", draft_id, version_id)
    new_version, new_content = version_service.restore_version(db, "WRITING_DRAFT", draft_id, version.version_number)
    return VersionRestoreResponse(
        success=True,
        message=f"Draft restored to version {version.version_number}",
        document_type="WRITING_DRAFT",
        document_id=draft_id,
        restored_from_version=version.version_number,
        new_version=new_version,
        updated_content=new_content,
        content=new_content
    )

# --- Style Intelligence ---

@router.post("/drafts/{draft_id}/style-check", response_model=StyleCheckResponse, summary="Audit style compliance")
def style_check_draft(
    draft_id: str,
    payload: Optional[StyleCheckRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    active_org: Optional[Organization] = Depends(get_active_organization)
):
    """Executes an automated style-compliance audit on a writing draft against a selected Editorial Style Profile."""
    draft = writing_service.get_draft(db, draft_id)
    check_draft_tenant_access(db, draft, current_user, OrgPermission.VIEW_CONTENT)

    org_id = active_org.id if active_org else draft.organization_id

    profile = None
    profile_id = payload.style_profile_id if payload else None

    # 1. Direct explicit profile requested
    if profile_id:
        p = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == profile_id).first()
        if p:
            if p.organization_id is None or (org_id and p.organization_id == org_id):
                profile = p
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Style profile not found in active organization.")

    # 2. Draft's attached profile
    if not profile and draft.style_profile_id:
        p = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == draft.style_profile_id).first()
        if p and (p.organization_id is None or (org_id and p.organization_id == org_id)):
            profile = p

    # 3. Active organization default profile
    if not profile and org_id:
        profile = db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id == org_id,
            EditorialStyleProfile.is_default == True
        ).first()

    # 4. Global system default profile
    if not profile:
        profile = db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id.is_(None),
            EditorialStyleProfile.is_default == True
        ).first()

    # 5. Any profile in this organization
    if not profile and org_id:
        profile = db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id == org_id
        ).first()

    # 6. Any system global template
    if not profile:
        profile = db.query(EditorialStyleProfile).filter(
            EditorialStyleProfile.organization_id.is_(None)
        ).first()

    # 7. Safe fallback profile created in org scope if none exists
    if not profile:
        import uuid
        profile = EditorialStyleProfile(
            id=str(uuid.uuid4()),
            organization_id=org_id,
            name="Standard Editorial",
            publication_name="AI Editorial Workspace",
            tone="Authoritative, analytical, objective",
            target_audience="General audience, industry practitioners, and decision-makers",
            is_default=True,
            target_flesch_score=60.0,
            max_sentence_length=35,
            max_paragraph_length=150,
            preferred_terminology={},
            words_to_avoid=["synergy", "paradigm shift", "disruptive", "game-changer"]
        )
        try:
            db.add(profile)
            db.commit()
            db.refresh(profile)
        except Exception:
            db.rollback()

    override_content = payload.content if payload else None
    return style_analyzer.analyze_and_update_draft(db, draft, profile, override_content=override_content)
