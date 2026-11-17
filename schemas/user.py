"""
User-related Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID

# Enums
class UserTypeEnum(str, Enum):
    LEARNER = "Learner"
    ADMIN = "Admin"

class UserStatusEnum(str, Enum):
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    

class GoogleAuth(BaseModel):
    token: str

# Base schemas
class UserBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr

class UserCreate(UserBase):
    user_type: UserTypeEnum = UserTypeEnum.LEARNER
    account_verified: bool = False

class CreateUserWithPassword(UserCreate):
    password: str

class VerifyAccountRequest(BaseModel):
    user_id: UUID
    otp: str

class EmailRequest(BaseModel):
    email: EmailStr

class LoginWithEmail(EmailRequest):
    password: str

class ResetPasswordRequest(BaseModel):
    user_id: UUID
    otp: str
    new_password: str

class ResendOTPRequest(BaseModel):
    user_id: UUID

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None

class EnrollmentResponse(BaseModel):
    Id: UUID
    user_id: UUID
    course_id: UUID
    purchased_at: Optional[datetime] = None
    purchase_completed: bool = False
    expires_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    Id: UUID
    user_type: UserTypeEnum
    created_at: datetime
    email: EmailStr
    updated_at: Optional[datetime] = None
    account_verified: bool
    is_active: bool
    learner_profile: Optional["LearnerProfileResponse"] = None
    admin_profile: Optional["AdminProfileResponse"] = None
    enrollments: Optional[List["EnrollmentResponse"]] = None
    
    model_config = ConfigDict(from_attributes=True)

class UpdateUserStatus(BaseModel):
    status: UserStatusEnum  # "activate" or "deactivate"

class PaginatedUserResponse(BaseModel):
    users: List["UserResponse"]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool

    

# Profile schemas
class LearnerProfileBase(BaseModel):
    bio: Optional[str] = None
    country: Optional[str] = None
    profession_id: Optional[UUID] = None
    industry: Optional[str] = None
    experience: Optional[int] = None
    age_group_id: Optional[UUID] = None

class ProfessionResponse(BaseModel):
    Id: UUID
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class LearnerProfileResponse(LearnerProfileBase):
    Id: UUID
    user_id: UUID
    age_group: Optional["AgeGroupResponse"] = None
    profession: Optional["ProfessionResponse"] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class AdminProfileBase(BaseModel):
    role: str = "admin"

class AdminProfileResponse(AdminProfileBase):
    Id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class AgeGroupResponse(BaseModel):
    Id: UUID
    name: str
    min_age: int
    max_age: int
    sort_order: int
    
    model_config = ConfigDict(from_attributes=True)
