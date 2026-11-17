from sqlalchemy import Column, String, ForeignKey, Text, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel
import datetime


class UserModel(BaseModel):
    """
    Main user model containing user information
    """
    __tablename__ = "users"
    
    first_name = Column(String(30), nullable=False)
    middle_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    account_verified = Column(Boolean, default=False)
    user_type = Column(String(50), nullable=False, default="Learner")  # e.g., learner, admin
    
    # Relationships
    learner_profile = relationship("LearnerProfileModel", uselist=False, back_populates="user")
    admin_profile = relationship("AdminProfileModel", uselist=False, back_populates="user", foreign_keys="[AdminProfileModel.user_id]")
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user")
    created_users = relationship("AdminProfileModel", back_populates="created_by", foreign_keys="[AdminProfileModel.creator_id]")
    enrollments = relationship("EnrollmentModel", back_populates="user_enrollments")
    lesson_progress = relationship("LearnerLessonProgressModel", back_populates="learner")
    module_progress = relationship("LearnerModuleProgressModel", back_populates="learner")
    otps = relationship("OTPModel", back_populates="user")
    created_courses = relationship("CourseModel", back_populates="creator")
    created_modules = relationship("ModuleModel", back_populates="creator")
    created_lessons = relationship("LessonModel", back_populates="creator")
    resumes = relationship("ResumeModel", back_populates="user")
    job_applications = relationship("JobApplicationModel", back_populates="owner")
    cv_analyses = relationship("CVAnalysisModel", back_populates="user", cascade="all, delete-orphan")
    interview_practice_sessions = relationship("InterviewPracticeSessionModel", back_populates="user", cascade="all, delete-orphan")
    policy_acknowledgements = relationship("PolicyAcknowledgementModel", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(Id={self.Id}, email={self.email}, is_active={self.is_active})>"

    @property
    def full_name(self):
        """Return the full name of the user"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
class OTPModel(BaseModel):
    """
    Model for storing OTPs for email verification and password reset
    """
    __tablename__ = "otps"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    # Relationships
    user = relationship("UserModel", back_populates="otps")

    def __repr__(self):
        return f"<OTP(Id={self.Id}, user_id={self.user_id}, used={self.used})>"


class LearnerProfileModel(BaseModel):
    """
    Profile information specific to learners
    """
    __tablename__ = "learner_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    experience = Column(Integer, nullable=True)
    age_group_id = Column(UUID(as_uuid=True), ForeignKey("age_groups.Id", ondelete="SET NULL"), nullable=True)
    profession_id = Column(UUID(as_uuid=True), ForeignKey("professions.Id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="learner_profile")
    age_group = relationship("AgeGroupModel", back_populates="profiles")
    profession = relationship("ProfessionModel", back_populates="learner_profiles")
    def __repr__(self):
        return f"<LearnerProfile(Id={self.Id}, user_id={self.user_id})>"
    

class AgeGroupModel(BaseModel):
    """
    Model for predefined age groups.
    Initial values should be seeded in the database.
    """
    __tablename__ = "age_groups"

    name = Column(String(100), nullable=False, unique=True)
    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)
    sort_order = Column(Integer, nullable=False)

    profiles = relationship("LearnerProfileModel", back_populates="age_group")

    def __repr__(self):
        return f"<AgeGroup(Id={self.Id}, name={self.name})>"


class AdminProfileModel(BaseModel):
    """
    Profile information specific to administrators
    """
    __tablename__ = "admin_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), unique=True, nullable=False)
    role = Column(String(100), nullable=False, default="admin")
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.Id"), nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="admin_profile", foreign_keys=[user_id])
    created_by = relationship("UserModel", back_populates="created_users", foreign_keys=[creator_id])
    
    def __repr__(self):
        return f"<AdminProfile(Id={self.Id}, user_id={self.user_id}, role={self.role})>"
    
    
class RefreshTokenModel(BaseModel):
    """
    Model for storing refresh tokens
    """
    __tablename__ = "refresh_tokens"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now() + datetime.timedelta(days=30))
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)


    # Relationships
    user = relationship("UserModel", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(Id={self.Id}, user_id={self.user_id})>"


class ProfessionModel(BaseModel):
    """
    Model for professions/job roles used in interview practice
    """
    __tablename__ = "professions"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    interview_questions = relationship("InterviewQuestionModel", back_populates="profession")
    learner_profiles = relationship("LearnerProfileModel", back_populates="profession")

    def __repr__(self):
        return f"<Profession(Id={self.Id}, name={self.name})>"
