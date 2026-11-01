from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import WritingDraft, WritingSuggestion
from backend.app.schemas.writing import DraftCompareResponse
from backend.app.services.writing.metrics_service import metrics_service
from backend.app.utils.text_processing import replace_text_safely

class SuggestionService:
    """
    Manages suggestion state transitions and non-destructive replacements on drafts.
    """

    def get_draft(self, db: Session, draft_id: str) -> WritingDraft:
        draft = db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail=f"Writing draft with ID '{draft_id}' not found.")
        return draft

    def get_suggestion(self, db: Session, suggestion_id: str) -> WritingSuggestion:
        suggestion = db.query(WritingSuggestion).filter(WritingSuggestion.id == suggestion_id).first()
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"Writing suggestion with ID '{suggestion_id}' not found.")
        return suggestion

    def accept_suggestion(self, db: Session, draft_id: str, suggestion_id: str) -> Dict[str, Any]:
        draft = self.get_draft(db, draft_id)
        suggestion = db.query(WritingSuggestion).filter(
            WritingSuggestion.id == suggestion_id,
            WritingSuggestion.draft_id == draft.id
        ).first()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion does not belong to this draft.")

        if suggestion.status.upper() == "ACCEPTED":
            return {
                "success": True,
                "message": "Suggestion was already accepted.",
                "revised_content": draft.revised_content
            }

        replacement = suggestion.suggested_text or suggestion.suggested_rewrite or ""
        if replacement.startswith("(") and replacement.endswith(")"):
            if "remove" in replacement.lower() or "omit" in replacement.lower():
                replacement = ""
            else:
                suggestion.status = "ACCEPTED"
                db.commit()
                return {
                    "success": True,
                    "message": "Suggestion reviewed and marked accepted.",
                    "revised_content": draft.revised_content
                }

        # Apply targeted non-destructive replacement on revised_content
        new_content, success, err = replace_text_safely(
            draft.revised_content,
            suggestion.original_text,
            replacement
        )

        if not success:
            raise HTTPException(status_code=400, detail=err or "Target text no longer matches current draft position (stale suggestion).")

        draft.revised_content = new_content
        draft.word_count = len(new_content.split())
        suggestion.status = "ACCEPTED"
        
        # Calculate updated readability
        new_metrics = metrics_service.calculate_metrics(new_content)
        draft.readability_score = new_metrics.readability_score

        db.commit()
        db.refresh(draft)

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
            raise HTTPException(status_code=404, detail="Suggestion does not belong to this draft.")

        suggestion.status = "REJECTED"
        db.commit()

        return {
            "success": True,
            "suggestion_id": suggestion.id,
            "status": "REJECTED",
            "revised_content": draft.revised_content
        }

    def accept_all_suggestions(self, db: Session, draft_id: str) -> Dict[str, Any]:
        draft = self.get_draft(db, draft_id)
        pending = db.query(WritingSuggestion).filter(
            WritingSuggestion.draft_id == draft.id,
            WritingSuggestion.status.in_(["pending", "PENDING"])
        ).all()

        current_content = draft.revised_content
        applied_count = 0
        skipped_conflicts = 0

        for sugg in pending:
            replacement = sugg.suggested_text or sugg.suggested_rewrite or ""
            if replacement.startswith("(") and replacement.endswith(")"):
                if "remove" in replacement.lower() or "omit" in replacement.lower():
                    replacement = ""
                else:
                    sugg.status = "ACCEPTED"
                    continue

            new_content, success, _ = replace_text_safely(
                current_content,
                sugg.original_text,
                replacement
            )
            if success:
                current_content = new_content
                sugg.status = "ACCEPTED"
                applied_count += 1
            else:
                skipped_conflicts += 1

        draft.revised_content = current_content
        draft.word_count = len(current_content.split())
        new_metrics = metrics_service.calculate_metrics(current_content)
        draft.readability_score = new_metrics.readability_score

        db.commit()
        db.refresh(draft)

        return {
            "success": True,
            "applied_count": applied_count,
            "skipped_conflicts": skipped_conflicts,
            "revised_content": draft.revised_content,
            "metrics": new_metrics.model_dump()
        }

    def compare_draft(self, db: Session, draft_id: str) -> DraftCompareResponse:
        draft = self.get_draft(db, draft_id)
        orig_metrics = metrics_service.calculate_metrics(draft.original_content)
        rev_metrics = metrics_service.calculate_metrics(draft.revised_content)

        suggs = db.query(WritingSuggestion).filter(WritingSuggestion.draft_id == draft.id).all()
        accepted = sum(1 for s in suggs if s.status.upper() == "ACCEPTED")
        rejected = sum(1 for s in suggs if s.status.upper() == "REJECTED")
        pending = sum(1 for s in suggs if s.status.upper() == "PENDING")

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

suggestion_service = SuggestionService()

