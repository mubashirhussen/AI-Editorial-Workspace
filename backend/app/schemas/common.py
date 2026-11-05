from typing import Generic, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")

class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 50
    total: int = 0
    total_pages: int = 1
    model_config = ConfigDict(extra="ignore")

class ApiErrorDetail(BaseModel):
    code: str
    details: Optional[Any] = None
    model_config = ConfigDict(extra="ignore")

class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: ApiErrorDetail
    request_id: Optional[str] = None
    detail: Optional[Any] = None  # Backward compatibility
    model_config = ConfigDict(extra="ignore")

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    meta: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(extra="ignore")

class PaginatedApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Items retrieved successfully"
    data: List[T] = Field(default_factory=list)
    meta: PaginationMeta
    model_config = ConfigDict(extra="ignore")
