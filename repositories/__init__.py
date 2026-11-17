"""
Career Elevate Backend Repositories Package

This package contains all repository classes for data access layer and manipulation.
"""

from .user_repository import UserRepository
from .course_repository import CourseRepository
from .module_repository import ModuleRepository
from .job_application_repository import JobApplicationRepository
from .profession_repository import ProfessionRepository
from .policy_repository import PolicyRepository

__all__ = [
    "UserRepository",
    "CourseRepository",
    "ModuleRepository",
    "JobApplicationRepository",
    "ProfessionRepository",
    "PolicyRepository"
]