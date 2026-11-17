"""
Career Elevate Backend Models Package

This package contains all SQLAlchemy models organized by domain.
Import models from here for consistency across the application.
"""

# Database components
from .database import Base, engine, SessionLocal, get_database

# Base model
from .base import BaseModel

# User models
froUserModelm .user import , LearnerProfileModel, AdminProfileModel, RefreshTokenModel, OTPModel, AgeGroupModel, ProfessionModel

# Course models
from .course import (
    CourseModel, 
    ModuleModel, 
    LessonModel, 
    EnrollmentModel,
    EnrollmentPurchaseModel,
    LearnerLessonProgressModel, 
    LearnerModuleProgressModel,
    LearnerCourseProgressModel, 
    CompletionCertificateModel,
    CourseStatusLookup,
    LessonContentType,
    LessonResourceModel,
    CourseImages,
)

# Job application models
from .job_applications import (
    ResumeModel, 
    JobApplicationModel, 
    JobApplicationActivityModel, 
    ActivityTypeModel, 
    CVAnalysisModel, 
    InterviewQuestionModel,
    InterviewPracticeSessionModel
)

# Policy models
from .policy import (
    PolicyTypeModel,
    PolicyModel,
    PolicyAcknowledgementModel
)

# Export all models for easy imports
__all__ = [
    # Database
    "Base",
    "engine", 
    "SessionLocal",
    "get_database",
    
    # Base
    "BaseModel",
    
    # User models
    "UserModel", 
    "LearnerProfileModel",
    "AdminProfileModel",
    "RefreshTokenModel",
    "OTPModel",
    "AgeGroupModel",
    "ProfessionModel",
    
    # Course models
    "CourseModel",
    "ModuleModel",
    "LessonModel", 
    "EnrollmentModel",
    "LearnerLessonProgressModel",
    "LearnerModuleProgressModel",
    "LearnerCourseProgressModel",
    "CompletionCertificateModel",
    "CourseStatusLookup",
    "LessonContentType",
    "LessonResourceModel",
    "CourseImages",

    # Job application models
    "ResumeModel",
    "JobApplicationModel",
    "JobApplicationActivityModel",
    "ActivityTypeModel",
    "CVAnalysisModel",
    "InterviewQuestionModel",
    "InterviewPracticeSessionModel",

    # Policy models
    "PolicyTypeModel",
    "PolicyModel",
    "PolicyAcknowledgementModel",
]
