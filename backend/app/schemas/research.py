from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.schemas.source import SourceResponse

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    topic: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    research_objective: Optional[str] = Field(None, max_length=10000)
    target_audience: Optional[str] = Field(None, max_length=255)
    research_scope: Optional[str] = Field(None, max_length=255)
    keywords: Optional[List[str]] = Field(default_factory=list)
    preferred_source_types: Optional[List[str]] = Field(default_factory=list)
    organization_id: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    topic: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    research_objective: Optional[str] = Field(None, max_length=10000)
    target_audience: Optional[str] = Field(None, max_length=255)
    research_scope: Optional[str] = Field(None, max_length=255)
    keywords: Optional[List[str]] = None
    preferred_source_types: Optional[List[str]] = None
    status: Optional[str] = Field(None, max_length=50)
    model_config = ConfigDict(extra="ignore")

class NewsletterAngle(BaseModel):
    id: str
    headline: str
    target_audience: str
    angle_pitch: str
    key_points: List[str] = Field(default_factory=list)
    why_now: str
    model_config = ConfigDict(extra="ignore")

class ResearchBriefContent(BaseModel):
    executive_summary: str
    what_happened: Optional[str] = ""
    why_it_matters: Optional[str] = ""
    who_should_care: Dict[str, str] = Field(
        default_factory=lambda: {
            "founders": "",
            "developers": "",
            "business_operators": "",
            "ai_researchers": "",
        }
    )
    evidence_verification: List[Dict[str, Any]] = Field(default_factory=list)
    facts_vs_analysis: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "facts": [],
            "analysis": [],
            "speculation": [],
        }
    )
    newsletter_angles: List[NewsletterAngle] = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore")

class ResearchBriefUpdate(BaseModel):
    title: Optional[str] = None
    executive_summary: Optional[str] = None
    what_happened: Optional[str] = None
    why_it_matters: Optional[str] = None
    key_developments: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    unanswered_questions: Optional[List[str]] = None
    user_notes: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class ResearchBriefResponse(BaseModel):
    id: str
    project_id: str
    title: Optional[str] = None
    executive_summary: Optional[str] = ""
    what_happened: Optional[str] = ""
    why_it_matters: Optional[str] = ""
    who_should_care: Optional[Dict[str, str]] = Field(default_factory=dict)
    evidence_verification: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    facts_vs_analysis: Optional[Dict[str, List[str]]] = Field(default_factory=dict)
    newsletter_angles: Optional[List[Any]] = Field(default_factory=list)
    recommended_angle: Optional[Any] = None
    brief_content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    evidence: Optional[List[Any]] = Field(default_factory=list)
    is_user_edited: Optional[bool] = False
    user_notes: Optional[str] = None
    version: Optional[int] = 1
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")

class ResearchBriefExportResponse(BaseModel):
    project_id: str
    brief_id: str
    title: str
    markdown_content: str
    plain_text_content: str
    json_content: str
    format: str = "markdown"
    exported_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectResponse(BaseModel):
    id: str
    title: str
    topic: Optional[str] = None
    description: Optional[str] = None
    research_objective: Optional[str] = None
    target_audience: Optional[str] = None
    research_scope: Optional[str] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    preferred_source_types: Optional[List[str]] = Field(default_factory=list)
    status: str
    organization_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sources: List[SourceResponse] = Field(default_factory=list)
    briefs: List[ResearchBriefResponse] = Field(default_factory=list)
    brief: Optional[ResearchBriefResponse] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")

class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
