from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_, text
from schemas import CourseCreate, CourseUpdate
from models import (
    CourseModel, ModuleModel, 
    CourseStatusLookup, LessonModel,
    EnrollmentModel, EnrollmentPurchaseModel, LearnerCourseProgressModel,
    LearnerModuleProgressModel, CompletionCertificateModel as CertificateModel,
    LearnerLessonProgressModel
)
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional

# Enrollment expiry period (3 months)
ENROLLMENT_EXPIRY_DAYS = 90

class CourseRepository:
    def __init__(self, db: Session):
        """
        Initialize course repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_course(self, course_data: CourseCreate) -> CourseModel:
        """
        Create a new course.
        
        Args:
            course_data: Course creation data
        
        Returns:
            CourseModel: The created course
        """
        course_dict = course_data.model_dump()
        db_course = CourseModel(**course_dict)
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return db_course
    
    def update_course(self, course_id: UUID, course_data: CourseUpdate) -> CourseModel:
        """
        Update course fields.
        
        Args:
            course_id: UUID of the course to update
            course_data: Updated course data
        
        Returns:
            CourseModel: The updated course
        """
        course = self.db.query(CourseModel).filter(CourseModel.Id == course_id).first()
        
        # Update all provided fields
        update_data = course_data.model_dump()
        for field, value in update_data.items():
            if value is not None:  # Only update non-None values
                setattr(course, field, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def learn_course_custom_sql(self, course_id: UUID, user_id: UUID) -> dict | None:
        """
        Get comprehensive course learning data with progress using custom SQL.
        Returns structured dict with course, modules, lessons, and user progress.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            dict: Structured course data with embedded progress, or None if not found
        """
        sql_query = text("""
            WITH course_data AS (
                SELECT 
                    -- Enrollment and Course Progress
                    e."Id" as enrollment_id,
                    e.user_id,
                    e.course_id,
                    e.purchased_at,
                    e.purchase_completed,
                    e.expires_at as enrollment_expires_at,
                    
                    -- Course Progress
                    cp.progress as course_progress_percentage,
                    cp.is_completed as course_is_completed,
                    cp.completed_at as course_completed_at,
                    
                    -- Course Details
                    c."Id" as course_id,
                    c.title as course_title,
                    c.description as course_description,
                    c.price as course_price,
                    c.currency as course_currency,
                    c.thumbnail_url as course_thumbnail_url,
                    c.preview_video_url as course_preview_video_url,
                    c.is_featured as course_is_featured,
                    c.certificate_enabled as course_certificate_enabled,
                    
                    -- Course Status
                    cs.name as course_status_name,
                    
                    -- Module Details with Progress
                    m."Id" as module_id,
                    m.title as module_title,
                    m.description as module_description,
                    m.sort_order as module_sort_order,
                    m.is_free as module_is_free,
                    
                    -- Module Progress
                    mp.is_completed as module_is_completed,
                    mp.started_at as module_started_at,
                    mp.completed_at as module_completed_at,
                    
                    -- Lesson Details with Progress
                    l."Id" as lesson_id,
                    l.title as lesson_title,
                    l.description as lesson_description,
                    l.sort_order as lesson_sort_order,
                    l.content_url as lesson_content_url,
                    l.content_text as lesson_content_text,
                    l.estimated_duration as lesson_estimated_duration,
                    
                    -- Lesson Progress
                    lp.is_completed as lesson_is_completed,
                    lp.started_at as lesson_started_at,
                    lp.completed_at as lesson_completed_at,
                    lp.is_last_viewed as lesson_is_last_viewed,
                    
                    -- Content Type
                    lct.name as lesson_content_type_name
                    
                FROM enrollments e
                
                -- Join course and course status
                INNER JOIN courses c ON e.course_id = c."Id"
                INNER JOIN course_statuses cs ON c.course_status_id = cs."Id"
                
                -- Join course progress (LEFT JOIN because progress might not exist yet)
                LEFT JOIN learner_course_progress cp ON e."Id" = cp.enrollment_id
                
                -- Join modules
                INNER JOIN modules m ON c."Id" = m.course_id
                
                -- Join module progress (LEFT JOIN because progress might not exist yet)
                LEFT JOIN learner_module_progress mp ON m."Id" = mp.module_id AND mp.user_id = e.user_id
                
                -- Join lessons
                INNER JOIN lessons l ON m."Id" = l.module_id
                
                -- Join lesson content type
                INNER JOIN lesson_content_types lct ON l.content_type_id = lct."Id"
                
                -- Join lesson progress (LEFT JOIN because progress might not exist yet)
                LEFT JOIN learner_lesson_progress lp ON l."Id" = lp.lesson_id AND lp.user_id = e.user_id
                
                WHERE e.course_id = :course_id 
                  AND e.user_id = :user_id
                  AND c."isDeleted" = false
                  AND (e.expires_at IS NULL OR e.expires_at > NOW())
                
                ORDER BY m.sort_order, l.sort_order
            ),
            lesson_resources AS (
                SELECT 
                    lr.lesson_id,
                    json_agg(
                        json_build_object(
                            'Id', lr."Id",
                            'resource_name', lr.resource_name,
                            'resource_url', lr.resource_url,
                            'is_downloadable', lr.is_downloadable,
                            'created_at', lr.created_at
                        ) ORDER BY lr.created_at
                    ) as resources
                FROM lesson_resources lr
                INNER JOIN lessons l ON lr.lesson_id = l."Id"
                INNER JOIN modules m ON l.module_id = m."Id"
                INNER JOIN courses c ON m.course_id = c."Id"
                INNER JOIN enrollments e ON c."Id" = e.course_id
                WHERE e.course_id = :course_id 
                  AND e.user_id = :user_id
                GROUP BY lr.lesson_id
            )
            
            SELECT 
                cd.*,
                COALESCE(lr.resources, '[]'::json) as lesson_resources
            FROM course_data cd
            LEFT JOIN lesson_resources lr ON cd.lesson_id = lr.lesson_id
        """)
        
        result = self.db.execute(sql_query, {
            'course_id': str(course_id),
            'user_id': str(user_id)
        }).fetchall()
        
        if not result:
            return None
            
        return self._structure_course_data(result)
    
    def _structure_course_data(self, raw_data) -> dict:
        """
        Convert raw SQL result into structured course data with embedded progress.
        """
        if not raw_data:
            return None
            
        first_row = raw_data[0]
        
        # Build course structure
        course_data = {
            # Enrollment info
            'enrollment': {
                'Id': first_row.enrollment_id,
                'user_id': first_row.user_id,
                'course_id': first_row.course_id,
                'purchased_at': first_row.purchased_at,
                'purchase_completed': first_row.purchase_completed,
                'expires_at': first_row.enrollment_expires_at,
            },
            
            # Course with embedded progress
            'course': {
                'Id': first_row.course_id,
                'title': first_row.course_title,
                'description': first_row.course_description,
                'price': first_row.course_price,
                'currency': first_row.course_currency,
                'thumbnail_url': first_row.course_thumbnail_url,
                'preview_video_url': first_row.course_preview_video_url,
                'is_featured': first_row.course_is_featured,
                'certificate_enabled': first_row.course_certificate_enabled,
                
                # Embedded course progress
                'is_completed': first_row.course_is_completed or False,
                'progress_percentage': first_row.course_progress_percentage or 0,
                'completed_at': first_row.course_completed_at,
                
                # Course status
                'status': {
                    'name': first_row.course_status_name,
                },
                
                'modules': []
            }
        }
        
        # Group data by modules and lessons
        modules_dict = {}
        
        for row in raw_data:
            module_id = row.module_id
            lesson_id = row.lesson_id
            
            # Create module if doesn't exist
            if module_id not in modules_dict:
                modules_dict[module_id] = {
                    'Id': module_id,
                    'title': row.module_title,
                    'description': row.module_description,
                    'sort_order': row.module_sort_order,
                    'is_free': row.module_is_free,
                    
                    # Embedded module progress
                    'is_completed': row.module_is_completed or False,
                    'started_at': row.module_started_at,
                    'completed_at': row.module_completed_at,
                    
                    'lessons': {}
                }
            
            # Create lesson if doesn't exist
            if lesson_id not in modules_dict[module_id]['lessons']:
                modules_dict[module_id]['lessons'][lesson_id] = {
                    'Id': lesson_id,
                    'title': row.lesson_title,
                    'description': row.lesson_description,
                    'sort_order': row.lesson_sort_order,
                    'content_url': row.lesson_content_url,
                    'content_text': row.lesson_content_text,
                    'estimated_duration': row.lesson_estimated_duration,
                    
                    # Embedded lesson progress
                    'is_completed': row.lesson_is_completed or False,
                    'started_at': row.lesson_started_at,
                    'completed_at': row.lesson_completed_at,
                    'is_last_viewed': row.lesson_is_last_viewed or False,
                    
                    # Content type
                    'content_type': {
                        'name': row.lesson_content_type_name
                    },
                    
                    # Resources (from JSON aggregation)
                    'resources': row.lesson_resources if row.lesson_resources else []
                }
        
        # Convert to lists and sort
        course_data['course']['modules'] = [
            {
                **module_data,
                'lessons': sorted(
                    list(module_data['lessons'].values()),
                    key=lambda x: x['sort_order']
                )
            }
            for module_data in sorted(
                modules_dict.values(),
                key=lambda x: x['sort_order']
            )
        ]
        
        return course_data

    def get_course_enrollment(self, course_id: UUID, user_id: UUID) -> EnrollmentModel | None:
        """
        Get user's enrollment in a course.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            EnrollmentModel: Enrollment record, or None if not enrolled
        """
        return (self.db.query(EnrollmentModel)
            .filter(
                EnrollmentModel.course_id == course_id,
                EnrollmentModel.user_id == user_id
            )
            .first()
        )
    
    def user_has_active_enrollment(self, user_id: UUID) -> bool:
        """
        Check if user has ANY active (non-expired) enrollment.
        Used for gating access to CV analysis and interview practice features.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            bool: True if user has at least one active enrollment, False otherwise
        """
        now = datetime.now(timezone.utc)
        active_enrollment = (self.db.query(EnrollmentModel)
            .filter(
                EnrollmentModel.user_id == user_id,
                EnrollmentModel.purchase_completed == True,
                (EnrollmentModel.expires_at.is_(None) | (EnrollmentModel.expires_at > now))
            )
            .first()
        )
        return active_enrollment is not None
    
    def get_user_active_enrollments(self, user_id: UUID) -> list[EnrollmentModel]:
        """
        Get all active (non-expired) enrollments for a user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            list[EnrollmentModel]: List of active enrollments
        """
        now = datetime.now(timezone.utc)
        return (self.db.query(EnrollmentModel)
            .filter(
                EnrollmentModel.user_id == user_id,
                EnrollmentModel.purchase_completed == True,
                (EnrollmentModel.expires_at.is_(None) | (EnrollmentModel.expires_at > now))
            )
            .all()
        )
    
    def get_user_certificate_by_course(self, course_id: UUID, user_id: UUID) -> Optional[CertificateModel]:
        """
        Get user's certificate for a specific course.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            CertificateModel: Certificate record, or None if not found
        """
        return (self.db.query(CertificateModel)
            .join(EnrollmentModel, CertificateModel.enrollment_id == EnrollmentModel.Id)
            .filter(
                EnrollmentModel.course_id == course_id,
                EnrollmentModel.user_id == user_id
            )
            .first()
        )

    def get_course_by_id(self, course_id: UUID) -> CourseModel | None:
        """
        Get course by ID with related modules, lessons, and enrollment count.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            CourseModel: Course with relations loaded, or None if not found
        """
        return (self.db.query(CourseModel)
            .options(
                joinedload(CourseModel.status),
                selectinload(CourseModel.modules)
                .selectinload(ModuleModel.lessons)
                .selectinload(LessonModel.content_type),
                selectinload(CourseModel.modules)
                .selectinload(ModuleModel.lessons)
                .selectinload(LessonModel.resources)
            )
            .filter(CourseModel.Id == course_id)
            .first()
        )
    
    def fetch_courses_by_slug(self, slug: str) -> list[CourseModel] | None:
        """
        Fetch courses by slug, excluding deleted courses.
        
        Args:
            slug: Course slug
        
        Returns:
            list[CourseModel]: List of matching courses, or None if not found
        """
        courses = self.db.query(CourseModel).filter(CourseModel.slug == slug, CourseModel.isDeleted == False).all()

        if not courses:
            return None

        return courses

    def feature_course(self, course_id: UUID) -> CourseModel | None:
        """
        Mark a course as featured.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            CourseModel: Updated course, or None if not found or deleted
        """
        course = self.db.query(CourseModel).filter(CourseModel.Id == course_id).first()
        if not course or course.isDeleted:
            return None
        course.is_featured = True
        self.db.commit()
        self.db.refresh(course)
        return course

    def get_all_courses(self, status: str | None, limit: int, offset: int, search: str | None) -> dict:
        """
        Get all non-deleted courses with pagination, filtering, and search.
        
        Args:
            status: Optional status filter (e.g., 'PUBLISHED', 'DRAFT')
            limit: Maximum number of courses to return
            offset: Number of courses to skip for pagination
            search: Optional search term for title/description/tags
        
        Returns:
            dict: Contains courses list, total count, and pagination metadata
        """
        base_query = self.db.query(CourseModel).filter(CourseModel.isDeleted == False)

        if status:
            base_query = base_query.filter(
                CourseModel.status.has(
                    CourseStatusLookup.name == status
                )
            )

        if search:
            search_term = f"%{search}%"
            base_query = base_query.filter(
                or_(
                    CourseModel.title.ilike(search_term),
                    CourseModel.description.ilike(search_term),
                    CourseModel.tags.ilike(search_term)
                )
            )

        # Get total count
        total_count = base_query.count()

        # Paginated results with eager loading
        courses = base_query.options(
            joinedload(CourseModel.status),
            selectinload(CourseModel.modules)
            .selectinload(ModuleModel.lessons)
            .selectinload(LessonModel.content_type)
        ).order_by(CourseModel.title)\
        .offset(offset)\
        .limit(limit)\
        .all()

        return {
            'courses': courses,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': offset + limit < total_count,
            'has_prev': offset > 0
        }

    def publish_course(self, course_id: UUID, status_id: UUID) -> CourseModel | None:
        """
        Publish a course by updating its status and timestamp.
        
        Args:
            course_id: UUID of the course
            status_id: UUID of the new status
        
        Returns:
            CourseModel: Updated course, or None if not found or deleted
        """
        course = self.db.query(CourseModel).filter(CourseModel.Id == course_id).first()

        if not course or course.isDeleted:
            return None
        if course:
            course.published_at = datetime.now(timezone.utc)
            course.course_status_id = status_id
            self.db.commit()
            self.db.refresh(course)
        return course

    def fetch_course_status_by_name(self, status_name: str) -> CourseStatusLookup | None:
        """
        Get course status by name.
        
        Args:
            status_name: Name of the status (e.g., 'PUBLISHED', 'DRAFT')
        
        Returns:
            CourseStatusLookup: Status object, or None if not found
        """
        return self.db.query(CourseStatusLookup).filter(CourseStatusLookup.name == status_name).first()

    def all_course_statuses(self) -> list[CourseStatusLookup]:
        """
        Get all available course statuses.
        
        Returns:
            list[CourseStatusLookup]: List of all course status options
        """
        return self.db.query(CourseStatusLookup).all()

    def delete_course(self, course_id: UUID) -> CourseModel | None:
        """
        Soft delete a course by marking isDeleted as True and setting deleted_at timestamp.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            CourseModel: Deleted course, or None if not found or already deleted
        """
        course = self.db.query(CourseModel).filter(CourseModel.Id == course_id).first()
        if not course or course.isDeleted:
            return None
        course.isDeleted = True
        course.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def enroll_user_in_course(
        self, 
        user_id: UUID, 
        course_id: UUID, 
        payment_reference: str = None,
        amount: int = None,
        currency: str = "EUR"
    ):
        """
        Enroll a user in a course or renew an existing expired enrollment.
        
        If user has an existing enrollment that expired before completion:
        - Renew it by updating the expiry date
        
        If no enrollment exists:
        - Create a new enrollment with 3-month expiry
        
        In both cases, create a purchase record for audit trail.
        
        Args:
            user_id: UUID of the user
            course_id: UUID of the course
            payment_reference: Optional payment transaction reference
            amount: Optional amount paid in cents
            currency: Currency code (default: EUR)
        
        Returns:
            EnrollmentModel: The created or renewed enrollment
        """
        # Check for existing enrollment
        existing_enrollment = self.db.query(EnrollmentModel).filter(
            EnrollmentModel.user_id == user_id,
            EnrollmentModel.course_id == course_id
        ).first()
        
        now = datetime.now(timezone.utc)
        new_expiry = now + timedelta(days=ENROLLMENT_EXPIRY_DAYS)
        
        if existing_enrollment:
            # Renew the enrollment - update expiry and payment reference
            existing_enrollment.expires_at = new_expiry
            existing_enrollment.payment_reference = payment_reference
            existing_enrollment.purchased_at = now
            existing_enrollment.purchase_completed = True
            self.db.commit()
            self.db.refresh(existing_enrollment)
            
            # Create purchase record for renewal
            purchase = EnrollmentPurchaseModel(
                enrollment_id=existing_enrollment.Id,
                user_id=user_id,
                amount=amount or 0,
                currency=currency,
                payment_reference=payment_reference,
                purchased_at=now,
                is_renewal=True
            )
            self.db.add(purchase)
            self.db.commit()
            
            return existing_enrollment
        
        # Create new enrollment
        enrollment = EnrollmentModel(
            user_id=user_id, 
            course_id=course_id,
            payment_reference=payment_reference,
            purchase_completed=True,
            expires_at=new_expiry
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        
        # Create purchase record for initial enrollment
        purchase = EnrollmentPurchaseModel(
            enrollment_id=enrollment.Id,
            user_id=user_id,
            amount=amount or 0,
            currency=currency,
            payment_reference=payment_reference,
            purchased_at=now,
            is_renewal=False
        )
        self.db.add(purchase)
        self.db.commit()
        
        return enrollment
    
    def complete_course(self, course_id: UUID, user_id: UUID):
        """
        Mark a course as completed for a user.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        Returns:
            bool: True if completed successfully, False otherwise
        """
        enrollment = self.get_course_enrollment(course_id, user_id)
        if not enrollment:
            return False
        
        enrollment.is_completed = True
        enrollment.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    def check_all_modules_completed(self, course_id: UUID, user_id: UUID) -> bool:
        """
        Check if all modules in a course are completed by a user.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            bool: True if all modules completed or no modules exist, False otherwise
        """
        # Count total modules in the course
        total_modules = self.db.query(ModuleModel)\
            .filter(ModuleModel.course_id == course_id)\
            .count()
        
        if total_modules == 0:
            return True  # No modules means course is "complete"
        
        # Count completed modules for this user in this course
        completed_modules = self.db.query(LearnerModuleProgressModel)\
            .join(ModuleModel, LearnerModuleProgressModel.module_id == ModuleModel.Id)\
            .filter(
                ModuleModel.course_id == course_id,
                LearnerModuleProgressModel.user_id == user_id,
                LearnerModuleProgressModel.is_completed == True
            )\
            .count()
        
        # Return True if all modules are completed
        return completed_modules == total_modules
    
    def get_enrollment_by_user_and_course(self, user_id: UUID, course_id: UUID) -> Optional[EnrollmentModel]:
        """
        Get enrollment record for a user and course.
        
        Args:
            user_id: UUID of the user
            course_id: UUID of the course
        
        Returns:
            EnrollmentModel: Enrollment record, or None if not found
        """
        return self.db.query(EnrollmentModel)\
            .filter(
                EnrollmentModel.user_id == user_id,
                EnrollmentModel.course_id == course_id,
                EnrollmentModel.purchase_completed == True
            )\
            .first()
    
    def is_course_completed(self, enrollment_id: UUID) -> bool:
        """
        Check if a course is already completed for an enrollment.
        
        Args:
            enrollment_id: UUID of the enrollment
        
        Returns:
            bool: True if course is completed, False otherwise
        """
        progress = self.db.query(LearnerCourseProgressModel)\
            .filter(LearnerCourseProgressModel.enrollment_id == enrollment_id)\
            .first()
        
        return progress.is_completed if progress else False
    
    def set_course_as_completed(self, enrollment_id: UUID) -> Optional[LearnerCourseProgressModel]:
        """
        Mark a course as completed for an enrollment with timestamp.
        Creates progress record if it doesn't exist.
        
        Args:
            enrollment_id: UUID of the enrollment
        
        Returns:
            LearnerCourseProgressModel: Updated/created course progress, or None if enrollment not found
        """
        # Verify enrollment exists
        enrollment = self.db.query(EnrollmentModel)\
            .filter(EnrollmentModel.Id == enrollment_id)\
            .first()
        
        if not enrollment:
            return None
        
        # Get or create course progress
        course_progress = self.db.query(LearnerCourseProgressModel)\
            .filter(LearnerCourseProgressModel.enrollment_id == enrollment_id)\
            .first()
        
        if not course_progress:
            course_progress = LearnerCourseProgressModel(
                enrollment_id=enrollment_id,
                progress=100,
                is_completed=True,
                completed_at=datetime.now()
            )
            self.db.add(course_progress)
        else:
            course_progress.progress = 100
            course_progress.is_completed = True
            course_progress.completed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(course_progress)
        return course_progress
    
    def calculate_course_progress(self, course_id: UUID, user_id: UUID) -> int:
        """
        Calculate course progress percentage based on completed modules.
        This is calculated on-the-fly to handle dynamic module additions.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            int: Progress percentage (0-100)
        """
        # Count total modules in the course
        total_modules = self.db.query(ModuleModel)\
            .filter(ModuleModel.course_id == course_id)\
            .count()
        
        if total_modules == 0:
            return 100  # No modules means 100% complete
        
        # Count completed modules for this user
        completed_modules = self.db.query(LearnerModuleProgressModel)\
            .join(ModuleModel, LearnerModuleProgressModel.module_id == ModuleModel.Id)\
            .filter(
                ModuleModel.course_id == course_id,
                LearnerModuleProgressModel.user_id == user_id,
                LearnerModuleProgressModel.is_completed == True
            )\
            .count()
        
        # Calculate percentage
        return int((completed_modules / total_modules) * 100)
    
    def create_certificate_record(
        self, 
        enrollment_id: UUID, 
        certificate_url: str, 
        certificate_number: str
    ) -> Optional[CertificateModel]:
        """
        Create a certificate record for a completed course.
        
        Args:
            enrollment_id: UUID of the enrollment
            certificate_url: S3 URL of the generated certificate
            certificate_number: Unique certificate number
        
        Returns:
            CertificateModel: Created certificate record, or None if enrollment not found
        """
        # Verify enrollment exists
        enrollment = self.db.query(EnrollmentModel)\
            .filter(EnrollmentModel.Id == enrollment_id)\
            .first()
        
        if not enrollment:
            return None
        
        # Check if certificate already exists
        existing_cert = self.db.query(CertificateModel)\
            .filter(CertificateModel.enrollment_id == enrollment_id)\
            .first()
        
        if existing_cert:
            # Update existing certificate
            existing_cert.certificate_url = certificate_url
            existing_cert.certificate_number = certificate_number
            existing_cert.issued_at = datetime.now()
            self.db.commit()
            self.db.refresh(existing_cert)
            return existing_cert
        
        # Create new certificate
        certificate = CertificateModel(
            enrollment_id=enrollment_id,
            certificate_url=certificate_url,
            certificate_number=certificate_number,
            issued_at=datetime.now()
        )
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        return certificate
    
    def initialize_course_progress(self, enrollment_id: UUID, course_id: UUID, user_id: UUID) -> dict:
        """
        Initialize all progress records for a user's course enrollment.
        Creates progress records for course, all modules, and all lessons upfront.
        This is called once at enrollment time.
        
        Args:
            enrollment_id: UUID of the enrollment
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            dict: Count of created records and status
        """
        try:
            # 1. Create course progress record (0% complete)
            course_progress = LearnerCourseProgressModel(
                enrollment_id=enrollment_id,
                progress=0,
                is_completed=False,
                completed_at=None
            )
            self.db.add(course_progress)
            
            # 2. Get all modules for this course
            modules = self.db.query(ModuleModel)\
                .filter(ModuleModel.course_id == course_id)\
                .all()
            
            module_count = len(modules)
            lesson_count = 0
            
            # 3. Create module progress records for each module
            module_progress_records = []
            lesson_progress_records = []
            
            for module in modules:
                # Create module progress (not started)
                module_progress = LearnerModuleProgressModel(
                    module_id=module.Id,
                    user_id=user_id,
                    started_at=None,
                    completed_at=None,
                    is_completed=False
                )
                module_progress_records.append(module_progress)
                
                # Get all lessons for this module
                lessons = self.db.query(LessonModel)\
                    .filter(LessonModel.module_id == module.Id)\
                    .all()
                
                # Create lesson progress records for each lesson
                for lesson in lessons:
                    lesson_progress = LearnerLessonProgressModel(
                        lesson_id=lesson.Id,
                        user_id=user_id,
                        started_at=None,
                        completed_at=None,
                        is_completed=False,
                        is_last_viewed=False
                    )
                    lesson_progress_records.append(lesson_progress)
                    lesson_count += 1
            
            # 4. Bulk insert all progress records
            self.db.bulk_save_objects(module_progress_records)
            self.db.bulk_save_objects(lesson_progress_records)
            
            # Commit all changes in one transaction
            self.db.commit()
            
            return {
                "success": True,
                "course_progress_created": True,
                "modules_initialized": module_count,
                "lessons_initialized": lesson_count,
                "total_records": 1 + module_count + lesson_count
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to initialize course progress: {str(e)}")

    def get_user_purchase_history(self, user_id: UUID):
        """
        Get all purchase history for a user across all enrollments.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            list: List of enrollment purchases with course information
        """
        return self.db.query(EnrollmentPurchaseModel)\
            .filter(EnrollmentPurchaseModel.user_id == user_id)\
            .order_by(EnrollmentPurchaseModel.purchased_at.desc())\
            .all()
    
    def get_enrollment_purchase_history(self, enrollment_id: UUID):
        """
        Get all purchase records for a specific enrollment.
        
        Args:
            enrollment_id: UUID of the enrollment
        
        Returns:
            list: List of purchases for this enrollment
        """
        return self.db.query(EnrollmentPurchaseModel)\
            .filter(EnrollmentPurchaseModel.enrollment_id == enrollment_id)\
            .order_by(EnrollmentPurchaseModel.purchased_at.desc())\
            .all()
    
    def get_course_purchase_history(self, user_id: UUID, course_id: UUID):
        """
        Get all purchase records for a user's enrollment in a specific course.
        
        Args:
            user_id: UUID of the user
            course_id: UUID of the course
        
        Returns:
            list: List of purchases for this course enrollment
        """
        enrollment = self.db.query(EnrollmentModel).filter(
            EnrollmentModel.user_id == user_id,
            EnrollmentModel.course_id == course_id
        ).first()
        
        if not enrollment:
            return []
        
        return self.db.query(EnrollmentPurchaseModel)\
            .filter(EnrollmentPurchaseModel.enrollment_id == enrollment.Id)\
            .order_by(EnrollmentPurchaseModel.purchased_at.desc())\
            .all()
