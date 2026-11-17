from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from services import AIService
from middleware.auth_middleware import get_current_active_user, require_admin
from models import UserModel
from schemas import (
    CreateInterviewQuestionRequest, UpdateInterviewQuestionRequest, InterviewQuestionResponse, PaginatedInterviewQuestionsResponse
)
from typing import Annotated, Optional
from dependencies import get_ai_service
from utils import API_PREFIX, get_logger, validate_file
from uuid import UUID

class AIController:
    ai_service_dependency = Annotated[AIService, Depends(get_ai_service)]
    current_active_user = Annotated[UserModel, Depends(get_current_active_user)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/ai", tags=["ai"])
        self.logger = get_logger("app.controllers.ai")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route("/resume-jd-analysis", self.analyze_resume_jd, methods=["POST"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/resume-jd-analyses", self.user_cv_analyses, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/resume-jd-analyses/{analysis_id}", self.get_analysis_by_id, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
        self.router.add_api_route("/resume-jd-analyses/{analysis_id}", self.delete_cv_analysis, methods=["DELETE"], status_code=status.HTTP_200_OK)

        # Interview Practice routes
        self.router.add_api_route("/interview/question/next", self.get_next_question, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/interview/analyze", self.analyze_interview_response, methods=["POST"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/interview/sessions", self.get_interview_practice_sessions, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/interview/sessions/{session_id}", self.get_interview_practice_session_by_id, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/interview/sessions/{session_id}", self.delete_interview_practice_session, methods=["DELETE"], status_code=status.HTTP_200_OK)
        
        # Admin interview question management routes
        self.router.add_api_route("/admin/interview/questions", self.create_interview_question, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/admin/interview/questions/{question_id}", self.update_interview_question, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/admin/interview/questions", self.get_all_interview_questions, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/admin/interview/questions/{question_id}", self.get_interview_question_by_id, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/admin/interview/questions/{question_id}", self.delete_interview_question, methods=["DELETE"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        
        self.logger.info("AIController routes have been set up")

    async def analyze_resume_jd(
        self,
        ai_service: ai_service_dependency,
        current_user: current_active_user,
        resume_text: Optional[str] = Form(None),
        jd_text: Optional[str] = Form(None),
        resume_file: Optional[UploadFile] = File(None),
        jd_file: Optional[UploadFile] = File(None)
    ):
        """Flexible resume and JD analysis supporting any combination of text and file inputs"""
        # Validate that we have at least one resume input and one JD input.
        if not resume_text and not resume_file:
            raise HTTPException(
                status_code=400,
                detail="Either resume_text or resume_file must be provided"
            )
        
        if not jd_text and not jd_file:
            raise HTTPException(
                status_code=400,
                detail="Either jd_text or jd_file must be provided"
            )
        
        # Process resume file if provided.
        resume_file_content = None
        resume_file_type = None
        
        if resume_file:
            # Validate resume file using existing utility
            file_content = await resume_file.read()
            is_valid, validation_message = validate_file(
                filename=resume_file.filename,
                file_size=len(file_content),
                allowed_extensions={'pdf', 'docx', 'txt'},
                max_size=20  # 20MB limit
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Resume file validation failed: {validation_message}"
                )
            
            resume_file_content = file_content
            resume_file_type = resume_file.content_type
        
        # Process JD file if provided
        jd_file_content = None
        jd_file_type = None
        
        if jd_file:
            # Validate JD file using existing utility
            file_content = await jd_file.read()
            is_valid, validation_message = validate_file(
                filename=jd_file.filename,
                file_size=len(file_content),
                allowed_extensions={'pdf', 'docx', 'txt'},
                max_size=20  # 20MB limit
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"JD file validation failed: {validation_message}"
                )
            
            jd_file_content = file_content
            jd_file_type = jd_file.content_type
        
        # Call the flexible analysis method
        result = ai_service.analyze_resume_and_jd_flexible(
            resume_text=resume_text,
            resume_file_content=resume_file_content,
            resume_file_type=resume_file_type,
            jd_text=jd_text,
            jd_file_content=jd_file_content,
            jd_file_type=jd_file_type,
            user_id=current_user.Id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("message", "Analysis failed")
            )
        
        return result

    def user_cv_analyses(
        self,
        ai_service: ai_service_dependency,
        current_user: current_active_user,
    ):
        """Get current user's CV analyses"""
        result = ai_service.get_user_resume_analyses(current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_analysis_by_id(
        self,
        analysis_id: str,
        ai_service: ai_service_dependency,
    ):
        """Get specific CV analysis by ID"""
        result = ai_service.get_cv_analysis_details(analysis_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    

    def delete_cv_analysis(
        self,
        analysis_id: str,
        ai_service: ai_service_dependency,
        current_user: current_active_user,
    ):
        """Delete specific CV analysis by ID"""
        result = ai_service.delete_cv_analysis(analysis_id, user_id=current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    # ===== Interview Practice Endpoints =====

    def get_next_question(
        self,
        ai_service: ai_service_dependency,
        current_user: current_active_user
    ):
        """Get the next interview question based on user's profession and progress"""
        result = ai_service.get_next_interview_question(current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    # ======= Admin Interview Question Management =======
    
    def create_interview_question(
        self,
        request: CreateInterviewQuestionRequest,
        ai_service: ai_service_dependency
    ):
        """Create a new interview question (Admin only)"""
        question_data = request.model_dump(exclude_unset=True)
        result = ai_service.create_interview_question(question_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def update_interview_question(
        self,
        question_id: str,
        request: UpdateInterviewQuestionRequest,
        ai_service: ai_service_dependency
    ):
        """Update an existing interview question (Admin only)"""
        try:
            question_uuid = UUID(question_id)
            question_data = request.model_dump(exclude_unset=True)
            result = ai_service.update_interview_question(question_uuid, question_data)
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")
        
    
    def get_all_interview_questions(
        self,
        ai_service: ai_service_dependency,
        limit: int = 20,
        offset: int = 0,
        profession_id: Optional[str] = None
    ):
        """Get paginated list of all interview questions (Admin only)"""
        profession_uuid = None
        if profession_id:
            try:
                profession_uuid = UUID(profession_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid profession ID format")
        
        result = ai_service.get_all_interview_questions(
            limit=limit,
            offset=offset,
            profession_id=profession_uuid
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
        
    
    def get_interview_question_by_id(
        self,
        question_id: str,
        ai_service: ai_service_dependency
    ):
        """Get a single interview question by ID (Admin only)"""
        try:
            question_uuid = UUID(question_id)
            result = ai_service.get_interview_question_by_id(question_uuid)
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")
        
    
    def delete_interview_question(
        self,
        question_id: str,
        ai_service: ai_service_dependency
    ):
        """Delete an interview question by ID (Admin only)"""
        try:
            question_uuid = UUID(question_id)
            result = ai_service.delete_interview_question(question_uuid)
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid question ID format")
        

    async def analyze_interview_response(
            self,
            ai_service: ai_service_dependency,
            current_user: current_active_user,
            audio_file: UploadFile = File(...),
            question_id: str = Form(...)
        ):
        """Analyze user's interview response"""
        try:
            audio_bytes = await audio_file.read()
            # Validate file format
            allowed_formats = {'flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm'}
            isValid, validation_message = validate_file(
                audio_file.filename,
                len(audio_bytes),
                allowed_formats,
                100
            )
            
            if not isValid:
                raise HTTPException(
                    status_code=400,
                    detail=validation_message
                )
            
            # Call service with both bytes and filename
            result = ai_service.analyze_interview_response(
                audio_bytes=audio_bytes,
                filename=audio_file.filename,
                user_id=current_user.Id,
                question_id=UUID(question_id)
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Interview response analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def get_interview_practice_sessions(
            self,
            ai_service: ai_service_dependency,
            current_user: current_active_user,
            search: Optional[str] = None
        ):
        """Get all interview practice sessions for the current user"""
        try:
            result = ai_service.get_user_interview_practice_sessions(
                user_id=current_user.Id,
                search=search
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve interview practice sessions: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def get_interview_practice_session_by_id(
            self,
            ai_service: ai_service_dependency,
            current_user: current_active_user,
            session_id: str
        ):
        """Get a single interview practice session by ID with full details"""
        try:
            # Validate session_id format
            try:
                session_uuid = UUID(session_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")
            
            result = ai_service.get_interview_practice_session_by_id(
                session_id=session_uuid,
                user_id=current_user.Id
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve interview practice session: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def delete_interview_practice_session(
            self,
            ai_service: ai_service_dependency,
            current_user: current_active_user,
            session_id: str
        ):
        """Delete an interview practice session by ID"""
        try:
            # Validate session_id format
            try:
                session_uuid = UUID(session_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid session ID format")
            
            result = ai_service.delete_interview_practice_session(
                session_id=session_uuid,
                user_id=current_user.Id
            )
            
            if not result.get("success"):
                raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete interview practice session: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
