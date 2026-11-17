from fastapi import APIRouter, HTTPException, Depends, status, Form, UploadFile, File, Body
from services import CourseService, S3Service
from models import UserModel
from schemas import CourseCreate, CourseUpdate
from dependencies import get_course_service, get_s3_service
from middleware.auth_middleware import get_current_active_user, require_admin
from uuid import UUID
from typing import Annotated, Optional
from utils import validate_file, sanitize_filename, get_logger, API_PREFIX

class CourseController:
    course_service_dependency = Annotated[CourseService, Depends(get_course_service)]
    current_active_user_dependency = Annotated[UserModel, Depends(get_current_active_user)]
    s3_service_dependency = Annotated[S3Service, Depends(get_s3_service)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/courses", tags=["courses"])
        self.logger = get_logger("app.controllers.course")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route("/", self.get_courses, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/active/check", self.check_user_has_active_course, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{course_id}", self.fetch_course_by_id, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{course_id}/learn", self.learn_course, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{course_id}/certificate", self.get_certificate, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{course_id}/purchases", self.get_course_purchases, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/purchases/history", self.get_purchase_history, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/", self.create_course, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{course_id}", self.update_course, methods=["PATCH"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{course_id}/publish", self.publish_course, methods=["PATCH"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/statuses/all", self.fetch_all_course_statuses, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{course_id}", self.delete_course, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{course_id}/feature", self.feature_course, methods=["PATCH"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{course_id}/stripe/session", self.course_checkout, methods=["POST"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/stripe/verify/{checkout_session_id}", self.verify_checkout_session, methods=["POST"], status_code=status.HTTP_200_OK)
        self.logger.info("CourseController routes have been set up.")

    
    def get_courses(self, course_service: course_service_dependency, search: str | None = None, status: str | None = None, limit: int = 10, offset: int = 0):
        result = course_service.fetch_all_courses(status=status, limit=limit, offset=offset, search=search)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def check_user_has_active_course(
            self,
            current_user: current_active_user_dependency,
            course_service: course_service_dependency
        ):
        """Check if the logged in user has an active (non-expired) course enrollment"""
        result = course_service.check_user_has_active_course(current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def fetch_course_by_id(self, course_id: UUID, course_service: course_service_dependency):
        result = course_service.fetch_course_by_id(course_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def learn_course(
            self,
            course_id: UUID,
            current_user: current_active_user_dependency,
            course_service: course_service_dependency
        ):
        result = course_service.learn_course(course_id, current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_certificate(
            self,
            course_id: UUID,
            current_user: current_active_user_dependency,
            course_service: course_service_dependency
        ):
        """Get user's certificate for a specific course"""
        result = course_service.get_user_certificate_by_course(course_id, current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    async def create_course(
            self, 
            course_service: course_service_dependency,
            s3_service: s3_service_dependency,
            current_user: current_active_user_dependency,
            title: str = Form(...),
            price: str = Form(...),
            course_status_id: str = Form(...),
            description: Optional[str] = Form(None),
            is_featured: str = Form("false"),
            thumbnail_url: Optional[str] = Form(None),
            preview_video_url: Optional[str] = Form(None),
            thumbnail_file: Optional[UploadFile] = File(None),
            preview_video_file: Optional[UploadFile] = File(None)
        ):
        """Create a new course with optional file uploads for thumbnail and preview video"""

        try:
            course_status_uuid = UUID(course_status_id)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid course_status_id format. Must be a valid UUID."
            )
        
        try:
            price_float = float(price)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid price format. Must be a valid number."
            )
        
        # Convert is_featured string to boolean
        is_featured_bool = is_featured.lower() in ("true", "1", "yes", "on")
        
        # Process thumbnail (required)
        final_thumbnail_url = await self._process_thumbnail(
            s3_service, thumbnail_url, thumbnail_file
        )
        
        final_preview_video_url = None
        if preview_video_file or preview_video_url:
            final_preview_video_url = await self._process_preview_video(
                s3_service, preview_video_url, preview_video_file
            )
        
        # Create course object
        course_data = CourseCreate(
            title=title,
            price=price_float,
            description=description,
            is_featured=is_featured_bool,
            course_status_id=course_status_uuid,
            thumbnail_url=final_thumbnail_url,
            preview_video_url=final_preview_video_url,
            created_by=current_user.Id
        )

        # Create course via service
        result = course_service.create_course(course_data)
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code"), 
                detail=result.get("message")
            )
        
        return result

    async def update_course(
            self, 
            course_id: UUID,
            course_service: course_service_dependency,
            s3_service: s3_service_dependency,
            title: str = Form(...),
            description: str = Form(...),
            price: str = Form(...),
            thumbnail_url: Optional[str] = Form(None),
            preview_video_url: Optional[str] = Form(None),
            thumbnail_file: Optional[UploadFile] = File(None),
            preview_video_file: Optional[UploadFile] = File(None)
        ):
        """Update course fields with optional file uploads for thumbnail and preview video"""
        
        # Validate and convert price
        try:
            price_float = float(price)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid price format. Must be a valid number."
            )
        
        # Validate thumbnail is provided
        if not thumbnail_file and not thumbnail_url:
            raise HTTPException(
                status_code=400,
                detail="Thumbnail is required (either thumbnail_url or thumbnail_file must be provided)"
            )
        
        # Process thumbnail (file takes precedence over URL)
        final_thumbnail_url = None
        if thumbnail_file:
            final_thumbnail_url = await self._upload_file(
                s3_service=s3_service,
                file=thumbnail_file,
                folder="course-thumbnails",
                allowed_types=["jpeg", "png", "svg", "jpg"],
                max_size_mb=50,
                default_mime_type="image/jpeg",
                error_message="Failed to upload thumbnail"
            )
        elif thumbnail_url:
            final_thumbnail_url = thumbnail_url
        
        # Process preview video (file takes precedence over URL)
        final_preview_video_url = None
        if preview_video_file:
            final_preview_video_url = await self._upload_file(
                s3_service=s3_service,
                file=preview_video_file,
                folder="course-preview-videos",
                allowed_types=["mp4", "mov", "avi"],
                max_size_mb=200,
                default_mime_type="video/mp4",
                error_message="Failed to upload preview video"
            )
        elif preview_video_url:
            final_preview_video_url = preview_video_url
        
        # Create update schema
        course_update = CourseUpdate(
            title=title,
            description=description,
            price=price_float,
            thumbnail_url=final_thumbnail_url,
            preview_video_url=final_preview_video_url
        )
        
        result = course_service.update_course(course_id, course_update)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code"), 
                detail=result.get("message")
            )
        
        return result

    async def _process_thumbnail(
        self, 
        s3_service: S3Service, 
        thumbnail_url: Optional[str], 
        thumbnail_file: Optional[UploadFile]
    ) -> str:
        """Process thumbnail upload or URL - thumbnail is required, file takes preference over URL"""
        
        if not thumbnail_url and not thumbnail_file:
            raise HTTPException(
                status_code=400, 
                detail="Thumbnail is required (either URL or file)"
            )
        
        # File takes preference over URL
        if thumbnail_file:
            return await self._upload_file(
                s3_service=s3_service,
                file=thumbnail_file,
                folder="course-thumbnails",
                allowed_types=["jpeg", "png", "svg", "jpg"],
                max_size_mb=50,
                default_mime_type="image/jpeg",
                error_message="Failed to upload thumbnail"
            )
        
        # Use URL if no file provided
        return thumbnail_url

    async def _process_preview_video(
        self, 
        s3_service: S3Service, 
        preview_video_url: Optional[str], 
        preview_video_file: Optional[UploadFile]
    ) -> Optional[str]:
        """Process preview video upload or URL - both are optional, file takes preference over URL"""
        
        # File takes preference over URL
        if preview_video_file:
            return await self._upload_file(
                s3_service=s3_service,
                file=preview_video_file,
                folder="course-preview-videos",
                allowed_types=["mp4", "mov", "avi"],
                max_size_mb=200,
                default_mime_type="video/mp4",
                error_message="Failed to upload preview video"
            )
        
        # Use URL if no file provided (could be None)
        return preview_video_url

    async def _upload_file(
        self,
        s3_service: S3Service,
        file: UploadFile,
        folder: str,
        allowed_types: list[str],
        max_size_mb: int,
        default_mime_type: str,
        error_message: str
    ) -> str:
        """Generic file upload handler with validation"""
        
        # Read file content
        file_content = await file.read()
        
        # Validate file
        is_valid, validation_message = validate_file(
            filename=file.filename,
            file_size=len(file_content),
            allowed_extensions=allowed_types,
            max_size=max_size_mb
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_message
            )
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Upload to S3
        upload_result = s3_service.upload_file(
            file=file_content,
            file_name=safe_filename,
            folder_path=folder,
            mime_type=file.content_type or default_mime_type
        )
        
        if not upload_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_message
            )
        
        return upload_result.get("url")
    
    def publish_course(self, course_id: UUID, course_service: course_service_dependency):
        result = course_service.publish_course(course_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def fetch_all_course_statuses(self, course_service: course_service_dependency):
        result = course_service.fetch_all_course_statuses()
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def delete_course(self, course_id: UUID, course_service: course_service_dependency):
        result = course_service.delete_course(course_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def feature_course(self, course_id: UUID, course_service: course_service_dependency):
        result = course_service.feature_course(course_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def course_checkout(
            self, 
            course_id: UUID, 
            current_user: current_active_user_dependency, 
            course_service: course_service_dependency
        ):
        """Create Stripe checkout session for course purchase"""
        result = course_service.course_checkout(
            course_id=course_id,
            user_id=current_user.Id
        )

        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))

        response = {"url": result.get("data", {}).get("url"), "id": result.get("data", {}).get("id")}

        return response

    async def verify_checkout_session(
            self,
            checkout_session_id: str,
            course_service: course_service_dependency
        ):


        result = course_service.enroll_user_in_course(
            checkout_session_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        
        return result

    def get_purchase_history(
            self,
            current_user: current_active_user_dependency,
            course_service: course_service_dependency
        ):
        """
        Get all enrollment purchase history for the current user.
        Returns a list of all purchases including initial enrollments and renewals.
        """
        result = course_service.get_user_purchase_history(current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def get_course_purchases(
            self,
            course_id: UUID,
            current_user: current_active_user_dependency,
            course_service: course_service_dependency
        ):
        """
        Get purchase history for a specific course enrollment.
        Returns all purchases made for the specified course (initial and renewals).
        """
        result = course_service.get_course_purchase_history(current_user.Id, course_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

