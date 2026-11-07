from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import WritingDraft, WritingSuggestion
from backend.app.schemas.writing import DraftCreate, DraftUpdate, WritingAnalysisRequest, WritingAnalysisResponse, WritingIssue, DraftCompareResponse
from backend.app.services.writing_analysis_service import writing_analysis_service
from backend.app.services.metrics_service import metrics_service
from backend.app.utils.text_processing import replace_text_safely
from backend.app.services.version_control.version_service import version_service

import io
import re
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from backend.app.models.base import WritingDraft, WritingSuggestion, ResearchProject, ResearchBrief, Source, EditorialStyleProfile
from backend.app.schemas.writing import (
    DraftCreate,
    DraftUpdate,
    WritingAnalysisRequest,
    WritingAnalysisResponse,
    WritingIssue,
    DraftCompareResponse,
    DraftGenerateRequest,
    DraftGenerateResponse,
    DraftSection,
    SelectionRewriteRequest,
    SelectionRewriteResponse,
    ResearchGroundingAuditResponse,
    ClaimVerification,
    DraftExportResponse
)
from backend.app.services.writing_analysis_service import writing_analysis_service
from backend.app.services.metrics_service import metrics_service
from backend.app.services.ai_service import ai_service
from backend.app.utils.text_processing import replace_text_safely, split_into_sentences
from backend.app.services.version_control.version_service import version_service

class WritingService:
    def create_draft(self, db: Session, data: DraftCreate, organization_id: Optional[str] = None, user_id: Optional[str] = None) -> WritingDraft:
        target_org_id = organization_id
        if data.project_id and not target_org_id:
            proj = db.query(ResearchProject).filter(ResearchProject.id == data.project_id).first()
            if proj:
                target_org_id = proj.organization_id

        word_count = 0
        readability_score = None
        if data.original_content:
            metrics = metrics_service.calculate_metrics(data.original_content)
            word_count = metrics.word_count
            readability_score = metrics.readability_score

        draft = WritingDraft(
            organization_id=target_org_id,
            project_id=data.project_id,
            brief_id=data.brief_id,
            title=data.title.strip(),
            content_type=data.content_type or "editorial_analysis",
            target_audience=data.target_audience or "Founders, builders, and operators",
            tone=data.tone or "Authoritative, analytical, objective",
            desired_length=data.desired_length or 800,
            style_profile_id=data.style_profile_id,
            author_id=user_id,
            original_content=data.original_content,
            revised_content=data.original_content,
            word_count=word_count,
            readability_score=readability_score,
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
                change_summary="Initial draft creation",
                user_id=user_id,
                org_id=draft.organization_id
            )
        except Exception as e:
            pass

        return draft

    def get_drafts(
        self,
        db: Session,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WritingDraft]:
        query = db.query(WritingDraft)

        if organization_id:
            query = query.filter(
                or_(
                    WritingDraft.organization_id == organization_id,
                    WritingDraft.organization_id == None
                )
            )

        if project_id:
            query = query.filter(WritingDraft.project_id == project_id)

        if status:
            query = query.filter(WritingDraft.status == status)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    WritingDraft.title.ilike(term),
                    WritingDraft.revised_content.ilike(term)
                )
            )

        return query.order_by(WritingDraft.updated_at.desc(), WritingDraft.created_at.desc()).offset(skip).limit(limit).all()

    def get_draft(self, db: Session, draft_id: str) -> WritingDraft:
        draft = db.query(WritingDraft).filter(WritingDraft.id == draft_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail="Writing draft not found.")
        return draft

    def delete_draft(self, db: Session, draft_id: str) -> bool:
        draft = self.get_draft(db, draft_id)
        db.delete(draft)
        db.commit()
        return True

    def update_draft(self, db: Session, draft_id: str, data: DraftUpdate, user_id: Optional[str] = None) -> WritingDraft:
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
        if data.content_type is not None:
            draft.content_type = data.content_type
        if data.target_audience is not None:
            draft.target_audience = data.target_audience
        if data.tone is not None:
            draft.tone = data.tone
        if data.desired_length is not None:
            draft.desired_length = data.desired_length
        if data.style_profile_id is not None:
            draft.style_profile_id = data.style_profile_id

        # Update metrics
        if draft.revised_content:
            metrics = metrics_service.calculate_metrics(draft.revised_content)
            draft.word_count = metrics.word_count
            draft.readability_score = metrics.readability_score

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
                    change_summary="Manual draft edit / autosave",
                    user_id=user_id,
                    org_id=draft.organization_id
                )
            except Exception:
                pass

        return draft

    def duplicate_draft(self, db: Session, draft_id: str, user_id: Optional[str] = None) -> WritingDraft:
        original = self.get_draft(db, draft_id)
        new_draft = WritingDraft(
            organization_id=original.organization_id,
            project_id=original.project_id,
            brief_id=original.brief_id,
            title=f"Copy of {original.title}",
            content_type=original.content_type,
            target_audience=original.target_audience,
            tone=original.tone,
            desired_length=original.desired_length,
            style_profile_id=original.style_profile_id,
            author_id=user_id,
            original_content=original.original_content,
            revised_content=original.revised_content,
            final_content=original.final_content,
            word_count=original.word_count,
            readability_score=original.readability_score,
            status="draft"
        )
        db.add(new_draft)
        db.commit()
        db.refresh(new_draft)

        try:
            version_service.create_snapshot(
                db=db,
                document_type="WRITING_DRAFT",
                document_id=new_draft.id,
                content=new_draft.revised_content,
                title=new_draft.title,
                change_type="INITIAL",
                change_summary=f"Duplicated from draft {original.id}",
                user_id=user_id,
                org_id=new_draft.organization_id
            )
        except Exception:
            pass

        return new_draft

    async def generate_editorial_draft(
        self,
        db: Session,
        req: DraftGenerateRequest,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> DraftGenerateResponse:
        brief_data = {}
        sources_data = []
        target_project_id = req.project_id

        # 1. Resolve research brief and connected sources if provided
        if req.brief_id:
            brief_obj = db.query(ResearchBrief).filter(ResearchBrief.id == req.brief_id).first()
            if brief_obj:
                target_project_id = target_project_id or brief_obj.project_id
                brief_data = {
                    "title": brief_obj.title,
                    "executive_summary": brief_obj.executive_summary,
                    "key_developments": brief_obj.key_developments or [],
                    "strategic_implications": brief_obj.strategic_implications or [],
                    "recommended_angle": brief_obj.recommended_angle or {}
                }
        elif req.project_id:
            brief_obj = db.query(ResearchBrief).filter(
                ResearchBrief.project_id == req.project_id
            ).order_by(ResearchBrief.created_at.desc()).first()
            if brief_obj:
                brief_data = {
                    "title": brief_obj.title,
                    "executive_summary": brief_obj.executive_summary,
                    "key_developments": brief_obj.key_developments or [],
                    "strategic_implications": brief_obj.strategic_implications or [],
                    "recommended_angle": brief_obj.recommended_angle or {}
                }

        if target_project_id:
            proj_sources = db.query(Source).filter(
                Source.project_id == target_project_id,
                Source.extraction_status == "completed"
            ).all()
            for s in proj_sources:
                sources_data.append({
                    "id": s.id,
                    "title": s.title,
                    "url": s.url or s.original_url or "",
                    "author": s.author or "",
                    "extracted_content": s.extracted_content or ""
                })

        # 2. Resolve style profile if requested
        style_dict = {}
        if req.style_profile_id:
            style_obj = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == req.style_profile_id).first()
            if style_obj:
                style_dict = {
                    "name": style_obj.name,
                    "publication_name": style_obj.publication_name,
                    "tone": style_obj.tone,
                    "target_audience": style_obj.target_audience,
                    "max_sentence_length": style_obj.max_sentence_length,
                    "preferred_sentence_length": style_obj.preferred_sentence_length,
                    "max_paragraph_length": style_obj.max_paragraph_length
                }

        effective_topic = req.topic or brief_data.get("title") or "Frontier Artificial Intelligence Architecture"

        # 3. Call AI Service synthesis
        generated = await ai_service.generate_editorial_draft(
            topic=effective_topic,
            brief_data=brief_data,
            sources=sources_data,
            content_type=req.content_type,
            target_audience=req.target_audience,
            tone=req.tone,
            style_profile=style_dict,
            desired_length=req.desired_length,
            keywords=req.keywords,
            editorial_instructions=req.editorial_instructions
        )

        full_content = generated["full_content"]
        metrics = metrics_service.calculate_metrics(full_content)

        # 4. Save into database
        draft = WritingDraft(
            organization_id=organization_id,
            project_id=target_project_id,
            brief_id=req.brief_id,
            title=generated["headline"],
            content_type=req.content_type,
            target_audience=req.target_audience,
            tone=req.tone,
            desired_length=req.desired_length,
            style_profile_id=req.style_profile_id,
            author_id=user_id,
            original_content=full_content,
            revised_content=full_content,
            word_count=metrics.word_count,
            readability_score=metrics.readability_score,
            research_grounding_score=generated.get("grounding_score", 100.0),
            unsupported_claims_count=len(generated.get("unsupported_claims_warning", [])),
            status="draft"
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        # 5. Snapshot version
        try:
            version_service.create_snapshot(
                db=db,
                document_type="WRITING_DRAFT",
                document_id=draft.id,
                content=draft.revised_content,
                title=draft.title,
                change_type="INITIAL",
                change_summary=f"AI Generated draft from research ({req.content_type})",
                user_id=user_id,
                org_id=draft.organization_id
            )
        except Exception:
            pass

        return DraftGenerateResponse(
            draft_id=draft.id,
            title=draft.title,
            headline=generated["headline"],
            subtitle=generated.get("subtitle", ""),
            content=full_content,
            content_type=req.content_type,
            word_count=metrics.word_count,
            sections=[
                DraftSection(
                    heading=s.get("heading", ""),
                    content=s.get("content", ""),
                    supporting_evidence_ids=s.get("supporting_evidence_ids", [])
                ) for s in generated.get("sections", [])
            ],
            key_takeaways=generated.get("key_takeaways", []),
            evidence_citations=generated.get("evidence_citations", []),
            unsupported_claims_warning=generated.get("unsupported_claims_warning", []),
            grounding_score=generated.get("grounding_score", 100.0),
            prompt_version=generated.get("prompt_version", "v1.0.0"),
            estimated_cost_usd=generated.get("estimated_cost_usd", 0.0)
        )

    async def rewrite_selection(self, db: Session, req: SelectionRewriteRequest) -> SelectionRewriteResponse:
        style_dict = {}
        if req.style_profile_id:
            style_obj = db.query(EditorialStyleProfile).filter(EditorialStyleProfile.id == req.style_profile_id).first()
            if style_obj:
                style_dict = {
                    "tone": style_obj.tone,
                    "target_audience": style_obj.target_audience
                }

        res = await ai_service.rewrite_selection(
            selected_text=req.selected_text,
            operation=req.operation,
            surrounding_context=req.surrounding_context,
            target_tone=req.target_tone,
            style_profile=style_dict,
            custom_instructions=req.custom_instructions
        )

        return SelectionRewriteResponse(
            operation=req.operation,
            original_text=res["original_text"],
            rewritten_text=res["rewritten_text"],
            explanation=res["explanation"]
        )

    def audit_research_grounding(self, db: Session, draft_id: str) -> ResearchGroundingAuditResponse:
        from backend.app.services.ai.claim_verification_service import claim_verification_service

        draft = self.get_draft(db, draft_id)

        # Gather reference corpus from connected project/brief
        brief = None
        sources = []
        if draft.brief_id:
            brief = db.query(ResearchBrief).filter(ResearchBrief.id == draft.brief_id).first()
        elif draft.project_id:
            brief = db.query(ResearchBrief).filter(
                ResearchBrief.project_id == draft.project_id
            ).order_by(ResearchBrief.created_at.desc()).first()

        if draft.project_id:
            sources = db.query(Source).filter(
                Source.project_id == draft.project_id,
                Source.extraction_status == "completed"
            ).all()

        source_dicts = [
            {
                "id": s.id,
                "title": s.title,
                "url": s.url,
                "extracted_content": s.extracted_content or s.raw_content or s.summary or ""
            }
            for s in sources
        ]
        if brief:
            source_dicts.append({
                "id": brief.id,
                "title": brief.title,
                "url": None,
                "extracted_content": f"{brief.title} {brief.executive_summary} " + " ".join(brief.key_developments or [])
            })

        # Run Phase 8 Evidence Grounding & Citation Validation Engine
        audit_rep = claim_verification_service.audit_draft(
            draft.revised_content or draft.original_content,
            source_dicts,
            project_id=draft.project_id
        )

        claims: List[ClaimVerification] = []
        source_title_map = {s.get("id"): s.get("title") for s in source_dicts}
        source_url_map = {s.get("id"): s.get("url") for s in source_dicts}

        for c in audit_rep.claims:
            if c.verification_status.value == "SUPPORTED":
                cls_val = "grounded"
            elif c.verification_status.value == "PARTIALLY_SUPPORTED":
                cls_val = "inferred"
            elif c.verification_status.value == "CONTRADICTED":
                cls_val = "contradictory"
            elif c.verification_status.value == "UNSUPPORTED":
                cls_val = "unsupported"
            else:
                cls_val = "inferred"

            claims.append(ClaimVerification(
                claim_text=c.claim_text,
                classification=cls_val,
                verification_status=c.verification_status.value,
                citation_tag=c.citation_tag,
                citation_integrity=c.citation_integrity.value,
                supporting_excerpt=c.supporting_excerpt,
                source_title=source_title_map.get(c.referenced_source_id, "Research Archive") if c.referenced_source_id else None,
                source_url=source_url_map.get(c.referenced_source_id) if c.referenced_source_id else None,
                confidence=c.confidence_score,
                warning=c.warning_message,
                remediation_suggestion=c.remediation_suggestion
            ))

        grounding_score_pct = round(audit_rep.grounding_score * 100, 1)

        recommendations = []
        if audit_rep.contradiction_warnings:
            recommendations.append(f"Critical: {len(audit_rep.contradiction_warnings)} potential factual contradiction(s) flagged against source documents.")
        if audit_rep.missing_citations:
            recommendations.append(f"{len(audit_rep.missing_citations)} statement(s) with statistics or quotes are missing explicit citation tags.")
        if audit_rep.unsupported_count > 0:
            recommendations.append(f"Found {audit_rep.unsupported_count} statement(s) lacking direct evidence citations. Consider attaching quotes or verifying numbers.")
        if grounding_score_pct >= 85:
            recommendations.append("High factual integrity: Over 85% of factual statements are substantiated by research archives.")
        else:
            recommendations.append("Grounding score is below editorial benchmark (85%). Ingest additional sources or run selection rewrite to strengthen factual backing.")

        # Persist updated metrics on draft
        draft.research_grounding_score = grounding_score_pct
        draft.unsupported_claims_count = audit_rep.unsupported_count
        db.commit()

        return ResearchGroundingAuditResponse(
            draft_id=draft.id,
            grounding_score=grounding_score_pct,
            total_claims=audit_rep.total_claims,
            grounded_count=audit_rep.supported_count,
            inferred_count=audit_rep.partially_supported_count + audit_rep.not_verifiable_count,
            unsupported_count=audit_rep.unsupported_count,
            contradiction_count=audit_rep.contradicted_count,
            citation_accuracy=audit_rep.citation_accuracy,
            claims=claims,
            actionable_recommendations=recommendations,
            unsupported_claims_summary=audit_rep.unsupported_claims_summary,
            missing_citations=audit_rep.missing_citations
        )

    def export_draft(self, db: Session, draft_id: str, export_format: str) -> Tuple[bytes, str, str]:
        draft = self.get_draft(db, draft_id)
        fmt = (export_format or "markdown").lower()
        title_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', draft.title.lower()).strip('_') or "editorial_article"
        content = draft.revised_content or draft.original_content

        if fmt in ("md", "markdown"):
            filename = f"{title_slug}.md"
            header = (
                f"---\n"
                f"title: \"{draft.title}\"\n"
                f"status: \"{draft.status}\"\n"
                f"word_count: {draft.word_count}\n"
                f"exported_at: \"{draft.updated_at.isoformat()}\"\n"
                f"---\n\n"
            )
            data = (header + content).encode("utf-8")
            return data, filename, "text/markdown; charset=utf-8"

        elif fmt in ("txt", "text", "plain"):
            filename = f"{title_slug}.txt"
            # Strip markdown formatting for pure plain text
            clean_txt = re.sub(r'#+\s*', '', content)
            clean_txt = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', clean_txt)
            clean_txt = f"{draft.title.upper()}\n{'=' * len(draft.title)}\n\n{clean_txt}"
            return clean_txt.encode("utf-8"), filename, "text/plain; charset=utf-8"

        elif fmt in ("docx", "word"):
            import docx
            from docx.shared import Pt, Inches, RGBColor

            doc = docx.Document()
            title_p = doc.add_paragraph()
            title_run = title_p.add_run(draft.title)
            title_run.font.size = Pt(22)
            title_run.font.bold = True

            meta_p = doc.add_paragraph()
            meta_run = meta_p.add_run(f"Word Count: {draft.word_count} | Status: {draft.status} | Grounding Score: {draft.research_grounding_score or 100}%")
            meta_run.font.size = Pt(9)
            meta_run.font.color.rgb = RGBColor(120, 120, 120)

            doc.add_paragraph()  # Spacer

            for block in content.split("\n\n"):
                b = block.strip()
                if not b:
                    continue
                if b.startswith("# "):
                    h = doc.add_heading(b[2:], level=1)
                elif b.startswith("## "):
                    h = doc.add_heading(b[3:], level=2)
                elif b.startswith("### "):
                    h = doc.add_heading(b[4:], level=3)
                elif b.startswith("- ") or b.startswith("* "):
                    doc.add_paragraph(b[2:], style='List Bullet')
                elif re.match(r'^\d+\.\s', b):
                    clean_b = re.sub(r'^\d+\.\s', '', b)
                    doc.add_paragraph(clean_b, style='List Number')
                else:
                    doc.add_paragraph(b)

            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            return buf.getvalue(), f"{title_slug}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        elif fmt in ("html", "htm"):
            filename = f"{title_slug}.html"
            html_content = (
                f"<!DOCTYPE html>\n<html>\n<head>\n"
                f"<meta charset='utf-8'>\n<title>{draft.title}</title>\n"
                f"<style>\n"
                f"body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; "
                f"max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1e293b; }}\n"
                f"h1 {{ font-size: 28px; margin-bottom: 8px; color: #0f172a; }}\n"
                f"h2 {{ font-size: 20px; margin-top: 32px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}\n"
                f"p {{ margin: 16px 0; }}\n"
                f".meta {{ color: #64748b; font-size: 13px; margin-bottom: 24px; }}\n"
                f"</style>\n</head>\n<body>\n"
                f"<h1>{draft.title}</h1>\n"
                f"<div class='meta'>Word count: {draft.word_count} | Grounding: {draft.research_grounding_score or 100}%</div>\n"
                f"<div>{content.replace(chr(10), '<br>')}</div>\n"
                f"</body>\n</html>"
            )
            return html_content.encode("utf-8"), filename, "text/html; charset=utf-8"

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format '{export_format}'. Supported formats: markdown, txt, docx, html.")


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
