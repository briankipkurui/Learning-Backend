from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from dependencies import get_job_application_service, get_s3_service
from services import JobApplicationService, S3Service
from utils.logger import get_logger
from utils.constants import API_PREFIX
from schemas import ResumeCreate, ResumeInDB, UpdateComments, JobApplicationCreate, JobApplicationInDB, JobApplicationActivityCreate, JobApplicationActivityTypeInDB
from models import UserModel
from typing import Optional, Annotated, List
from middleware.auth_middleware import get_current_active_user
from utils import validate_file, sanitize_filename
from uuid import UUID



class JobApplicationController:
    job_appication_service_dependency = Annotated[JobApplicationService, Depends(get_job_application_service)]
    s3_service_dependency = Annotated[S3Service, Depends(get_s3_service)]
    current_active_user_dependency = Annotated[UserModel, Depends(get_current_active_user)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/job-application", tags=["job-applications"])
        self.logger = get_logger("app.controllers.job_application")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route("/", self.create_job_application, methods=["POST"], status_code=status.HTTP_201_CREATED)
        self.router.add_api_route("/user/{user_id}", self.fetch_job_applications_by_user, methods=["GET"], response_model=List[JobApplicationInDB], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{application_id}", self.fetch_job_application_by_id, methods=["GET"], response_model=JobApplicationInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/{application_id}", self.delete_job_application, methods=["DELETE"], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/activities", self.create_job_application_activity, methods=["POST"], response_model=JobApplicationActivityCreate, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/activities/{activity_id}", self.delete_job_application_activity, methods=["DELETE"], response_model=dict, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/activities/types", self.fetch_all_activity_types, methods=["GET"], response_model=List[JobApplicationActivityTypeInDB], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/resumes", self.create_resume, methods=["POST"], response_model=ResumeInDB, status_code=status.HTTP_201_CREATED)
        self.router.add_api_route("/resumes/user/{user_id}", self.get_resumes_by_user, methods=["GET"], response_model=List[ResumeInDB], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/resumes/{resume_id}", self.get_resume_by_id, methods=["GET"], response_model=ResumeInDB, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/resumes/{resume_id}", self.delete_resume, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/resumes/{resume_id}/comments", self.update_resume_comments, methods=["PATCH"], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.logger.info("Job Application Controller routes have been set up.")

    def _cleanup_uploaded_files(self, s3_service: S3Service, uploaded_files: List[dict]):
        """
        Helper method to cleanup uploaded files from S3 in case of failure
        """
        for file_info in uploaded_files:
            try:
                file_key = f"{file_info['folder_path']}/{file_info['file_name']}"
                delete_result = s3_service.delete_file(file_key)
                if delete_result.get("success"):
                    self.logger.info(f"Cleaned up uploaded file: {file_key}")
                else:
                    self.logger.warning(f"Failed to cleanup file {file_key}: {delete_result.get('message')}")
            except Exception as e:
                self.logger.error(f"Error during cleanup of file {file_info['file_name']}: {str(e)}")

    def _validate_form_fields(self, company_name: str, position: str) -> None:
        """Validate basic form fields for job application"""
        if not company_name.strip() or not position.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name and position are required fields"
            )

    async def _validate_files(
            self, resume_file: Optional[UploadFile],
            cover_letter: Optional[UploadFile]
        ) -> tuple[Optional[bytes], Optional[bytes]]:
        """
        Validate both resume and cover letter files if provided.
        Returns tuple of (resume_content, cover_letter_content)
        """
        resume_content = None
        cover_letter_content = None
        
        if resume_file:
            resume_content = await resume_file.read()
            resume_validation_status, resume_validation_message = validate_file(
                resume_file.filename, 
                len(resume_content), 
                allowed_extensions={"pdf", "docx"}, 
                max_size=10
            )

            if not resume_validation_status:
                self.logger.error(f"Resume file validation failed: {resume_validation_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resume_validation_message
                )
                
        if cover_letter:
            cover_letter_content = await cover_letter.read()
            cover_letter_validation_status, cover_letter_validation_message = validate_file(
                cover_letter.filename, 
                len(cover_letter_content), 
                allowed_extensions={"pdf", "docx"}, 
                max_size=10
            )

            if not cover_letter_validation_status:
                self.logger.error(f"Cover letter file validation failed: {cover_letter_validation_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=cover_letter_validation_message
                )
        
        return resume_content, cover_letter_content

    def _upload_files_to_s3(
            self, 
            s3_service: S3Service, 
            current_user: UserModel,
            resume_file: Optional[UploadFile], 
            cover_letter: Optional[UploadFile],
            resume_content: Optional[bytes], 
            cover_letter_content: Optional[bytes]
        ) -> tuple[Optional[str], Optional[str], List[dict]]:
        """
        Upload validated files to S3.
        Returns tuple of (resume_url, cover_letter_url, uploaded_files_list)
        """
        uploaded_files = []
        resume_url = None
        cover_letter_url = None
        
        # Upload resume if provided
        if resume_file and resume_content:
            safe_resume_filename = sanitize_filename(resume_file.filename)
            unique_resume_filename = f"{current_user.Id}-{safe_resume_filename}"

            resume_upload_result = s3_service.upload_file(
                file=resume_content, 
                file_name=unique_resume_filename,
                folder_path="resumes",
                mime_type=resume_file.content_type or "application/pdf"
            )

            if not resume_upload_result.get("success"):
                self.logger.error(f"Failed to upload resume to S3: {resume_upload_result.get('message')}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=resume_upload_result.get("message")
                )
            
            uploaded_files.append({
                "file_name": unique_resume_filename,
                "folder_path": "resumes"
            })
            resume_url = resume_upload_result.get("url")
            self.logger.info(f"Resume uploaded successfully: {unique_resume_filename}")

        # Upload cover letter if provided
        if cover_letter and cover_letter_content:
            safe_cover_letter_filename = sanitize_filename(cover_letter.filename)
            unique_cover_letter_filename = f"{current_user.Id}-{safe_cover_letter_filename}"

            cover_letter_upload_result = s3_service.upload_file(
                file=cover_letter_content, 
                file_name=unique_cover_letter_filename,
                folder_path="cover_letters",
                mime_type=cover_letter.content_type or "application/pdf"
            )

            if not cover_letter_upload_result.get("success"):
                self.logger.error(f"Failed to upload cover letter to S3: {cover_letter_upload_result.get('message')}")
                # Cleanup the successfully uploaded resume before raising the error
                self._cleanup_uploaded_files(s3_service, uploaded_files)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=cover_letter_upload_result.get("message")
                )
            
            uploaded_files.append({
                "file_name": unique_cover_letter_filename,
                "folder_path": "cover_letters"
            })
            cover_letter_url = cover_letter_upload_result.get("url")
            self.logger.info(f"Cover letter uploaded successfully: {unique_cover_letter_filename}")
        
        return resume_url, cover_letter_url, uploaded_files

    def _create_job_application_record(
            self, 
            job_application_service: JobApplicationService,
            s3_service: S3Service,
            uploaded_files: List[dict],
            company_name: str,
            position: str,
            job_application_url: Optional[str],
            application_date: Optional[str],
            notes: Optional[str],
            resume_url: Optional[str],
            cover_letter_url: Optional[str],
            current_user: UserModel
        ) -> dict:
        """
        Create job application record in database and return response data
        """
        job_application_data = JobApplicationCreate(
            company_name=company_name,
            job_application_url=job_application_url,
            position=position,
            application_date=application_date,
            notes=notes,
            resume_url=resume_url,
            cover_letter_url=cover_letter_url,
            user_id=current_user.Id
        )
        
        application_result = job_application_service.create_job_application(job_application_data)
        
        if not application_result.get("success"):
            self.logger.error(f"Failed to create job application record: {application_result.get('message')}")
            # Cleanup uploaded files if database creation fails
            self._cleanup_uploaded_files(s3_service, uploaded_files)
            raise HTTPException(
                status_code=application_result.get("status_code", 500),
                detail=application_result.get("message")
            )
        
        return application_result.get("data")

    async def create_job_application(self, 
        job_application_service: job_appication_service_dependency,
        s3_service: s3_service_dependency,
        current_user: current_active_user_dependency,
        resume_file: Optional[UploadFile] = File(None),
        cover_letter: Optional[UploadFile] = File(None),
        company_name: str = Form(..., max_length=100),
        job_application_url: Optional[str] = Form(None, max_length=255),
        position: str = Form(..., max_length=100),
        application_date: Optional[str] = Form(None),
        notes: Optional[str] = Form(None, max_length=1000)
    ):
        """Create a new job application for the current user"""
        uploaded_files = []
        
        try:
            self._validate_form_fields(company_name, position)
            
            resume_content, cover_letter_content = await self._validate_files(resume_file, cover_letter)
            
            resume_url, cover_letter_url, uploaded_files = self._upload_files_to_s3(
                s3_service, current_user, resume_file, cover_letter, 
                resume_content, cover_letter_content
            )
            
            return self._create_job_application_record(
                job_application_service, s3_service, uploaded_files,
                company_name, position, job_application_url, application_date,
                notes, resume_url, cover_letter_url, current_user
            )

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Exception during job application creation: {str(e)}")
            self._cleanup_uploaded_files(s3_service, uploaded_files)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during job application creation"
            )
        finally:
            if resume_file:
                await resume_file.close()
            if cover_letter:
                await cover_letter.close()

    def fetch_job_applications_by_user(
        self,
        job_application_service: job_appication_service_dependency,
        user_id: UUID
    ):
        """Fetch all job applications for a specific user"""
        result = job_application_service.get_job_applications_by_user(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")
    
    def fetch_job_application_by_id(
        self,
        job_application_service: job_appication_service_dependency,
        application_id: UUID
    ):
        """Fetch a specific job application by ID"""
        result = job_application_service.get_job_application_by_id(application_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")
    
    def delete_job_application(
        self,
        job_application_service: job_appication_service_dependency,
        application_id: UUID
    ):
        """Delete a specific job application by ID"""
        result = job_application_service.delete_job_application(application_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return {"message": result.get("message")}
    
    def create_job_application_activity(
        self,
        job_application_service: job_appication_service_dependency,
        activity_data: JobApplicationActivityCreate
    ):
        """
        Create a new job application activity in the repository.

        :param activity_data: Job application activity data.
        """
        try:
            result = job_application_service.create_job_application_activity(activity_data)
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
            
            return result.get("data")
        except Exception as e:
            return {"success": False, "message": str(e), "status_code": 500}
        
    def delete_job_application_activity(
        self,
        job_application_service: job_appication_service_dependency,
        activity_id: UUID
    ):
        """
        Delete a specific job application activity by its ID.

        :param activity_id: Activity ID.
        """
        try:
            result = job_application_service.delete_job_application_activity(activity_id)
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
            return {"message": result.get("message")}
        except Exception as e:
            return {"success": False, "message": str(e), "status_code": 500}

    def fetch_all_activity_types(
        self,
        job_application_service: job_appication_service_dependency
    ):
        """
        Fetch all job application activity types.
        """
        try:
            result = job_application_service.fetch_all_activity_types()
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
            
            return result.get("data")
        except Exception as e:
            return {"success": False, "message": str(e), "status_code": 500}

    async def create_resume(
        self,
        job_application_service: job_appication_service_dependency,
        current_user: current_active_user_dependency,
        s3_service: s3_service_dependency,
        user_id: UUID = Form(...),
        comments: Optional[str] = Form(None, max_length=1000),
        file: UploadFile = File(...)
    ):
        """Create a new resume for the current user"""
        try:
            content = await file.read()
            validation_status, validation_message = validate_file(
                file.filename, 
                len(content), 
                allowed_extensions={"pdf", "docx"}, 
                max_size=10
            )

            if not validation_status:
                self.logger.error(f"File validation failed: {validation_message}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_message
                )
            
            user_resumes = job_application_service.get_resumes_by_user(current_user.Id)

            if len(user_resumes.get("data", [])) >= 5:
                raise HTTPException(
                    status_code=400,
                    detail="Sorry, you reached the maximum number of resumes."
                )

            
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            unique_filename = f"{current_user.Id}-{safe_filename}"

            # Upload resume to S3
            upload_result = s3_service.upload_file(
                file=content, 
                file_name=unique_filename,
                folder_path="resumes",
                mime_type=file.content_type or "application/pdf"
            )

            if not upload_result.get("success"):
                self.logger.error(f"Failed to upload resume to S3: {upload_result.get('message')}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=upload_result.get("message")
                )

            # Create resume record in the database
            resume_data = ResumeCreate(
                file_url=upload_result.get("url"),
                user_id=user_id,
                comments=comments
            )

            result = job_application_service.create_resume(resume_data)

            if not result.get("success"):
                self.logger.error(f"Failed to create resume record: {result.get('message')}")
                raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
            
            return result.get("data")

        except HTTPException:
            raise
        
        except Exception as e:
            self.logger.error(f"Exception in create_resume: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

        finally:
            await file.close()

    def get_resumes_by_user(
        self,
        job_application_service: job_appication_service_dependency,
        user_id: UUID
    ):
        """Retrieve all resumes for the current user"""
        result = job_application_service.get_resumes_by_user(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")

    def get_resume_by_id(
        self,
        job_application_service: job_appication_service_dependency,
        resume_id: UUID
    ):
        """Retrieve a specific resume by ID"""
        result = job_application_service.get_resume_by_id(resume_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")

    def update_resume_comments(
        self,
        job_application_service: job_appication_service_dependency,
        resume_id: UUID,
        payload: UpdateComments
    ):
        """Update comments for a specific resume"""
        result = job_application_service.update_resume_comments(resume_id, payload.comments)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")

    def delete_resume(
        self,
        job_application_service: job_appication_service_dependency,
        resume_id: UUID
    ):
        """Delete a specific resume by ID"""
        result = job_application_service.delete_resume(resume_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code", 500), detail=result.get("message"))
        
        return result.get("data")
    

