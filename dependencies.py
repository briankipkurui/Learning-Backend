"""
Centralized dependency injection functions for FastAPI

This file contains all dependency providers for services, repositories, 
and other components used throughout the application.
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from services import UserService, AuthService, CourseService, ModuleService, EmailService, S3Service, JobApplicationService, CertificateGenerationService, AIService, ProfessionService, PolicyService
from repositories import UserRepository, CourseRepository, ModuleRepository, JobApplicationRepository, ProfessionRepository, PolicyRepository
from models.database import get_database
from typing import Generator
import os


# Database Dependencies
def get_db() -> Generator[Session, None, None]:
    """Alias for get_database for consistency"""
    yield from get_database()

# Repository Dependencies
def get_user_repository(db: Session = Depends(get_database)) -> UserRepository:
    """Dependency to provide UserRepository"""
    return UserRepository(db)

def get_course_repository(db: Session = Depends(get_database)) -> CourseRepository:
    """Dependency to provide CourseRepository"""
    return CourseRepository(db)

def get_module_repository(db: Session = Depends(get_database)) -> ModuleRepository:
    """Dependency to provide ModuleRepository"""
    return ModuleRepository(db)

def get_job_application_repository(db: Session = Depends(get_database)) -> JobApplicationRepository:
    """Dependency to provide JobApplicationRepository"""
    return JobApplicationRepository(db)

def get_email_service() -> EmailService:
    """Dependency to provide EmailService"""
    return EmailService()

def get_s3_service() -> S3Service:
    """Dependency to provide S3Service"""
    return S3Service(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION"),
        bucket_name=os.getenv("AWS_S3_BUCKET_NAME"),
        cloudfront_domain=os.getenv("CLOUDFRONT_DOMAIN")
    )

def get_certificate_service(s3: S3Service = Depends(get_s3_service)) -> CertificateGenerationService:
    """Dependency to provide CertificateGenerationService"""
    return CertificateGenerationService(s3)

# Service Dependencies
def get_user_service(user_repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Dependency to provide UserService with injected UserRepository"""
    return UserService(user_repository)

def get_course_service(
        course_repository: CourseRepository = Depends(get_course_repository),
        user_repository: UserRepository = Depends(get_user_repository),
        mailing_service: EmailService = Depends(get_email_service),
        certificate_service: CertificateGenerationService = Depends(get_certificate_service)
    ) -> CourseService:
    """Dependency to provide CourseService with injected repositories and services"""
    return CourseService(course_repository, mailing_service, user_repository, certificate_service)

def get_module_service(
        module_repository: ModuleRepository = Depends(get_module_repository),
        course_service: CourseService = Depends(get_course_service)
    ) -> ModuleService:
    """Dependency to provide ModuleService with injected ModuleRepository and CourseService"""
    return ModuleService(module_repository, course_service)

def get_auth_service(
        user_repository: UserRepository = Depends(get_user_repository), 
        mailing_service: EmailService = Depends(get_email_service)
    ) -> AuthService:
    """Dependency to provide AuthService"""
    return AuthService(user_repository, mailing_service)


def get_job_application_service(
        job_application_repository: JobApplicationRepository = Depends(get_job_application_repository)
    ) -> JobApplicationService:
    """Dependency to provide JobApplicationService"""
    return JobApplicationService(job_application_repository)

def get_ai_service(
    job_application_repository: JobApplicationRepository = Depends(get_job_application_repository),
    s3: S3Service = Depends(get_s3_service),
    course_repository: CourseRepository = Depends(get_course_repository)
) -> AIService:
    """Dependency to provide AIService with S3 support and enrollment verification"""
    return AIService(
        job_application_repository=job_application_repository,
        s3_service=s3,
        course_repository=course_repository
    )

def get_profession_repository(db: Session = Depends(get_database)) -> ProfessionRepository:
    """Dependency to provide ProfessionRepository"""
    return ProfessionRepository(db)

def get_profession_service(profession_repository: ProfessionRepository = Depends(get_profession_repository)) -> ProfessionService:
    """Dependency to provide ProfessionService with injected ProfessionRepository"""
    return ProfessionService(profession_repository)

def get_policy_repository(db: Session = Depends(get_database)) -> PolicyRepository:
    """Dependency to provide PolicyRepository"""
    return PolicyRepository(db)

def get_policy_service(policy_repository: PolicyRepository = Depends(get_policy_repository)) -> PolicyService:
    """Dependency to provide PolicyService with injected PolicyRepository"""
    return PolicyService(policy_repository)