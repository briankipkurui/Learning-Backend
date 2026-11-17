"""
Controllers package for Career Elevate Backend API.
This package contains all FastAPI route handlers organized by domain.
"""

from .auth_controller import AuthController
from .user_controller import UserController
from .user_controller import HealthController
from .course_controller import CourseController
from .module_controller import ModuleController
from .job_application_controller import JobApplicationController
from .ai_controller import AIController
from .profession_controller import ProfessionController
from .policy_controller import PolicyController

__all__ = [
    "AuthController",
    "UserController",
    "HealthController",
    "CourseController",
    "ModuleController",
    "JobApplicationController",
    "AIController",
    "ProfessionController",
    "PolicyController"
]