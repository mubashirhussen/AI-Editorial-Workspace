from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import WritingDraft, WritingSuggestion
from backend.app.schemas.writing import DraftCreate, DraftUpdate, WritingAnalysisRequest, WritingAnalysisResponse, WritingIssue, DraftCompareResponse
from backend.app.services.writing_analysis_service import writing_analysis_service
from backend.app.services.metrics_service import metrics_service
from backend.app.utils.text_processing import replace_text_safely
from backend.app.services.version_control.version_service import version_service

class WritingService:
    def create_draft(self, db: Session, data: DraftCreate) -> WritingDraft:
        draft = WritingDraft(
            project_id=data.project_id,
            title=data.title.strip(),
            original_content=data.original_content,
            revised_content=data.original_content,
            status="draft"
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        try:
            version_service.create_snapshot(
                db=db,
                document_type="WRITING_DRAFT",
                document_id=draft.id,
                content=draft.revised_content,
                title=draft.title,
                change_type="INITIAL",
                change_summary="Initial draft creation"
            )
        except Exception:
            pass

        return draft

    def get_draft(self, db: Session, draft_id: str) -> WritingDraft:
        draft = db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail="Writing draft not found.")
        return draft

    def update_draft(self, db: Session, draft_id: str, data: DraftUpdate) -> WritingDraft:
        draft = self.get_draft(db, draft_id)
        old_content = draft.revised_content

        if data.title is not None:
            draft.title = data.title.strip()
        if data.revised_content is not None:
            draft.revised_content = data.revised_content
        if data.final_content is not None:
            draft.final_content = data.final_content
        if data.status is not None:
            draft.status = data.status
        db.commit()
        db.refresh(draft)

        if data.revised_content is not None and data.revised_content != old_content:
            try:
                version_service.create_snapshot(
                    db=db,
                    document_type="WRITING_DRAFT",
                    document_id=draft.id,
                    content=draft.revised_content,
                    title=draft.title,
                    change_type="MANUAL_EDIT",
                    change_summary="Manual draft edit"
                )
            except Exception:
                pass

        return draft

    async def analyze_and_store(self, db: Session, req: WritingAnalysisRequest) -> WritingAnalysisResponse:
        # If draft_id is not given, create one automatically
        draft = None
        is_new = False
        if req.draft_id:
            draft = db.query(WritingDraft).filter(WritingDraft.id == req.draft_id).first()

        if not draft:
            is_new = True
            draft = WritingDraft(
                project_id=req.project_id,
                title=req.title or "Editorial Draft",
                original_content=req.text,
                revised_content=req.text,
                status="analyzed"
            )
            db.add(draft)
            db.commit()
            db.refresh(draft)
        else:
            # If draft already exists and text was edited, update revised_content
            if draft.revised_content != req.text:
                draft.revised_content = req.text
                draft.status = "analyzed"
                db.commit()
                db.refresh(draft)

        if is_new:
            try:
                version_service.create_snapshot(
                    db=db,
                    document_type="WRITING_DRAFT",
                    document_id=draft.id,
                    content=draft.revised_content,
                    title=draft.title,
                    change_type="INITIAL",
                    change_summary="Initial draft created from analysis"
                )
            except Exception:
                pass

        # Delete previous pending suggestions for this draft to re-evaluate fresh
        db.query(WritingSuggestion).filter(
            WritingSuggestion.draft_id == draft.id,
            WritingSuggestion.status == "pending"
        ).delete()
        db.commit()

        # Run analysis service
        analysis_result = await writing_analysis_service.analyze_text(req.text, draft_id=draft.id)

        # Persist suggestions
        stored_issues = []
        for issue in analysis_result.issues:
            sugg = WritingSuggestion(
                id=issue.id,
                draft_id=draft.id,
                category=issue.category,
                severity=issue.severity,
                original_text=issue.original_text,
                suggested_rewrite=issue.suggested_rewrite,
                explanation=issue.explanation,
                reason=issue.reason or "",
                confidence=issue.confidence,
                status="pending"
            )
            db.add(sugg)
            stored_issues.append(issue)

        db.commit()

        return WritingAnalysisResponse(
            draft_id=draft.id,
            overall_feedback=analysis_result.overall_feedback,
            issues=stored_issues,
            metrics=analysis_result.metrics
        )

    def accept_suggestion(self, db: Session, draft_id: str, suggestion_id: str) -> Dict[str, Any]:
        draft = self.get_draft(db, draft_id)
        suggestion = db.query(WritingSuggestion).filter(
            WritingSuggestion.id == suggestion_id,
            WritingSuggestion.draft_id == draft.id
        ).first()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found for this draft.")

        if suggestion.status == "accepted":
            return {"success": True, "message": "Suggestion was already accepted.", "revised_content": draft.revised_content}

        # Apply single replacement onto revised_content
        replacement = suggestion.suggested_rewrite
        if replacement.startswith("(") and replacement.endswith(")"):
            # Handle omit flags like "(remove filler)"
            if "remove" in replacement.lower():
                replacement = ""
            elif "synonym" in replacement.lower():
                # Cannot automatically replace without user explicit choice
                suggestion.status = "accepted"
                db.commit()
                return {"success": True, "message": "Marked reviewed.", "revised_content": draft.revised_content}

        new_content, success, err = replace_text_safely(
            draft.revised_content,
            suggestion.original_text,
            replacement
        )

        if not success:
            raise HTTPException(status_code=400, detail=err or "Could not locate target text in current revised draft.")

        draft.revised_content = new_content
        suggestion.status = "accepted"
        db.commit()
        db.refresh(draft)

        try:
            version_service.create_snapshot(
                db=db,
                document_type="WRITING_DRAFT",
                document_id=draft.id,
                content=draft.revised_content,
                title=draft.title,
                change_type="SUGGESTION_ACCEPTED",
                change_summary=f"Accepted suggestion: {suggestion.category} ('{suggestion.original_text[:25]}' -> '{replacement[:25]}')"
            )
        except Exception:
            pass

        new_metrics = metrics_service.calculate_metrics(draft.revised_content)

        return {
            "success": True,
            "suggestion_id": suggestion.id,
            "revised_content": draft.revised_content,
            "metrics": new_metrics.model_dump()
        }

    def reject_suggestion(self, db: Session, draft_id: str, suggestion_id: str) -> Dict[str, Any]:
        draft = self.get_draft(db, draft_id)
        suggestion = db.query(WritingSuggestion).filter(
            WritingSuggestion.id == suggestion_id,
            WritingSuggestion.draft_id == draft.id
        ).first()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found for this draft.")

        suggestion.status = "rejected"
        db.commit()

        return {
            "success": True,
            "suggestion_id": suggestion.id,
            "status": "rejected",
            "revised_content": draft.revised_content
        }

    def accept_all_suggestions(self, db: Session, draft_id: str) -> Dict[str, Any]:
        draft = self.get_draft(db, draft_id)
        pending_suggestions = db.query(WritingSuggestion).filter(
            WritingSuggestion.draft_id == draft.id,
            WritingSuggestion.status == "pending"
        ).all()

        current_content = draft.revised_content
        applied_count = 0

        for sugg in pending_suggestions:
            replacement = sugg.suggested_rewrite
            if replacement.startswith("(") and replacement.endswith(")"):
                if "remove" in replacement.lower():
                    replacement = ""
                else:
                    sugg.status = "accepted"
                    continue

            new_content, success, _ = replace_text_safely(
                current_content,
                sugg.original_text,
                replacement
            )
            if success:
                current_content = new_content
                sugg.status = "accepted"
                applied_count += 1
            else:
                sugg.status = "rejected"

        draft.revised_content = current_content
        db.commit()
        db.refresh(draft)

        if applied_count > 0:
            try:
                version_service.create_snapshot(
                    db=db,
                    document_type="WRITING_DRAFT",
                    document_id=draft.id,
                    content=draft.revised_content,
                    title=draft.title,
                    change_type="SUGGESTION_ACCEPTED",
                    change_summary=f"Accepted all suggestions ({applied_count} applied)"
                )
            except Exception:
                pass

        new_metrics = metrics_service.calculate_metrics(draft.revised_content)

        return {
            "success": True,
            "applied_count": applied_count,
            "revised_content": draft.revised_content,
            "metrics": new_metrics.model_dump()
        }

    def compare_draft(self, db: Session, draft_id: str) -> DraftCompareResponse:
        draft = self.get_draft(db, draft_id)
        orig_metrics = metrics_service.calculate_metrics(draft.original_content)
        rev_metrics = metrics_service.calculate_metrics(draft.revised_content)

        suggs = db.query(WritingSuggestion).filter(WritingSuggestion.draft_id == draft.id).all()
        accepted = sum(1 for s in suggs if s.status == "accepted")
        rejected = sum(1 for s in suggs if s.status == "rejected")
        pending = sum(1 for s in suggs if s.status == "pending")

        diff_score = 0.0
        if rev_metrics.readability_score and orig_metrics.readability_score:
            diff_score = round(rev_metrics.readability_score - orig_metrics.readability_score, 1)

        return DraftCompareResponse(
            draft_id=draft.id,
            original_content=draft.original_content,
            revised_content=draft.revised_content,
            word_count_diff=rev_metrics.word_count - orig_metrics.word_count,
            readability_diff=diff_score,
            total_suggestions=len(suggs),
            accepted_count=accepted,
            rejected_count=rejected,
            pending_count=pending
        )

writing_service = WritingService()
