import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.models.base import (
    EditorialVersion,
    WritingDraft,
    ResearchBrief,
    EditorialOutput,
    ResearchProject,
    User
)
from backend.app.schemas.version import (
    EditorialVersionResponse,
    VersionComparisonResponse,
    DiffChunk,
    WordDiffChunk
)
from backend.app.services.version_control.diff_engine import diff_engine

logger = logging.getLogger("editorial_workspace.version_control")

SUPPORTED_DOCUMENT_TYPES = {"WRITING_DRAFT", "RESEARCH_BRIEF", "EDITORIAL_OUTPUT"}
VALID_CHANGE_TYPES = {
    "INITIAL",
    "MANUAL_EDIT",
    "AI_REVISION",
    "SUGGESTION_ACCEPTED",
    "SUGGESTION_REJECTED",
    "RESTORE"
}

class VersionService:
    """
    Manages persistent, append-only version history and snapshots for
    research briefs, writing drafts, and editorial newsletter outputs.
    """

    def resolve_document(self, db: Session, document_type: str, document_id: str) -> Tuple[Any, Optional[str], str, str]:
        """
        Validates document existence and retrieves (doc_instance, org_id, title, content).
        """
        doc_type_upper = document_type.upper()
        if doc_type_upper not in SUPPORTED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported document type '{document_type}'. Supported: {sorted(list(SUPPORTED_DOCUMENT_TYPES))}"
            )

        if doc_type_upper == "WRITING_DRAFT":
            draft = db.query(WritingDraft).filter(WritingDraft.id == document_id).first()
            if not draft:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Writing draft not found")
            org_id = None
            if draft.project_id:
                proj = db.query(ResearchProject).filter(ResearchProject.id == draft.project_id).first()
                if proj:
                    org_id = proj.organization_id
            content = draft.revised_content or draft.original_content or ""
            return draft, org_id, draft.title or "Editorial Draft", content

        elif doc_type_upper == "EDITORIAL_OUTPUT":
            output = db.query(EditorialOutput).filter(EditorialOutput.id == document_id).first()
            if not output:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial output not found")
            org_id = None
            if output.project_id:
                proj = db.query(ResearchProject).filter(ResearchProject.id == output.project_id).first()
                if proj:
                    org_id = proj.organization_id
            content = output.content or ""
            return output, org_id, output.headline or "Newsletter Article", content

        elif doc_type_upper == "RESEARCH_BRIEF":
            brief = db.query(ResearchBrief).filter(ResearchBrief.id == document_id).first()
            if not brief:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research brief not found")
            org_id = None
            if brief.project_id:
                proj = db.query(ResearchProject).filter(ResearchProject.id == brief.project_id).first()
                if proj:
                    org_id = proj.organization_id
            content = brief.executive_summary or ""
            return brief, org_id, brief.title or "Research Synthesis Brief", content

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported document type '{document_type}'")

    def create_snapshot(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        content: str,
        title: Optional[str] = None,
        change_type: str = "MANUAL_EDIT",
        change_summary: str = "",
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        force: bool = False
    ) -> Optional[EditorialVersion]:
        """
        Creates an immutable snapshot if content has changed.
        Maintains sequential version numbers per document using atomic queries.
        """
        doc_type_upper = document_type.upper()
        if doc_type_upper not in SUPPORTED_DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported document type: {document_type}")

        norm_change_type = change_type.upper() if change_type.upper() in VALID_CHANGE_TYPES else "MANUAL_EDIT"

        # Check latest version for this document
        latest = (
            db.query(EditorialVersion)
            .filter(
                EditorialVersion.document_type == doc_type_upper,
                EditorialVersion.document_id == document_id
            )
            .order_by(EditorialVersion.version_number.desc())
            .first()
        )

        content_clean = (content or "").strip()

        # Prevent duplicate snapshot if content is identical
        if not force and latest and latest.content_snapshot.strip() == content_clean:
            logger.debug(f"Snapshot skipped: content identical to version {latest.version_number}")
            return latest

        # Version numbering
        next_ver = (latest.version_number + 1) if latest else 1

        if not change_summary:
            default_summaries = {
                "INITIAL": "Initial document snapshot",
                "MANUAL_EDIT": "Manual editorial updates",
                "AI_REVISION": "AI-assisted content refinement",
                "SUGGESTION_ACCEPTED": "Applied editorial suggestion",
                "SUGGESTION_REJECTED": "Reviewed editorial suggestion",
                "RESTORE": "Restored previous version"
            }
            change_summary = default_summaries.get(norm_change_type, "Content revision")

        version = EditorialVersion(
            organization_id=org_id,
            document_type=doc_type_upper,
            document_id=document_id,
            version_number=next_ver,
            title=title,
            content_snapshot=content or "",
            change_summary=change_summary,
            change_type=norm_change_type,
            created_by=user_id
        )

        try:
            db.add(version)
            db.commit()
            db.refresh(version)
            logger.info(f"Created version {next_ver} for {doc_type_upper} {document_id} [{norm_change_type}]")
            return version
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create version snapshot: {e}")
            raise

    def list_versions(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        limit: int = 100
    ) -> List[EditorialVersionResponse]:
        """
        Lists all versions for a document in descending order (latest first).
        """
        # Validate document exists
        self.resolve_document(db, document_type, document_id)
        doc_type_upper = document_type.upper()

        versions = (
            db.query(EditorialVersion)
            .filter(
                EditorialVersion.document_type == doc_type_upper,
                EditorialVersion.document_id == document_id
            )
            .order_by(EditorialVersion.version_number.desc())
            .limit(limit)
            .all()
        )

        results = []
        for v in versions:
            results.append(self._to_response(v, db))
        return results

    def get_version(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        version_ref: str
    ) -> EditorialVersionResponse:
        """
        Retrieves a single version by UUID or version number.
        """
        self.resolve_document(db, document_type, document_id)
        doc_type_upper = document_type.upper()

        version = None
        if version_ref.isdigit():
            version = (
                db.query(EditorialVersion)
                .filter(
                    EditorialVersion.document_type == doc_type_upper,
                    EditorialVersion.document_id == document_id,
                    EditorialVersion.version_number == int(version_ref)
                )
                .first()
            )
        else:
            version = (
                db.query(EditorialVersion)
                .filter(
                    EditorialVersion.id == version_ref,
                    EditorialVersion.document_type == doc_type_upper,
                    EditorialVersion.document_id == document_id
                )
                .first()
            )

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Version '{version_ref}' not found for {document_type} '{document_id}'."
            )

        return self._to_response(version, db)

    def compare_versions(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        from_ref: str,
        to_ref: str
    ) -> VersionComparisonResponse:
        """
        Compares any two versions of a document with additions, deletions,
        word count deltas, and timestamp tracking.
        """
        ver_a = self.get_version(db, document_type, document_id, from_ref)
        ver_b = self.get_version(db, document_type, document_id, to_ref)

        diff_data = diff_engine.compare_texts(ver_a.content_snapshot, ver_b.content_snapshot)

        return VersionComparisonResponse(
            document_type=document_type.upper(),
            document_id=document_id,
            version_a=ver_a,
            version_b=ver_b,
            word_count_a=diff_data["word_count_a"],
            word_count_b=diff_data["word_count_b"],
            word_count_diff=diff_data["word_count_diff"],
            char_count_a=diff_data["char_count_a"],
            char_count_b=diff_data["char_count_b"],
            char_count_diff=diff_data["char_count_diff"],
            additions_count=diff_data["additions_count"],
            deletions_count=diff_data["deletions_count"],
            unchanged_count=diff_data["unchanged_count"],
            diff_chunks=[DiffChunk(**c) for c in diff_data["diff_chunks"]],
            word_diff_chunks=[WordDiffChunk(**c) for c in diff_data["word_diff_chunks"]]
        )

    def restore_version(
        self,
        db: Session,
        document_type: str,
        document_id: str,
        version_ref: str,
        user_id: Optional[str] = None,
        note: Optional[str] = None
    ) -> Tuple[EditorialVersionResponse, str]:
        """
        Restores an earlier version by creating a NEW version snapshot.
        Never deletes existing versions. Preserves original draft content immutability.
        """
        doc, org_id, title, current_content = self.resolve_document(db, document_type, document_id)
        doc_type_upper = document_type.upper()

        # Retrieve target version to restore from
        target_version_resp = self.get_version(db, document_type, document_id, version_ref)
        restored_content = target_version_resp.content_snapshot

        # Ensure current live content is saved if it has unsaved changes before restoring
        latest_ver = (
            db.query(EditorialVersion)
            .filter(
                EditorialVersion.document_type == doc_type_upper,
                EditorialVersion.document_id == document_id
            )
            .order_by(EditorialVersion.version_number.desc())
            .first()
        )
        if latest_ver and latest_ver.content_snapshot.strip() != current_content.strip():
            # Capture active pre-restore state so no edits are ever lost
            self.create_snapshot(
                db=db,
                document_type=doc_type_upper,
                document_id=document_id,
                content=current_content,
                title=title,
                change_type="MANUAL_EDIT",
                change_summary="Pre-restore working draft capture",
                user_id=user_id,
                org_id=org_id
            )

        # Create the RESTORE snapshot
        summary = f"Restored from version {target_version_resp.version_number}"
        if note:
            summary += f": {note}"

        new_version = self.create_snapshot(
            db=db,
            document_type=doc_type_upper,
            document_id=document_id,
            content=restored_content,
            title=target_version_resp.title or title,
            change_type="RESTORE",
            change_summary=summary,
            user_id=user_id,
            org_id=org_id,
            force=True  # Force new snapshot to record restore action
        )

        # Apply restored content onto active document
        if doc_type_upper == "WRITING_DRAFT":
            doc.revised_content = restored_content
            doc.word_count = diff_engine.count_words(restored_content)
            # original_content remains strictly untouched!
        elif doc_type_upper == "EDITORIAL_OUTPUT":
            doc.content = restored_content
            doc.word_count = diff_engine.count_words(restored_content)
        elif doc_type_upper == "RESEARCH_BRIEF":
            doc.executive_summary = restored_content

        db.commit()
        db.refresh(doc)

        return self._to_response(new_version, db), restored_content

    def _to_response(self, version: EditorialVersion, db: Session) -> EditorialVersionResponse:
        author_name = "System Editor"
        if version.created_by:
            u = db.query(User).filter(User.id == version.created_by).first()
            if u:
                author_name = u.full_name or u.email

        content = version.content_snapshot or ""
        word_count = diff_engine.count_words(content)
        char_count = len(content)

        return EditorialVersionResponse(
            id=version.id,
            organization_id=version.organization_id,
            document_type=version.document_type,
            document_id=version.document_id,
            version_number=version.version_number,
            title=version.title,
            content_snapshot=content,
            change_summary=version.change_summary or "",
            change_type=version.change_type or "MANUAL_EDIT",
            created_by=version.created_by,
            author_name=author_name,
            created_at=version.created_at,
            word_count=word_count,
            char_count=char_count
        )

version_service = VersionService()
