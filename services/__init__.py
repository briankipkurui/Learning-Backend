"""
Career Elevate Backend Services Package.

This package contains all service classes for business logic and operations.
"""

from .user_service import UserService
from .auth_service import AuthService
from .course_service import CourseService
from .module_service import ModuleService
from .mailing_service import EmailService
from .aws_s3_service import S3Service
from .job_application_service import JobApplicationService
from .certificate_service import CertificateGenerationService
from .ai_service import AIService
from .profession_service import ProfessionService
from .policy_service import PolicyService

__all__ = [
    "UserService",
    "AuthService",
    "CourseService",
    "EmailService",
    "ModuleService",
    "S3Service",
    "JobApplicationService",
    "CertificateGenerationService",
    "AIService",
    "ProfessionService",
    "PolicyService"
]