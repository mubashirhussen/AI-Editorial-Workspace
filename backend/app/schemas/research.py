from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.schemas.source import SourceResponse

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    organization_id: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
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
