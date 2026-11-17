import os
from uuid import UUID
import openai
from typing import Dict, Optional, Any
from utils import (
    get_logger, 
    resume_jd_analysis_prompt,
    process_document_input,
    generate_resume_pdf,
    sanitize_filename,
    interview_analysis_prompt
)
from repositories import JobApplicationRepository, CourseRepository
from services import S3Service
import json
import mimetypes

class AIService:
    def __init__(
        self, 
        job_application_repository: JobApplicationRepository, 
        s3_service: S3Service,
        course_repository: CourseRepository
    ):
        """
        Initialize AI service with OpenAI client and required dependencies.
        
        Args:
            job_application_repository: Repository for job application and CV analysis operations
            s3_service: Service for S3 file upload operations
            course_repository: Repository for course enrollment verification
        """
        self.logger = get_logger("app.services.ai")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.job_application_repository = job_application_repository
        self.s3_service = s3_service
        self.course_repository = course_repository
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        self.default_model = "gpt-5-mini"
        self.transcribe_model = "whisper-1"
        
        self.logger.info("AIService initialized successfully")

    

    def resume_jd_analyzer(self, resume_text: str, jd_text: str) -> str:
        """
        Analyze resume against job description using OpenAI.
        
        Args:
            resume_text: The resume content as text
            jd_text: The job description content as text
        
        Returns:
            str: JSON string containing the analysis results
        """
        prompt = resume_jd_analysis_prompt(resume_text, jd_text)

        try:
            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior career strategist and executive resume consultant with deep expertise in ATS systems, Fortune 500 recruiting practices, and C-suite positioning. You provide direct, sophisticated guidance to high-performing professionals. Your feedback is always actionable, specific to the candidate and role, and focused on material impact."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=20000
            )
            
            analysis = response.choices[0].message.content
            if analysis:
                analysis = analysis.strip()
            else:
                raise ValueError("OpenAI returned empty response content")

            return analysis
            
        except Exception as e:
            raise

    def analyze_resume_and_jd_flexible(
            self,
            user_id: UUID,
            resume_text: Optional[str] = None,
            resume_file_content: Optional[bytes] = None,
            resume_file_type: Optional[str] = None,
            jd_text: Optional[str] = None,
            jd_file_content: Optional[bytes] = None,
            jd_file_type: Optional[str] = None,
        ) -> Dict[str, Any]:
        """
        Analyze resume against job description with flexible input formats.
        Supports text input, file upload, or both. Deducts credit on success.
        
        Args:
            user_id: UUID of the user requesting analysis
            resume_text: Resume content as plain text (optional)
            resume_file_content: Resume file content as bytes (optional)
            resume_file_type: MIME type of resume file (optional)
            jd_text: Job description as plain text (optional)
            jd_file_content: Job description file content as bytes (optional)
            jd_file_type: MIME type of JD file (optional)
        
        Returns:
            Dict containing success status, analysis data, and status code
        """
        try:
            # Check if user has an active (non-expired) enrollment
            if not self.course_repository.user_has_active_enrollment(user_id):
                return {
                    "success": False,
                    "message": "Active course enrollment required. Please purchase a course to access CV analysis.",
                    "status_code": 402
                }
            
            # Process resume input using utils
            try:
                final_resume_text = process_document_input(
                    text_input=resume_text,
                    file_content=resume_file_content,
                    file_type=resume_file_type
                )
            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Resume processing error: {str(e)}",
                    "status_code": 400
                }

            if not final_resume_text:
                return {
                    "success": False,
                    "message": "Resume content is empty or could not be extracted",
                    "status_code": 400
                }

            # Process JD input using utils
            try:
                final_jd_text = process_document_input(
                    text_input=jd_text,
                    file_content=jd_file_content,
                    file_type=jd_file_type
                )

            except ValueError as e:
                return {
                    "success": False,
                    "message": f"Job description processing error: {str(e)}",
                    "status_code": 400
                }
            
            if not final_jd_text:
                return {
                    "success": False,
                    "message": "Job description content is empty or could not be extracted",
                    "status_code": 400
                }

            # Perform analysis using existing method
            analysis = self.resume_jd_analyzer(final_resume_text, final_jd_text)
            analysis_json = json.loads(analysis)

            error = analysis_json.get("error", False)
            if error:
                error_type = analysis_json.get("error_type", "unknown_error")
                error_message = analysis_json.get("error_message", "An unknown error occurred during analysis")
                return {
                    "success": False,
                    "message": f"Analysis error ({error_type}): {error_message}",
                    "status_code": 400
                }
            position = analysis_json.pop("job_title", None)

            # Handle old resume upload or text
            old_resume_url = None
            resume_text_to_save = None
            if resume_file_content:
                # Upload original resume to S3
                file_extension = resume_file_type.split('/')[-1] if resume_file_type else 'pdf'
                filename = sanitize_filename(f"resume_{user_id}_{position or 'analysis'}.{file_extension}")
                upload_result = self.s3_service.upload_file(
                    file=resume_file_content,
                    file_name=filename,
                    folder_path="resume-uploads",
                    mime_type=resume_file_type or "application/pdf"
                )
                if upload_result.get("success"):
                    old_resume_url = upload_result.get("url")
            else:
                # Save resume as text if no file was uploaded
                resume_text_to_save = final_resume_text

            # Handle JD upload or text
            jd_url = None
            jd_text_to_save = None
            if jd_file_content:
                # Upload JD to S3
                file_extension = jd_file_type.split('/')[-1] if jd_file_type else 'pdf'
                filename = sanitize_filename(f"jd_{user_id}_{position or 'analysis'}.{file_extension}")
                upload_result = self.s3_service.upload_file(
                    file=jd_file_content,
                    file_name=filename,
                    folder_path="jd-uploads",
                    mime_type=jd_file_type or "application/pdf"
                )
                if upload_result.get("success"):
                    jd_url = upload_result.get("url")
            else:
                # Save JD as text if no file was uploaded
                jd_text_to_save = final_jd_text

            # Handle optimized resume generation and upload
            new_resume_url = None
            new_resume_content = analysis_json.pop("optimized_resume", None)
            if new_resume_content:
                resume_bytes = generate_resume_pdf(
                    resume_data=new_resume_content,
                    user_id=str(user_id)
                )
                
                # Upload generated resume to S3
                filename = sanitize_filename(f"optimized_resume_{user_id}_{position or 'analysis'}.pdf")
                upload_result = self.s3_service.upload_file(
                    file=resume_bytes,
                    file_name=filename,
                    folder_path="optimized-resumes",
                    mime_type="application/pdf"
                )
                if upload_result.get("success"):
                    new_resume_url = upload_result.get("url")
                
            if position:
                new_analysis = self.job_application_repository.create_cv_analysis(
                    user_id=user_id,
                    job_title=position,
                    analysis_result=analysis_json,
                    new_resume_url=new_resume_url,
                    old_resume_url=old_resume_url,
                    jd_url=jd_url,
                    resume_text=resume_text_to_save,
                    jd_text=jd_text_to_save
                )
                self.logger.info(f"Stored CV analysis for position: {position}, Analysis ID: {new_analysis.Id}")
            
            return {
                "success": True,
                "data": {
                    "Id": str(new_analysis.Id) if position else None,
                    "job_title": position,
                    "analysis_result": analysis_json,
                    "new_resume_url": new_resume_url,
                    "old_resume_url": old_resume_url,
                    "jd_url": jd_url,
                    "resume_text": resume_text_to_save,
                    "jd_text": jd_text_to_save,
                    "created_at": new_analysis.created_at.isoformat() if position and new_analysis.created_at else None
                },
                "status_code": 200
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "An error occurred during analysis",
                "status_code": 500
            }
        
    def get_user_resume_analyses(self, user_id: UUID) -> Dict[str, Any]:
        """
        Retrieve all CV analyses for a specific user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            Dict containing success status, list of analysis snapshots, and status code
        """
        try:
            analyses = self.job_application_repository.fetch_user_resume_analyses(user_id)
            analyses_snapshot = [
                {
                    "job_title": analysis.job_title,
                    "Id": str(analysis.Id),
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                }
                for analysis in analyses]
            return {
                "success": True,
                "data": analyses_snapshot,
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": "An error occurred while retrieving CV analyses",
                "status_code": 500
            }
        
    def get_cv_analysis_details(self, analysis_id: UUID) -> Dict[str, Any]:
        """
        Retrieve detailed CV analysis by its ID.
        
        Args:
            analysis_id: UUID of the CV analysis
        
        Returns:
            Dict containing success status, analysis details, and status code
        """
        try:
            analysis = self.job_application_repository.get_cv_analysis_by_id(analysis_id)
            if not analysis:
                return {
                    "success": False,
                    "message": "CV analysis not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": {
                    "job_title": analysis.job_title,
                    "analysis_result": analysis.analysis_result,
                    "new_resume_url": analysis.new_resume_url,
                    "old_resume_url": analysis.old_resume_url,
                    "jd_url": analysis.jd_url,
                    "resume_text": analysis.resume_text,
                    "jd_text": analysis.jd_text,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None
                },
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": "An error occurred while retrieving the CV analysis",
                "status_code": 500
            }
        
    def delete_cv_analysis(self, analysis_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Delete a CV analysis by its ID.
        
        Args:
            analysis_id: UUID of the CV analysis to delete
            user_id: UUID of the user requesting deletion (for authorization)
        
        Returns:
            Dict containing success status, message, and status code
        """
        try:
            success = self.job_application_repository.delete_cv_analysis(analysis_id, user_id)
            if not success:
                return {
                    "success": False,
                    "message": "CV analysis not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "CV analysis deleted successfully",
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": "An error occurred while deleting the CV analysis",
                "status_code": 500
            }
    
    # ===== Interview Practice Methods =====
    
    def get_next_interview_question(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get the next interview question for a user based on profession and progress.
        
        Prioritizes questions from user's profession, unanswered questions, and easiest difficulty first.
        If all questions answered, restarts from easiest question.
        
        Args:
            user_id: UUID of the user requesting next question
        
        Returns:
            Dict containing success status, question data, and status code
        """
        try:
            # Get user's profession from learner profile
            profession_id = self.job_application_repository.get_user_profession_id(user_id)
            
            # Get next question (prioritizes profession, unanswered, and difficulty)
            question = self.job_application_repository.get_next_interview_question(
                user_id=user_id,
                profession_id=profession_id
            )
            
            if not question:
                return {
                    "success": False,
                    "message": "No interview questions available",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Interview question retrieved successfully",
                "data": {
                    "id": str(question.Id),
                    "question_text": question.question_text,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "framework": question.framework,
                    "skills_tested": question.skills_tested,
                    "framework_description": question.framework_description,
                    "good_answer_criteria": question.good_answer_criteria,
                    "listening_guideline": question.listening_guideline,
                    "common_issues": question.common_issues,
                    "notes": question.notes,
                    "time_limit": question.time_limit,
                    "profession_id": str(question.profession_id) if question.profession_id else None,
                    "profession_name": question.profession.name if question.profession else None
                },
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while retrieving question: {str(e)}",
                "status_code": 500
            }
    
    # ======= Admin CRUD Operations for Interview Questions =======
    
    def create_interview_question(self, question_data: dict) -> Dict[str, Any]:
        """
        Create a new interview question (admin only).
        
        Args:
            question_data: Dictionary containing question fields (question_text, category, difficulty, etc.)
        
        Returns:
            Dict containing success status, created question data, and status code
        """
        try:
            # Create question via repository
            new_question = self.job_application_repository.create_interview_question(question_data)
            
            # Load profession name if profession_id exists
            profession_name = None
            if new_question.profession_id:
                profession_name = new_question.profession.name if new_question.profession else None
            
            return {
                "success": True,
                "message": "Interview question created successfully",
                "data": {
                    "Id": str(new_question.Id),
                    "question_text": new_question.question_text,
                    "category": new_question.category,
                    "difficulty": new_question.difficulty,
                    "framework": new_question.framework,
                    "skills_tested": new_question.skills_tested,
                    "framework_description": new_question.framework_description,
                    "good_answer_criteria": new_question.good_answer_criteria,
                    "listening_guideline": new_question.listening_guideline,
                    "common_issues": new_question.common_issues,
                    "notes": new_question.notes,
                    "time_limit": new_question.time_limit,
                    "profession_id": str(new_question.profession_id) if new_question.profession_id else None,
                    "profession_name": profession_name,
                    "created_at": new_question.created_at,
                    "updated_at": new_question.updated_at
                },
                "status_code": 201
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while creating question: {str(e)}",
                "status_code": 500
            }
    
    def update_interview_question(self, question_id: UUID, question_data: dict) -> Dict[str, Any]:
        """
        Update an existing interview question (admin only).
        
        Args:
            question_id: UUID of the question to update
            question_data: Dictionary containing fields to update
        
        Returns:
            Dict containing success status, updated question data, and status code
        """
        try:
            # Update question via repository
            updated_question = self.job_application_repository.update_interview_question(
                question_id, question_data
            )
            
            if not updated_question:
                return {
                    "success": False,
                    "message": "Interview question not found",
                    "status_code": 404
                }
            
            # Load profession name if profession_id exists
            profession_name = None
            if updated_question.profession_id:
                profession_name = updated_question.profession.name if updated_question.profession else None
            
            return {
                "success": True,
                "message": "Interview question updated successfully",
                "data": {
                    "Id": str(updated_question.Id),
                    "question_text": updated_question.question_text,
                    "category": updated_question.category,
                    "difficulty": updated_question.difficulty,
                    "framework": updated_question.framework,
                    "skills_tested": updated_question.skills_tested,
                    "framework_description": updated_question.framework_description,
                    "good_answer_criteria": updated_question.good_answer_criteria,
                    "listening_guideline": updated_question.listening_guideline,
                    "common_issues": updated_question.common_issues,
                    "notes": updated_question.notes,
                    "time_limit": updated_question.time_limit,
                    "profession_id": str(updated_question.profession_id) if updated_question.profession_id else None,
                    "profession_name": profession_name,
                    "created_at": updated_question.created_at,
                    "updated_at": updated_question.updated_at
                },
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while updating question: {str(e)}",
                "status_code": 500
            }
    
    def get_all_interview_questions(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        profession_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of all interview questions with optional profession filter (admin only).
        
        Args:
            limit: Number of questions per page (default: 20)
            offset: Number of questions to skip (default: 0)
            profession_id: Optional UUID to filter by profession
        
        Returns:
            Dict containing success status, paginated questions list with metadata, and status code
        """
        try:
            # Get paginated questions from repository
            result = self.job_application_repository.get_all_interview_questions(
                limit=limit,
                offset=offset,
                profession_id=profession_id
            )
            
            # Format question data with profession names
            questions_data = []
            for question in result["questions"]:
                profession_name = None
                if question.profession_id:
                    profession_name = question.profession.name if question.profession else None
                
                questions_data.append({
                    "Id": str(question.Id),
                    "question_text": question.question_text,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "framework": question.framework,
                    "skills_tested": question.skills_tested,
                    "framework_description": question.framework_description,
                    "good_answer_criteria": question.good_answer_criteria,
                    "listening_guideline": question.listening_guideline,
                    "common_issues": question.common_issues,
                    "notes": question.notes,
                    "time_limit": question.time_limit,
                    "profession_id": str(question.profession_id) if question.profession_id else None,
                    "profession_name": profession_name,
                    "created_at": question.created_at,
                    "updated_at": question.updated_at
                })
            
            return {
                "success": True,
                "message": "Interview questions retrieved successfully",
                "data": {
                    "questions": questions_data,
                    "total": result["total"],
                    "limit": result["limit"],
                    "offset": result["offset"],
                    "has_next": result["has_next"],
                    "has_prev": result["has_prev"]
                },
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while retrieving questions: {str(e)}",
                "status_code": 500
            }
    
    def get_interview_question_by_id(self, question_id: UUID) -> Dict[str, Any]:
        """
        Get a single interview question by its ID (admin only).
        
        Args:
            question_id: UUID of the question to retrieve
        
        Returns:
            Dict containing success status, question data, and status code
        """
        try:
            question = self.job_application_repository.get_interview_question_by_id(question_id)
            
            if not question:
                return {
                    "success": False,
                    "message": "Interview question not found",
                    "status_code": 404
                }
            
            # Load profession name if profession_id exists
            profession_name = None
            if question.profession_id:
                profession_name = question.profession.name if question.profession else None
            
            return {
                "success": True,
                "message": "Interview question retrieved successfully",
                "data": {
                    "Id": str(question.Id),
                    "question_text": question.question_text,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "framework": question.framework,
                    "skills_tested": question.skills_tested,
                    "framework_description": question.framework_description,
                    "good_answer_criteria": question.good_answer_criteria,
                    "listening_guideline": question.listening_guideline,
                    "common_issues": question.common_issues,
                    "notes": question.notes,
                    "time_limit": question.time_limit,
                    "profession_id": str(question.profession_id) if question.profession_id else None,
                    "profession_name": profession_name,
                    "created_at": question.created_at,
                    "updated_at": question.updated_at
                },
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while retrieving question: {str(e)}",
                "status_code": 500
            }
    
    def delete_interview_question(self, question_id: UUID) -> Dict[str, Any]:
        """
        Delete an interview question by its ID (admin only).
        
        Args:
            question_id: UUID of the question to delete
        
        Returns:
            Dict containing success status, message, and status code
        """
        try:
            deleted = self.job_application_repository.delete_interview_question(question_id)
            
            if not deleted:
                return {
                    "success": False,
                    "message": "Interview question not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "message": "Interview question deleted successfully",
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while deleting question: {str(e)}",
                "status_code": 500
            }

    def analyze_interview_response(
            self, 
            audio_bytes: bytes, 
            filename: str, 
            user_id: UUID,
            question_id: UUID
        ) -> Dict[str, Any]:
        """
        Analyze user's audio interview response. Transcribes audio, analyzes with AI, and saves session.
        Requires active course enrollment.
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original audio filename with extension
            user_id: UUID of the user submitting response
            question_id: UUID of the interview question being answered
        
        Returns:
            Dict containing success status, analysis results, transcript, and status code
        """
        try:
            # Check if user has an active (non-expired) enrollment
            if not self.course_repository.user_has_active_enrollment(user_id):
                return {
                    "success": False,
                    "message": "Active course enrollment required. Please purchase a course to access interview practice.",
                    "status_code": 402
                }

            question = self.job_application_repository.get_interview_question_by_id(question_id)

            if not question:
                return {
                    "success": False,
                    "message": "Interview question not found",
                    "status_code": 404
                }

            transcription = self._transcribe_audio(audio_bytes, filename)

            if len(transcription.strip()) <= 30:
                return {
                    "success": False,
                    "message": "Audio too short for analysis. Please try again with a longer recording.",
                    "status_code": 400
                }

            prompt = interview_analysis_prompt(
                question=question.question_text,
                transcript=transcription,
                category=question.category,
                framework=question.framework,
                skills_tested=question.skills_tested,
                profession=question.profession.name,
                notes=question.notes or "",
                framework_description=question.framework_description or "",
                good_answer_criteria=question.good_answer_criteria or "",
                listening_guideline=question.listening_guideline or "",
                common_issues=question.common_issues or ""
            )

            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {"role": "system", "content": "You are an expert interview coach specializing in objective assessment and actionable feedback. You analyze candidate responses with precision, providing honest evaluations and specific improvement strategies that directly impact interview success."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=20000
            )

            s3_url = self._upload_audio_to_s3(
                audio_bytes=audio_bytes,
                filename=filename,
                user_id=user_id,
                question_id=question_id
            )


            analysis = response.choices[0].message.content
            if analysis:
                analysis = analysis.strip()
            else:
                raise ValueError("OpenAI returned empty response content")

            analysis_data = json.loads(analysis)

            session_result = self._save_interview_practice_session(
                user_id=user_id,
                question_id=question_id,
                audio_url=s3_url,
                transcript=transcription,
                analysis_result=analysis_data
            )

            if not session_result.get("success"):
                return session_result

            error = analysis_data.get("error")
            if error:
                error_message = analysis_data.get("error_message", "An unknown error occurred during analysis")
                return {
                    "success": False,
                    "message": error_message,
                    "status_code": 400
                }
            
            # Fetch the full session details for consistent response
            session_id = UUID(session_result["data"]["session_id"])
            full_session_result = self.get_interview_practice_session_by_id(
                session_id=session_id,
                user_id=user_id
            )
            
            if not full_session_result.get("success"):
                return full_session_result

            return {
                "success": True,
                "message": "Analysis completed successfully",
                "data": full_session_result["data"],
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while transcribing audio: {str(e)}",
                "status_code": 500
            }


    def _transcribe_audio(self, audio_bytes: bytes, filename: str) -> str:
        """
        Transcribe audio bytes to text using OpenAI Whisper.
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original filename with extension (for format detection)
        
        Returns:
            str: Transcribed text from the audio
        """
        try:
            # Create a file tuple (filename, content) so OpenAI can detect the format
            file_tuple = (filename, audio_bytes)
            
            response = self.client.audio.transcriptions.create(
                file=file_tuple,
                model=self.transcribe_model
            )

            transcription = response.text
            return transcription

        except Exception as e:
            raise


    def _upload_audio_to_s3(
        self, 
        audio_bytes: bytes, 
        filename: str, 
        user_id: UUID,
        question_id: UUID
    ) -> str:
        """
        Upload interview audio file to S3 with organized folder structure.
        
        Args:
            audio_bytes: Audio file content as bytes
            filename: Original filename with extension
            user_id: UUID of the user (used in folder path)
            question_id: UUID of the interview question (used in folder path)
        
        Returns:
            str: Public URL of the uploaded audio file
        """
        try:
            folder_path = f"interview-practice/{user_id}/{question_id}"
            
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                # Default to audio/mpeg if mime type cannot be determined
                mime_type = "audio/mpeg"
            
            result = self.s3_service.upload_file(
                file=audio_bytes,
                file_name=filename,
                folder_path=folder_path,
                mime_type=mime_type,
                metadata={
                    "user_id": str(user_id),
                    "question_id": str(question_id),
                    "type": "interview_audio"
                }
            )
            
            return result["url"]
            
        except Exception as e:
            raise Exception(f"Failed to upload audio to S3: {str(e)}")

    def _save_interview_practice_session(
        self,
        user_id: UUID,
        question_id: UUID,
        audio_url: str,
        transcript: str,
        analysis_result: dict,
        duration_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save interview practice session record to database.
        
        Args:
            user_id: UUID of the user
            question_id: UUID of the interview question answered
            audio_url: S3 URL of the audio recording
            transcript: Text transcript of the audio
            analysis_result: AI analysis result as dictionary
            duration_seconds: Optional duration of audio in seconds
        
        Returns:
            Dict containing the saved session data
        """
        try:
            session = self.job_application_repository.create_interview_practice_session(
                user_id=user_id,
                question_id=question_id,
                audio_file_url=audio_url,
                transcript=transcript,
                analysis_result=analysis_result,
                duration_seconds=duration_seconds
            )
            
            return {
                "success": True,
                "message": "Interview practice session saved successfully",
                "data": {
                    "session_id": str(session.Id),
                    "audio_url": session.audio_file_url,
                    "created_at": session.created_at.isoformat() if session.created_at else None
                },
                "status_code": 201
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to save interview practice session: {str(e)}",
                "status_code": 500
            }

    def get_user_interview_practice_sessions(self, user_id: UUID, search: str) -> Dict[str, Any]:
        """
        Retrieve all interview practice sessions for a user with optional search.
        Returns lightweight session data (ID, creation date, question info only).
        
        Args:
            user_id: UUID of the user
            search: Optional search term to filter by transcript or question text
        
        Returns:
            dict: Success status, sessions data, and status code
        """
        try:
            sessions = self.job_application_repository.get_user_interview_practice_sessions(
                user_id=user_id,
                search=search
            )
            
            # Transform sessions to only include required fields
            lightweight_sessions = []
            for session in sessions:
                lightweight_sessions.append({
                    "Id": str(session.Id),
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "question": {
                        "Id": str(session.question.Id),
                        "question_text": session.question.question_text,
                        "difficulty": session.question.difficulty,
                        "profession_id": str(session.question.profession_id) if session.question.profession_id else None
                    }
                })
            
            # Return with lightweight sessions
            return {
                "success": True,
                "data": lightweight_sessions,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Failed to retrieve interview practice sessions: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def delete_interview_practice_session(self, session_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Delete an interview practice session by ID.
        
        Args:
            session_id: UUID of the session to delete
            user_id: UUID of the user (for ownership verification)
        
        Returns:
            Dict containing success status and message
        """
        try:
            deleted = self.job_application_repository.delete_interview_practice_session(session_id, user_id)
            
            if not deleted:
                return {
                    "success": False,
                    "status_code": 404,
                    "message": "Interview practice session not found or you don't have permission to delete it"
                }
            
            self.logger.info(f"Interview practice session {session_id} deleted successfully for user {user_id}")
            return {
                "success": True,
                "message": "Interview practice session deleted successfully"
            }
        except Exception as e:
            self.logger.error(f"Error deleting interview practice session: {str(e)}")
            return {
                "success": False,
                "status_code": 500,
                "message": f"Failed to delete interview practice session: {str(e)}"
            }
    
    def get_interview_practice_session_by_id(self, session_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Retrieve a single interview practice session by ID with full details.
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the user (for ownership verification)
        
        Returns:
            dict: Success status, session data with full details, and status code
        """
        try:
            session = self.job_application_repository.get_interview_practice_session_by_id(
                session_id=session_id,
                user_id=user_id
            )
            
            if not session:
                return {
                    "success": False,
                    "message": "Session not found",
                    "status_code": 404
                }
            
            return {
                "success": True,
                "data": session,
                "status_code": 200
            }
        except Exception as e:
            self.logger.error(f"Failed to retrieve interview practice session: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
