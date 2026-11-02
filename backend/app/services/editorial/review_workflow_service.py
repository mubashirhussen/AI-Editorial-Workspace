"""
Editorial Review Workflow Service.
Handles human-in-the-loop lifecycle operations, automated AI pre-reviews,
status transition validation, version-aware revisions, and dashboard metrics.
"""

import re
import difflib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from backend.app.models.base import (
    EditorialOutput,
    EditorialReview,
    EditorialComment,
    ResearchProject,
    utc_now
)
from backend.app.schemas.editorial_review import (
    WorkflowStatus,
    is_valid_transition,
    EditorialReviewCreate,
    EditorialCommentCreate,
    EditorialCommentUpdate,
    EditorialChangeRequest,
    EditorialApproveRequest,
    EditorialFinalizeRequest,
    EditorialRevisionUpdate,
    EditorialDashboardStats
)
from backend.app.services.writing.writing_analyzer import writing_analyzer
from backend.app.evaluation.metrics.scoring import calculate_word_count_compliance

class EditorialReviewWorkflowService:
    # =====================================================================
    # 1. AI PRE-REVIEW INTEGRATION
    # =====================================================================
    def run_ai_pre_review(self, db: Session, editorial_id: str) -> Dict[str, Any]:
        """
        Executes automated quality checks before human review:
        - Word count compliance (300-500 words)
        - Writing quality analysis (issues, readability grade)
        - Missing section detection
        - Source reference verification
        - Uncertainty & grounding check
        Transitions status to AI_REVIEW_COMPLETED -> HUMAN_REVIEW_PENDING.
        NOTE: AI review NEVER approves or finalizes an editorial.
        """
        editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
        if not editorial:
            raise HTTPException(status_code=404, detail="Editorial not found.")

        if editorial.status == WorkflowStatus.FINALIZED:
            raise HTTPException(status_code=400, detail="Cannot run review on finalized editorial.")

        content = editorial.content or ""
        sources = editorial.source_references or []

        # 1. Word Count Validation
        wc_info = calculate_word_count_compliance(content, min_words=300, max_words=500)

        # 2. Writing Quality Analysis
        writing_audit = writing_analyzer.analyze_text(content)
        issues_summary = [
            {
                "category": iss.category,
                "original_text": iss.original_text,
                "suggested_rewrite": iss.suggested_rewrite,
                "explanation": iss.explanation
            }
            for iss in writing_audit.issues
        ]

        # 3. Missing Sections Check
        expected_sections = ["Opening", "What Happened", "Context", "Strategic Analysis", "Practical Implications", "Bottom Line"]
        missing_sections = []
        for sec in expected_sections:
            sec_pattern = re.compile(rf"\b{re.escape(sec)}\b", re.IGNORECASE)
            if not sec_pattern.search(content):
                missing_sections.append(sec)

        # 4. Source Reference & Anchor Verification
        citations_found = re.findall(r"\[(\d+)\]", content)
        valid_source_indices = {str(s.get("index", idx + 1)) for idx, s in enumerate(sources)}
        invalid_citations = [c for c in citations_found if c not in valid_source_indices]

        # 5. Uncertainty & Hedging Indicators
        speculative_words = ["may", "might", "could", "perhaps", "alleged", "rumored", "unconfirmed"]
        uncertainty_matches = []
        for word in speculative_words:
            pattern = re.compile(rf"\b{word}\b", re.IGNORECASE)
            matches = pattern.findall(content)
            if matches:
                uncertainty_matches.append({"term": word, "count": len(matches)})

        ai_review_data = {
            "evaluated_at": utc_now().isoformat(),
            "word_count_compliance": wc_info,
            "readability_score": writing_audit.metrics.readability_score,
            "readability_grade": writing_audit.metrics.readability_grade,
            "writing_issues_count": len(issues_summary),
            "writing_issues": issues_summary[:10],
            "missing_sections": missing_sections,
            "citations_found_count": len(citations_found),
            "invalid_citations": invalid_citations,
            "uncertainty_indicators": uncertainty_matches,
            "ai_verdict": "READY_FOR_HUMAN_REVIEW" if wc_info["is_compliant"] and not invalid_citations else "FLAGGED_WITH_WARNINGS"
        }

        editorial.ai_review_results = ai_review_data

        # Transition status: DRAFT_CREATED -> AI_REVIEW_COMPLETED -> HUMAN_REVIEW_PENDING
        if editorial.status.upper() in [WorkflowStatus.DRAFT_CREATED, WorkflowStatus.DRAFT]:
            editorial.status = WorkflowStatus.HUMAN_REVIEW_PENDING

        db.commit()
        db.refresh(editorial)

        return ai_review_data

    # =====================================================================
    # 2. STATUS TRANSITION VALIDATION
    # =====================================================================
    def transition_editorial_status(
        self,
        db: Session,
        editorial: EditorialOutput,
        new_status: str,
        reviewer_name: str = "Human Editor",
        notes: Optional[str] = None
    ) -> EditorialOutput:
        """
        Enforces strict lifecycle transition rules.
        Prevents unauthorized or premature transitions (e.g. unapproved to FINALIZED).
        """
        current_status = editorial.status
        if current_status == new_status:
            return editorial

        if current_status == WorkflowStatus.FINALIZED and new_status != WorkflowStatus.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Finalized editorial is locked and immutable. Only archiving is allowed."
            )

        if new_status == WorkflowStatus.FINALIZED and current_status != WorkflowStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot finalize an editorial with status '{current_status}'. Editorial must be 'APPROVED' first."
            )

        if not is_valid_transition(current_status, new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal status transition: '{current_status}' -> '{new_status}'. Allowed transitions: {sorted(list(is_valid_transition.__globals__['VALID_STATUS_TRANSITIONS'].get(current_status, set())))}"
            )

        editorial.status = new_status
        editorial.updated_at = utc_now()

        # Create audit review record
        review = EditorialReview(
            editorial_id=editorial.id,
            reviewer_name=reviewer_name,
            review_status=new_status,
            overall_feedback=notes,
            reviewed_at=utc_now()
        )
        db.add(review)
        db.commit()
        db.refresh(editorial)
        return editorial

    # =====================================================================
    # 3. REVISION MANAGEMENT & DIFFS
    # =====================================================================
    def update_editorial_revision(
        self,
        db: Session,
        editorial_id: str,
        req: EditorialRevisionUpdate
    ) -> Tuple[EditorialOutput, Dict[str, Any]]:
        """
        Applies version-aware text revisions.
        Preserves original_content, increments version, and produces diff output.
        """
        editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
        if not editorial:
            raise HTTPException(status_code=404, detail="Editorial not found.")

        if editorial.status == WorkflowStatus.FINALIZED:
            raise HTTPException(status_code=400, detail="Cannot edit a finalized editorial.")

        # Ensure original_content is preserved
        if not editorial.original_content:
            editorial.original_content = editorial.content

        old_text = editorial.content
        new_text = req.revised_content

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=f"v{editorial.version}",
            tofile=f"v{editorial.version + 1}",
            lineterm=""
        ))

        editorial.content = new_text
        if req.headline:
            editorial.headline = req.headline
        editorial.version += 1
        editorial.word_count = len(re.findall(r"\b[a-zA-Z0-9'-]+\b", new_text))
        editorial.updated_at = utc_now()

        # If changes were requested, revising moves back to HUMAN_REVIEW_PENDING
        if editorial.status == WorkflowStatus.CHANGES_REQUESTED:
            editorial.status = WorkflowStatus.HUMAN_REVIEW_PENDING

        db.commit()
        db.refresh(editorial)

        diff_summary = {
            "version": editorial.version,
            "diff": "\n".join(diff_lines),
            "added_lines": sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++")),
            "removed_lines": sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
        }

        return editorial, diff_summary

    # =====================================================================
    # 4. REVIEW ACTIONS (APPROVE, REQUEST CHANGES, FINALIZE)
    # =====================================================================
    def request_changes(
        self,
        db: Session,
        editorial_id: str,
        req: EditorialChangeRequest
    ) -> EditorialOutput:
        editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
        if not editorial:
            raise HTTPException(status_code=404, detail="Editorial not found.")

        return self.transition_editorial_status(
            db=db,
            editorial=editorial,
            new_status=WorkflowStatus.CHANGES_REQUESTED,
            reviewer_name=req.reviewer_name,
            notes=req.feedback
        )

    def approve_editorial(
        self,
        db: Session,
        editorial_id: str,
        req: EditorialApproveRequest
    ) -> EditorialOutput:
        editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
        if not editorial:
            raise HTTPException(status_code=404, detail="Editorial not found.")

        return self.transition_editorial_status(
            db=db,
            editorial=editorial,
            new_status=WorkflowStatus.APPROVED,
            reviewer_name=req.reviewer_name,
            notes=req.approval_notes or "Editorial approved by human reviewer."
        )

    def finalize_editorial(
        self,
        db: Session,
        editorial_id: str,
        req: EditorialFinalizeRequest
    ) -> EditorialOutput:
        editorial = db.query(EditorialOutput).filter(EditorialOutput.id == editorial_id).first()
        if not editorial:
            raise HTTPException(status_code=404, detail="Editorial not found.")

        return self.transition_editorial_status(
            db=db,
            editorial=editorial,
            new_status=WorkflowStatus.FINALIZED,
            reviewer_name=req.finalized_by,
            notes=req.publication_notes or "Editorial finalized and locked for distribution."
        )

    # =====================================================================
    # 5. COMMENTS MANAGEMENT
    # =====================================================================
    def add_comment(
        self,
        db: Session,
        review_id: str,
        req: EditorialCommentCreate
    ) -> EditorialComment:
        review = db.query(EditorialReview).filter(EditorialReview.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found.")

        comment = EditorialComment(
            review_id=review_id,
            section_reference=req.section_reference,
            original_text=req.original_text,
            comment=req.comment,
            suggested_revision=req.suggested_revision,
            resolution_status="open"
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    def update_comment(
        self,
        db: Session,
        comment_id: str,
        req: EditorialCommentUpdate
    ) -> EditorialComment:
        comment = db.query(EditorialComment).filter(EditorialComment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found.")

        if req.resolution_status:
            comment.resolution_status = req.resolution_status
        if req.comment:
            comment.comment = req.comment
        if req.suggested_revision is not None:
            comment.suggested_revision = req.suggested_revision

        db.commit()
        db.refresh(comment)
        return comment

    # =====================================================================
    # 6. DASHBOARD STATISTICS
    # =====================================================================
    def get_dashboard_stats(self, db: Session) -> EditorialDashboardStats:
        """
        Computes real database-backed workflow counts.
        """
        total = db.query(EditorialOutput).count()
        pending = db.query(EditorialOutput).filter(EditorialOutput.status.in_([WorkflowStatus.HUMAN_REVIEW_PENDING, WorkflowStatus.AI_REVIEW_COMPLETED])).count()
        approved = db.query(EditorialOutput).filter(EditorialOutput.status == WorkflowStatus.APPROVED).count()
        changes = db.query(EditorialOutput).filter(EditorialOutput.status == WorkflowStatus.CHANGES_REQUESTED).count()
        finalized = db.query(EditorialOutput).filter(EditorialOutput.status == WorkflowStatus.FINALIZED).count()

        # Fetch recent review activity
        recent_reviews = (
            db.query(EditorialReview)
            .order_by(desc(EditorialReview.created_at))
            .limit(10)
            .all()
        )

        activity_list = [
            {
                "review_id": r.id,
                "editorial_id": r.editorial_id,
                "reviewer_name": r.reviewer_name,
                "review_status": r.review_status,
                "overall_feedback": r.overall_feedback,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_reviews
        ]

        return EditorialDashboardStats(
            pending_human_reviews=pending,
            approved_editorials=approved,
            changes_requested=changes,
            finalized_editorials=finalized,
            total_editorials=total,
            recent_activity=activity_list
        )

review_workflow_service = EditorialReviewWorkflowService()
