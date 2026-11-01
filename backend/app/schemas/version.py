from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EditorialVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    document_type: str
    document_id: str
    version_number: int
    title: Optional[str] = None
    content_snapshot: str
    change_summary: str
    change_type: str
    created_by: Optional[str] = None
    author_name: Optional[str] = None
    created_at: datetime
    word_count: int
    char_count: int

class DiffChunk(BaseModel):
    type: str  # "addition", "deletion", "unchanged"
    text: str

class WordDiffChunk(BaseModel):
    type: str  # "insert", "delete", "equal"
    text: str

class VersionComparisonResponse(BaseModel):
    document_type: str
    document_id: str
    version_a: EditorialVersionResponse
    version_b: EditorialVersionResponse
    word_count_a: int
    word_count_b: int
    word_count_diff: int
    char_count_a: int
    char_count_b: int
    char_count_diff: int
    additions_count: int
    deletions_count: int
    unchanged_count: int
    diff_chunks: List[DiffChunk]
    word_diff_chunks: List[WordDiffChunk]

class RestoreVersionRequest(BaseModel):
    confirm: bool = True
    note: Optional[str] = None

class RestoreVersionResponse(BaseModel):
    success: bool
    message: str
    document_type: str
    document_id: str
    restored_from_version: int
    new_version: EditorialVersionResponse
    updated_content: str
