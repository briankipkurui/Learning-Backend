from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import List

class JobApplicationBase(BaseModel):
    company_name: str
    position: str
    application_date: datetime | None = None
    job_application_url: str | None = None
    resume_url: str | None = None
    cover_letter_url: str | None = None
    notes: str | None = None

class JobApplicationCreate(JobApplicationBase):
    user_id: UUID

class JobApplicationInDB(JobApplicationBase):
    Id: UUID
    user_id: UUID
    activities: List['JobApplicationActivityInDB'] = []
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class JobApplicationActivityBase(BaseModel):
    activity_type_id: UUID
    notes: str | None = None

class JobApplicationActivityCreate(JobApplicationActivityBase):
    job_application_id: UUID

class JobApplicationActivityInDB(JobApplicationActivityBase):
    Id: UUID
    job_application_id: UUID
    activity_type: 'JobApplicationActivityTypeInDB'
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class JobApplicationActivityTypeInDB(BaseModel):
    Id: UUID
    name: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class UpdateComments(BaseModel):
    comments: str
class ResumeBase(UpdateComments):
    user_id: UUID

class ResumeCreate(ResumeBase):
    file_url: str

class ResumeInDB(ResumeCreate):
    Id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)