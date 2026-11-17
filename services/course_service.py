from repositories import CourseRepository, UserRepository
from schemas import CourseCreate, CourseUpdate
from services.mailing_service import EmailService
from services.certificate_service import CertificateGenerationService
from slugify import slugify
from uuid import UUID
from typing import Optional
import stripe
import os
import asyncio
from utils import CourseStatus


import logging

logger = logging.getLogger(__name__)

class CourseService:
    def __init__(
            self, 
            course_repository: CourseRepository, 
            mailing_service: EmailService, 
            user_repository: UserRepository, 
            certificate_service: CertificateGenerationService
        ):
        """
        Initialize course service with required dependencies.
        
        Args:
            course_repository: Repository for course data access
            mailing_service: Service for sending emails
            user_repository: Repository for user data access
            certificate_service: Service for generating certificates
        """
        self._repository = course_repository
        self._user_repository = user_repository
        self._mailing_service = mailing_service
        self._certificate_service = certificate_service

    # Add course completion check and generate certificate.
    # IMport S3 into cert generator then attach the cert to S3 and return the link
    def create_course(self, course_data: CourseCreate):
        """
        Create a new course in draft status with auto-generated slug.
        
        Args:
            course_data: Course creation data
        
        Returns:
            dict: Success status, created course, and status code (201 on success)
        """
        try:
            draft_course_status = self._repository.fetch_course_status_by_name(CourseStatus.DRAFT)
            slug = slugify(course_data.title)

            existing_slug_courses = self._repository.fetch_courses_by_slug(slug)
            if existing_slug_courses:
                slug = f"{slug}-{len(existing_slug_courses) + 1}"
            course_data.slug = slug
            course_data.course_status_id = draft_course_status.Id
            return {"success": True, "data": self._repository.create_course(course_data), "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def update_course(self, course_id: UUID, course_data: CourseUpdate):
        """
        Update an existing course. Auto-generates new slug if title changes.
        
        Args:
            course_id: UUID of the course to update
            course_data: Updated course data
        
        Returns:
            dict: Success status, updated course, and status code
        """
        try:
            # Check if course exists
            existing_course = self._repository.get_course_by_id(course_id)
            if not existing_course:
                return {"success": False, "message": "Course not found", "status_code": 404}
            
            # If title has changed, update slug as well
            if course_data.title and course_data.title != existing_course.title:
                new_slug = slugify(course_data.title)
                
                # Check if slug already exists
                existing_slug_courses = self._repository.fetch_courses_by_slug(new_slug)
                if existing_slug_courses:
                    new_slug = f"{new_slug}-{len(existing_slug_courses) + 1}"
                
                # Add slug to update data
                course_data.slug = new_slug
            
            course = self._repository.update_course(course_id, course_data)
            return {"success": True, "data": course, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def fetch_all_courses(self, status: str | None, limit: int, offset: int, search: str | None):
        """
        Fetch all courses with optional filtering, pagination, and search.
        
        Args:
            status: Optional status filter (e.g., 'PUBLISHED', 'DRAFT')
            limit: Maximum number of courses to return
            offset: Number of courses to skip for pagination
            search: Optional search term for title/description/tags
        
        Returns:
            dict: Success status, courses list with pagination metadata, and status code
        """
        try:
            return {"success": True, "data": self._repository.get_all_courses(status=status, limit=limit, offset=offset, search=search), "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def fetch_course_by_id(self, course_id: UUID):
        """
        Fetch a course by its ID, excluding deleted courses.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            dict: Success status, course data, and status code (404 if not found/deleted)
        """
        try:
            course = self._repository.get_course_by_id(course_id)
            if not course or course.isDeleted:
                return {"success": False, "message": "Course not found", "status_code": 404}
            return {"success": True, "data": course, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def check_user_has_active_course(self, user_id: UUID):
        """
        Check if user has any active (non-expired) course enrollment.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Success status with has_active_course boolean in data
        """
        try:
            has_active = self._repository.user_has_active_enrollment(user_id)
            return {
                "success": True, 
                "data": {"has_active_course": has_active}, 
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def learn_course(self, course_id: UUID, user_id: UUID):
        """
        Fetch course learning data with user's progress for enrolled students.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the learner
        
        Returns:
            dict: Success status, structured course data with progress, status code (404 if not enrolled)
        """
        try:
            course = self._repository.learn_course_custom_sql(course_id, user_id)
            if not course:
                return {"success": False, "message": "Not enrolled", "status_code": 404}
            return {"success": True, "data": course, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def publish_course(self, course_id: UUID):
        """
        Publish a course by setting status to PUBLISHED with timestamp.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            dict: Success status, published course, and status code (404 if not found)
        """
        try:
            published_status = self._repository.fetch_course_status_by_name(CourseStatus.PUBLISHED)
            course = self._repository.publish_course(course_id, published_status.Id)
            if not course:
                return {"success": False, "message": "Course not found or could not be published", "status_code": 404}
            return {"success": True, "data": course, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def fetch_all_course_statuses(self):
        """
        Fetch all available course status options.
        
        Returns:
            dict: Success status, list of course statuses, and status code
        """
        try:
            statuses = self._repository.all_course_statuses()
            return {"success": True, "data": statuses, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def get_user_certificate_by_course(self, course_id: UUID, user_id: UUID):
        """
        Get user's certificate for a specific course.
        Validates enrollment and certificate existence.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            dict: Success status, certificate data, and status code
        """
        try:
            # Check if user is enrolled
            enrollment = self._repository.get_course_enrollment(course_id, user_id)
            if not enrollment:
                return {
                    "success": False,
                    "message": "You are not enrolled in this course",
                    "status_code": 403
                }
            
            # Get certificate
            certificate = self._repository.get_user_certificate_by_course(course_id, user_id)
            if not certificate:
                return {
                    "success": False,
                    "message": "Certificate not found. You may not have completed the course yet",
                    "status_code": 404
                }
            
            return {"success": True, "data": certificate, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def delete_course(self, course_id: UUID):
        """
        Soft delete a course by marking isDeleted=True with timestamp.
        
        Args:
            course_id: UUID of the course
        
        Returns:
            dict: Success status, message, and status code (404 if not found/already deleted)
        """
        try:
            course = self._repository.delete_course(course_id)
            if not course:
                return {"success": False, "message": "Course not found or already deleted", "status_code": 404}
            return {"success": True, "message": "Course deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def feature_course(self, course_id: UUID):
        """
        Mark a course as featured (promoted on homepage/featured section).
        
        Args:
            course_id: UUID of the course
        
        Returns:
            dict: Success status, updated course, and status code (404 if not found)
        """
        try:
            course = self._repository.feature_course(course_id)
            if not course:
                return {"success": False, "message": "Course not found or could not be featured", "status_code": 404}
            return {"success": True, "data": course, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def course_checkout(
            self, 
            course_id: UUID, 
            user_id: UUID
        ):
        """
        Create Stripe checkout session for course purchase.
        Course purchase includes unlimited CV analysis and interview practice access
        for 3 months from enrollment date.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the purchasing user
        
        Returns:
            dict: Success status, Stripe session data, and status code
        """
        try:
            stripe_api_key = os.getenv("STRIPE_SECRET_KEY", "")

            if not stripe_api_key:
                return {"success": False, "message": "Could not process payment at this time", "status_code": 500}

            stripe.api_key = stripe_api_key

            course = self._repository.get_course_by_id(course_id)
            if not course or course.isDeleted:
                return {"success": False, "message": "Course not found", "status_code": 404}
            
            # Build line items with just the course
            line_items = [{
                'price_data': {
                    'currency': course.currency,
                    'product_data': {
                        'name': course.title,
                        'description': 'Includes 3 months access to CV Analysis and Interview Practice features'
                    },
                    'unit_amount': round(course.price * 100),
                },
                'quantity': 1,
            }]
            
            # Prepare metadata
            metadata = {
                "course_id": str(course.Id),
                "user_id": str(user_id),
                "purchase_type": "course"
            }
            
            session = stripe.checkout.Session.create(
                line_items=line_items,
                payment_method_types=["card"],
                mode='payment',
                success_url=os.getenv("UI_DOMAIN", '') + '/payment-confirmation?session_id={CHECKOUT_SESSION_ID}&purchase_type=course',
                cancel_url=os.getenv("UI_DOMAIN", '') + '/payment/cancel',
                metadata=metadata
            )

            return {"success": True, "data": session, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

        
    def enroll_user_in_course(self, checkout_session_id: str):
        """
        Complete course enrollment after successful Stripe payment.
        Creates or renews enrollment with 3-month access to all features.
        
        Args:
            checkout_session_id: Stripe checkout session ID
        
        Returns:
            dict: Success status, enrollment data, and status code (400 if payment not completed)
        """
        try:
            stripe_api_key = os.getenv("STRIPE_SECRET_KEY", "")

            if not stripe_api_key:
                return {"success": False, "message": "Could not process payment at this time", "status_code": 500}

            stripe.api_key = stripe_api_key
            session = stripe.checkout.Session.retrieve(checkout_session_id)

            if session["payment_status"] != "paid":
                return {"success": False, "message": "Payment not completed", "status_code": 400}
        
            course_id = session.metadata["course_id"]
            user_id = session.metadata["user_id"]
            purchase_type = session.metadata.get("purchase_type", "course")
            payment_reference = session.payment_intent if session.payment_intent else checkout_session_id
            
            # Get amount and currency from Stripe session
            amount_total = session.get("amount_total", 0)  # Amount in cents
            currency = session.get("currency", "EUR").upper()

            # This will either create a new enrollment or renew an existing expired one
            enrollment = self._repository.enroll_user_in_course(
                user_id, 
                course_id, 
                payment_reference,
                amount=amount_total,
                currency=currency
            ) 

            if not enrollment:
                return {"success": False, "message": "Enrollment failed", "status_code": 400}
            
            # Initialize all progress records upfront (course, modules, lessons)
            try:
                progress_init = self._repository.initialize_course_progress(
                    enrollment.Id, 
                    UUID(course_id), 
                    UUID(user_id)
                )
                logger.info(f"Progress initialized: {progress_init['total_records']} records created for enrollment {enrollment.Id}")
            except Exception as e:
                # Log error but don't fail enrollment - progress can be created later
                logger.error(f"Failed to initialize progress (non-blocking): {str(e)}", exc_info=True)
            
            user = self._user_repository.get_by_id(user_id) if self._user_repository else None
            course = self._repository.get_course_by_id(course_id)
            
            if user and course:
                asyncio.create_task(
                    self._mailing_service.send_course_enrollment_email(
                        to_email=user.email,
                        user_name=f"{user.first_name}",
                        course_title=course.title,
                        course_id=str(course.Id)
                    )
                )
            
            enrollment_data = {
                "Id": str(enrollment.Id),
                "user_id": str(enrollment.user_id),
                "course_id": str(enrollment.course_id),
                "purchased_at": enrollment.purchased_at.isoformat() if enrollment.purchased_at else None,
                "purchase_completed": enrollment.purchase_completed,
                "expires_at": enrollment.expires_at.isoformat() if enrollment.expires_at else None,
                "payment_reference": enrollment.payment_reference,
                "purchase_type": purchase_type,
                "created_at": enrollment.created_at.isoformat() if enrollment.created_at else None,
                "updated_at": enrollment.updated_at.isoformat() if enrollment.updated_at else None
            }
            
            return {"success": True, "data": enrollment_data, "message": "Enrollment successful", "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def check_all_modules_completed(self, course_id: UUID, user_id: UUID) -> bool:
        """
        Check if all modules in a course are completed by a user.
        
        Args:
            course_id: UUID of the course
            user_id: UUID of the user
        
        Returns:
            bool: True if all modules completed, False otherwise
        """
        return self._repository.check_all_modules_completed(course_id, user_id)
    
    def get_enrollment_by_user_and_course(self, user_id: UUID, course_id: UUID):
        """
        Get enrollment record for a user and course.
        
        Args:
            user_id: UUID of the user
            course_id: UUID of the course
        
        Returns:
            EnrollmentModel: Enrollment record, or None if not found
        """
        return self._repository.get_enrollment_by_user_and_course(user_id, course_id)
    
    async def complete_course(self, enrollment_id: UUID, user_id: UUID, course_id: UUID):
        """
        Complete a course: mark as complete, generate certificate, and send completion email.
        Certificate generation and email failures don't block completion.
        Only generates certificate and sends email if this is the first completion.
        
        Args:
            enrollment_id: UUID of the enrollment
            user_id: UUID of the user
            course_id: UUID of the course
        
        Returns:
            dict: Success status, completion data, and status code
        """
        try:
            # Check if course was already completed (prevents duplicate certificates)
            from models import LearnerCourseProgressModel
            if self._repository.is_course_completed(enrollment_id):
                logger.info(f"Course already completed for enrollment {enrollment_id}, skipping certificate generation")
                return {
                    "success": True,
                    "message": "Course already completed",
                    "data": {
                        "enrollment_id": str(enrollment_id),
                        "already_completed": True
                    },
                    "status_code": 200
                }
            
            # Mark course as completed (first time)
            course_progress = self._repository.set_course_as_completed(enrollment_id)
            if not course_progress:
                logger.error(f"Failed to mark course as complete for enrollment {enrollment_id}")
                return {"success": False, "message": "Failed to mark course as complete", "status_code": 500}
            
            # Get course and user details for certificate and email
            course = self._repository.get_course_by_id(course_id)
            user = self._user_repository.get_by_id(user_id) if self._user_repository else None
            
            if not course or not user:
                logger.error(f"Course or user not found for completion: course_id={course_id}, user_id={user_id}")
                return {
                    "success": True, 
                    "message": "Course marked as complete but certificate generation skipped",
                    "status_code": 200
                }
            
            # Check if certificate is enabled for this course
            if not course.certificate_enabled:
                logger.info(f"Certificate disabled for course {course_id}, skipping generation")
                # Still send completion email without certificate
                asyncio.create_task(
                    self._mailing_service.send_course_completion_email(
                        to_email=user.email,
                        user_name=f"{user.first_name} {user.last_name}",
                        course_title=course.title,
                        has_certificate=False
                    )
                )
                return {
                    "success": True, 
                    "message": "Course completed successfully (no certificate)",
                    "status_code": 200
                }
            
            certificate_url = None
            certificate_number = None
            
            try:
                # Generate unique certificate number
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                certificate_number = f"CE-{str(course_id)[:8].upper()}-{str(user_id)[:8].upper()}-{timestamp}"
                
                # Create verification URL
                verification_url = f"{os.getenv('UI_DOMAIN', '')}/certificates/{user_id}"
                
                # Generate and upload certificate
                user_full_name = f"{user.first_name} {user.last_name}"
                _, certificate_url = self._certificate_service.generate_and_upload_certificate(
                    user_name=user_full_name.title(),
                    course_title=course.title,
                    verification_url=verification_url
                )
                
                if certificate_url:
                    self._repository.create_certificate_record(
                        enrollment_id=enrollment_id,
                        certificate_url=certificate_url,
                        certificate_number=certificate_number
                    )
                    logger.info(f"Certificate generated successfully for user {user_id}, course {course_id}")
                
            except Exception as cert_error:
                logger.error(f"Certificate generation failed (non-blocking): {str(cert_error)}", exc_info=True)
            
            try:
                asyncio.create_task(
                    self._mailing_service.send_course_completion_email(
                        to_email=user.email,
                        user_name=user.first_name,
                        course_title=course.title,
                        certificate_url=certificate_url,
                        has_certificate=certificate_url is not None
                    )
                )
            except Exception as email_error:
                logger.error(f"Completion email failed (non-blocking): {str(email_error)}", exc_info=True)
            
            completion_data = {
                "enrollment_id": str(enrollment_id),
                "course_id": str(course_id),
                "user_id": str(user_id),
                "completed_at": course_progress.completed_at.isoformat() if course_progress.completed_at else None,
                "progress": 100,
                "certificate_url": certificate_url,
                "certificate_number": certificate_number
            }
            
            return {
                "success": True, 
                "data": completion_data,
                "message": "Congratulations! Course completed successfully",
                "status_code": 200
            }
            
        except Exception as e:
            logger.error(f"Course completion failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while completing the course",
                "status_code": 500
            }

    def get_user_purchase_history(self, user_id: UUID):
        """
        Get all enrollment purchase history for a user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Success status and list of purchase records
        """
        try:
            purchases = self._repository.get_user_purchase_history(user_id)
            
            # Group purchases by enrollment and include course info
            purchase_data = []
            for purchase in purchases:
                enrollment = purchase.enrollment
                course = enrollment.enrolled_course if enrollment else None
                
                purchase_data.append({
                    "id": str(purchase.Id),
                    "enrollment_id": str(purchase.enrollment_id),
                    "course_id": str(enrollment.course_id) if enrollment else None,
                    "course_title": course.title if course else "Unknown Course",
                    "amount": purchase.amount,
                    "currency": purchase.currency,
                    "payment_reference": purchase.payment_reference,
                    "purchased_at": purchase.purchased_at.isoformat() if purchase.purchased_at else None,
                    "is_renewal": purchase.is_renewal,
                    "created_at": purchase.created_at.isoformat() if purchase.created_at else None
                })
            
            return {
                "success": True,
                "data": purchase_data,
                "total_purchases": len(purchase_data),
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Failed to get purchase history: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred while fetching purchase history",
                "status_code": 500
            }

    def get_course_purchase_history(self, user_id: UUID, course_id: UUID):
        """
        Get purchase history for a specific course enrollment.
        
        Args:
            user_id: UUID of the user
            course_id: UUID of the course
        
        Returns:
            dict: Success status and list of purchase records for the course
        """
        try:
            purchases = self._repository.get_course_purchase_history(user_id, course_id)
            course = self._repository.get_course_by_id(course_id)
            
            purchase_data = []
            total_spent = 0
            currency = "EUR"
            
            for purchase in purchases:
                total_spent += purchase.amount
                currency = purchase.currency
                
                purchase_data.append({
                    "id": str(purchase.Id),
                    "amount": purchase.amount,
                    "currency": purchase.currency,
                    "payment_reference": purchase.payment_reference,
                    "purchased_at": purchase.purchased_at.isoformat() if purchase.purchased_at else None,
                    "is_renewal": purchase.is_renewal
                })
            
            return {
                "success": True,
                "data": {
                    "course_id": str(course_id),
                    "course_title": course.title if course else "Unknown Course",
                    "purchases": purchase_data,
                    "total_spent": total_spent,
                    "currency": currency
                },
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Failed to get course purchase history: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred while fetching course purchase history",
                "status_code": 500
            }