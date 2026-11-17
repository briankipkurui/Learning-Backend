from sqlalchemy import Column, String, ForeignKey, Text, Boolean, DateTime, Integer, Numeric, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, object_session
from models.base import BaseModel
from sqlalchemy.sql import func, select

class CourseModel(BaseModel):
    """
        Main course model containing course information.
    """
    __tablename__ = "courses"

    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    language = Column(String(100), default="en")
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="EUR")
    published_at = Column(DateTime, nullable=True)
    thumbnail_url = Column(String(255), nullable=True)
    preview_video_url = Column(String(255), nullable=True)
    is_featured = Column(Boolean, default=False)
    isDeleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="SET NULL"), nullable=False)
    certificate_enabled = Column(Boolean, default=True)
    course_status_id = Column(UUID(as_uuid=True), ForeignKey("course_statuses.Id"), nullable=False)

    status = relationship("CourseStatusLookup", back_populates="courses")
    creator = relationship("UserModel", back_populates="created_courses")
    modules = relationship("ModuleModel", back_populates="course")
    enrollments = relationship("EnrollmentModel", back_populates="enrolled_course")

    def __repr__(self):
        return f"<Course(Id={self.Id}, title={self.title})>"
    

class ModuleModel(BaseModel):
    """
        Model for course modules.
    """
    __tablename__ = "modules"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.Id"), nullable=False)
    is_free = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="SET NULL"), nullable=False)

    course = relationship("CourseModel", back_populates="modules")
    lessons = relationship("LessonModel", back_populates="module")
    user_progress = relationship("LearnerModuleProgressModel", back_populates="module")
    creator = relationship("UserModel", back_populates="created_modules")

    __table_args__ = (
        UniqueConstraint('course_id', 'sort_order', name='uq_course_sort'),
    )

    def __repr__(self):
        return f"<Module(Id={self.Id}, title={self.title})>"
    
    @property
    def last_lesson_sort_order(self) -> int:
        """Get the highest sort order among the module's lessons"""
        if not self.lessons:
            return 0
        return max(lesson.sort_order for lesson in self.lessons)


class LessonModel(BaseModel):
    """
        Model for course lessons.
    """

    __tablename__ = "lessons"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.Id", ondelete="CASCADE"), nullable=False)
    content_type_id = Column(UUID(as_uuid=True), ForeignKey("lesson_content_types.Id"), nullable=False)
    content_url = Column(String(255), nullable=True)
    content_text = Column(Text, nullable=True)
    estimated_duration = Column(Integer, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="SET NULL"), nullable=False)

    module = relationship("ModuleModel", back_populates="lessons")
    content_type = relationship("LessonContentType", back_populates="lessons")
    lesson_progress = relationship("LearnerLessonProgressModel", back_populates="lesson")
    creator = relationship("UserModel", back_populates="created_lessons")
    resources = relationship("LessonResourceModel", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('module_id', 'sort_order', name='uq_module_sort'),
        CheckConstraint(
            "content_url IS NOT NULL OR content_text IS NOT NULL",
            name="check_lesson_content"
        ),
    )

    def __repr__(self):
        return f"<Lesson(Id={self.Id}, title={self.title})>"
    
    @property
    def is_module_first_lesson(self) -> bool:
        """Check if this lesson is the first in its module"""

        
        session = object_session(self)
        if not session:
            return False
            
        # Get the minimum sort_order for this module
        min_sort_order = session.scalar(
            select(func.min(LessonModel.sort_order))
            .where(LessonModel.module_id == self.module_id)
        )
        
        return self.sort_order == min_sort_order
    
class CourseImages(BaseModel):
    """
        Model for course images used in lesson content.
        These Images help us to host images used in lesson content locally.
    """

    __tablename__ = "course_images"

    image_url = Column(String(255), nullable=False)
    image_name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<CourseImage(Id={self.Id}, url={self.name})>"

class LessonResourceModel(BaseModel):
    """
        Model for lesson resources.
    """

    __tablename__ = "lesson_resources"

    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.Id", ondelete="CASCADE"), nullable=False)
    resource_name = Column(String(255), nullable=False)
    resource_url = Column(String(255), nullable=False)
    is_downloadable = Column(Boolean, default=True)

    lesson = relationship("LessonModel", back_populates="resources")

    def __repr__(self):
        return f"<LessonResource(Id={self.Id}, name={self.resource_name})>"


class EnrollmentModel(BaseModel):
    """
        Course enrollments.
        Includes access to CV analysis and interview practice features.
        Access expires after expires_at date.
    """

    __tablename__ = "enrollments"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.Id"), nullable=False)
    purchased_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    purchase_completed = Column(Boolean, default=False)
    payment_reference = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Enrollment expiry date (3 months from purchase)

    user_enrollments = relationship("UserModel", back_populates="enrollments")
    enrolled_course = relationship("CourseModel", back_populates="enrollments")
    progress = relationship("LearnerCourseProgressModel", back_populates="enrollment")
    certificate = relationship("CompletionCertificateModel", back_populates="enrollment", uselist=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='uq_enrollment_user_course'),
    )

    def __repr__(self):
        return f"<Enrollment(Id={self.Id}, purchase_completed={self.purchase_completed}, user_id={self.user_id}, course_id={self.course_id})>"


class EnrollmentPurchaseModel(BaseModel):
    """
        Purchase history for course enrollments.
        Tracks each payment made for a course (initial purchase and renewals).
    """

    __tablename__ = "enrollment_purchases"

    enrollment_id = Column(UUID(as_uuid=True), ForeignKey("enrollments.Id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False, comment="Amount paid in cents")
    currency = Column(String(3), nullable=False, default="EUR")
    payment_reference = Column(String(255), nullable=True, comment="Stripe payment intent ID")
    purchased_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_renewal = Column(Boolean, default=False, comment="True if this is a renewal purchase")

    enrollment = relationship("EnrollmentModel", backref="purchases")
    user = relationship("UserModel", backref="enrollment_purchases")

    def __repr__(self):
        return f"<EnrollmentPurchase(Id={self.Id}, enrollment_id={self.enrollment_id}, amount={self.amount})>"


class LearnerLessonProgressModel(BaseModel):
    """
        Lesson Progress Tracking.
    """

    __tablename__ = "learner_lesson_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), index=True, nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.Id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_last_viewed = Column(Boolean, default=False)

    learner = relationship("UserModel", back_populates="lesson_progress")
    lesson = relationship("LessonModel", back_populates="lesson_progress")

    __table_args__ = (
        UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress'),
        CheckConstraint('completed_at IS NULL OR started_at IS NOT NULL', name='ck_lesson_progress_dates')
    )

    def __repr__(self):
        return f"<UserLessonProgress(Id={self.Id}, user_id={self.user_id}, lesson_id={self.lesson_id})>"
    

class LearnerModuleProgressModel(BaseModel):
    """
        Module progress tracking for learners.
    """

    __tablename__ = "learner_module_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.Id", ondelete="CASCADE"), index=True, nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("modules.Id", ondelete="CASCADE"), index=True, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)

    learner = relationship("UserModel", back_populates="module_progress")
    module = relationship("ModuleModel", back_populates="user_progress")

    __table_args__ = (
        UniqueConstraint('user_id', 'module_id', name='uq_user_module_progress'),
    )

    def __repr__(self):
        return f"<LearnerModuleProgress(Id={self.Id}, user_id={self.user_id}, module_id={self.module_id})>"


class LearnerCourseProgressModel(BaseModel):
    """
        Course learning Progress tracking.
    """

    __tablename__ = "learner_course_progress"
    
    enrollment_id = Column(UUID, ForeignKey("enrollments.Id", ondelete="CASCADE"), index=True, nullable=False)
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    enrollment = relationship("EnrollmentModel", back_populates="progress")

    __table_args__ = (
        UniqueConstraint('enrollment_id', name='uq_enrollment_progress'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='ck_valid_progress_percentage'),
    )


class CompletionCertificateModel(BaseModel):
    """
        Course Completion Certificate.
    """

    __tablename__ = "certificates"

    enrollment_id = Column(UUID, ForeignKey("enrollments.Id", ondelete="CASCADE"), index=True, nullable=False)
    certificate_url = Column(String(255))
    issued_at = Column(DateTime)
    certificate_number = Column(String(100), unique=True)

    enrollment = relationship("EnrollmentModel", back_populates="certificate")

    __table_args__ = (
        UniqueConstraint('enrollment_id', name='uq_enrollment_certificate'),
        CheckConstraint('certificate_url IS NOT NULL', name='ck_certificate_url_required'),
        CheckConstraint('certificate_number IS NOT NULL', name='ck_certificate_number_required'),
    )

class CourseStatusLookup(BaseModel):
    """
        Lookup table for course statuses.
    """

    __tablename__ = "course_statuses"

    name = Column(String(100), nullable=False, index=True, unique=True)
    courses = relationship("CourseModel", back_populates="status")

    def __repr__(self):
        return f"<CourseStatus(Id={self.Id}, name={self.name})>"

class LessonContentType(BaseModel):
    """
        Model for lesson content types.
    """
    __tablename__ = "lesson_content_types"

    name = Column(String(100), nullable=False, index=True)
    lessons = relationship("LessonModel", back_populates="content_type")

    def __repr__(self):
        return f"<LessonContentType(Id={self.Id}, name={self.name})>"
