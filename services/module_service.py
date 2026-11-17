from repositories import ModuleRepository
from schemas import ModuleBase, LessonBase, UpdateLesson
from uuid import UUID
from psycopg2 import errors
from sqlalchemy.exc import IntegrityError
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.course_service import CourseService

import logging

logger = logging.getLogger(__name__)

class ModuleService:
    def __init__(self, module_repository: ModuleRepository, course_service: 'CourseService' = None):
        """
        Initialize module service with repository dependency.
        
        Args:
            module_repository: Repository for module and lesson data access
            course_service: Optional course service for triggering course completion
        """
        self._repository = module_repository
        self._course_service = course_service

    def create_module(self, module_data: ModuleBase):
        """
        Create a new module in a course.
        
        Args:
            module_data: Module creation data
        
        Returns:
            dict: Success status, created module, and status code (201 on success, 409 if duplicate)
        """
        try:
            return {"success": True, "data": self._repository.create_module(module_data), "status_code": 201}
        
        except IntegrityError as e:
            if isinstance(e.orig, errors.UniqueViolation):
                return {
                    "success": False,
                    "message": "Similar record already exists",
                    "status_code": 409
                }
        
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def fetch_module_by_id(self, module_id: UUID):
        """
        Fetch a module by ID with all its lessons.
        
        Args:
            module_id: UUID of the module
        
        Returns:
            dict: Success status, module data with lessons, and status code (404 if not found)
        """
        try:
            module = self._repository.get_module_by_id(module_id)
            if not module:
                return {"success": False, "message": "Module not found", "status_code": 404}
            return {"success": True, "data": module, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def update_module(self, module_id: UUID, module_data: ModuleBase):
        """
        Update an existing module.
        
        Args:
            module_id: UUID of the module
            module_data: Updated module data
        
        Returns:
            dict: Success status, updated module, and status code (404 if not found, 409 if duplicate)
        """
        try:
            module = self._repository.update_module(module_id, module_data)
            if not module:
                return {"success": False, "message": "Module not found", "status_code": 404}
            return {"success": True, "data": module, "status_code": 200}

        except IntegrityError as e:
            if isinstance(e.orig, errors.UniqueViolation):
                return {
                    "success": False,
                    "message": "Similar record already exists",
                    "status_code": 409
                }

        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def delete_module(self, module_id: UUID):
        """
        Hard delete a module and all its lessons.
        
        Args:
            module_id: UUID of the module
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            success = self._repository.delete_module(module_id)
            if not success:
                return {"success": False, "message": "Module not found", "status_code": 404}
            return {"success": True, "message": "Module deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def set_module_as_free(self, module_id: UUID):
        """
        Mark a module as free (accessible without course enrollment).
        
        Args:
            module_id: UUID of the module
        
        Returns:
            dict: Success status, updated module, and status code (404 if not found)
        """
        try:
            module = self._repository.set_module_as_free(module_id)
            if not module:
                return {"success": False, "message": "Module not found", "status_code": 404}
            return {"success": True, "data": module, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        

    def create_lesson(self, lesson_data: LessonBase):
        """
        Create a new lesson in a module.
        
        Args:
            lesson_data: Lesson creation data including module_id
        
        Returns:
            dict: Success status, created lesson, and status code (201 on success, 404 if module not found, 409 if duplicate)
        """
        try:
            module = self._repository.get_module_by_id(lesson_data.module_id)
            if not module:
                return {"success": False, "message": "Module not found for the given module_id", "status_code": 404}
            
            return {"success": True, "data": self._repository.create_lesson(lesson_data), "status_code": 201}
        
        except IntegrityError as e:
            if isinstance(e.orig, errors.UniqueViolation):
                return {
                    "success": False,
                    "message": "Similar record already exists",
                    "status_code": 409
                }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_lesson_by_id(self, lesson_id: UUID):
        """
        Fetch a lesson by ID with content type information.
        
        Args:
            lesson_id: UUID of the lesson
        
        Returns:
            dict: Success status, lesson data, and status code (404 if not found)
        """
        try:
            lesson = self._repository.get_lesson_by_id(lesson_id)

            if not lesson:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            return {"success": True, "data": lesson, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def delete_lesson(self, lesson_id: UUID):
        """
        Hard delete a lesson and all its resources.
        
        Args:
            lesson_id: UUID of the lesson
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            success = self._repository.delete_lesson(lesson_id)
            if not success:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            return {"success": True, "message": "Lesson deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def update_lesson(self, lesson_id: UUID, lesson_data: UpdateLesson):
        """
        Update an existing lesson.
        
        Args:
            lesson_id: UUID of the lesson
            lesson_data: Updated lesson data
        
        Returns:
            dict: Success status, updated lesson, and status code (404 if not found, 409 if duplicate)
        """
        try:
            # Check if lesson exists
            existing_lesson = self._repository.get_lesson_by_id(lesson_id)
            if not existing_lesson:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            lesson = self._repository.updateLesson(lesson_id, lesson_data)
            return {"success": True, "data": lesson, "status_code": 200}
        except IntegrityError as e:
            if isinstance(e.orig, errors.UniqueViolation):
                return {
                    "success": False,
                    "message": "Similar record already exists",
                    "status_code": 409
                }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def add_lesson_resource(self, lesson_id: UUID, resource_url: str, resource_name: str, is_downloadable: bool):
        """
        Add a downloadable resource (file/link) to a lesson.
        
        Args:
            lesson_id: UUID of the lesson
            resource_url: URL of the resource
            resource_name: Display name for the resource
            is_downloadable: Whether the resource can be downloaded
        
        Returns:
            dict: Success status, created resource, and status code (201 on success, 404 if lesson not found)
        """
        try:
            resource = self._repository.add_lesson_resource(lesson_id, resource_url, resource_name, is_downloadable)
            if not resource:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            return {"success": True, "data": resource, "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def delete_lesson_resource(self, resource_id: UUID):
        """
        Delete a lesson resource.
        
        Args:
            resource_id: UUID of the resource
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            success = self._repository.delete_lesson_resource(resource_id)
            if not success:
                return {"success": False, "message": "Resource not found", "status_code": 404}
            
            return {"success": True, "message": "Resource deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    async def set_lesson_as_last_viewed(self, lesson_id: UUID, user_id: UUID):
        """
        Track lesson as last viewed by user. Creates progress record and module progress if first lesson.
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            dict: Success status, lesson data, and status code (404 if lesson not found)
        """
        try:
            lesson = self._repository.get_lesson_by_id(lesson_id)
            if not lesson:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            lesson_progress = self._repository.get_learner_lesson_progress(lesson_id, user_id)

            self._repository.unset_module_lessons_as_last_viewed(lesson.module_id, user_id)
            if not lesson_progress:
                self._repository.create_lesson_progress(lesson_id, user_id)
            else:
                self._repository.update_lesson_progress_last_viewed(lesson_progress.Id, True)

            if lesson.is_module_first_lesson:
                asyncio.create_task(
                    self._repository.create_module_progress(lesson.module_id, user_id)
                )

            return {"success": True, "data": lesson, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    async def mark_module_as_completed(self, module_id: UUID, user_id: UUID):
        """
        Mark a module as completed for a user with timestamp.
        Triggers course completion check if all modules are complete.
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        
        Returns:
            dict: Success status, updated module progress, and status code (404 if module not found)
        """
        try:
            logger.info(f"Marking module {module_id} as completed for user {user_id}")
            module = self._repository.get_module_by_id(module_id)

            if not module:
                return {"success": False, "message": "Module not found", "status_code": 404}

            updated_module = self._repository.set_module_as_completed(module.Id, user_id)

            # Check if this completes the entire course
            if self._course_service:
                try:
                    # Check if all modules in the course are completed
                    all_modules_complete = self._course_service.check_all_modules_completed(module.course_id, user_id)
                    
                    if all_modules_complete:
                        # Get enrollment for this user and course
                        enrollment = self._course_service.get_enrollment_by_user_and_course(user_id, module.course_id)
                        
                        if enrollment:
                            # Trigger course completion asynchronously
                            asyncio.create_task(
                                self._course_service.complete_course(
                                    enrollment.Id, 
                                    user_id, 
                                    module.course_id
                                )
                            )
                            logger.info(f"Course completion triggered for user {user_id}, course {module.course_id}")
                except Exception as completion_error:
                    # Log but don't fail module completion if course completion check fails
                    logger.error(f"Failed to check/trigger course completion: {str(completion_error)}", exc_info=True)

            return {"success": True, "data": updated_module, "message": "All lessons marked as completed", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    async def set_lesson_as_completed(self, lesson_id: UUID, user_id: UUID):
        """
        Mark a lesson as completed. Auto-completes module if all lessons finished.
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            dict: Success status, lesson progress, and status code (404 if lesson not found)
        """
        try:
            lesson = self._repository.get_lesson_by_id(lesson_id)
            if not lesson:
                return {"success": False, "message": "Lesson not found", "status_code": 404}
            
            lesson_progress = self._repository.set_lesson_as_completed(lesson.Id, user_id)

            if not lesson_progress:
                return {"success": False, "message": "Failed to set lesson as completed", "status_code": 500}

            all_lesson_complete = self._repository.module_lessons_completed(lesson.module_id, user_id)

            if all_lesson_complete:
                asyncio.create_task(
                    self.mark_module_as_completed(lesson.module_id, user_id)
                )

            return {"success": True, "data": lesson_progress, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    async def undo_lesson_completion(self, lesson_id: UUID, user_id: UUID):
        """
        Mark a previously completed lesson as incomplete. Also undoes module completion.
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            dict: Success status, updated progress, and status code (404 if progress not found)
        """
        try:
            lesson_progress = self._repository.undo_lesson_completion(lesson_id, user_id)

            if not lesson_progress:
                return {"success": False, "message": "Lesson progress not found", "status_code": 404}
            
            asyncio.create_task(
                self._repository.undo_module_completion(lesson_progress.lesson.module_id, user_id)
            )

            return {"success": True, "data": lesson_progress, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def fetch_lesson_content_types(self):
        """
        Fetch all available lesson content types (video, text, quiz, etc.).
        
        Returns:
            dict: Success status, list of content types, and status code
        """
        try:
            content_types = self._repository.get_lesson_content_types()
            return {"success": True, "data": content_types, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def add_content_image(self, image_url: str, image_name: str):
        """
        Add a course content image for use in lesson rich text content.
        
        Args:
            image_url: URL of the uploaded image
            image_name: Display name for the image
        
        Returns:
            dict: Success status, created image record, and status code (201 on success)
        """
        try:
            content_image = self._repository.create_content_images(image_url, image_name)
            return {"success": True, "data": content_image, "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def fetch_course_images(self, limit: int = 20, offset: int = 0, search: str | None = None):
        """
        Fetch course content images with pagination and search functionality.
        
        Args:
            limit: Maximum number of images to return (default 20)
            offset: Number of images to skip for pagination (default 0)
            search: Optional search term for image names
        
        Returns:
            dict: Success status, images list with pagination metadata, and status code
        """
        try:
            result = self._repository.get_course_images(limit=limit, offset=offset, search=search)
            return {"success": True, "data": result, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }