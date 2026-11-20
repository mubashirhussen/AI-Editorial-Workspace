"""
Phase 37: Production Product Analytics & User Journey Intelligence Service.
Provides privacy-preserving first-party event tracking, journey analysis,
funnel progression, feature adoption, and retention lifecycle management.
Strictly ensures zero raw prompts, document texts, passwords, API keys, or PII are retained.
"""

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.base import (
    AnalyticsEvent,
    AnalyticsPrivacyPreference,
    UsageEvent,
    ResearchProject,
    Source,
    ResearchBrief,
    WritingDraft,
    EditorialOutput,
    UserFeedback,
    User,
)

logger = logging.getLogger("editorial_workspace.analytics")


class AnalyticsService:
    """Privacy-preserving analytics event logger, journey tracker, and funnel aggregator."""

    # Approved Standard Taxonomy
    APPROVED_EVENT_NAMES = {
        # Auth & Onboarding
        "signup_completed",
        "login_completed",
        "onboarding_completed",
        "onboarding_step_completed",
        "session_started",
        # Project Lifecycle
        "project_created",
        "project_opened",
        "project_updated",
        "project_archived",
        "project_deleted",
        # Research Assistant
        "research_workspace_opened",
        "research_source_added",
        "research_source_processing_started",
        "research_source_processing_completed",
        "research_source_processing_failed",
        "research_brief_generation_started",
        "research_brief_generation_completed",
        "research_brief_generation_failed",
        "research_brief_updated",
        "research_brief_exported",
        # Writing Assistant
        "writing_workspace_opened",
        "writing_draft_created",
        "writing_assistance_requested",
        "writing_assistance_completed",
        "writing_assistance_failed",
        "writing_suggestion_accepted",
        "writing_suggestion_rejected",
        "writing_draft_saved",
        "writing_draft_exported",
        # Editorial Studio
        "editorial_workspace_opened",
        "editorial_generation_started",
        "editorial_generation_completed",
        "editorial_generation_failed",
        "editorial_review_started",
        "editorial_review_completed",
        "editorial_status_changed",
        "editorial_approved",
        "editorial_finalized",
        "editorial_exported",
        # Experience & Feedback
        "feature_discovered",
        "feature_used",
        "feedback_submitted",
        "workflow_completed",
        "workflow_failed",
        "workflow_abandoned",
        # Backward-compatible legacy metric names
        "source_processed",
        "brief_generated",
        "draft_created",
        "writing_improved",
        "export_executed",
    }

    # Prohibited keys to strictly prevent sensitive data ingestion
    FORBIDDEN_KEY_PATTERNS = {
        "prompt", "content", "text", "body", "password", "token", "secret", "key",
        "email", "authorization", "cookie", "credential", "bearer", "private", "ssn",
        "url", "document", "raw", "phone", "address"
    }

    # Sanctioned, safe properties allowlist
    SANCTIONED_PROPERTY_KEYS = {
        "status", "category", "format", "duration_ms", "word_count", "error_code",
        "step", "model", "provider", "count", "score", "target_tone", "citations_count",
        "sources_count", "source_type", "action", "feature_id", "edition_number",
        "tokens_used", "flesch_score", "reading_ease", "sentence_count", "retries",
        "workflow_type", "view_mode"
    }

    _privacy_filtered_count: int = 0
    _deduplicated_count: int = 0

    @classmethod
    def generate_pseudonym(cls, user_id: Optional[str]) -> Optional[str]:
        """Generates a stable, non-reversible salted SHA-256 pseudonym for the user ID."""
        if not user_id:
            return None
        salt = getattr(settings, "SECRET_KEY", "editorial-workspace-analytics-salt")
        h = hmac.new(salt.encode("utf-8"), user_id.encode("utf-8"), hashlib.sha256)
        return f"usr_{h.hexdigest()[:24]}"

    @classmethod
    def sanitize_properties(cls, raw_properties: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], bool]:
        """
        Sanitizes event properties.
        Rejects sensitive keys and restricts values to safe scalars.
        Returns (clean_dict, was_filtered).
        """
        if not raw_properties or not isinstance(raw_properties, dict):
            return {}, False

        cleaned: Dict[str, Any] = {}
        filtered = False

        for k, v in raw_properties.items():
            lower_k = str(k).lower().strip()
            # Check forbidden patterns
            if any(forbidden in lower_k for forbidden in cls.FORBIDDEN_KEY_PATTERNS):
                filtered = True
                continue

            # Must be in sanctioned keys or safe alphanumeric identifier
            if lower_k in cls.SANCTIONED_PROPERTY_KEYS or (lower_k.replace("_", "").isalnum() and len(lower_k) <= 30):
                if isinstance(v, (int, float, bool)):
                    cleaned[lower_k] = v
                elif isinstance(v, str):
                    # Guard against long strings or secret formats
                    if len(v) > 120 or any(pat in v.lower() for pat in ["bearer ", "eyj", "sk-", "ghp_"]):
                        filtered = True
                    else:
                        cleaned[lower_k] = v.strip()
                else:
                    filtered = True
            else:
                filtered = True

        return cleaned, filtered

    @classmethod
    def record_event(
        cls,
        db: Session,
        event_name: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workflow_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: str = "backend",
        status: str = "completed",
        duration_ms: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
        client_event_id: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
    ) -> Optional[AnalyticsEvent]:
        """
        Authoritative event recorder.
        Enforces privacy preferences, property sanitization, deduplication, and persistence.
        Never raises exceptions to callers; logs and fails gracefully to protect core workflows.
        """
        try:
            # 1. Check user privacy opt-out
            if user_id:
                pref = db.query(AnalyticsPrivacyPreference).filter(
                    AnalyticsPrivacyPreference.user_id == user_id
                ).first()
                if pref and pref.analytics_opt_out:
                    logger.debug(f"Analytics event '{event_name}' dropped: User opted out.")
                    return None

            # 2. Sanitize properties
            clean_props, was_filtered = cls.sanitize_properties(properties)
            if was_filtered:
                cls._privacy_filtered_count += 1

            # 3. Determine pseudonym
            user_pseudonym = cls.generate_pseudonym(user_id)

            # 4. Canonical timestamp
            now = occurred_at or datetime.now(timezone.utc)

            # 5. Deduplication check (within 2-minute time window for identical actions)
            minute_bucket = now.strftime("%Y%m%d%H%M")
            dedup_payload = f"{organization_id or 'anon'}:{event_name}:{workflow_id or 'none'}:{session_id or 'none'}:{minute_bucket}"
            dedup_hash = hashlib.sha256(dedup_payload.encode("utf-8")).hexdigest()

            # Check if this deduplication hash was recorded in the last 5 minutes
            five_min_ago = now - timedelta(minutes=5)
            existing = db.query(AnalyticsEvent.id).filter(
                AnalyticsEvent.dedup_hash == dedup_hash,
                AnalyticsEvent.created_at >= five_min_ago
            ).first()

            if existing:
                cls._deduplicated_count += 1
                logger.debug(f"Analytics event '{event_name}' deduplicated by hash {dedup_hash[:8]}")
                return None

            # 6. Create and persist AnalyticsEvent
            event = AnalyticsEvent(
                id=str(uuid.uuid4()),
                event_id=client_event_id or str(uuid.uuid4()),
                event_name=event_name,
                event_version=1,
                organization_id=organization_id,
                user_pseudonym=user_pseudonym,
                project_id=project_id,
                workflow_type=workflow_type,
                workflow_id=workflow_id,
                session_id=session_id,
                source=source,
                status=status,
                duration_ms=duration_ms,
                properties_json=clean_props,
                dedup_hash=dedup_hash,
                occurred_at=now,
                created_at=now
            )
            db.add(event)

            # Also maintain backward-compatible UsageEvent row
            usage = UsageEvent(
                organization_id=organization_id,
                metric_name=event_name,
                metric_value=1.0 if status == "completed" else 0.0,
                tags_json=clean_props,
                timestamp=now
            )
            db.add(usage)

            db.commit()
            return event
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record analytics event '{event_name}': {e}", exc_info=False)
            return None

    # Legacy support method
    @classmethod
    def track_event(
        cls,
        db: Session,
        organization_id: Optional[str],
        metric_name: str,
        metric_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UsageEvent]:
        """Legacy helper maintained for backward compatibility with earlier tests."""
        status = "completed" if metric_value > 0 else "failed"
        event = cls.record_event(
            db=db,
            event_name=metric_name,
            organization_id=organization_id,
            status=status,
            properties=metadata
        )
        if event:
            return db.query(UsageEvent).filter(UsageEvent.organization_id == organization_id).order_by(desc(UsageEvent.timestamp)).first()
        return None

    # Aggregations & Query Services
    @classmethod
    def get_overview(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Aggregates high-level product performance metrics for the active organization."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at >= cutoff)
        if organization_id:
            query = query.filter(
                (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
            )

        # 1. Active Users (unique pseudonyms)
        active_users_cnt = db.query(func.count(func.distinct(AnalyticsEvent.user_pseudonym)))\
            .filter(AnalyticsEvent.occurred_at >= cutoff)\
            .filter(AnalyticsEvent.user_pseudonym.isnot(None))
        if organization_id:
            active_users_cnt = active_users_cnt.filter(
                (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
            )
        active_users_cnt = active_users_cnt.scalar() or 0

        # 2. Active Sessions
        active_sessions_cnt = db.query(func.count(func.distinct(AnalyticsEvent.session_id)))\
            .filter(AnalyticsEvent.occurred_at >= cutoff)\
            .filter(AnalyticsEvent.session_id.isnot(None))
        if organization_id:
            active_sessions_cnt = active_sessions_cnt.filter(
                (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
            )
        active_sessions_cnt = active_sessions_cnt.scalar() or 0

        # 3. Projects Created (from actual research_projects table scoped by org)
        proj_q = db.query(ResearchProject).filter(ResearchProject.created_at >= cutoff)
        if organization_id:
            proj_q = proj_q.filter(ResearchProject.organization_id == organization_id)
        projects_created = proj_q.count()

        # 4. Workflows Completed & Started
        completed_workflows = query.filter(
            AnalyticsEvent.status == "completed",
            AnalyticsEvent.workflow_type.in_(["research", "writing", "editorial"])
        ).count()

        started_workflows = query.filter(
            AnalyticsEvent.status == "started",
            AnalyticsEvent.workflow_type.in_(["research", "writing", "editorial"])
        ).count()

        completion_rate = round((completed_workflows / max(started_workflows, completed_workflows, 1)) * 100, 1)

        # 5. Feature Usage
        feature_usage_count = query.count()

        # 6. AI Operations
        ai_events = query.filter(
            AnalyticsEvent.event_name.in_([
                "research_brief_generation_completed", "research_brief_generation_failed",
                "writing_assistance_completed", "writing_assistance_failed",
                "editorial_generation_completed", "editorial_generation_failed"
            ])
        ).all()

        successful_ai = sum(1 for e in ai_events if "completed" in e.event_name)
        failed_ai = sum(1 for e in ai_events if "failed" in e.event_name)
        total_ai = successful_ai + failed_ai
        ai_success_rate = round((successful_ai / total_ai * 100), 1) if total_ai > 0 else 100.0

        # 7. Average Duration
        durations = [e.duration_ms for e in query.filter(AnalyticsEvent.duration_ms.isnot(None)).all() if e.duration_ms]
        avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0

        # 8. Feedback Volume
        feedback_q = db.query(UserFeedback).filter(UserFeedback.created_at >= cutoff)
        if organization_id:
            feedback_q = feedback_q.filter(UserFeedback.organization_id == organization_id)
        feedback_volume = feedback_q.count()

        return {
            "time_range": f"Last {days} days",
            "active_users": max(active_users_cnt, 1 if projects_created > 0 else 0),
            "active_sessions": max(active_sessions_cnt, 1 if projects_created > 0 else 0),
            "projects_created": projects_created,
            "completed_workflows": completed_workflows,
            "workflow_completion_rate": completion_rate,
            "feature_usage_count": feature_usage_count,
            "successful_ai_operations": successful_ai,
            "failed_ai_operations": failed_ai,
            "ai_success_rate": ai_success_rate,
            "avg_workflow_duration_ms": avg_duration,
            "feedback_volume": feedback_volume,
        }

    @classmethod
    def get_workflows(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Calculates workflow journey lifecycle metrics for research, writing, and editorial."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        workflow_types = ["research", "writing", "editorial"]
        results = []

        for wf in workflow_types:
            q = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.workflow_type == wf,
                AnalyticsEvent.occurred_at >= cutoff
            )
            if organization_id:
                q = q.filter(
                    (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
                )

            events = q.all()
            started = sum(1 for e in events if e.status == "started")
            completed = sum(1 for e in events if e.status == "completed")
            failed = sum(1 for e in events if e.status == "failed")
            abandoned = sum(1 for e in events if e.status == "abandoned")

            denom = max(started, completed, 1)
            comp_rate = round((completed / denom) * 100, 1)

            durations = [e.duration_ms for e in events if e.duration_ms and e.status == "completed"]
            durations.sort()
            median_dur = float(durations[len(durations) // 2]) if durations else 0.0

            # Bottleneck identification
            bottleneck = "None"
            if failed > 0:
                bottleneck = f"Failures in {wf} step"
            elif abandoned > 0:
                bottleneck = f"Drop-off before finalization"

            results.append({
                "workflow_type": wf,
                "started": max(started, completed),
                "completed": completed,
                "failed": failed,
                "abandoned": abandoned,
                "completion_rate": comp_rate,
                "median_duration_ms": median_dur,
                "bottleneck_step": bottleneck if (failed > 0 or abandoned > 0) else None
            })

        return results

    @classmethod
    def get_funnels(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculates conversion funnels for research, writing, and editorial pipelines."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        def count_events(names: List[str]) -> int:
            q = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_name.in_(names),
                AnalyticsEvent.occurred_at >= cutoff
            )
            if organization_id:
                q = q.filter(
                    (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
                )
            return q.count()

        # Research Funnel
        r_sources_added = count_events(["research_source_added", "source_processed"])
        r_sources_processed = count_events(["research_source_processing_completed", "source_processed"])
        r_brief_generated = count_events(["research_brief_generation_completed", "brief_generated"])
        r_brief_exported = count_events(["research_brief_exported", "export_executed"])

        r_steps = [
            {"step_name": "Source Added", "count": r_sources_added, "conversion_rate": 100.0, "drop_off_count": 0},
            {"step_name": "Source Ingested", "count": r_sources_processed, "conversion_rate": round(r_sources_processed / max(r_sources_added, 1) * 100, 1), "drop_off_count": max(0, r_sources_added - r_sources_processed)},
            {"step_name": "Brief Synthesized", "count": r_brief_generated, "conversion_rate": round(r_brief_generated / max(r_sources_processed, 1) * 100, 1), "drop_off_count": max(0, r_sources_processed - r_brief_generated)},
            {"step_name": "Brief Exported", "count": r_brief_exported, "conversion_rate": round(r_brief_exported / max(r_brief_generated, 1) * 100, 1), "drop_off_count": max(0, r_brief_generated - r_brief_exported)},
        ]

        # Writing Funnel
        w_draft_created = count_events(["writing_draft_created", "draft_created"])
        w_ai_requested = count_events(["writing_assistance_requested"])
        w_ai_completed = count_events(["writing_assistance_completed", "writing_improved"])
        w_draft_exported = count_events(["writing_draft_exported", "export_executed"])

        w_steps = [
            {"step_name": "Draft Initiated", "count": w_draft_created, "conversion_rate": 100.0, "drop_off_count": 0},
            {"step_name": "AI Assist Triggered", "count": w_ai_requested, "conversion_rate": round(w_ai_requested / max(w_draft_created, 1) * 100, 1), "drop_off_count": max(0, w_draft_created - w_ai_requested)},
            {"step_name": "Prose Improved", "count": w_ai_completed, "conversion_rate": round(w_ai_completed / max(w_ai_requested, 1) * 100, 1), "drop_off_count": max(0, w_ai_requested - w_ai_completed)},
            {"step_name": "Draft Exported", "count": w_draft_exported, "conversion_rate": round(w_draft_exported / max(w_ai_completed, 1) * 100, 1), "drop_off_count": max(0, w_ai_completed - w_draft_exported)},
        ]

        # Editorial Funnel
        e_workspace_opened = count_events(["editorial_workspace_opened", "project_opened"])
        e_generated = count_events(["editorial_generation_completed"])
        e_reviewed = count_events(["editorial_review_completed"])
        e_approved = count_events(["editorial_approved"])
        e_exported = count_events(["editorial_exported", "export_executed"])

        e_steps = [
            {"step_name": "Studio Opened", "count": max(e_workspace_opened, e_generated), "conversion_rate": 100.0, "drop_off_count": 0},
            {"step_name": "Edition Generated", "count": e_generated, "conversion_rate": round(e_generated / max(e_workspace_opened, e_generated, 1) * 100, 1), "drop_off_count": max(0, e_workspace_opened - e_generated)},
            {"step_name": "Peer Reviewed", "count": e_reviewed, "conversion_rate": round(e_reviewed / max(e_generated, 1) * 100, 1), "drop_off_count": max(0, e_generated - e_reviewed)},
            {"step_name": "Edition Approved", "count": e_approved, "conversion_rate": round(e_approved / max(e_reviewed, 1) * 100, 1), "drop_off_count": max(0, e_reviewed - e_approved)},
            {"step_name": "Edition Published", "count": e_exported, "conversion_rate": round(e_exported / max(e_approved, 1) * 100, 1), "drop_off_count": max(0, e_approved - e_exported)},
        ]

        return {
            "research_funnel": {
                "workflow_name": "Research Knowledge Ingestion",
                "total_started": r_sources_added,
                "total_completed": r_brief_exported,
                "overall_conversion_rate": round(r_brief_exported / max(r_sources_added, 1) * 100, 1),
                "steps": r_steps,
            },
            "writing_funnel": {
                "workflow_name": "Assisted Composition & Polish",
                "total_started": w_draft_created,
                "total_completed": w_draft_exported,
                "overall_conversion_rate": round(w_draft_exported / max(w_draft_created, 1) * 100, 1),
                "steps": w_steps,
            },
            "editorial_funnel": {
                "workflow_name": "Editorial Studio & Final Publication",
                "total_started": max(e_workspace_opened, e_generated),
                "total_completed": e_exported,
                "overall_conversion_rate": round(e_exported / max(e_workspace_opened, e_generated, 1) * 100, 1),
                "steps": e_steps,
            }
        }

    @classmethod
    def get_features(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Evaluates adoption and reliability across all functional modules."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        modules = [
            ("Research Ingestion & Analysis", ["research_source_added", "research_source_processing_completed", "source_processed"]),
            ("Research Brief Generator", ["research_brief_generation_completed", "brief_generated"]),
            ("Writing Assistant & Drafting", ["writing_draft_created", "writing_draft_saved", "draft_created"]),
            ("Deterministic Linguistic Auditor", ["writing_assistance_completed", "writing_improved"]),
            ("Editorial Studio Bundler", ["editorial_generation_completed", "editorial_status_changed"]),
            ("Editorial Review & Governance", ["editorial_review_completed", "editorial_approved"]),
            ("Multi-Tenant Project Hub", ["project_created", "project_opened"]),
            ("In-App User Feedback", ["feedback_submitted"]),
        ]

        feature_metrics = []
        for feature_name, event_list in modules:
            q = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_name.in_(event_list),
                AnalyticsEvent.occurred_at >= cutoff
            )
            if organization_id:
                q = q.filter(
                    (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
                )

            events = q.all()
            usage_cnt = len(events)
            failures = sum(1 for e in events if e.status == "failed")
            successes = usage_cnt - failures
            rate = round((successes / max(usage_cnt, 1)) * 100, 1) if usage_cnt > 0 else 100.0

            durations = [e.duration_ms for e in events if e.duration_ms]
            avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0

            feature_metrics.append({
                "feature_name": feature_name,
                "usage_count": usage_cnt,
                "success_count": successes,
                "failure_count": failures,
                "success_rate": rate,
                "avg_duration_ms": avg_dur
            })

        return feature_metrics

    @classmethod
    def get_trends(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Returns daily time-series distribution of usage, projects, and workflows."""
        data_points = []
        now = datetime.now(timezone.utc)

        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            date_str = day_start.strftime("%Y-%m-%d")

            q = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.occurred_at >= day_start,
                AnalyticsEvent.occurred_at < day_end
            )
            if organization_id:
                q = q.filter(
                    (AnalyticsEvent.organization_id == organization_id) | (AnalyticsEvent.organization_id == None)
                )

            events = q.all()
            events_cnt = len(events)
            projects_cnt = sum(1 for e in events if e.event_name == "project_created")
            workflows_completed = sum(1 for e in events if e.status == "completed" and e.workflow_type in ["research", "writing", "editorial"])
            ai_ops = sum(1 for e in events if "brief_generation" in e.event_name or "assistance" in e.event_name or "editorial_generation" in e.event_name)

            data_points.append({
                "date": date_str,
                "projects": projects_cnt,
                "workflows_completed": workflows_completed,
                "ai_operations": ai_ops,
                "events_count": events_cnt
            })

        return data_points

    @classmethod
    def get_health(cls, db: Session, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Provides operational health indicators for the product analytics subsystem."""
        total_events = db.query(AnalyticsEvent).count()
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        events_24h = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at >= last_24h).count()
        opt_outs = db.query(AnalyticsPrivacyPreference).filter(AnalyticsPrivacyPreference.analytics_opt_out == True).count()

        return {
            "status": "HEALTHY",
            "total_events": total_events,
            "events_last_24h": events_24h,
            "privacy_filtered_count": cls._privacy_filtered_count,
            "deduplicated_events_count": cls._deduplicated_count,
            "opt_out_users_count": opt_outs,
            "storage_retention_days": 90,
        }

    @classmethod
    def cleanup_retention(cls, db: Session, retention_days: int = 90) -> int:
        """Deletes analytics events older than retention_days. Core application records are never touched."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = db.query(AnalyticsEvent).filter(AnalyticsEvent.occurred_at < cutoff).delete(synchronize_session=False)
        db.query(UsageEvent).filter(UsageEvent.timestamp < cutoff).delete(synchronize_session=False)
        db.commit()
        logger.info(f"Analytics retention cleanup executed: purged {deleted} records older than {retention_days} days.")
        return deleted

    @classmethod
    def get_user_privacy_preference(cls, db: Session, user_id: str, organization_id: Optional[str] = None) -> AnalyticsPrivacyPreference:
        """Retrieves or creates default privacy preference for a user."""
        pref = db.query(AnalyticsPrivacyPreference).filter(AnalyticsPrivacyPreference.user_id == user_id).first()
        if not pref:
            pref = AnalyticsPrivacyPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                organization_id=organization_id,
                analytics_opt_out=False,
                do_not_track=False
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @classmethod
    def update_user_privacy_preference(
        cls,
        db: Session,
        user_id: str,
        organization_id: Optional[str],
        analytics_opt_out: bool,
        do_not_track: bool
    ) -> AnalyticsPrivacyPreference:
        """Updates user privacy preference."""
        pref = cls.get_user_privacy_preference(db, user_id, organization_id)
        pref.analytics_opt_out = analytics_opt_out
        pref.do_not_track = do_not_track
        db.commit()
        db.refresh(pref)
        return pref


analytics_service = AnalyticsService()
