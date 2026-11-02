from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

class ClaimItem(BaseModel):
    claim: str
    evidence: str
    evidence_type: Literal["direct", "reported", "inferred"]
    supporting_excerpt: str
    source_id: Optional[str] = None

class SourceAnalysisSchema(BaseModel):
    source_id: Optional[str] = None
    source_title: str
    source_url: Optional[str] = None
    summary: str
    key_developments: List[str] = Field(default_factory=list)
    important_claims: List[ClaimItem] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    analysis: List[str] = Field(default_factory=list)
    speculation: List[str] = Field(default_factory=list)
    technical_implications: List[str] = Field(default_factory=list)
    business_implications: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    generation_mode: Literal["llm_verified", "deterministic_fallback"] = "deterministic_fallback"

SourceAnalysisResponse = SourceAnalysisSchema

class SourceUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    text_content: Optional[str] = Field(None, max_length=500_000)
    raw_content: Optional[str] = Field(None, max_length=500_000)

class SourceCreate(BaseModel):
    url: Optional[str] = Field(None, max_length=2048)
    title: Optional[str] = Field(None, max_length=255)
    text_content: Optional[str] = Field(None, max_length=500_000)
    source_type: Literal["url", "text"] = "url"

class SourceResponse(BaseModel):
    id: str
    project_id: str
    title: str
    url: Optional[str] = None
    source_type: str
    extracted_content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    extraction_status: str
    error_message: Optional[str] = None
    created_at: datetime
    analysis: Optional[SourceAnalysisSchema] = None

    model_config = ConfigDict(from_attributes=True)

class SourceListResponse(BaseModel):
    items: List[SourceResponse]
    total: int
