from models import ResumeModel, JobApplicationModel, JobApplicationActivityModel, ActivityTypeModel, CVAnalysisModel, InterviewQuestionModel, InterviewPracticeSessionModel, LearnerProfileModel
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from schemas import ResumeCreate, JobApplicationCreate, JobApplicationBase, JobApplicationActivityCreate
from typing import List, Optional

class JobApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def _simple_single_job_fetch(self, application_id: UUID) -> JobApplicationModel | None:
        """
        Private helper to fetch a job application by ID without eager loading.
        
        Args:
            application_id: UUID of the job application
        
        Returns:
            JobApplicationModel: Job application or None if not found
        """
        return self.db.query(JobApplicationModel).filter(JobApplicationModel.Id == application_id).first()

    def create_job_application(self, job_application_data: JobApplicationCreate) -> JobApplicationModel:
        """
        Create a new job application.
        
        Args:
            job_application_data: Job application creation data
        
        Returns:
            JobApplicationModel: The created job application
        """
        new_application_dict = job_application_data.model_dump(exclude_unset=True)

        new_application = JobApplicationModel(**new_application_dict)
        self.db.add(new_application)
        self.db.commit()
        self.db.refresh(new_application)
        return new_application

    def get_job_applications_by_user(self, user_id: UUID) -> list[JobApplicationModel]:
        """
        Get all job applications for a user, ordered by creation date (newest first).
        
        Args:
            user_id: UUID of the user
        
        Returns:
            list[JobApplicationModel]: List of user's job applications
        """
        return self.db.query(JobApplicationModel) \
            .filter(JobApplicationModel.user_id == user_id) \
            .order_by(JobApplicationModel.created_at.desc()) \
            .all()
    
    def get_job_application_by_id(self, application_id: UUID) -> JobApplicationModel | None:
        """
        Get a job application by ID with activities and activity types eager-loaded.
        
        Args:
            application_id: UUID of the job application
        
        Returns:
            JobApplicationModel: Job application with activities, or None if not found
        """
        application = self.db.query(JobApplicationModel) \
            .options(
                joinedload(JobApplicationModel.activities) \
                .joinedload(JobApplicationActivityModel.activity_type)
            ) \
            .filter(JobApplicationModel.Id == application_id) \
            .first()
        return application
    
    def update_job_application(self, application_id: UUID, update_data: JobApplicationBase) -> JobApplicationModel | None:
        """
        Update an existing job application.
        
        Args:
            application_id: UUID of the job application
            update_data: Updated job application data
        
        Returns:
            JobApplicationModel: Updated job application, or None if not found
        """
        application = self._simple_single_job_fetch(application_id)

        if not application:
            return None
        
        for key, value in update_data.items():
            setattr(application, key, value)
        
        self.db.commit()
        self.db.refresh(application)
        return application
    
    def delete_job_application(self, application_id: UUID) -> bool:
        """
        Hard delete a job application from the database.
        
        Args:
            application_id: UUID of the job application
        
        Returns:
            bool: True if deleted, False if not found
        """
        application = self._simple_single_job_fetch(application_id)
        if not application:
            return False
        
        self.db.delete(application)
        self.db.commit()
        return True
    

    def create_job_application_activity(self, activity_data: JobApplicationActivityCreate) -> JobApplicationActivityModel:
        """
        Create a new job application activity (e.g., interview, offer, rejection).
        
        Args:
            activity_data: Activity creation data
        
        Returns:
            JobApplicationActivityModel: The created activity
        """
        new_activity_dict = activity_data.model_dump(exclude_unset=True)

        new_activity = JobApplicationActivityModel(**new_activity_dict)
        self.db.add(new_activity)
        self.db.commit()
        self.db.refresh(new_activity)
        return new_activity
    

    def delete_job_application_activity(self, activity_id: UUID) -> bool:
        """
        Hard delete a job application activity.
        
        Args:
            activity_id: UUID of the activity
        
        Returns:
            bool: True if deleted, False if not found
        """
        activity = self.db.query(JobApplicationActivityModel) \
            .filter(JobApplicationActivityModel.Id == activity_id) \
            .first()
        
        if not activity:
            return False
        
        self.db.delete(activity)
        self.db.commit()
        return True
    
    def fetch_all_activity_types(self) -> list[ActivityTypeModel]:
        """
        Get all available job application activity types, sorted by name.
        
        Returns:
            list[ActivityTypeModel]: List of all activity types
        """
        activity_types =  self.db.query(ActivityTypeModel).order_by(ActivityTypeModel.name.asc()).all()
        return activity_types


    def create_resume(self, resume_data: ResumeCreate) -> ResumeModel:
        """
        Create a new resume record.
        
        Args:
            resume_data: Resume creation data
        
        Returns:
            ResumeModel: The created resume
        """
        new_resume_dict = resume_data.model_dump(exclude_unset=True)

        new_resume = ResumeModel(**new_resume_dict)
        self.db.add(new_resume)
        self.db.commit()
        self.db.refresh(new_resume)
        return new_resume

    def get_resumes_by_user(self, user_id: UUID) -> list[ResumeModel]:
        """
        Get all resumes for a user, ordered by creation date (newest first).
        
        Args:
            user_id: UUID of the user
        
        Returns:
            list[ResumeModel]: List of user's resumes
        """
        return self.db.query(ResumeModel) \
            .filter(ResumeModel.user_id == user_id) \
            .order_by(ResumeModel.created_at.desc()) \
            .all()

    def get_resume_by_id(self, resume_id: UUID) -> ResumeModel | None:
        """
        Get a resume by ID.
        
        Args:
            resume_id: UUID of the resume
        
        Returns:
            ResumeModel: Resume or None if not found
        """
        resume = self.db.query(ResumeModel).filter(ResumeModel.Id == resume_id).first()
        return resume
    
    def update_resume_comments(self, resume_id: UUID, comments: str) -> ResumeModel | None:
        """
        Update the comments field of a resume.
        
        Args:
            resume_id: UUID of the resume
            comments: New comments text
        
        Returns:
            ResumeModel: Updated resume, or None if not found
        """
        resume = self.get_resume_by_id(resume_id)
        if not resume:
            return None
        
        resume.comments = comments
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def delete_resume(self, resume_id: UUID) -> bool:
        """
        Hard delete a resume from the database.
        
        Args:
            resume_id: UUID of the resume
        
        Returns:
            bool: True if deleted, False if not found
        """
        resume = self.get_resume_by_id(resume_id)
        if not resume:
            return False
        
        self.db.delete(resume)
        self.db.commit()
        return True
    
    def create_cv_analysis(
        self, 
        user_id: UUID, 
        job_title: str, 
        analysis_result: dict,
        new_resume_url: str = None,
        old_resume_url: str = None,
        jd_url: str = None,
        resume_text: str = None,
        jd_text: str = None
    ) -> CVAnalysisModel:
        """
        Create a new CV analysis record with results and file URLs.
        
        Args:
            user_id: UUID of the user
            job_title: Job title from the analysis
            analysis_result: Analysis results from AI service
            new_resume_url: Optional URL of the improved resume
            old_resume_url: Optional URL of the original resume
            jd_url: Optional URL of the job description
            resume_text: Optional extracted resume text
            jd_text: Optional extracted job description text
        
        Returns:
            CVAnalysisModel: The created CV analysis record
        """
        new_analysis = CVAnalysisModel(
            user_id=user_id,
            job_title=job_title,
            analysis_result=analysis_result,
            new_resume_url=new_resume_url,
            old_resume_url=old_resume_url,
            jd_url=jd_url,
            resume_text=resume_text,
            jd_text=jd_text
        )
        self.db.add(new_analysis)
        self.db.commit()
        self.db.refresh(new_analysis)
        return new_analysis
    
    def fetch_user_resume_analyses(self, user_id: UUID) -> List[CVAnalysisModel]:
        """
        Get all CV analyses for a user, ordered by creation date (newest first).
        
        Args:
            user_id: UUID of the user
        
        Returns:
            List[CVAnalysisModel]: List of user's CV analyses
        """
        return self.db.query(CVAnalysisModel)\
            .filter_by(user_id=user_id)\
            .order_by(CVAnalysisModel.created_at.desc())\
            .all()
    
    def get_cv_analysis_by_id(self, analysis_id: UUID) -> CVAnalysisModel | None:
        """
        Get a CV analysis by ID.
        
        Args:
            analysis_id: UUID of the CV analysis
        
        Returns:
            CVAnalysisModel: CV analysis or None if not found
        """
        analysis = self.db.query(CVAnalysisModel).filter(CVAnalysisModel.Id == analysis_id).first()
        if not analysis:
            return None
        return analysis
    
    def delete_cv_analysis(self, analysis_id: UUID, user_id: UUID) -> bool:
        """
        Hard delete a CV analysis record (only if owned by user).
        
        Args:
            analysis_id: UUID of the CV analysis
            user_id: UUID of the user (for ownership verification)
        
        Returns:
            bool: True if deleted, False if not found or not owned by user
        """
        analysis = self.db.query(CVAnalysisModel)\
            .filter(
                CVAnalysisModel.Id == analysis_id, 
                CVAnalysisModel.user_id == user_id
            )\
            .first()
        if not analysis:
            return False
        
        self.db.delete(analysis)
        self.db.commit()
        return True
    
    # ===== Interview Question Management =====
    
    def get_user_profession_id(self, user_id: UUID) -> Optional[UUID]:
        """
        Get the profession_id from user's learner profile.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            profession_id if found, None otherwise
        """
        learner_profile = self.db.query(LearnerProfileModel)\
            .filter(LearnerProfileModel.user_id == user_id)\
            .first()
        
        return learner_profile.profession_id if learner_profile else None
    
    def get_answered_question_ids(self, user_id: UUID) -> List[UUID]:
        """
        Get list of question IDs the user has already answered.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of question IDs
        """
        sessions = self.db.query(InterviewPracticeSessionModel.question_id)\
            .filter(InterviewPracticeSessionModel.user_id == user_id)\
            .all()
        
        return [session.question_id for session in sessions]
    
    def get_next_interview_question(
        self,
        user_id: UUID,
        profession_id: Optional[UUID] = None
    ) -> Optional[InterviewQuestionModel]:
        """
        Get the next interview question for a user based on their progress.
        
        Prioritizes:
        1. Questions from user's profession (if provided)
        2. Unanswered questions
        3. Easiest difficulty first
        
        Args:
            user_id: UUID of the user
            profession_id: Optional profession_id to filter by
            
        Returns:
            InterviewQuestionModel or None
        """
        # Get questions already answered by user
        answered_ids = self.get_answered_question_ids(user_id)
        
        # Build base query
        query = self.db.query(InterviewQuestionModel)
        
        # Filter by profession if provided
        if profession_id:
            query = query.filter(InterviewQuestionModel.profession_id == profession_id)
        
        # First try to get unanswered questions
        unanswered_query = query.filter(~InterviewQuestionModel.Id.in_(answered_ids)) if answered_ids else query
        
        # Order by difficulty (lower number = easier)
        unanswered_question = unanswered_query\
            .order_by(
                InterviewQuestionModel.difficulty.asc().nullslast(),
                func.random()
            )\
            .first()
        
        # If we found an unanswered question, return it
        if unanswered_question:
            return unanswered_question
        
        # If all questions answered, start over with easiest first
        return query\
            .order_by(
                InterviewQuestionModel.difficulty.asc().nullslast(),
                func.random()
            )\
            .first()
    
    # ======= Admin CRUD Operations for Interview Questions =======
    
    def create_interview_question(self, question_data: dict) -> InterviewQuestionModel:
        """
        Create a new interview question (admin only).
        
        Args:
            question_data: Dictionary containing question fields
        
        Returns:
            InterviewQuestionModel: The created interview question
        """
        new_question = InterviewQuestionModel(**question_data)
        self.db.add(new_question)
        self.db.commit()
        self.db.refresh(new_question)
        return new_question
    
    def update_interview_question(self, question_id: UUID, question_data: dict) -> InterviewQuestionModel | None:
        """
        Update an existing interview question (admin only).
        
        Args:
            question_id: UUID of the interview question
            question_data: Dictionary of fields to update
        
        Returns:
            InterviewQuestionModel: Updated question, or None if not found
        """
        question = self.db.query(InterviewQuestionModel)\
            .filter(InterviewQuestionModel.Id == question_id)\
            .first()
        
        if not question:
            return None
        
        # Update only provided fields
        for key, value in question_data.items():
            if value is not None:  # Only update if value is provided
                setattr(question, key, value)
        
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def get_all_interview_questions(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        profession_id: Optional[UUID] = None
    ) -> dict:
        """
        Get paginated list of all interview questions (admin only).
        
        Args:
            limit: Maximum number of questions to return (default 20)
            offset: Number of questions to skip for pagination (default 0)
            profession_id: Optional profession filter
        
        Returns:
            dict: Contains questions list, total count, and pagination metadata
        """
        # Base query
        query = self.db.query(InterviewQuestionModel)
        
        # Filter by profession if provided
        if profession_id:
            query = query.filter(InterviewQuestionModel.profession_id == profession_id)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        questions = query\
            .order_by(InterviewQuestionModel.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return {
            "questions": questions,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": (offset + limit) < total,
            "has_prev": offset > 0
        }
    
    def get_interview_question_by_id(self, question_id: UUID) -> InterviewQuestionModel | None:
        """
        Get a single interview question by ID (admin only).
        
        Args:
            question_id: UUID of the interview question
        
        Returns:
            InterviewQuestionModel: Interview question or None if not found
        """
        return self.db.query(InterviewQuestionModel)\
            .filter(InterviewQuestionModel.Id == question_id)\
            .first()
    
    def delete_interview_question(self, question_id: UUID) -> bool:
        """
        Delete an interview question by ID (admin only).
        
        Args:
            question_id: UUID of the interview question
        
        Returns:
            bool: True if deleted, False if not found
        """
        question = self.db.query(InterviewQuestionModel)\
            .filter(InterviewQuestionModel.Id == question_id)\
            .first()
        
        if not question:
            return False
        
        self.db.delete(question)
        self.db.commit()
        return True

    def create_interview_practice_session(
        self,
        user_id: UUID,
        question_id: UUID,
        audio_file_url: str,
        transcript: str,
        analysis_result: dict,
        duration_seconds: Optional[int] = None
    ) -> InterviewPracticeSessionModel:
        """
        Create a new interview practice session record.
        
        Args:
            user_id: UUID of the user
            question_id: UUID of the interview question
            audio_file_url: URL of the audio file in S3
            transcript: Text transcript of the audio
            analysis_result: Analysis result from OpenAI (JSON)
            duration_seconds: Duration of the audio in seconds (optional)
            
        Returns:
            InterviewPracticeSessionModel: The created session record
        """
        session = InterviewPracticeSessionModel(
            user_id=user_id,
            question_id=question_id,
            audio_file_url=audio_file_url,
            transcript=transcript,
            analysis_result=analysis_result,
            duration_seconds=duration_seconds
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_user_interview_practice_sessions(
        self,
        user_id: UUID,
        search: Optional[str]
    ) -> list[InterviewPracticeSessionModel]:
        """
        Get all interview practice sessions for a user with optional search.
        
        Args:
            user_id: UUID of the user
            search: Optional search term to filter by transcript or question text
        
        Returns:
            list[InterviewPracticeSessionModel]: List of user's sessions
        """
        # Base query - only load question, not other relationships
        query = self.db.query(InterviewPracticeSessionModel)\
            .options(joinedload(InterviewPracticeSessionModel.question)\
                .load_only(
                    InterviewQuestionModel.question_text,
                    InterviewQuestionModel.difficulty
                )
            )\
            .filter(InterviewPracticeSessionModel.user_id == user_id)
        
        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            query = query.join(InterviewQuestionModel)\
                .filter(
                    (InterviewQuestionModel.question_text.ilike(search_pattern))
                )
        
        # Get all results ordered by most recent first
        return query\
            .order_by(InterviewPracticeSessionModel.created_at.desc())\
            .all()
    
    def get_interview_practice_session_by_id(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> Optional[InterviewPracticeSessionModel]:
        """
        Get a single interview practice session by ID (only if owned by user).
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the user (for ownership verification)
        
        Returns:
            InterviewPracticeSessionModel or None if not found or not owned by user
        """
        return self.db.query(InterviewPracticeSessionModel)\
            .options(joinedload(InterviewPracticeSessionModel.question))\
            .filter(
                InterviewPracticeSessionModel.Id == session_id,
                InterviewPracticeSessionModel.user_id == user_id
            )\
            .first()
    
    def delete_interview_practice_session(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete an interview practice session by ID (only if owned by user).
        
        Args:
            session_id: UUID of the session
            user_id: UUID of the user (for ownership verification)
        
        Returns:
            bool: True if deleted, False if not found or not owned by user
        """
        session = self.db.query(InterviewPracticeSessionModel)\
            .filter(
                InterviewPracticeSessionModel.Id == session_id,
                InterviewPracticeSessionModel.user_id == user_id
            )\
            .first()
        
        if not session:
            return False
        
        self.db.delete(session)
        self.db.commit()
        return True

