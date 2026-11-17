from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from services import ModuleService, S3Service
from middleware.auth_middleware import get_current_active_user, require_admin
from models import UserModel
from schemas import ModuleBase, LessonBase, UpdateModule, UpdateLesson
from uuid import UUID
from typing import Annotated, Optional
from dependencies import get_module_service, get_s3_service
from utils import validate_file, sanitize_filename, API_PREFIX, get_logger

class ModuleController:
    module_service_dependency = Annotated[ModuleService, Depends(get_module_service)]
    current_active_user = Annotated[UserModel, Depends(get_current_active_user)]
    s3_service_dependency = Annotated[S3Service, Depends(get_s3_service)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/modules", tags=["modules"])
        self.logger = get_logger("app.controllers.module")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route("/", self.get_modules, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{module_id}", self.fetch_module_by_id, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/", self.create_module, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{module_id}", self.update_module, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{module_id}", self.delete_module, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{module_id}/free", self.set_module_as_free, methods=["PATCH"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons", self.create_lesson, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/{lesson_id}", self.get_lesson_by_id, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/{lesson_id}", self.delete_lesson, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/{lesson_id}", self.update_lesson, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/{lesson_id}/resources", self.add_lesson_resource, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/resources/{resource_id}", self.delete_lesson_resource, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/content/type", self.fetch_lesson_content_types, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/{lesson_id}/last-viewed", self.mark_lesson_as_last_viewed, methods=["PATCH"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/lessons/{lesson_id}/complete", self.mark_lesson_as_completed, methods=["PATCH"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/lessons/{lesson_id}/undo-completion", self.undo_lesson_completion, methods=["PATCH"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/lessons/content/images", self.add_course_image, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/lessons/content/images", self.get_course_images, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.logger.info("ModuleController routes have been set up")


    def get_modules(self, module_service: module_service_dependency):
        result = module_service.fetch_all_modules()
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def fetch_module_by_id(self, module_id: UUID, module_service: module_service_dependency):
        result = module_service.fetch_module_by_id(module_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def create_module(self, module_data: ModuleBase, module_service: module_service_dependency):
        result = module_service.create_module(module_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def update_module(self, module_id: UUID, module_data: UpdateModule, module_service: module_service_dependency):
        result = module_service.update_module(module_id, module_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def delete_module(self, module_id: UUID, module_service: module_service_dependency):
        result = module_service.delete_module(module_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def set_module_as_free(self, module_id: UUID, module_service: module_service_dependency):
        result = module_service.set_module_as_free(module_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    async def create_lesson(
        self, 
        module_service: module_service_dependency,
        s3_service: s3_service_dependency,
        title: str = Form(...),
        module_id: str = Form(...),
        content_type_id: str = Form(...),
        created_by: str = Form(...),
        description: Optional[str] = Form(None),
        sort_order: int = Form(...),
        content_url: Optional[str] = Form(None),
        content_text: Optional[str] = Form(None),
        estimated_duration: Optional[int] = Form(None),
        content_file: Optional[UploadFile] = File(None)
    ):
        """Create a lesson with optional file upload for content"""
        
        try:
            module_uuid = UUID(module_id)
            content_type_uuid = UUID(content_type_id)
            created_by_uuid = UUID(created_by)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid UUID format for module_id, content_type_id, or created_by"
            )
        
        final_content_url = content_url
        
        if content_file:
            final_content_url = await self._upload_lesson_content_file(
                s3_service, content_file
            )
        elif not content_url and not content_text:
            raise HTTPException(
                status_code=400,
                detail="Either content_file, content_url, or content_text must be provided"
            )
        
        lesson_data = LessonBase(
            title=title,
            description=description,
            sort_order=sort_order,
            module_id=module_uuid,
            content_type_id=content_type_uuid,
            content_url=final_content_url,
            content_text=content_text,
            estimated_duration=estimated_duration,
            created_by=created_by_uuid
        )
        
        result = module_service.create_lesson(lesson_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    async def _upload_lesson_content_file(
        self, 
        s3_service: S3Service, 
        content_file: UploadFile
    ) -> str:
        """Upload lesson content file to S3 and return the URL"""
        
        file_content = await content_file.read()
        
        is_valid, validation_message = validate_file(
            filename=content_file.filename,
            file_size=len(file_content),
            allowed_extensions={"pdf", "docx", "pptx", "mp4", "mov", "avi", "jpeg", "jpg", "png", "txt", "md"},
            max_size=200
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_message
            )
        
        safe_filename = sanitize_filename(content_file.filename)
        
        upload_result = s3_service.upload_file(
            file=file_content,
            file_name=safe_filename,
            folder_path="lesson-content",
            mime_type=content_file.content_type or "application/octet-stream"
        )
        
        if not upload_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload lesson content file"
            )
        
        return upload_result.get("url")

    def get_lesson_by_id(self, lesson_id: UUID, module_service: module_service_dependency):
        result = module_service.get_lesson_by_id(lesson_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def delete_lesson(self, lesson_id: UUID, module_service: module_service_dependency):
        result = module_service.delete_lesson(lesson_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    async def update_lesson(
        self,
        lesson_id: UUID,
        module_service: module_service_dependency,
        s3_service: s3_service_dependency,
        title: str = Form(...),
        description: str = Form(...),
        sort_order: int = Form(...),
        content_type_id: str = Form(...),
        estimated_duration: int = Form(...),
        content_url: Optional[str] = Form(None),
        content_text: Optional[str] = Form(None),
        content_file: Optional[UploadFile] = File(None)
    ):
        """Update a lesson with optional file upload for content"""
        
        try:
            content_type_uuid = UUID(content_type_id)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid UUID format for content_type_id"
            )
        
        final_content_url = None
        
        # File takes precedence over URL
        if content_file:
            final_content_url = await self._upload_lesson_content_file(
                s3_service, content_file
            )
        elif content_url:
            final_content_url = content_url
        elif not content_text:
            raise HTTPException(
                status_code=400,
                detail="Either content_file, content_url, or content_text must be provided"
            )
        
        lesson_data = UpdateLesson(
            title=title,
            description=description,
            sort_order=sort_order,
            content_type_id=content_type_uuid,
            content_url=final_content_url,
            content_text=content_text,
            estimated_duration=estimated_duration
        )
        
        result = module_service.update_lesson(lesson_id, lesson_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    async def add_lesson_resource(
            self,
            lesson_id: UUID,
            s3_service: s3_service_dependency,
            module_service: module_service_dependency,
            resource_file: Optional[UploadFile] = File(None),
            resource_url: Optional[str] = Form(None),
            resource_name: str = Form(..., max_length=100),
            is_downloadable: str = Form("true")
        ):

        if not resource_url and not resource_file:
            raise HTTPException(status_code=400, detail="Either resource_url or resource_file must be provided")

        # Convert string to boolean properly
        downloadable = is_downloadable.lower() in ("true", "1", "yes", "on")

        upload_result = {}
        
        if resource_file:
            resource_content = await resource_file.read()

            is_valid, validation_message = validate_file(
                resource_file.filename, 
                len(resource_content), 
                allowed_extensions={'pdf', 'docx', 'pptx', 'jpeg', 'jpg', 'png', 'svg'}, 
                max_size=10
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=validation_message
                )
            
            safe_resource_name = f"{sanitize_filename(resource_file.filename)}-{lesson_id}"
        
            upload_result = s3_service.upload_file(
                file=resource_content, 
                file_name=safe_resource_name, 
                folder_path="lesson-resources",
                mime_type=resource_file.content_type or "application/pdf"
            )

            if not upload_result.get("success"):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload resource file")

        result = module_service.add_lesson_resource(
            lesson_id, 
            upload_result.get("url") if upload_result else resource_url,
            resource_name, 
            downloadable
        )

        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def delete_lesson_resource(self, resource_id: UUID, module_service: module_service_dependency):
        result = module_service.delete_lesson_resource(resource_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    async def mark_lesson_as_last_viewed(
        self,
        lesson_id: UUID,
        module_service: module_service_dependency,
        current_user: current_active_user
    ):
        result = await module_service.set_lesson_as_last_viewed(lesson_id, current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    async def mark_lesson_as_completed(
        self,
        lesson_id: UUID,
        module_service: module_service_dependency,
        current_user: current_active_user
    ):
        result = await module_service.set_lesson_as_completed(lesson_id, current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    async def undo_lesson_completion(
        self,
        lesson_id: UUID,
        module_service: module_service_dependency,
        current_user: current_active_user
    ):
        result = await module_service.undo_lesson_completion(lesson_id, current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result

    def fetch_lesson_content_types(self, module_service: module_service_dependency):
        result = module_service.fetch_lesson_content_types()
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    async def add_course_image(
            self,
            module_service: module_service_dependency,
            s3_service: s3_service_dependency,
            image_name: str = Form(...),
            image_file: UploadFile = File(None)
        ):

        image_content = await image_file.read()
        is_valid, validation_message = validate_file(
            image_file.filename, 
            len(image_content), 
            allowed_extensions={'jpeg', 'jpg', 'png', 'svg'}, 
            max_size=20
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=validation_message
            )
        
        safe_image_name = f"{sanitize_filename(image_file.filename)}"

        upload_result = s3_service.upload_file(
            file=image_content,
            file_name=safe_image_name,
            folder_path="course-images",
            mime_type=image_file.content_type or "image/jpeg"
        )

        if not upload_result.get("success"):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload course image file")

        result = module_service.add_content_image(upload_result.get("url"), image_name)

        return result

    def get_course_images(
        self,
        module_service: module_service_dependency,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0
    ):
        """Get course images with pagination and search"""
        result = module_service.fetch_course_images(limit=limit, offset=offset, search=search)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result