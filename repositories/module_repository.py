from sqlalchemy.orm import Session, selectinload, joinedload
from models import (
    ModuleModel, LessonModel, 
    LessonResourceModel, LearnerLessonProgressModel,
    LearnerModuleProgressModel, LessonContentType,
    CourseImages
)
from uuid import UUID
from datetime import datetime
from schemas.course import (
    ModuleBase, ModuleResponse, 
    ModuleWithLessonsResponse, LessonResponse, 
    LessonBase, UpdateLesson
)

class ModuleRepository:
    def __init__(self, db: Session):
        """
        Initialize module repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_module_by_id(self, module_id: UUID) -> ModuleWithLessonsResponse:
        """
        Get a module by ID with all its lessons eager-loaded.
        
        Args:
            module_id: UUID of the module
        
        Returns:
            ModuleWithLessonsResponse: Module with lessons, or None if not found
        """
        module = (
            self.db.query(ModuleModel)
            .options(
                selectinload(ModuleModel.lessons)
            )
            .filter(ModuleModel.Id == module_id)
            .first()
        )

        return module


    def create_module(self, module_data: ModuleBase) -> ModuleResponse:
        """
        Create a new module.
        
        Args:
            module_data: Module creation data
        
        Returns:
            ModuleResponse: The created module
        """
        module_dict = module_data.model_dump(exclude={"Id", "created_at", "updated_at"})
        db_module = ModuleModel(**module_dict)
        self.db.add(db_module)
        self.db.commit()
        self.db.refresh(db_module)

        return db_module
    
    def delete_module(self, module_id: UUID) -> bool:
        """
        Hard delete a module from the database.
        
        Args:
            module_id: UUID of the module
        
        Returns:
            bool: True if deleted, False if not found
        """
        module = self.db.query(ModuleModel).filter(ModuleModel.Id == module_id).first()

        if not module:
            return False
        
        self.db.delete(module)
        self.db.commit()
        return True
    
    def update_module(self, module_id: UUID, module_data: ModuleBase) -> ModuleBase:
        """
        Update an existing module.
        
        Args:
            module_id: UUID of the module
            module_data: Updated module data
        
        Returns:
            ModuleBase: Updated module, or None if not found
        """
        module = self.get_module_by_id(module_id)
        if not module:
            return None

        update_data = module_data.model_dump(exclude_unset=True, exclude={"Id", "created_at", "updated_at"})
        for field, value in update_data.items():
            setattr(module, field, value)

        self.db.commit()
        self.db.refresh(module)
        return module
    
    def set_module_as_free(self, module_id: UUID) -> ModuleBase:
        """
        Mark a module as free (accessible without payment).
        
        Args:
            module_id: UUID of the module
        
        Returns:
            ModuleBase: Updated module, or None if not found
        """
        module = self.get_module_by_id(module_id)
        if not module:
            return None
        
        module.is_free = True
        self.db.commit()
        self.db.refresh(module)
        return module
    
    def create_lesson(self, lesson_data: LessonBase) -> LessonResponse:
        """
        Create a new lesson.
        
        Args:
            lesson_data: Lesson creation data
        
        Returns:
            LessonResponse: The created lesson
        """
        lesson_dict = lesson_data.model_dump(exclude_unset=True)
        db_lesson = LessonModel(**lesson_dict)
        self.db.add(db_lesson)
        self.db.commit()
        self.db.refresh(db_lesson)

        return db_lesson
    
    def get_lesson_by_id(self, lesson_id: UUID) -> LessonResponse:
        """
        Get a lesson by ID with content type eager-loaded.
        
        Args:
            lesson_id: UUID of the lesson
        
        Returns:
            LessonResponse: Lesson with content type, or None if not found
        """
        lesson = self.db.query(LessonModel)\
        .options(joinedload(LessonModel.content_type))\
        .filter(LessonModel.Id == lesson_id)\
        .first()

        if not lesson:
            return None

        return lesson

    def add_lesson_resource(self, lesson_id: UUID, resource_url: str, resource_name: str, is_downloadable) -> LessonResourceModel:
        """
        Add a resource (file/link) to a lesson.
        
        Args:
            lesson_id: UUID of the lesson
            resource_url: URL of the resource
            resource_name: Display name for the resource
            is_downloadable: Whether the resource can be downloaded
        
        Returns:
            LessonResourceModel: Created resource, or None if lesson not found
        """
        lesson = self.get_lesson_by_id(lesson_id)
        if not lesson:
            return None
        
        lesson_resource = LessonResourceModel(
            lesson_id=lesson_id,
            resource_url=resource_url,
            resource_name=resource_name,
            is_downloadable=is_downloadable
        )

        self.db.add(lesson_resource)
        self.db.commit()
        self.db.refresh(lesson_resource)
        return lesson_resource
    
    def delete_lesson_resource(self, resource_id: UUID) -> bool:
        """
        Hard delete a lesson resource.
        
        Args:
            resource_id: UUID of the resource
        
        Returns:
            bool: True if deleted, False if not found
        """
        resource = self.db.query(LessonResourceModel).filter(LessonResourceModel.Id == resource_id).first()

        if not resource:
            return False
        
        self.db.delete(resource)
        self.db.commit()
        return True
    
    def delete_lesson(self, lesson_id: UUID) -> bool:
        """
        Hard delete a lesson from the database.
        
        Args:
            lesson_id: UUID of the lesson
        
        Returns:
            bool: True if deleted, False if not found
        """
        lesson = self.db.query(LessonModel).filter(LessonModel.Id == lesson_id).first()

        if not lesson:
            return False
        
        self.db.delete(lesson)
        self.db.commit()
        return True
    
    def updateLesson(self, lesson_id: UUID, lesson_data: UpdateLesson) -> LessonResponse:
        """
        Update an existing lesson.
        
        Args:
            lesson_id: UUID of the lesson
            lesson_data: Updated lesson data
        
        Returns:
            LessonResponse: Updated lesson
        """
        lesson = self.db.query(LessonModel).filter(LessonModel.Id == lesson_id).first()

        # Update all provided fields
        update_data = lesson_data.model_dump()
        for field, value in update_data.items():
            if value is not None:  # Only update non-None values
                setattr(lesson, field, value)

        self.db.commit()
        self.db.refresh(lesson)
        return lesson
    
    def unset_module_lessons_as_last_viewed(self, module_id: UUID, user_id: UUID) -> None:
        """
        Mark all lessons in a module as not last viewed for a user.
        Used when switching to a different lesson.
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        """
        lesson_progress_records = self.db.query(LearnerLessonProgressModel)\
            .join(LessonModel, LearnerLessonProgressModel.lesson_id == LessonModel.Id)\
            .filter(
                LessonModel.module_id == module_id,
                LearnerLessonProgressModel.user_id == user_id,
                LearnerLessonProgressModel.is_last_viewed == True  # Only update currently "last viewed"
            )\
            .all()
        
        for progress in lesson_progress_records:
            progress.is_last_viewed = False
        
        self.db.commit()

    def set_lesson_as_completed(self, lesson_id: UUID, user_id: UUID) -> LearnerLessonProgressModel:
        """
        Mark a lesson as completed for a user with timestamp.
        Progress record must exist (created at enrollment).
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            LearnerLessonProgressModel: Updated lesson progress, or None if not found
        """
        lesson_progress = self.db.query(LearnerLessonProgressModel)\
            .filter(
                LearnerLessonProgressModel.lesson_id == lesson_id, 
                LearnerLessonProgressModel.user_id == user_id
            )\
            .first()
        
        if not lesson_progress:
            return None
        
        # Mark as started if not already
        if not lesson_progress.started_at:
            lesson_progress.started_at = datetime.now()
            
        lesson_progress.completed_at = datetime.now()
        lesson_progress.is_completed = True

        self.db.commit()
        self.db.refresh(lesson_progress)
        return lesson_progress

    def create_lesson_progress(self, lesson_id: UUID, user_id: UUID) -> LearnerLessonProgressModel:
        """
        Update lesson progress when user views it (marks as started and last viewed).
        Progress record must exist (created at enrollment).
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            LearnerLessonProgressModel: Updated progress record, or None if not found
        """
        lesson_progress = self.db.query(LearnerLessonProgressModel)\
            .filter(
                LearnerLessonProgressModel.lesson_id == lesson_id,
                LearnerLessonProgressModel.user_id == user_id
            )\
            .first()
        
        if not lesson_progress:
            return None

        # Mark as started if not already
        if not lesson_progress.started_at:
            lesson_progress.started_at = datetime.now()
        
        lesson_progress.is_last_viewed = True
        lesson_progress.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(lesson_progress)
        return lesson_progress

    async def create_module_progress(self, module_id: UUID, user_id: UUID) -> LearnerModuleProgressModel:
        """
        Update module progress when user starts it (marks as started).
        Progress record must exist (created at enrollment).
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        
        Returns:
            LearnerModuleProgressModel: Updated progress record, or None if not found
        """
        module_progress = self.db.query(LearnerModuleProgressModel)\
            .filter(
                LearnerModuleProgressModel.module_id == module_id,
                LearnerModuleProgressModel.user_id == user_id
            )\
            .first()
        
        if not module_progress:
            return None

        # Mark as started if not already
        if not module_progress.started_at:
            module_progress.started_at = datetime.now()
            module_progress.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(module_progress)
        
        return module_progress

    def module_lessons_completed(self, module_id: UUID, user_id: UUID) -> bool:
        """
        Check if all lessons in a module are completed by a user.
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        
        Returns:
            bool: True if all lessons completed or no lessons exist, False otherwise
        """
        # Count total lessons in the module
        total_lessons = self.db.query(LessonModel)\
            .filter(LessonModel.module_id == module_id)\
            .count()
        
        if total_lessons == 0:
            return True
        
        # Count completed lessons for this user in this module
        completed_lessons = self.db.query(LearnerLessonProgressModel)\
            .join(LessonModel, LearnerLessonProgressModel.lesson_id == LessonModel.Id)\
            .filter(
                LessonModel.module_id == module_id,
                LearnerLessonProgressModel.user_id == user_id,
                LearnerLessonProgressModel.is_completed == True
            )\
            .count()
        
        # Return True if all lessons are completed
        return completed_lessons == total_lessons

    def set_module_as_completed(self, module_id: UUID, user_id: UUID) -> None:
        """
        Mark a module as completed for a user with timestamp.
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        
        Returns:
            LearnerModuleProgressModel: Updated module progress, or None if not found
        """
        module_progress = self.db.query(LearnerModuleProgressModel)\
            .filter(
                LearnerModuleProgressModel.module_id == module_id, 
                LearnerModuleProgressModel.user_id == user_id
            )\
            .first()

        if not module_progress:
            return None

        module_progress.completed_at = datetime.now()
        module_progress.is_completed = True

        self.db.commit()
        self.db.refresh(module_progress)
        return module_progress
    
    def undo_lesson_completion(self, lesson_id: UUID, user_id: UUID) -> LearnerLessonProgressModel | None:
        """
        Mark a previously completed lesson as incomplete.
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            LearnerLessonProgressModel: Updated progress, or None if not found
        """
        lesson_progress = self.db.query(LearnerLessonProgressModel)\
            .filter(
                LearnerLessonProgressModel.lesson_id == lesson_id,
                LearnerLessonProgressModel.user_id == user_id
            )\
            .first()

        if not lesson_progress:
            return None

        lesson_progress.updated_at = datetime.now()
        lesson_progress.is_completed = False
        lesson_progress.completed_at = None

        self.db.commit()
        self.db.refresh(lesson_progress)

        return lesson_progress
    
    async def undo_module_completion(self, module_id: UUID, user_id: UUID) -> LearnerModuleProgressModel | None:
        """
        Mark a previously completed module as incomplete.
        
        Args:
            module_id: UUID of the module
            user_id: UUID of the user
        
        Returns:
            LearnerModuleProgressModel: Updated progress, or None if not found
        """
        module_progress = self.db.query(LearnerModuleProgressModel)\
            .filter(
                LearnerModuleProgressModel.module_id == module_id,
                LearnerModuleProgressModel.user_id == user_id
            )\
            .first()

        if not module_progress:
            return None

        module_progress.updated_at = datetime.now()
        module_progress.is_completed = False
        module_progress.completed_at = None

        self.db.commit()
        self.db.refresh(module_progress)

        return module_progress
    
    def get_learner_lesson_progress(self, lesson_id: UUID, user_id: UUID) -> LearnerLessonProgressModel | None:
        """
        Get a user's progress record for a specific lesson.
        
        Args:
            lesson_id: UUID of the lesson
            user_id: UUID of the user
        
        Returns:
            LearnerLessonProgressModel: Progress record, or None if not found
        """
        lesson_progress = self.db.query(LearnerLessonProgressModel)\
            .filter(
                LearnerLessonProgressModel.lesson_id == lesson_id,
                LearnerLessonProgressModel.user_id == user_id
            )\
            .first()
        
        if not lesson_progress:
            return None
        return lesson_progress
    
    def update_lesson_progress_last_viewed(self, lesson_progress_id: UUID, is_last_viewed: bool) -> LearnerLessonProgressModel | None:
        """
        Update whether a lesson is the last viewed lesson for a user.
        
        Args:
            lesson_progress_id: UUID of the lesson progress record
            is_last_viewed: Whether this is the last viewed lesson
        
        Returns:
            LearnerLessonProgressModel: Updated progress record
        """
        lesson_progress = self.db.query(LearnerLessonProgressModel)\
            .filter(LearnerLessonProgressModel.Id == lesson_progress_id)\
            .first()

        lesson_progress.is_last_viewed = is_last_viewed
        lesson_progress.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(lesson_progress)

        return lesson_progress

    def get_lesson_content_types(self) -> list[LessonContentType]:
        """
        Get all available lesson content types (video, text, quiz, etc.).
        
        Returns:
            list[LessonContentType]: List of all content type options
        """
        lesson_content_types = self.db.query(LessonContentType).all()
        return lesson_content_types
    
    def create_content_images(self, image_url: str, image_name: str) -> CourseImages:
        """
        Upload and store a course content image.
        
        Args:
            image_url: URL of the uploaded image
            image_name: Display name for the image
        
        Returns:
            CourseImages: Created image record
        """
        course_image = CourseImages(
            image_url=image_url,
            image_name=image_name
        )

        self.db.add(course_image)
        self.db.commit()
        self.db.refresh(course_image)
        return course_image

    def get_course_images(self, limit: int = 20, offset: int = 0, search: str | None = None) -> dict:
        """
        Fetch course images with pagination and search functionality.
        Returns course images with their Id, image_name, and image_url.
        """
        base_query = self.db.query(CourseImages)\
            .order_by(CourseImages.image_name)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.filter(
                CourseImages.image_name.ilike(search_term)
            )

        # Get total count
        total_count = base_query.count()

        # Paginated results
        images = base_query.order_by(CourseImages.image_name)\
            .offset(offset)\
            .limit(limit)\
            .all()

        return {
            'images': [
                {
                    'Id': image.Id,
                    'image_name': image.image_name,
                    'image_url': image.image_url,
                    'created_at': image.created_at
                }
                for image in images
            ],
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': offset + limit < total_count,
            'has_prev': offset > 0
        }


