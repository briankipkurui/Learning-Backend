from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Boolean, JSON, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import BaseModel

class ResumeModel(BaseModel):
    """
        Model for storing job application resumes
    """
    __tablename__ = "resumes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    file_url = Column(String(255), nullable=False)
    comments = Column(String(255), nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="resumes")

    def __repr__(self):
        return f"<Resume(Id={self.Id}, user_id={self.user_id}, file_url={self.file_url})>"

class JobApplicationModel(BaseModel):
    """
        Model for storing job applications
    """
    __tablename__ = "job_applications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    application_date = Column(DateTime, nullable=True)
    job_application_url = Column(String(255), nullable=True)
    resume_url = Column(String(255), nullable=True)
    cover_letter_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    activities = relationship("JobApplicationActivityModel", back_populates="job_application", order_by="desc(JobApplicationActivityModel.created_at)", cascade="all, delete-orphan")

    # Relationships
    owner = relationship("UserModel", back_populates="job_applications")

    def __repr__(self):
        return f"<JobApplication(Id={self.Id}, user_id={self.user_id}, company_name={self.company_name}, position={self.position})>"

class JobApplicationActivityModel(BaseModel):
    """
        Model for storing activities related to job applications
    """
    __tablename__ = "job_application_activities"

    job_application_id = Column(UUID(as_uuid=True), ForeignKey("job_applications.Id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type_id = Column(UUID(as_uuid=True), ForeignKey("activity_types.Id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)

    # Relationships
    job_application = relationship("JobApplicationModel", back_populates="activities")
    activity_type = relationship("ActivityTypeModel", back_populates="activities")

    def __repr__(self):
        return f"<JobApplicationActivity(Id={self.Id}, job_application_id={self.job_application_id}, activity_type={self.activity_type_id})>"

class ActivityTypeModel(BaseModel):
    """
        Model for predefined activity types.
        Initial values should be seeded in the database.
    """
    __tablename__ = "activity_types"

    name = Column(String(100), nullable=False, unique=True)
    is_custom = Column(Boolean, default=False)

    # Relationships
    activities = relationship("JobApplicationActivityModel", back_populates="activity_type")

    def __repr__(self):
        return f"<ActivityType(Id={self.Id}, name={self.name})>"

class CVAnalysisModel(BaseModel):
    """
        Model for storing CV analysis results
    """
    __tablename__ = "cv_analysis"

    job_title = Column(String(100), nullable=False)
    analysis_result = Column(JSON, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    new_resume_url = Column(String(255), nullable=True)
    old_resume_url = Column(String(255), nullable=True)
    jd_url = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=True)
    jd_text = Column(Text, nullable=True)

    user = relationship("UserModel", back_populates="cv_analyses")

    def __repr__(self):
        return f"<CVAnalysis(Id={self.Id}, job_title={self.job_title})>"

    
class InterviewQuestionModel(BaseModel):
    """
    Predefined interview questions
    """
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint('question_text', 'profession_id', 'category', name='uq_question_profession_category'),
    )

    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=True)
    framework = Column(String(100), nullable=True)
    skills_tested = Column(String(255), nullable=True)
    framework_description = Column(Text, nullable=True)
    good_answer_criteria = Column(Text, nullable=True)
    listening_guideline = Column(Text, nullable=True)
    common_issues = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    time_limit = Column(Integer, nullable=True)  # in minutes
    profession_id = Column(UUID(as_uuid=True), ForeignKey("professions.Id", ondelete="SET NULL"), nullable=True)

    # Relationships
    sessions = relationship("InterviewPracticeSessionModel", back_populates="question")
    profession = relationship("ProfessionModel", back_populates="interview_questions")

    def __repr__(self):
        return f"<InterviewQuestion(Id={self.Id}, category={self.category})>"


class InterviewPracticeSessionModel(BaseModel):
    """
    Tracks each interview practice session (persists responses)
    """
    __tablename__ = "interview_practice_sessions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("interview_questions.Id", ondelete="RESTRICT"), nullable=False, index=True)
    audio_file_url = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    
    analysis_result = Column(JSON, nullable=False)

    duration_seconds = Column(Integer, nullable=True)

    # Relationships
    user = relationship("UserModel", back_populates="interview_practice_sessions")
    question = relationship("InterviewQuestionModel", back_populates="sessions")

    def __repr__(self):
        return f"<InterviewPracticeSession(Id={self.Id}, user_id={self.user_id}, question_id={self.question_id})>"

