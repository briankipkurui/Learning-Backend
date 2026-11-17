"""
Common schemas used across multiple domains
"""
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar('T')

class SuccessResponse(BaseModel):
    """Standard success response format"""
    success: bool = True
    message: str
    timestamp: datetime = datetime.utcnow()

class ErrorResponse(BaseModel):
    """Standard error response format"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool

class PaginationResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    data: List[T]
    meta: PaginationMeta

class IDResponse(BaseModel):
    """Simple ID response for creation operations"""
    Id: str
    message: str = "Created successfully"
