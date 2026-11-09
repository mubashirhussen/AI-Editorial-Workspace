"""
Seed Demonstration Environment for FDE Assessment Demonstration
AI Editorial Workspace - Phase 16

Creates a clean, reproducible demonstration environment using non-sensitive,
realistic research sources and editorial drafts.
Usage:
    python backend/scripts/seed_demo_environment.py [--reset]
"""

import sys
import os
import uuid
from datetime import datetime

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models.base import (
    User, Organization, OrganizationMembership, ResearchProject,
    Source, SourceAnalysis, ResearchBrief, WritingDraft,
    EditorialVersion, EditorialOutput, EditorialReview
)

DEMO_ORG_SLUG = "demo-this-week-in-ai"
DEMO_USER_EMAIL = "demo_editor@thisweekin.ai"


def seed_demo_environment(reset: bool = False):
    """Provisions a pristine, reproducible demonstration dataset."""
    db = SessionLocal()
    try:
        print("[*] Checking existing demonstration records...")
        existing_org = db.query(Organization).filter(Organization.slug == DEMO_ORG_SLUG).first()

        if existing_org:
            if reset:
                print("[!] Resetting existing demonstration environment...")
                # Fetch projects to clean children
                proj_ids = [p.id for p in db.query(ResearchProject).filter(ResearchProject.organization_id == existing_org.id).all()]
                if proj_ids:
                    # Clean editorial reviews
                    ed_ids = [e.id for e in db.query(EditorialOutput).filter(EditorialOutput.project_id.in_(proj_ids)).all()]
                    if ed_ids:
                        db.query(EditorialReview).filter(EditorialReview.editorial_id.in_(ed_ids)).delete(synchronize_session=False)
                    db.query(EditorialOutput).filter(EditorialOutput.project_id.in_(proj_ids)).delete(synchronize_session=False)
                    db.query(EditorialVersion).filter(EditorialVersion.organization_id == existing_org.id).delete(synchronize_session=False)
                    db.query(WritingDraft).filter(WritingDraft.organization_id == existing_org.id).delete(synchronize_session=False)
                    db.query(ResearchBrief).filter(ResearchBrief.project_id.in_(proj_ids)).delete(synchronize_session=False)
                    
                    src_ids = [s.id for s in db.query(Source).filter(Source.project_id.in_(proj_ids)).all()]
                    if src_ids:
                        db.query(SourceAnalysis).filter(SourceAnalysis.source_id.in_(src_ids)).delete(synchronize_session=False)
                    db.query(Source).filter(Source.project_id.in_(proj_ids)).delete(synchronize_session=False)
                    db.query(ResearchProject).filter(ResearchProject.id.in_(proj_ids)).delete(synchronize_session=False)
                
                db.query(OrganizationMembership).filter(OrganizationMembership.organization_id == existing_org.id).delete(synchronize_session=False)
                db.query(Organization).filter(Organization.id == existing_org.id).delete(synchronize_session=False)
                db.commit()
                print("[+] Existing demo records successfully purged.")
            else:
                print("[+] Demonstration environment already provisioned. Run with --reset to re-create.")
                return

        print("[*] Creating Demonstration Organization & User...")
        # 1. Organization
        demo_org = Organization(
            id=str(uuid.uuid4()),
            name="This Week in AI — Editorial Desk",
            slug=DEMO_ORG_SLUG
        )
        db.add(demo_org)
        db.flush()

        # 2. User
        demo_user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if not demo_user:
            demo_user = User(
                id=str(uuid.uuid4()),
                email=DEMO_USER_EMAIL,
                hashed_password=hash_password("DemoEditor2026!"),
                full_name="Alex Vance (Staff Editor)",
                is_active=True,
                is_verified=True
            )
            db.add(demo_user)
            db.flush()

        # 3. Membership
        membership = OrganizationMembership(
            id=str(uuid.uuid4()),
            organization_id=demo_org.id,
            user_id=demo_user.id,
            role="OWNER",
            joined_at=datetime.utcnow()
        )
        db.add(membership)

        # 4. Research Project
        demo_project = ResearchProject(
            id=str(uuid.uuid4()),
            organization_id=demo_org.id,
            title="Autonomous AI Reasoning & Factual Grounding",
            description="Evaluating open-weights reasoning architectures, context protocols, and verified citation pipelines for newsletter publishing.",
            status="ACTIVE"
        )
        db.add(demo_project)
        db.flush()

        # 5. Legitimate Research Sources
        sources_meta = [
            {
                "title": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning",
                "url": "https://arxiv.org/abs/2501.12948",
                "source_type": "URL",
                "content": (
                    "DeepSeek-R1 introduces pure reinforcement learning without supervised fine-tuning (SFT) as a primary "
                    "mechanism to unlock reasoning capabilities in large language models. The architecture demonstrates "
                    "self-evolution, reflective thinking, and autonomous verification of mathematical proofs. Empirical benchmarks "
                    "achieve 79.8% Pass@1 on AIME 2024 and 97.3% on MATH-500, rivaling leading closed commercial frontier models."
                )
            },
            {
                "title": "Model Context Protocol: Standardizing AI Integration",
                "url": "https://www.anthropic.com/news/model-context-protocol",
                "source_type": "URL",
                "content": (
                    "The Model Context Protocol (MCP) is an open standard designed to solve the isolated context problem in AI systems. "
                    "MCP establishes a unified JSON-RPC protocol allowing client assistants to discover external tools, inspect "
                    "versioned resources, and execute deterministic database prompts across enterprise environments without vendor lock-in."
                )
            },
            {
                "title": "Attention Is All You Need: The Foundation of Modern Transformers",
                "url": "https://arxiv.org/abs/1706.03762",
                "source_type": "URL",
                "content": (
                    "The dominant sequence transduction models rely on complex recurrent or convolutional neural networks. "
                    "The Transformer architecture replaces recurrent layers entirely with multi-head self-attention mechanisms. "
                    "Experiments on WMT 2014 English-to-German translation demonstrate state-of-the-art BLEU scores of 28.4 while "
                    "requiring significantly less training time."
                )
            }
        ]

        created_sources = []
        for s in sources_meta:
            src = Source(
                id=str(uuid.uuid4()),
                project_id=demo_project.id,
                title=s["title"],
                url=s["url"],
                source_type=s["source_type"],
                raw_content=s["content"],
                extracted_content=s["content"],
                summary=s["content"][:200] + "...",
                author="Research Authors",
                extraction_status="COMPLETED"
            )
            db.add(src)
            db.flush()
            created_sources.append(src)

            # Add source analysis
            analysis = SourceAnalysis(
                id=str(uuid.uuid4()),
                source_id=src.id,
                key_points=["Artificial Intelligence", "Empirical Evaluation", "Transformer Architecture"],
                reported_facts=[s["content"][:100]],
                important_claims=[s["content"][:100]],
                summary=s["content"][:150]
            )
            db.add(analysis)

        # 6. Research Brief
        demo_brief = ResearchBrief(
            id=str(uuid.uuid4()),
            project_id=demo_project.id,
            title="Frontier Reasoning & Factual Verification Architecture",
            executive_summary=(
                "Recent advancements in open-weights reasoning (DeepSeek-R1) and contextual protocol standards (MCP) "
                "represent a fundamental shift for technical media publishing. Rather than relying on closed vendor APIs, "
                "editorial teams can now deploy deterministic, self-verifying pipelines that reduce factual hallucinations below 2.4% "
                "while maintaining full cryptographic citation provenance."
            ),
            key_developments=[
                "Pure reinforcement learning unlocks reasoning behaviors without massive human demonstration datasets.",
                "Open protocols like MCP eliminate bespoke integration code between editors and external knowledge bases.",
                "Attention-based transformer backbones remain the universal foundation for all reasoning and synthesis tasks."
            ],
            strategic_implications={
                "media_workflow": "Technical publications can automate initial source synthesis without sacrificing editorial voice.",
                "trust_boundary": "Traceable citations [1], [2] are non-negotiable for enterprise technical trust."
            },
            newsletter_angles=[
                "Why Enterprise AI Demands Verified Citations Over Fluent Prose",
                "The Open Weights Advantage: How Self-Correction Changes Editorial Verification"
            ],
            source_references=[
                {"id": s.id, "title": s.title, "url": s.url} for s in created_sources
            ]
        )
        db.add(demo_brief)
        db.flush()

        # 7. Writing Draft (Baseline Revision 1)
        raw_draft_content = (
            "In order to understand the significance of recent reasoning benchmarks, it is important to note that "
            "a large number of tests were conducted by the research team. Due to the fact that retrieval-augmented "
            "generation relies on embeddings and vector database search, basically the architecture has the ability "
            "to process unstructured technical documentation with high throughput.\n\n"
            "Furthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous "
            "subordinate clauses and technical parameters without giving the reader a single moment of pause or cognitive respite, "
            "which obviously makes it exceedingly difficult to parse in a fast-paced executive editorial environment.\n\n"
            "At the end of the day, founders who implement verifiable evaluation metrics will dominate the commercial landscape, "
            "while fragile wrapper applications will face commoditization."
        )

        revised_draft_content = (
            "Recent reasoning benchmarks demonstrate a structural inflection point for technical media. "
            "DeepSeek-R1 achieves a 79.8% Pass@1 on AIME 2024 through pure reinforcement learning, proving that "
            "models can self-correct logical deduction without human-supervised fine-tuning [1].\n\n"
            "Simultaneously, the Model Context Protocol (MCP) standardizes how AI assistants interface with external databases [2]. "
            "Together, these advancements enable newsrooms to replace brittle wrappers with verifiable, evidence-grounded pipelines. "
            "Founders who prioritize empirical evaluation metrics will dominate the editorial landscape."
        )

        demo_draft = WritingDraft(
            id=str(uuid.uuid4()),
            organization_id=demo_org.id,
            project_id=demo_project.id,
            brief_id=demo_brief.id,
            title="Why Enterprise AI Demands Verified Citations Over Fluent Prose",
            original_content=raw_draft_content,
            revised_content=revised_draft_content,
            content_type="NEWSLETTER",
            word_count=len(revised_draft_content.split()),
            readability_score=68.5,
            research_grounding_score=94.2,
            status="IN_REVIEW"
        )
        db.add(demo_draft)
        db.flush()

        # 8. Version Snapshots (Version 1 & Version 2)
        v1 = EditorialVersion(
            id=str(uuid.uuid4()),
            organization_id=demo_org.id,
            document_type="WRITING_DRAFT",
            document_id=demo_draft.id,
            version_number=1,
            title="Baseline Unaudited Draft",
            content_snapshot=raw_draft_content,
            change_summary="Initial raw draft with run-on sentences and passive voice.",
            change_type="INITIAL",
            created_by=demo_user.id
        )
        v2 = EditorialVersion(
            id=str(uuid.uuid4()),
            organization_id=demo_org.id,
            document_type="WRITING_DRAFT",
            document_id=demo_draft.id,
            version_number=2,
            title="Audited & Polished Draft (v2)",
            content_snapshot=revised_draft_content,
            change_summary="Applied Hemingway readability fixes and bound verified citations [1], [2].",
            change_type="AI_REVISION",
            created_by=demo_user.id
        )
        db.add_all([v1, v2])

        # 9. Editorial Output
        demo_output = EditorialOutput(
            id=str(uuid.uuid4()),
            project_id=demo_project.id,
            draft_id=demo_draft.id,
            title="This Week in AI — Edition #104: The Proof-First Architecture",
            headline="Why Enterprise AI Demands Verified Citations Over Fluent Prose",
            content=(
                "# Why Enterprise AI Demands Verified Citations Over Fluent Prose\n\n"
                "**By Alex Vance** | *This Week in AI — Editorial Brief*\n\n"
                "Recent reasoning benchmarks demonstrate a structural inflection point for technical media. "
                "DeepSeek-R1 achieves a 79.8% Pass@1 on AIME 2024 through pure reinforcement learning, proving that "
                "models can self-correct logical deduction without human-supervised fine-tuning [1].\n\n"
                "Simultaneously, the Model Context Protocol (MCP) standardizes how AI assistants interface with external databases [2]. "
                "Together, these advancements enable newsrooms to replace brittle wrappers with verifiable, evidence-grounded pipelines. "
                "Founders who prioritize empirical evaluation metrics will dominate the editorial landscape.\n\n"
                "### Key Editorial Takeaways\n"
                "- **Reasoning over Hype:** Autonomous self-correction is now achievable on open-weights infrastructure.\n"
                "- **Protocol Standardization:** MCP provides deterministic schemas for tool and data discovery.\n"
                "- **Citation Provenance:** Never publish AI-synthesized assertions without sentence-level evidence anchors.\n\n"
                "### References\n"
                "[1] DeepSeek-AI. *DeepSeek-R1 Technical Report*, arXiv:2501.12948 (2025).\n"
                "[2] Anthropic. *Model Context Protocol Specification*, anthropic.com (2024).\n"
                "[3] Vaswani et al. *Attention Is All You Need*, NeurIPS (2017).\n"
            ),
            word_count=182,
            source_references=[
                {"citation_id": "[1]", "title": "DeepSeek-R1 Technical Report", "url": "https://arxiv.org/abs/2501.12948"},
                {"citation_id": "[2]", "title": "Model Context Protocol Specification", "url": "https://www.anthropic.com/news/model-context-protocol"},
                {"citation_id": "[3]", "title": "Attention Is All You Need", "url": "https://arxiv.org/abs/1706.03762"}
            ],
            status="PUBLISHED"
        )
        db.add(demo_output)
        db.flush()

        # 10. Peer Review
        demo_review = EditorialReview(
            id=str(uuid.uuid4()),
            editorial_id=demo_output.id,
            reviewer_name="Elena Rostova (Executive Editor)",
            review_status="APPROVED",
            overall_feedback="Superb technical clarity. Citations are fully grounded and traceable to source literature.",
            reviewed_at=datetime.utcnow()
        )
        db.add(demo_review)

        db.commit()
        print("\n" + "=" * 65)
        print(" DEMONSTRATION ENVIRONMENT PROVISIONED SUCCESSFULLY")
        print("=" * 65)
        print(f" Organization: {demo_org.name} ({demo_org.slug})")
        print(f" User Email:   {demo_user.email}")
        print(f" Password:     DemoEditor2026!")
        print(f" Project:      {demo_project.title}")
        print(f" Sources (3):  DeepSeek-R1, MCP Specification, Attention Paper")
        print(f" Brief:        {demo_brief.title}")
        print(f" Draft:        {demo_draft.title}")
        print(f" Versions (2): Version 1 (Baseline) & Version 2 (Audited)")
        print(f" Edition:      {demo_output.title} (Status: APPROVED)")
        print("=" * 65 + "\n")

    except Exception as e:
        db.rollback()
        print(f"[!] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    should_reset = "--reset" in sys.argv or "-r" in sys.argv
    seed_demo_environment(reset=should_reset)
