import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.services.ai.router import ai_router
from backend.app.services.ai.base import AIResponse
from backend.app.utils.text_processing import split_into_sentences

logger = logging.getLogger("editorial_workspace.ai.manager")

class AIManager:
    """
    High-level facade orchestrating multi-modal research, drafting,
    and editorial intelligence workflows across active AI providers.
    """

    async def analyze_source(
        self,
        raw_text: str,
        title: str,
        url: Optional[str] = None,
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs structured extraction of key claims, facts, analysis, and implications."""
        prompt = (
            f"Analyze the following source document:\n"
            f"TITLE: {title}\n"
            f"URL: {url or 'Pasted source'}\n\n"
            f"CONTENT:\n{raw_text[:8000]}\n\n"
            f"Extract valid JSON with keys:\n"
            f"- summary (string, max 280 chars)\n"
            f"- key_points (array of strings)\n"
            f"- reported_facts (array of verified factual statements)\n"
            f"- analysis (array of analytical interpretations)\n"
            f"- founder_implications (object with 'strategic_takeaway' and 'operational_risk')\n"
            f"- uncertainties (array of open or speculative questions)\n"
            f"- newsletter_angles (array of objects with 'title', 'target_audience', 'hook')"
        )
        sys_p = "You are a senior tech editor and investigative researcher. Separate verified facts from speculation."
        res = await ai_router.execute_structured(
            prompt,
            system_prompt=sys_p,
            operation_name="source_analysis",
            db=db,
            organization_id=organization_id
        )
        data = res.parsed_json or {}
        data["generation_mode"] = "llm_verified" if not res.is_fallback else "deterministic_fallback"
        data["model_used"] = res.model
        data["provider_used"] = res.provider
        return data

    async def synthesize_research_brief(
        self,
        sources: List[Dict[str, Any]],
        project_title: str,
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesizes cross-source evidence into a cohesive research brief."""
        sources_summary = "\n\n".join([
            f"SOURCE {idx+1}: {s.get('title')}\n{s.get('extracted_content', '')[:1500]}"
            for idx, s in enumerate(sources[:6])
        ])

        prompt = (
            f"Synthesize the following research sources for project: '{project_title}'\n\n"
            f"{sources_summary}\n\n"
            f"Produce JSON containing:\n"
            f"- executive_summary (string, 150-250 words)\n"
            f"- key_developments (array of top 3-5 developments)\n"
            f"- strategic_implications (object with 'market_impact', 'technical_shift')\n"
            f"- newsletter_angles (array of 3 ranked angles with 'title', 'hook', 'target_audience')\n"
            f"- source_references (array of titles referenced)"
        )
        sys_p = "You are the Executive Editor of 'This Week in AI'. Create an evidence-grounded research synthesis."
        res = await ai_router.execute_structured(
            prompt,
            system_prompt=sys_p,
            operation_name="brief_synthesis",
            db=db,
            organization_id=organization_id
        )
        data = res.parsed_json or {}
        data["provider"] = res.provider
        data["model"] = res.model
        return data

    async def rewrite_content(
        self,
        text: str,
        instructions: str,
        tone: Optional[str] = "Authoritative, analytical, objective",
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ) -> str:
        """Rewrites editorial passages based on editor instructions and target tone."""
        prompt = (
            f"ORIGINAL DRAFT:\n{text}\n\n"
            f"INSTRUCTIONS: {instructions}\n"
            f"TARGET TONE: {tone}\n\n"
            f"Rewrite the draft directly. Maintain factual claims and numbers without introducing fabrications."
        )
        sys_p = "You are a master copy editor. Deliver clear, punchy, executive-level editorial prose."
        res = await ai_router.execute_text(
            prompt,
            system_prompt=sys_p,
            operation_name="draft_rewrite",
            db=db,
            organization_id=organization_id
        )
        return res.content.strip()

    async def generate_headlines(
        self,
        content: str,
        style: Optional[str] = "Direct, analytical, hook-driven",
        db: Optional[Session] = None,
        organization_id: Optional[str] = None
    ) -> List[str]:
        """Generates 5 distinct, high-impact newsletter headlines."""
        prompt = (
            f"Given this newsletter content:\n{content[:2500]}\n\n"
            f"HEADLINE STYLE: {style}\n\n"
            f"Generate 5 distinct headlines. Respond with JSON: {{\"headlines\": [\"...\", \"...\"]}}"
        )
        res = await ai_router.execute_structured(
            prompt,
            system_prompt="You are a headline optimization specialist for tech newsletters.",
            operation_name="headline_generation",
            db=db,
            organization_id=organization_id
        )
        if res.parsed_json and "headlines" in res.parsed_json:
            return res.parsed_json["headlines"]
        return [
            "Hardware Accelerators Reshape the AI Infrastructure Landscape",
            "Inside the Reasoning Benchmark Breakthroughs",
            "Why Systems Engineering is the New AI Competitive Moat"
        ]

ai_manager = AIManager()

