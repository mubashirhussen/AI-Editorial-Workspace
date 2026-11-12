from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EditorialSourceRef(BaseModel):
    index: int
    source_id: Optional[str] = None
    title: str
    url: Optional[str] = None
    citation_text: Optional[str] = ""
    supported_claim: Optional[str] = None
    supporting_excerpt: Optional[str] = None
    evidence_classification: Optional[str] = "reported"

class HeadlineOption(BaseModel):
    headline: str
    editorial_angle: str
    explanation: str

class HeadlineGenerateRequest(BaseModel):
    project_id: str
    research_brief_id: Optional[str] = None
    audience: Optional[str] = "founders, builders, and operators"
    editorial_angle: Optional[str] = None
    tone: Optional[str] = "Newsletter-style"

class HeadlineGenerateResponse(BaseModel):
    project_id: str
    headlines: List[HeadlineOption] = Field(default_factory=list)
    recommended_headline: Optional[str] = None

class EditorialGenerateRequest(BaseModel):
    project_id: str
    research_brief_id: Optional[str] = None
    headline: Optional[str] = Field(None, max_length=500)
    selected_headline: Optional[str] = Field(None, max_length=500)
    angle_headline: Optional[str] = Field(None, max_length=500) # Backward compatibility
    audience: Optional[str] = Field("founders, builders, and operators", max_length=255)
    target_audience: Optional[str] = Field(None, max_length=255) # Backward compatibility
    editorial_angle: Optional[str] = Field(None, max_length=500)
    tone: Optional[str] = Field("Newsletter-style", max_length=100)
    min_words: Optional[int] = Field(300, ge=50, le=2000)
    max_words: Optional[int] = Field(500, ge=50, le=3000)
    key_takeaway: Optional[str] = Field(None, max_length=1000)

class EditorialCreateRequest(BaseModel):
    project_id: str
    headline: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=500_000)
    draft_id: Optional[str] = None
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    status: Optional[str] = Field("draft", max_length=50)

class EditorialUpdateRequest(BaseModel):
    headline: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, max_length=500_000)
    status: Optional[str] = Field(None, max_length=50)

class EditorialResponse(BaseModel):
    id: str
    project_id: str
    draft_id: Optional[str] = None
    title: Optional[str] = None
    headline: str
    content: str
    word_count: int
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

EditorialOutputResponse = EditorialResponse

class EditorialExportResponse(BaseModel):
    editorial_id: str
    headline: str
    markdown_content: str
    plain_text_content: str
    html_content: Optional[str] = None
    json_content: Optional[str] = None
    format: str = "markdown"
    word_count: int
    exported_at: datetime
