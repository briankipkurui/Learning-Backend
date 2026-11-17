from repositories import JobApplicationRepository
from schemas import (
     ResumeCreate,  JobApplicationCreate, 
    JobApplicationBase, JobApplicationActivityCreate
)
import logging

logger = logging.getLogger(__name__)

class JobApplicationService:
    def __init__(self, job_application_repository: JobApplicationRepository):
        """
        Initialize job application service with repository dependency.
        
        Args:
            job_application_repository: Repository for job application data access
        """
        self._repository = job_application_repository


    def create_job_application(self, job_application_data: JobApplicationCreate):
        """
        Create a new job application.
        
        Args:
            job_application_data: Job application creation data
        
        Returns:
            dict: Success status, created application, and status code (201 on success)
        """
        try:
            application = self._repository.create_job_application(job_application_data)
            return {"success": True, "data": application, "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_job_applications_by_user(self, user_id):
        """
        Retrieve all job applications for a specific user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Success status, list of applications, and status code
        """
        try:
            applications = self._repository.get_job_applications_by_user(user_id)
            return {"success": True, "data": applications, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        

    def get_job_application_by_id(self, application_id):
        """
        Retrieve a specific job application by its ID.
        
        Args:
            application_id: UUID of the job application
        
        Returns:
            dict: Success status, application data, and status code (404 if not found)
        """
        try:
            application = self._repository.get_job_application_by_id(application_id)
            if not application:
                return {"success": False, "message": "Job application not found", "status_code": 404}

            return {"success": True, "data": application, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def update_job_application(self, application_id, update_data: JobApplicationBase):
        """
        Update a specific job application.
        
        Args:
            application_id: UUID of the job application
            update_data: Updated application data
        
        Returns:
            dict: Success status, updated application, and status code (404 if not found)
        """
        try:
            updated_application = self._repository.update_job_application(application_id, update_data)
            if not updated_application:
                return {"success": False, "message": "Job application not found", "status_code": 404}
            return {"success": True, "data": updated_application, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def delete_job_application(self, application_id):
        """
        Delete a specific job application by its ID.
        
        Args:
            application_id: UUID of the job application
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            deleted = self._repository.delete_job_application(application_id)
            if not deleted:
                return {"success": False, "message": "Job application not found", "status_code": 404}
            return {"success": True, "message": "Job application deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def create_job_application_activity(self, activity_data: JobApplicationActivityCreate):
        """
        Create a new job application activity (e.g., interview, offer).
        
        Args:
            activity_data: Activity creation data
        
        Returns:
            dict: Success status, created activity, and status code (201 on success)
        """
        try:
            activity = self._repository.create_job_application_activity(activity_data)

            return {"success": True, "data": activity, "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def delete_job_application_activity(self, activity_id):
        """
        Delete a specific job application activity by its ID.
        
        Args:
            activity_id: UUID of the activity
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            deleted = self._repository.delete_job_application_activity(activity_id)
            if not deleted:
                return {"success": False, "message": "Job application activity not found", "status_code": 404}
            return {"success": True, "message": "Job application activity deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def fetch_all_activity_types(self):
        """
        Fetch all available job application activity types.
        
        Returns:
            dict: Success status, list of activity types, and status code
        """
        try:
            activity_types = self._repository.fetch_all_activity_types()
            return {
                "success": True,
                "data": activity_types,
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def create_resume(self, resume_data: ResumeCreate):
        """
        Create a new resume record.
        
        Args:
            resume_data: Resume creation data
        
        Returns:
            dict: Success status, created resume, and status code (201 on success)
        """
        try:
            resume = self._repository.create_resume(resume_data)
            return {"success": True, "data": resume, "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_resumes_by_user(self, user_id):
        """
        Retrieve all resumes for a specific user.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Success status, list of resumes, and status code
        """
        try:
            resumes = self._repository.get_resumes_by_user(user_id)

            return {"success": True, "data": resumes, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_resume_by_id(self, resume_id):
        """
        Retrieve a specific resume by its ID.
        
        Args:
            resume_id: UUID of the resume
        
        Returns:
            dict: Success status, resume data, and status code (404 if not found)
        """
        try:
            resume = self._repository.get_resume_by_id(resume_id)
            if not resume:
                return {"success": False, "message": "Resume not found", "status_code": 404}
            return {"success": True, "data": resume, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def update_resume_comments(self, resume_id, comments):
        """
        Update comments for a specific resume.
        
        Args:
            resume_id: UUID of the resume
            comments: New comments text
        
        Returns:
            dict: Success status, updated resume, and status code (404 if not found)
        """
        try:
            updated_resume = self._repository.update_resume_comments(resume_id, comments)
            if not updated_resume:
                return {"success": False, "message": "Resume not found", "status_code": 404}
            return {"success": True, "data": updated_resume, "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def delete_resume(self, resume_id):
        """
        Delete a specific resume by its ID.
        
        Args:
            resume_id: UUID of the resume
        
        Returns:
            dict: Success status, message, and status code (404 if not found)
        """
        try:
            deleted = self._repository.delete_resume(resume_id)
            if not deleted:
                return {"success": False, "message": "Resume not found", "status_code": 404}
            return {"success": True, "message": "Resume deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }