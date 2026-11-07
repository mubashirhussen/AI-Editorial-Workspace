"""
Privacy-Conscious Product Analytics Service.
Tracks high-level operational funnel metrics (projects created, sources processed,
briefs generated, drafts created, writing improvements, export operations, failures)
without storing passwords, API keys, private source contents, or PII.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.models.base import UsageEvent, Organization


class AnalyticsService:
    """Privacy-preserving analytics event logger and funnel aggregator."""

    # Approved privacy-safe metric names
    VALID_METRICS = {
        "project_created",
        "source_processed",
        "brief_generated",
        "draft_created",
        "writing_improved",
        "export_executed",
        "workflow_failed"
    }

    # Prohibited keys to ensure zero PII or credentials in metadata
    SANCTIONED_KEYS = {"format", "status", "category", "duration_ms", "count", "error_code", "word_count"}

    @classmethod
    def track_event(
        cls,
        db: Session,
        organization_id: Optional[str],
        metric_name: str,
        metric_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UsageEvent]:
        """
        Records a sanitized product analytics event.
        Guarantees no raw text, secrets, or PII are retained.
        """
        if metric_name not in cls.VALID_METRICS:
            # Fallback for dynamic valid metrics
            if not metric_name.replace("_", "").isalnum():
                return None

        # Sanitize metadata to only allow safe non-PII keys
        clean_tags: Dict[str, Any] = {}
        if metadata and isinstance(metadata, dict):
            for k, v in metadata.items():
                if k.lower() in cls.SANCTIONED_KEYS:
                    # Sanitize value
                    if isinstance(v, (int, float, bool)):
                        clean_tags[k.lower()] = v
                    elif isinstance(v, str):
                        clean_tags[k.lower()] = v[:100]  # truncate long strings

        try:
            event = UsageEvent(
                organization_id=organization_id,
                metric_name=metric_name,
                metric_value=float(metric_value),
                tags_json=clean_tags,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(event)
            db.commit()
            return event
        except Exception as e:
            db.rollback()
            return None

    @classmethod
    def get_funnel_summary(
        cls,
        db: Session,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregates product analytics into an executive funnel summary.
        """
        query = db.query(
            UsageEvent.metric_name,
            func.count(UsageEvent.id).label("count"),
            func.sum(UsageEvent.metric_value).label("total_value")
        )
        if organization_id:
            query = query.filter(
                (UsageEvent.organization_id == organization_id) | (UsageEvent.organization_id == None)
            )

        grouped = query.group_by(UsageEvent.metric_name).all()
        summary_dict = {
            "projects_created": 0,
            "sources_processed": 0,
            "briefs_generated": 0,
            "drafts_created": 0,
            "writing_improved": 0,
            "exports_executed": 0,
            "workflow_failures": 0,
            "total_events": 0
        }

        mapping = {
            "project_created": "projects_created",
            "source_processed": "sources_processed",
            "brief_generated": "briefs_generated",
            "draft_created": "drafts_created",
            "writing_improved": "writing_improved",
            "export_executed": "exports_executed",
            "workflow_failed": "workflow_failures"
        }

        total_cnt = 0
        for metric, count, _ in grouped:
            total_cnt += count
            if metric in mapping:
                summary_dict[mapping[metric]] = count

        summary_dict["total_events"] = total_cnt

        # Calculate conversion rates
        # Research conversion: sources processed -> brief generated
        if summary_dict["sources_processed"] > 0:
            summary_dict["research_synthesis_rate"] = round(
                (summary_dict["briefs_generated"] / summary_dict["sources_processed"]) * 100, 1
            )
        else:
            summary_dict["research_synthesis_rate"] = 0.0

        # Editorial conversion: briefs generated -> drafts created
        if summary_dict["briefs_generated"] > 0:
            summary_dict["draft_generation_rate"] = round(
                (summary_dict["drafts_created"] / summary_dict["briefs_generated"]) * 100, 1
            )
        else:
            summary_dict["draft_generation_rate"] = 0.0

        return summary_dict

    @classmethod
    def get_recent_events(
        cls,
        db: Session,
        organization_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Returns recent privacy-safe events for debugging and monitoring."""
        query = db.query(UsageEvent)
        if organization_id:
            query = query.filter(
                (UsageEvent.organization_id == organization_id) | (UsageEvent.organization_id == None)
            )
        records = query.order_by(desc(UsageEvent.timestamp)).limit(limit).all()

        return [
            {
                "id": r.id,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "tags": r.tags_json or {},
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in records
        ]


analytics_service = AnalyticsService()

