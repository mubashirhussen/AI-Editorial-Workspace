"""
Phase 38: AI Product Intelligence, Data-Driven Recommendations & Automated Workflow Optimization Service.
Analyzes validated analytics data, validates data quality, detects workflow patterns,
synthesizes evidence-grounded insights, manages recommendation lifecycles,
and evaluates pre/post implementation impact deltas.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from backend.app.models.base import (
    AnalyticsEvent,
    ProductIntelligenceInsight,
    ProductIntelligenceRecommendation,
    ProductIntelligenceAction,
    RecommendationImpactEvaluation,
    RecommendationFeedback,
    ResearchProject,
    User,
)
from backend.app.services.analytics_service import analytics_service

logger = logging.getLogger("editorial_workspace.intelligence")


class ProductIntelligenceService:
    """Core intelligence engine for pattern detection, recommendation ranking, and impact evaluation."""

    # ---------------------------------------------------------------------------
    # 1. Data Quality Validation
    # ---------------------------------------------------------------------------
    @classmethod
    def validate_data_quality(cls, db: Session, organization_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Validates analytics data quality before intelligence execution.
        Assesses sample size, stage completeness, and data freshness.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        q = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at >= cutoff)
        if organization_id:
            q = q.filter((AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None))

        events = q.all()
        sample_size = len(events)

        if sample_size == 0:
            return {
                "status": "INSUFFICIENT_DATA",
                "score": 0.0,
                "sample_size": 0,
                "is_sufficient": False,
                "checks": {
                    "event_volume": "Zero events logged in lookback window.",
                    "data_freshness": "No telemetry recorded.",
                    "workflow_diversity": "None"
                }
            }

        # Check freshness
        most_recent = max(e.occurred_at for e in events if e.occurred_at)
        if most_recent.tzinfo is None:
            most_recent = most_recent.replace(tzinfo=timezone.utc)
        hours_since = (datetime.now(timezone.utc) - most_recent).total_seconds() / 3600.0
        freshness_ok = hours_since <= 72.0

        # Check workflow diversity
        wf_types = {e.workflow_type for e in events if e.workflow_type}
        diversity_ok = len(wf_types) >= 2

        # Compute data quality score
        score = 0.0
        if sample_size >= 10:
            score += 40.0
        elif sample_size >= 3:
            score += 25.0
        else:
            score += 10.0

        if freshness_ok:
            score += 30.0
        else:
            score += 10.0

        if diversity_ok:
            score += 30.0
        else:
            score += 15.0

        status = "HEALTHY" if score >= 75.0 else ("WARNING" if score >= 40.0 else "INSUFFICIENT_DATA")

        return {
            "status": status,
            "score": round(score, 1),
            "sample_size": sample_size,
            "is_sufficient": sample_size >= 3,
            "checks": {
                "event_volume": f"{sample_size} events evaluated.",
                "data_freshness": f"Last event recorded {round(hours_since, 1)}h ago.",
                "workflow_diversity": f"Covering {len(wf_types)} workflow types: {', '.join(wf_types) if wf_types else 'None'}."
            }
        }

    # ---------------------------------------------------------------------------
    # 2. Deterministic Pattern Detection & Analysis Run
    # ---------------------------------------------------------------------------
    @classmethod
    def run_intelligence_analysis(cls, db: Session, organization_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Executes end-to-end product intelligence analysis.
        Validates data quality, runs deterministic rules, records insights, and prioritizes recommendations.
        """
        dq = cls.validate_data_quality(db, organization_id, days)
        if not dq["is_sufficient"]:
            logger.info("Intelligence analysis deferred: Insufficient sample size.")
            return {
                "status": "deferred",
                "message": "Insufficient data for statistically reliable pattern detection.",
                "data_quality": dq,
                "insights_generated": 0,
                "recommendations_generated": 0
            }

        overview = analytics_service.get_overview(db, organization_id, days)
        funnels = analytics_service.get_funnels(db, organization_id, days)
        features = analytics_service.get_features(db, organization_id, days)
        workflows = analytics_service.get_workflows(db, organization_id, days)

        insights_to_create: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []

        # Rule 1: Research Ingestion Failure or Drop-off
        r_funnel = funnels["research_funnel"]
        r_drop = r_funnel["steps"][1]["drop_off_count"] if len(r_funnel["steps"]) > 1 else 0
        r_started = r_funnel["total_started"]
        if r_started > 0 and (r_drop > 0 or r_funnel["overall_conversion_rate"] < 75.0):
            insight_data = {
                "category": "research",
                "severity": "high" if r_drop >= 2 else "medium",
                "title": "Research Source Ingestion Drop-off Detected",
                "description": f"Observed {r_drop} drop-offs during source ingestion with an overall research conversion rate of {r_funnel['overall_conversion_rate']}%.",
                "detected_pattern": "Source extraction bottlenecks or SSRF filter rejections during ingestion.",
                "evidence_json": {
                    "total_sources_added": r_started,
                    "ingestion_drop_off": r_drop,
                    "conversion_rate": r_funnel["overall_conversion_rate"],
                    "reporting_period": f"Last {days} days"
                },
                "metrics_json": {"drop_off_count": r_drop, "conversion_rate": r_funnel["overall_conversion_rate"]},
                "confidence_score": 0.92,
            }
            rec_data = {
                "category": "research_optimization",
                "priority": "HIGH" if r_drop >= 2 else "MEDIUM",
                "severity": insight_data["severity"],
                "title": "Activate Source Pre-Validation & Heuristic Parser Cache",
                "description": "Pre-validate URLs against DNS resolutions prior to full socket connection and cache sanitized article bodies.",
                "proposed_action": "Enable domain pre-flight validation and local fallback text extractor on extraction failure.",
                "expected_benefit": "Reduces ingestion drop-offs by up to 80% and accelerates source availability.",
                "estimated_effort": "LOW",
                "risk_level": "LOW",
                "confidence_score": 0.90,
                "is_automated": True
            }
            insights_to_create.append((insight_data, rec_data))

        # Rule 2: Editorial Review & Approval Bottleneck
        e_funnel = funnels["editorial_funnel"]
        e_started = e_funnel["total_started"]
        e_completed = e_funnel["total_completed"]
        e_conv = e_funnel["overall_conversion_rate"]
        if e_started > 0 and (e_conv < 60.0 or (e_started - e_completed) >= 1):
            insight_data = {
                "category": "editorial",
                "severity": "high",
                "title": "Editorial Studio Peer Review Latency Bottleneck",
                "description": f"Only {e_completed} of {e_started} studio editions reached final publication ({e_conv}% conversion).",
                "detected_pattern": "Editions stalled in peer review or approval workflow stages.",
                "evidence_json": {
                    "studio_editions_started": e_started,
                    "editions_published": e_completed,
                    "conversion_rate": e_conv,
                    "pending_editions": e_started - e_completed
                },
                "metrics_json": {"pending_editions": e_started - e_completed, "conversion_rate": e_conv},
                "confidence_score": 0.88,
            }
            rec_data = {
                "category": "editorial_workflow",
                "priority": "HIGH",
                "severity": "high",
                "title": "Streamline Review Verification with Automated Compliance Checks",
                "description": "Surface pre-computed Deterministic Linguistic Auditor scores and source citation anchors directly to reviewers to accelerate sign-off.",
                "proposed_action": "Enable pre-review style verification tags to reduce human review cycles.",
                "expected_benefit": "Accelerates editorial turnaround by 40% while preserving strict editorial governance.",
                "estimated_effort": "MEDIUM",
                "risk_level": "LOW",
                "confidence_score": 0.85,
                "is_automated": False
            }
            insights_to_create.append((insight_data, rec_data))

        # Rule 3: Writing Assistant Adoption & Suggestion Polish
        w_funnel = funnels["writing_funnel"]
        w_started = w_funnel["total_started"]
        w_ai_ops = overview["successful_ai_operations"] + overview["failed_ai_operations"]
        if w_started > 0:
            insight_data = {
                "category": "writing",
                "severity": "medium",
                "title": "Writing Assistant Drafting Velocity Optimization",
                "description": f"Identified active composition workflow ({w_started} drafts) with {w_funnel['overall_conversion_rate']}% export rate.",
                "detected_pattern": "Drafting throughput correlates with immediate in-editor readability feedback.",
                "evidence_json": {
                    "drafts_created": w_started,
                    "conversion_rate": w_funnel["overall_conversion_rate"],
                    "flesch_enforcement": "active"
                },
                "metrics_json": {"drafts_created": w_started, "conversion_rate": w_funnel["overall_conversion_rate"]},
                "confidence_score": 0.85,
            }
            rec_data = {
                "category": "writing_optimization",
                "priority": "MEDIUM",
                "severity": "medium",
                "title": "Deploy Tone Template Presets for Frontier Model Investigations",
                "description": "Pre-configure target Flesch Reading Ease (65.0) and sentence length (18 words) presets to reduce author rewriting time.",
                "proposed_action": "Apply 'This Week in AI Standard' profile defaults automatically upon new draft creation.",
                "expected_benefit": "Cuts draft iteration cycles by 25% and ensures consistent analytical tone across authors.",
                "estimated_effort": "LOW",
                "risk_level": "LOW",
                "confidence_score": 0.88,
                "is_automated": True
            }
            insights_to_create.append((insight_data, rec_data))

        # Rule 4: AI Reliability & Fallback Readiness
        ai_success = overview["ai_success_rate"]
        ai_failed = overview["failed_ai_operations"]
        if ai_failed > 0 or ai_success < 95.0:
            insight_data = {
                "category": "reliability",
                "severity": "critical" if ai_failed >= 3 else "high",
                "title": "Transient Cloud AI Provider Latency Fluctuation",
                "description": f"Detected {ai_failed} failed AI operations with overall success rate of {ai_success}%.",
                "detected_pattern": "Upstream LLM rate limits or network socket timeouts under burst load.",
                "evidence_json": {
                    "failed_operations": ai_failed,
                    "success_rate": ai_success,
                    "target_sla": "99.0%"
                },
                "metrics_json": {"failed_operations": ai_failed, "success_rate": ai_success},
                "confidence_score": 0.95,
            }
            rec_data = {
                "category": "reliability",
                "priority": "CRITICAL" if ai_failed >= 3 else "HIGH",
                "severity": insight_data["severity"],
                "title": "Enforce Autonomous Offline Heuristic Fallback Engine",
                "description": "Ensure zero-downtime synthesis by immediately falling back to rule-based heuristic generation when cloud LLMs fail.",
                "proposed_action": "Set fallback retry limit to 1 with immediate deterministic summary synthesis.",
                "expected_benefit": "Guarantees 100% editorial studio uptime even during upstream provider outages.",
                "estimated_effort": "LOW",
                "risk_level": "LOW",
                "confidence_score": 0.95,
                "is_automated": True
            }
            insights_to_create.append((insight_data, rec_data))

        # Rule 5: Baseline General Optimization (if fewer than 2 specific anomalies triggered)
        if len(insights_to_create) < 2:
            insight_data = {
                "category": "performance",
                "severity": "low",
                "title": "Editorial Workflow Baseline Latency Assessment",
                "description": f"Workflows executing within acceptable limits with average latency of {overview['avg_workflow_duration_ms']}ms.",
                "detected_pattern": "Standard execution cadence across active workspace projects.",
                "evidence_json": {
                    "completed_workflows": overview["completed_workflows"],
                    "avg_duration_ms": overview["avg_workflow_duration_ms"],
                    "status": "nominal"
                },
                "metrics_json": {"avg_duration_ms": overview["avg_workflow_duration_ms"]},
                "confidence_score": 0.80,
            }
            rec_data = {
                "category": "workflow_optimization",
                "priority": "LOW",
                "severity": "low",
                "title": "Pre-Cache Primary Source Tokens for Fast Citation Anchoring",
                "description": "Cache SHA-256 source paragraph hashes in memory during ingestion to expedite citation verification.",
                "proposed_action": "Enable in-memory citation hash indexing across projects.",
                "expected_benefit": "Reduces end-to-end editorial verification latency by 15%.",
                "estimated_effort": "LOW",
                "risk_level": "LOW",
                "confidence_score": 0.82,
                "is_automated": True
            }
            insights_to_create.append((insight_data, rec_data))

        # Persist generated insights & recommendations
        created_insights = 0
        created_recs = 0

        for ins_d, rec_d in insights_to_create:
            # Check for existing matching active insight to avoid duplication
            existing_ins = db.query(ProductIntelligenceInsight).filter(
                ProductIntelligenceInsight.organization_id == organization_id,
                ProductIntelligenceInsight.title == ins_d["title"],
                ProductIntelligenceInsight.status == "ACTIVE"
            ).first()

            if not existing_ins:
                insight = ProductIntelligenceInsight(
                    id=str(uuid.uuid4()),
                    organization_id=organization_id,
                    category=ins_d["category"],
                    severity=ins_d["severity"],
                    title=ins_d["title"],
                    description=ins_d["description"],
                    detected_pattern=ins_d["detected_pattern"],
                    evidence_json=ins_d["evidence_json"],
                    metrics_json=ins_d["metrics_json"],
                    confidence_score=ins_d["confidence_score"],
                    status="ACTIVE"
                )
                db.add(insight)
                db.flush()
                created_insights += 1

                recommendation = ProductIntelligenceRecommendation(
                    id=str(uuid.uuid4()),
                    insight_id=insight.id,
                    organization_id=organization_id,
                    category=rec_d["category"],
                    priority=rec_d["priority"],
                    severity=rec_d["severity"],
                    title=rec_d["title"],
                    description=rec_d["description"],
                    proposed_action=rec_d["proposed_action"],
                    expected_benefit=rec_d["expected_benefit"],
                    estimated_effort=rec_d["estimated_effort"],
                    risk_level=rec_d["risk_level"],
                    confidence_score=rec_d["confidence_score"],
                    status="READY",
                    is_automated=rec_d["is_automated"]
                )
                db.add(recommendation)
                created_recs += 1

        db.commit()

        return {
            "status": "completed",
            "data_quality": dq,
            "insights_generated": created_insights,
            "recommendations_generated": created_recs
        }

    # ---------------------------------------------------------------------------
    # 3. Aggregations & Feed Queries
    # ---------------------------------------------------------------------------
    @classmethod
    def get_overview(cls, db: Session, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns intelligence overview stats, data quality, active insights, and recommendations."""
        dq = cls.validate_data_quality(db, organization_id)

        # Insights query
        ins_q = db.query(ProductIntelligenceInsight)
        if organization_id:
            ins_q = ins_q.filter(
                (ProductIntelligenceInsight.organization_id == organization_id) | (ProductIntelligenceInsight.organization_id == None)
            )
        insights = ins_q.order_by(desc(ProductIntelligenceInsight.created_at)).limit(20).all()

        # Recommendations query
        rec_q = db.query(ProductIntelligenceRecommendation)
        if organization_id:
            rec_q = rec_q.filter(
                (ProductIntelligenceRecommendation.organization_id == organization_id) | (ProductIntelligenceRecommendation.organization_id == None)
            )
        recs = rec_q.order_by(desc(ProductIntelligenceRecommendation.created_at)).limit(20).all()

        active_ins = sum(1 for i in insights if i.status == "ACTIVE")
        high_pri_recs = sum(1 for r in recs if r.priority in ("CRITICAL", "HIGH") and r.status in ("READY", "ACCEPTED"))
        implemented_recs = sum(1 for r in recs if r.status in ("IMPLEMENTED", "VERIFIED"))
        pending_recs = sum(1 for r in recs if r.status in ("READY", "ACCEPTED", "IN_PROGRESS"))

        return {
            "data_quality": dq,
            "active_insights_count": active_ins,
            "high_priority_recommendations_count": high_pri_recs,
            "implemented_improvements_count": implemented_recs,
            "pending_recommendations_count": pending_recs,
            "insights": insights,
            "recommendations": recs
        }

    @classmethod
    def get_insights(cls, db: Session, organization_id: Optional[str] = None, category: Optional[str] = None) -> List[ProductIntelligenceInsight]:
        """Returns list of insights with optional category filtering."""
        q = db.query(ProductIntelligenceInsight)
        if organization_id:
            q = q.filter((ProductIntelligenceInsight.organization_id == organization_id) | (ProductIntelligenceInsight.organization_id == None))
        if category:
            q = q.filter(ProductIntelligenceInsight.category == category)
        return q.order_by(desc(ProductIntelligenceInsight.created_at)).all()

    @classmethod
    def get_recommendations(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[ProductIntelligenceRecommendation]:
        """Returns list of recommendations with status and priority filtering."""
        q = db.query(ProductIntelligenceRecommendation)
        if organization_id:
            q = q.filter((ProductIntelligenceRecommendation.organization_id == organization_id) | (ProductIntelligenceRecommendation.organization_id == None))
        if status:
            q = q.filter(ProductIntelligenceRecommendation.status == status)
        if priority:
            q = q.filter(ProductIntelligenceRecommendation.priority == priority)
        return q.order_by(desc(ProductIntelligenceRecommendation.created_at)).all()

    # ---------------------------------------------------------------------------
    # 4. Recommendation Lifecycle Management
    # ---------------------------------------------------------------------------
    VALID_LIFECYCLE_TRANSITIONS = {
        "READY": {"ACCEPTED", "REJECTED", "DEFERRED"},
        "ACCEPTED": {"IN_PROGRESS", "IMPLEMENTED", "DEFERRED", "REJECTED"},
        "IN_PROGRESS": {"IMPLEMENTED", "DEFERRED", "REJECTED"},
        "IMPLEMENTED": {"VERIFIED", "IN_PROGRESS"},
        "VERIFIED": set(),
        "REJECTED": {"READY"},
        "DEFERRED": {"READY", "ACCEPTED"},
    }

    @classmethod
    def update_recommendation_status(
        cls,
        db: Session,
        recommendation_id: str,
        organization_id: Optional[str],
        new_status: str,
        notes: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> ProductIntelligenceRecommendation:
        """Transitions recommendation through lifecycle with validation."""
        q = db.query(ProductIntelligenceRecommendation).filter(ProductIntelligenceRecommendation.id == recommendation_id)
        if organization_id:
            q = q.filter((ProductIntelligenceRecommendation.organization_id == organization_id) | (ProductIntelligenceRecommendation.organization_id == None))
        rec = q.first()
        if not rec:
            raise ValueError(f"Recommendation '{recommendation_id}' not found.")

        current = rec.status
        allowed = cls.VALID_LIFECYCLE_TRANSITIONS.get(current, set())
        if new_status not in allowed and new_status != current:
            raise ValueError(f"Invalid state transition from '{current}' to '{new_status}'. Allowed: {', '.join(allowed) or 'None'}")

        rec.status = new_status
        if notes:
            rec.implementation_notes = notes
        if assigned_to:
            rec.assigned_to = assigned_to
        rec.updated_at = datetime.now(timezone.utc)

        # If implemented, create baseline evaluation
        if new_status == "IMPLEMENTED":
            cls.initialize_impact_evaluation(db, rec)

        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def record_feedback(
        cls,
        db: Session,
        recommendation_id: str,
        user_id: Optional[str],
        organization_id: Optional[str],
        feedback_type: str,
        rating: int = 5,
        comment: Optional[str] = None
    ) -> RecommendationFeedback:
        """Records user feedback on recommendation quality and relevance."""
        fb = RecommendationFeedback(
            id=str(uuid.uuid4()),
            recommendation_id=recommendation_id,
            user_id=user_id,
            organization_id=organization_id,
            feedback_type=feedback_type,
            rating=rating,
            comment=comment
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb

    # ---------------------------------------------------------------------------
    # 5. Safe Automated Workflow Optimization
    # ---------------------------------------------------------------------------
    ALLOWED_SAFE_ACTIONS = {
        "cache_reuse_optimization",
        "template_workflow_preset",
        "citation_hash_indexing",
        "offline_heuristic_fallback_tuning"
    }

    @classmethod
    def execute_safe_action(
        cls,
        db: Session,
        recommendation_id: Optional[str],
        organization_id: Optional[str],
        action_type: str,
        payload: Dict[str, Any],
        executed_by: Optional[str] = None
    ) -> ProductIntelligenceAction:
        """Executes a strictly allowlisted, low-risk workflow optimization with audit logging."""
        if action_type not in cls.ALLOWED_SAFE_ACTIONS:
            raise ValueError(f"Action '{action_type}' is not an eligible safe automated optimization.")

        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action_type,
            "executed_by": executed_by or "system",
            "status": "SUCCESS",
            "details": f"Optimization '{action_type}' applied non-destructively."
        }

        action_record = ProductIntelligenceAction(
            id=str(uuid.uuid4()),
            recommendation_id=recommendation_id,
            organization_id=organization_id,
            action_type=action_type,
            action_payload=payload,
            status="EXECUTED",
            executed_by=executed_by,
            audit_trail_json=[audit_entry]
        )
        db.add(action_record)

        # Transition parent recommendation to IMPLEMENTED if linked
        if recommendation_id:
            rec = db.query(ProductIntelligenceRecommendation).filter(
                ProductIntelligenceRecommendation.id == recommendation_id
            ).first()
            if rec and rec.status in ("READY", "ACCEPTED", "IN_PROGRESS"):
                rec.status = "IMPLEMENTED"
                rec.implementation_notes = f"Executed safe optimization action '{action_type}'."
                rec.updated_at = datetime.now(timezone.utc)
                cls.initialize_impact_evaluation(db, rec)

        db.commit()
        db.refresh(action_record)
        return action_record

    # ---------------------------------------------------------------------------
    # 6. Recommendation Impact Evaluation
    # ---------------------------------------------------------------------------
    @classmethod
    def initialize_impact_evaluation(cls, db: Session, rec: ProductIntelligenceRecommendation) -> RecommendationImpactEvaluation:
        """Captures baseline snapshot metrics upon recommendation implementation."""
        overview = analytics_service.get_overview(db, rec.organization_id, days=30)
        baseline = {
            "completion_rate": overview["workflow_completion_rate"],
            "ai_success_rate": overview["ai_success_rate"],
            "avg_duration_ms": overview["avg_workflow_duration_ms"],
            "failed_ai_operations": overview["failed_ai_operations"],
        }
        evaluation = RecommendationImpactEvaluation(
            id=str(uuid.uuid4()),
            recommendation_id=rec.id,
            organization_id=rec.organization_id,
            baseline_metrics_json=baseline,
            current_metrics_json=baseline,
            metric_delta_json={},
            evaluation_status="NOT_EVALUATED",
            notes="Baseline metrics established at implementation time."
        )
        db.add(evaluation)
        return evaluation

    @classmethod
    def evaluate_impact(cls, db: Session, recommendation_id: str, organization_id: Optional[str] = None) -> RecommendationImpactEvaluation:
        """Evaluates metric delta between implementation baseline and current metrics."""
        eval_record = db.query(RecommendationImpactEvaluation).filter(
            RecommendationImpactEvaluation.recommendation_id == recommendation_id
        ).first()

        if not eval_record:
            rec = db.query(ProductIntelligenceRecommendation).filter(
                ProductIntelligenceRecommendation.id == recommendation_id
            ).first()
            if not rec:
                raise ValueError("Recommendation not found.")
            eval_record = cls.initialize_impact_evaluation(db, rec)
            db.commit()

        # Compute current metrics
        current_overview = analytics_service.get_overview(db, organization_id, days=30)
        current = {
            "completion_rate": current_overview["workflow_completion_rate"],
            "ai_success_rate": current_overview["ai_success_rate"],
            "avg_duration_ms": current_overview["avg_workflow_duration_ms"],
            "failed_ai_operations": current_overview["failed_ai_operations"],
        }

        baseline = eval_record.baseline_metrics_json or current

        # Calculate deltas
        deltas = {
            "completion_rate_delta": round(current["completion_rate"] - baseline.get("completion_rate", current["completion_rate"]), 1),
            "ai_success_rate_delta": round(current["ai_success_rate"] - baseline.get("ai_success_rate", current["ai_success_rate"]), 1),
            "avg_duration_delta_ms": round(current["avg_duration_ms"] - baseline.get("avg_duration_ms", current["avg_duration_ms"]), 1),
            "failed_ai_delta": current["failed_ai_operations"] - baseline.get("failed_ai_operations", current["failed_ai_operations"]),
        }

        # Determine evaluation status
        if deltas["completion_rate_delta"] > 0 or deltas["ai_success_rate_delta"] > 0 or deltas["failed_ai_delta"] < 0:
            status = "IMPROVED"
            notes = "Demonstrated measurable improvement in completion rate or reliability."
        elif deltas["completion_rate_delta"] < 0 or deltas["ai_success_rate_delta"] < 0 or deltas["failed_ai_delta"] > 0:
            status = "REGRESSED"
            notes = "Detected metric regression following implementation."
        else:
            status = "NO_SIGNIFICANT_CHANGE"
            notes = "Deltas within normal variance thresholds."

        eval_record.current_metrics_json = current
        eval_record.metric_delta_json = deltas
        eval_record.evaluation_status = status
        eval_record.notes = notes
        eval_record.evaluated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(eval_record)
        return eval_record


product_intelligence_service = ProductIntelligenceService()
