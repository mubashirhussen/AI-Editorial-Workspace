import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.base import (
    ResearchProject,
    Source,
    ResearchEntity,
    ResearchClaim,
    ResearchRelationship,
    ResearchContradiction,
    ResearchTrend
)
from backend.app.services.research_intelligence.entity_extractor import EntityExtractor
from backend.app.services.research_intelligence.claim_extractor import ClaimExtractor
from backend.app.services.research_intelligence.relationship_analyzer import RelationshipAnalyzer
from backend.app.services.research_intelligence.contradiction_detector import ContradictionDetector
from backend.app.services.research_intelligence.trend_detector import TrendDetector

logger = logging.getLogger(__name__)

class ResearchIntelligenceEngine:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.claim_extractor = ClaimExtractor()
        self.relationship_analyzer = RelationshipAnalyzer()
        self.contradiction_detector = ContradictionDetector()
        self.trend_detector = TrendDetector()

    def analyze_project(self, db: Session, project_id: str) -> Dict[str, Any]:
        """
        Executes end-to-end research intelligence discovery across all sources in a project.
        Extracts entities, claims, semantic relationships, cross-source contradictions,
        and trends, and persists them into the relational knowledge schema.
        """
        project = db.query(ResearchProject).filter(ResearchProject.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        sources = db.query(Source).filter(Source.project_id == project_id).all()
        if not sources:
            return {
                "project_id": project_id,
                "status": "completed",
                "entities_count": 0,
                "claims_count": 0,
                "relationships_count": 0,
                "contradictions_count": 0,
                "trends_count": 0,
                "summary": "No sources available for analysis in this project.",
                "created_at": datetime.now(timezone.utc)
            }

        # Clear existing intelligence cache for this project to ensure fresh, atomic analysis
        db.query(ResearchEntity).filter(ResearchEntity.project_id == project_id).delete()
        db.query(ResearchClaim).filter(ResearchClaim.project_id == project_id).delete()
        db.query(ResearchRelationship).filter(ResearchRelationship.project_id == project_id).delete()
        db.query(ResearchContradiction).filter(ResearchContradiction.project_id == project_id).delete()
        db.query(ResearchTrend).filter(ResearchTrend.project_id == project_id).delete()
        db.commit()

        # 1. Entity Extraction
        all_entities_data: List[Dict[str, Any]] = []
        for src in sources:
            content = src.extracted_content or src.raw_content or ""
            ents = self.entity_extractor.extract_entities(
                text=content,
                source_id=src.id,
                source_title=src.title
            )
            all_entities_data.extend(ents)

        # Persist entities
        db_entities: List[ResearchEntity] = []
        for ent in all_entities_data:
            re_obj = ResearchEntity(
                project_id=project_id,
                name=ent["name"],
                normalized_name=ent["normalized_name"],
                entity_type=ent["entity_type"],
                source_id=ent.get("source_id"),
                supporting_excerpt=ent.get("supporting_excerpt"),
                confidence=ent.get("confidence", 0.9),
                extraction_method=ent.get("extraction_method", "heuristic_nlp")
            )
            db.add(re_obj)
            db_entities.append(re_obj)
        db.commit()

        # 2. Claim Extraction
        all_claims_data: List[Dict[str, Any]] = []
        for src in sources:
            content = src.extracted_content or src.raw_content or ""
            claims = self.claim_extractor.extract_claims(
                text=content,
                source_id=src.id,
                source_title=src.title,
                known_entities=all_entities_data,
                publication_date=src.published_at
            )
            all_claims_data.extend(claims)

        # Persist claims
        db_claims: List[ResearchClaim] = []
        for c in all_claims_data:
            rc_obj = ResearchClaim(
                project_id=project_id,
                source_id=c["source_id"],
                claim_text=c["claim_text"],
                supporting_excerpt=c["supporting_excerpt"],
                evidence_classification=c["evidence_classification"],
                entity_references=c["entity_references"],
                confidence=c["confidence"],
                publication_date=c.get("publication_date")
            )
            db.add(rc_obj)
            db_claims.append(rc_obj)
        db.commit()

        # Update all_claims_data with database assigned IDs
        for i, rc_obj in enumerate(db_claims):
            all_claims_data[i]["id"] = rc_obj.id

        # 3. Relationship Analysis
        relationships_data = self.relationship_analyzer.analyze_relationships(
            claims=all_claims_data,
            entities=all_entities_data
        )

        db_relationships: List[ResearchRelationship] = []
        for r in relationships_data:
            rel_obj = ResearchRelationship(
                project_id=project_id,
                source_entity_name=r["source_entity_name"],
                target_entity_name=r["target_entity_name"],
                relationship_type=r["relationship_type"],
                source_id=r.get("source_id"),
                supporting_evidence=r["supporting_evidence"],
                confidence=r["confidence"],
                explanation=r["explanation"]
            )
            db.add(rel_obj)
            db_relationships.append(rel_obj)
        db.commit()

        # 4. Contradiction Detection
        contradictions_data = self.contradiction_detector.detect_contradictions(
            claims=all_claims_data
        )

        db_contradictions: List[ResearchContradiction] = []
        for cd in contradictions_data:
            cont_obj = ResearchContradiction(
                project_id=project_id,
                claim_a_id=cd.get("claim_a_id"),
                claim_b_id=cd.get("claim_b_id"),
                source_a_id=cd.get("source_a_id"),
                source_b_id=cd.get("source_b_id"),
                claim_a_text=cd["claim_a_text"],
                claim_b_text=cd["claim_b_text"],
                disagreement_nature=cd["disagreement_nature"],
                possible_explanations=cd["possible_explanations"],
                unresolved_questions=cd["unresolved_questions"]
            )
            db.add(cont_obj)
            db_contradictions.append(cont_obj)
        db.commit()

        # 5. Trend Detection
        sources_payload = [{"id": s.id, "title": s.title} for s in sources]
        trends_data = self.trend_detector.detect_trends(
            claims=all_claims_data,
            sources=sources_payload
        )

        db_trends: List[ResearchTrend] = []
        for td in trends_data:
            trend_obj = ResearchTrend(
                project_id=project_id,
                theme=td["theme"],
                category=td["category"],
                supporting_source_ids=td["supporting_source_ids"],
                evidence_summary=td["evidence_summary"],
                is_prediction=td["is_prediction"],
                confidence=td["confidence"]
            )
            db.add(trend_obj)
            db_trends.append(trend_obj)
        db.commit()

        summary_msg = (
            f"Extracted {len(db_entities)} entities, {len(db_claims)} evidentiary claims, "
            f"{len(db_relationships)} semantic relationships, {len(db_contradictions)} cross-source contradictions, "
            f"and {len(db_trends)} emerging corroborated trends."
        )

        return {
            "project_id": project_id,
            "status": "completed",
            "entities_count": len(db_entities),
            "claims_count": len(db_claims),
            "relationships_count": len(db_relationships),
            "contradictions_count": len(db_contradictions),
            "trends_count": len(db_trends),
            "summary": summary_msg,
            "created_at": datetime.now(timezone.utc)
        }

    def build_knowledge_graph(self, db: Session, project_id: str) -> Dict[str, Any]:
        """
        Assembles graph representation (nodes & edges) from entities, relationships,
        claims, and source provenance.
        """
        entities = db.query(ResearchEntity).filter(ResearchEntity.project_id == project_id).all()
        relationships = db.query(ResearchRelationship).filter(ResearchRelationship.project_id == project_id).all()
        claims = db.query(ResearchClaim).filter(ResearchClaim.project_id == project_id).all()
        contradictions = db.query(ResearchContradiction).filter(ResearchContradiction.project_id == project_id).all()
        sources = db.query(Source).filter(Source.project_id == project_id).all()

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        seen_node_ids = set()

        # 1. Source Nodes
        for s in sources:
            node_id = f"source-{s.id}"
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": s.title[:50],
                    "type": "SOURCE",
                    "metadata": {"source_id": s.id, "url": s.url}
                })

        # 2. Entity Nodes
        for ent in entities:
            node_id = f"ent-{ent.normalized_name.lower().replace(' ', '_')}"
            if node_id not in seen_node_ids:
                seen_node_ids.add(node_id)
                nodes.append({
                    "id": node_id,
                    "label": ent.name,
                    "type": ent.entity_type,
                    "metadata": {
                        "normalized_name": ent.normalized_name,
                        "confidence": ent.confidence,
                        "extraction_method": ent.extraction_method
                    }
                })

            # Add SOURCED_FROM edge to Source Node if source exists
            if ent.source_id:
                src_node_id = f"source-{ent.source_id}"
                if src_node_id in seen_node_ids:
                    edges.append({
                        "id": f"edge-src-{ent.id}",
                        "source": node_id,
                        "target": src_node_id,
                        "relationship": "REPORTED_BY",
                        "evidence": ent.supporting_excerpt or "",
                        "confidence": ent.confidence,
                        "source_id": ent.source_id
                    })

        # 3. Relationship Edges between Entities
        for rel in relationships:
            src_node_id = f"ent-{rel.source_entity_name.lower().replace(' ', '_')}"
            tgt_node_id = f"ent-{rel.target_entity_name.lower().replace(' ', '_')}"

            # Ensure nodes exist
            if src_node_id in seen_node_ids and tgt_node_id in seen_node_ids:
                edges.append({
                    "id": f"edge-rel-{rel.id}",
                    "source": src_node_id,
                    "target": tgt_node_id,
                    "relationship": rel.relationship_type,
                    "evidence": rel.supporting_evidence,
                    "confidence": rel.confidence,
                    "source_id": rel.source_id
                })

        # 4. Contradiction Edges
        for cont in contradictions:
            if cont.claim_a_id and cont.claim_b_id:
                edges.append({
                    "id": f"edge-contra-{cont.id}",
                    "source": f"claim-{cont.claim_a_id}",
                    "target": f"claim-{cont.claim_b_id}",
                    "relationship": "CONTRADICTS",
                    "evidence": cont.disagreement_nature,
                    "confidence": 0.90,
                    "source_id": cont.source_a_id
                })

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entities": len(entities),
            "relationships": len(relationships),
            "sources": len(sources),
            "contradictions": len(contradictions)
        }

        return {
            "project_id": project_id,
            "nodes": nodes,
            "edges": edges,
            "stats": stats
        }

intelligence_engine = ResearchIntelligenceEngine()

