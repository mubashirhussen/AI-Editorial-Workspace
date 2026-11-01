from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.app.schemas.source import SourceResponse

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    status: Optional[str] = Field(None, max_length=50)

class NewsletterAngle(BaseModel):
    id: str
    headline: str
    target_audience: str
    angle_pitch: str
    key_points: List[str] = Field(default_factory=list)
    why_now: str

class ResearchBriefContent(BaseModel):
    executive_summary: str
    what_happened: str
    why_it_matters: str
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
    opportunities_and_risks: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "opportunities": [],
            "risks": [],
        }
    )
    newsletter_angles: List[NewsletterAngle] = Field(default_factory=list)
    recommended_story: Dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: List[str] = Field(default_factory=list)

class ResearchBriefResponse(BaseModel):
    id: str
    project_id: str
    executive_summary: str
    brief_content: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    newsletter_angles: List[Dict[str, Any]]
    recommended_angle: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    sources: List[SourceResponse] = Field(default_factory=list)
    briefs: List[ResearchBriefResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
