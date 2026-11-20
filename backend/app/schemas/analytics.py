"""
Phase 37: Analytics Schemas
Pydantic schemas for privacy-preserving event ingestion, workflow intelligence,
funnel reporting, and privacy preferences.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    event_id: Optional[str] = Field(default=None, description="Optional client-generated UUID for idempotency")
    event_name: str = Field(..., max_length=100, description="Approved taxonomy event name")
    event_version: int = Field(default=1, ge=1, le=10, description="Schema version of the event")
    occurred_at: Optional[datetime] = Field(default=None, description="Timestamp when event occurred (defaults to UTC now)")
    project_reference: Optional[str] = Field(default=None, description="Project ID reference if applicable")
    workflow_type: Optional[str] = Field(default=None, description="Workflow category (research, writing, editorial, project, auth)")
    workflow_reference: Optional[str] = Field(default=None, description="Journey/Workflow correlation ID")
    session_reference: Optional[str] = Field(default=None, description="Client session reference")
    source: str = Field(default="frontend", description="Source of event: backend or frontend")
    status: str = Field(default="completed", description="Execution status: started, completed, failed, abandoned")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Execution duration in milliseconds")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Sanitized, non-sensitive event properties")


class AnalyticsEventResponse(BaseModel):
    id: str
    event_id: Optional[str] = None
    event_name: str
    event_version: int
    occurred_at: datetime
    user_reference: Optional[str] = None
    organization_reference: Optional[str] = None
    project_reference: Optional[str] = None
    workflow_type: Optional[str] = None
    workflow_reference: Optional[str] = None
    session_reference: Optional[str] = None
    source: str
    status: str
    duration_ms: Optional[int] = None
    properties: Dict[str, Any]


class AnalyticsOverviewResponse(BaseModel):
    time_range: str
    active_users: int
    active_sessions: int
    projects_created: int
    completed_workflows: int
    workflow_completion_rate: float
    feature_usage_count: int
    successful_ai_operations: int
    failed_ai_operations: int
    ai_success_rate: float
    avg_workflow_duration_ms: float
    feedback_volume: int


class WorkflowMetric(BaseModel):
    workflow_type: str
    started: int
    completed: int
    failed: int
    abandoned: int
    completion_rate: float
    median_duration_ms: float
    bottleneck_step: Optional[str] = None


class AnalyticsWorkflowsResponse(BaseModel):
    time_range: str
    workflows: List[WorkflowMetric]


class FunnelStep(BaseModel):
    step_name: str
    count: int
    conversion_rate: float
    drop_off_count: int


class FunnelSummary(BaseModel):
    workflow_name: str
    total_started: int
    total_completed: int
    overall_conversion_rate: float
    steps: List[FunnelStep]


class AnalyticsFunnelsResponse(BaseModel):
    research_funnel: FunnelSummary
    writing_funnel: FunnelSummary
    editorial_funnel: FunnelSummary


class FeatureMetric(BaseModel):
    feature_name: str
    usage_count: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float


class AnalyticsFeaturesResponse(BaseModel):
    features: List[FeatureMetric]


class TrendDataPoint(BaseModel):
    date: str
    projects: int
    workflows_completed: int
    ai_operations: int
    events_count: int


class AnalyticsTrendsResponse(BaseModel):
    period: str
    data_points: List[TrendDataPoint]


class AnalyticsHealthResponse(BaseModel):
    status: str
    total_events: int
    events_last_24h: int
    privacy_filtered_count: int
    deduplicated_events_count: int
    opt_out_users_count: int
    storage_retention_days: int


class AnalyticsPrivacyPreferenceRequest(BaseModel):
    analytics_opt_out: bool = Field(default=False, description="Opt-out of all non-essential analytics tracking")
    do_not_track: bool = Field(default=False, description="Respect browser DNT signal")


class AnalyticsPrivacyPreferenceResponse(BaseModel):
    user_id: str
    organization_id: Optional[str] = None
    analytics_opt_out: bool
    do_not_track: bool
    updated_at: datetime
