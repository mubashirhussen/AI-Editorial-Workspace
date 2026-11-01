import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.base import ResearchBrief, ResearchProject
from backend.app.schemas.editorial import HeadlineOption, HeadlineGenerateResponse, HeadlineGenerateRequest
from backend.app.services.ai_service import ai_service

logger = logging.getLogger("editorial_workspace")

class HeadlineService:
    """
    Generates at least five professional, non-clickbait headline options tailored to 
    an editorial angle and target executive audience.
    """

    async def generate_headlines(self, db: Session, req: HeadlineGenerateRequest) -> HeadlineGenerateResponse:
        project = db.query(ResearchProject).filter(ResearchProject.id == req.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with ID '{req.project_id}' not found.")

        # Find brief
        query = db.query(ResearchBrief).filter(ResearchBrief.project_id == req.project_id)
        if req.research_brief_id:
            query = query.filter(ResearchBrief.id == req.research_brief_id)
        brief = query.first()

        if not brief:
            raise HTTPException(
                status_code=400, 
                detail="A synthesized research brief is required before generating headline angles."
            )

        # Cross-project brief ownership check
        if brief.project_id != project.id:
            raise HTTPException(
                status_code=400,
                detail="Specified research brief does not belong to the selected project."
            )

        audience = req.audience or "founders, builders, and operators"
        target_angle = req.editorial_angle or ""
        tone = req.tone or "Newsletter-style"

        # Check existing angles in brief
        existing_angles = brief.newsletter_angles or []
        recommended_angle = brief.recommended_angle or {}

        # Attempt AI generation if configured
        ai_headlines = await self._generate_ai_headlines(
            project_title=project.title,
            brief_content=brief.brief_content or {},
            existing_angles=existing_angles,
            audience=audience,
            target_angle=target_angle,
            tone=tone
        )

        if ai_headlines and len(ai_headlines) >= 5:
            return HeadlineGenerateResponse(
                project_id=project.id,
                headlines=ai_headlines,
                recommended_headline=ai_headlines[0].headline
            )

        # Robust Deterministic Synthesis Fallback (Guarantees >= 5 options)
        deterministic_headlines = self._generate_deterministic_headlines(
            project_title=project.title,
            brief=brief,
            target_angle=target_angle,
            audience=audience
        )

        return HeadlineGenerateResponse(
            project_id=project.id,
            headlines=deterministic_headlines,
            recommended_headline=deterministic_headlines[0].headline
        )

    async def _generate_ai_headlines(
        self,
        project_title: str,
        brief_content: Dict[str, Any],
        existing_angles: List[Dict[str, Any]],
        audience: str,
        target_angle: str,
        tone: str
    ) -> Optional[List[HeadlineOption]]:
        if not ai_service.is_configured:
            return None

        prompt = (
            f"Generate 5 distinct, high-impact editorial newsletter headlines based on this verified research.\n\n"
            f"PROJECT: {project_title}\n"
            f"AUDIENCE: {audience}\n"
            f"DESIRED TONE: {tone}\n"
            f"EDITORIAL ANGLE FOCUS: {target_angle or 'General industry breakthrough'}\n"
            f"RESEARCH SUMMARY: {brief_content.get('executive_summary', '')}\n\n"
            "CRITICAL EDITORIAL GUIDELINES:\n"
            "- Avoid clickbait, hype words, all-caps, and sensationalism.\n"
            "- Make headlines punchy, substantive, and relevant to decision-makers.\n"
            "- Provide 5 options covering: Technical Breakdown, Founder Strategy, Industry Shift, Operational Risk, Future Outlook.\n"
            "Format response as JSON array with keys: headline, editorial_angle, explanation."
        )

        try:
            res = await ai_service.call_llm_json(prompt)
            if isinstance(res, list) and len(res) >= 5:
                options = []
                for item in res[:6]:
                    if isinstance(item, dict) and "headline" in item:
                        options.append(HeadlineOption(
                            headline=item["headline"].strip('"'),
                            editorial_angle=item.get("editorial_angle", "Strategic Analysis"),
                            explanation=item.get("explanation", "Targets analytical executive interest.")
                        ))
                if len(options) >= 5:
                    return options
        except Exception as e:
            logger.warning(f"AI headline generation failed, falling back to deterministic synthesis: {e}")

        return None

    def _generate_deterministic_headlines(
        self,
        project_title: str,
        brief: ResearchBrief,
        target_angle: str,
        audience: str
    ) -> List[HeadlineOption]:
        headlines: List[HeadlineOption] = []
        clean_title = project_title.replace(" Research", "").replace(" Analysis", "").strip()

        # Extract context points
        angles = brief.newsletter_angles or []
        for a in angles:
            hl = a.get("headline")
            if hl and hl not in [h.headline for h in headlines]:
                headlines.append(HeadlineOption(
                    headline=hl,
                    editorial_angle=a.get("angle_pitch", a.get("target_audience", "Market Analysis")),
                    explanation=f"Directly derived from synthesized newsletter angle targeting {a.get('target_audience', audience)}."
                ))

        # Add curated strategic archetypes
        templates = [
            (
                f"Why {clean_title} Is Reshaping Production System Architecture",
                "Infrastructure & Architecture",
                "Appeals to CTOs and lead architects evaluating technical tradeoffs."
            ),
            (
                f"The Commercial Reality of {clean_title}: Cost, Latency, and Scalability",
                "Unit Economics & Operator Tradeoffs",
                "Targets operators balancing infrastructure budgets against model accuracy."
            ),
            (
                f"Beyond the Hype: What Builders Actually Need to Know About {clean_title}",
                "Pragmatic Implementation",
                "Cuts through vendor marketing to provide actionable deployment takeaways."
            ),
            (
                f"How Open Foundation Models Are Shifting Competitive Advantage in {clean_title}",
                "Founder Strategy & Moats",
                "Examines whether proprietary data moats withstand open-weight acceleration."
            ),
            (
                f"The Technical Bottlenecks Holding Back Enterprise {clean_title}",
                "Risk & Limitations",
                "Analyzes unaddressed failure modes, memory ceilings, and context drift."
            )
        ]

        for hl, angle, explanation in templates:
            if len(headlines) >= 5:
                break
            if hl not in [h.headline for h in headlines]:
                headlines.append(HeadlineOption(
                    headline=hl,
                    editorial_angle=angle,
                    explanation=explanation
                ))

        return headlines[:6]

headline_service = HeadlineService()

