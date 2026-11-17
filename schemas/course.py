from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class CourseBase(BaseModel):
    title: str
    price: float
    description: Optional[str] = None

class CourseCreate(CourseBase):
    slug: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    is_featured: bool = False
    course_status_id: Optional[UUID] = None
    created_by: UUID

class CourseUpdate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    thumbnail_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    slug: Optional[str] = None

class UpdateModule(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_free: Optional[bool] = None

class ModuleBase(UpdateModule):
    course_id: UUID
    created_by: UUID

class ModuleResponse(ModuleBase):
    Id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

class ModuleWithLessonsResponse(ModuleResponse):
    lessons: list["LessonResponse"] = []

class UpdateLesson(BaseModel):
    title: str
    description: Optional[str] = None
    sort_order: int
    content_type_id: UUID
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    estimated_duration: int

class LessonBase(BaseModel):
    title: str
    description: str | None = None
    sort_order: int
    module_id: UUID
    created_by: UUID
    content_type_id: UUID
    content_url: str | None = None
    content_text: str | None = None
    estimated_duration: int | None = None

class LessonResponse(LessonBase):
    Id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class LessonResourceBase(BaseModel):
    lesson_id: UUID
    resource_url: str
    resource_name: str
    is_downloadable: bool | None = None


class EnrollmentPurchaseResponse(BaseModel):
    """Response schema for enrollment purchase records"""
    Id: UUID
    enrollment_id: UUID
    user_id: UUID
    amount: int
    currency: str
    payment_reference: Optional[str] = None
    purchased_at: datetime
    is_renewal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentPurchaseHistoryResponse(BaseModel):
    """Response schema for enrollment purchase history"""
    enrollment_id: UUID
    course_id: UUID
    course_title: str
    purchases: List[EnrollmentPurchaseResponse]
    total_spent: int
    currency: str

    class Config:
        from_attributes = True