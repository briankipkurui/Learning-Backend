"""
Career Elevate Backend API Schemas

This package contains all Pydantic models used for API request/response validation.
These are separate from database models (SQLAlchemy) for clean separation of concerns.
"""

# User schemas
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse,
    LearnerProfileResponse, AdminProfileResponse,
    UserTypeEnum, LearnerProfileBase, AdminProfileBase, LearnerProfileResponse,
    UpdateUserStatus, LoginWithEmail, ResendOTPRequest, ResetPasswordRequest,
    CreateUserWithPassword, VerifyAccountRequest, AgeGroupResponse, EmailRequest, PaginatedUserResponse
)

# Common schemas
from .common import ErrorResponse, PaginationResponse, IDResponse

# Course schemas
from .course import (
    CourseCreate,
    ModuleBase,
    ModuleResponse,
    ModuleWithLessonsResponse,
    UpdateModule,
    LessonBase,
    LessonResponse,
    LessonResourceBase,
    UpdateLesson,
    CourseUpdate,
    EnrollmentPurchaseResponse,
    EnrollmentPurchaseHistoryResponse
)

from .job_applications import (
    ResumeBase, ResumeInDB, 
    ResumeCreate, UpdateComments, 
    JobApplicationBase, JobApplicationCreate, 
    JobApplicationInDB, JobApplicationActivityBase, 
    JobApplicationActivityCreate, JobApplicationActivityInDB, 
    JobApplicationActivityTypeInDB
)

# AI schemas
from .ai import (
    CreateInterviewQuestionRequest,
    UpdateInterviewQuestionRequest,
    InterviewQuestionResponse,
    PaginatedInterviewQuestionsResponse
)

# Profession schemas
from .profession import (
    ProfessionBase,
    CreateProfessionRequest,
    UpdateProfessionRequest,
    ProfessionResponse
)

# Policy schemas
from .policy import (
    PolicyTypeBase,
    CreatePolicyTypeRequest,
    UpdatePolicyTypeRequest,
    PolicyTypeResponse,
    PolicyBase,
    CreatePolicyRequest,
    UpdatePolicyRequest,
    PolicyResponse
)


# Export all schemas for easy imports
__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse",
    "LearnerProfileResponse", "AdminProfileResponse",
    "UserTypeEnum", "LearnerProfileBase", "AdminProfileBase", "LearnerProfileResponse",
    "UpdateUserStatus", "OTPModel", "LoginWithEmail", "ResendOTPRequest", "ResetPasswordRequest",
    "CreateUserWithPassword", "VerifyAccountRequest", "AgeGroupResponse", "EmailRequest",
    "PaginatedUserResponse",

    # Common schemas
    "SuccessResponse", "ErrorResponse", "PaginationResponse", "IDResponse",

    # Course schemas
    "CourseCreate", "CourseUpdate", "ModuleBase", "ModuleResponse", 
    "ModuleWithLessonsResponse", "LessonBase", "LessonResponse", 
    "UpdateModule", "LessonResourceBase", "UpdateLesson",

    # Job application schemas
    "ResumeBase", "ResumeInDB", "ResumeCreate", 
    "UpdateComments", "JobApplicationBase", "JobApplicationCreate", 
    "JobApplicationInDB", "JobApplicationActivityBase", "JobApplicationActivityCreate", 
    "JobApplicationActivityInDB", "JobApplicationActivityTypeInDB",

    # AI schemas
    "CreatePackageRequest", "UpdatePackageRequest", "PurchasePackageRequest", "CompletePurchaseRequest",
    "CreateInterviewPackageRequest", "UpdateInterviewPackageRequest", "PurchaseInterviewPackageRequest", 
    "CompleteInterviewPurchaseRequest", "CreateInterviewQuestionRequest", "UpdateInterviewQuestionRequest",
    "InterviewQuestionResponse", "PaginatedInterviewQuestionsResponse",
    
    # Profession schemas
    "ProfessionBase", "CreateProfessionRequest", "UpdateProfessionRequest", "ProfessionResponse",
    
    # Policy schemas
    "PolicyTypeBase", "CreatePolicyTypeRequest", "UpdatePolicyTypeRequest", "PolicyTypeResponse",
    "PolicyBase", "CreatePolicyRequest", "UpdatePolicyRequest", "PolicyResponse"
]
