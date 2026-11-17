from repositories.user_repository import UserRepository
from schemas import UserCreate, UserUpdate, UserResponse, LearnerProfileBase, LearnerProfileResponse, AgeGroupResponse
from typing import List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository):
        self._repository = user_repository
    
    def get_all_users(self, limit: int = 10, offset: int = 0, search: str | None = None):
        """
        Get all users from the repository with pagination and search.
        
        Args:
            limit: Maximum number of users to return (default: 10)
            offset: Number of users to skip for pagination (default: 0)
            search: Optional search query to filter users
        
        Returns:
            dict: Response dictionary with paginated user list and metadata
        """
        try:
            result = self._repository.get_all(limit=limit, offset=offset, search=search)
            return {
                "success": True, 
                "data": {
                    "users": [UserResponse.model_validate(user) for user in result['users']],
                    "total": result['total'],
                    "limit": result['limit'],
                    "offset": result['offset'],
                    "has_next": result['has_next'],
                    "has_prev": result['has_prev']
                }, 
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        """
        Get a user by their ID.
        
        Args:
            user_id: UUID of the user to retrieve
        
        Returns:
            dict: Response dictionary with user data or error message
        """
        try:
            user = self._repository.get_by_id(user_id)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            return {"success": True, "data": UserResponse.model_validate(user), "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user in the repository.
        
        Args:
            user_data: User creation data including email and profile information
        
        Returns:
            dict: Response dictionary with created user data
        """
        try:
            existing_user = self._repository.get_by_email(user_data.email)
            if existing_user:
                return {"success": False, "message": "Email already registered", "status_code": 400}

            user = self._repository.create(user_data)
            return {"success": True, "data": UserResponse.model_validate(user), "status_code": 201}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def update_learner_profile(self, user_id: UUID, profile_data: LearnerProfileBase):
        """
        Update the learner profile for a user.
        
        Args:
            user_id: UUID of the user
            profile_data: Learner profile data including bio, country, industry, etc.
        
        Returns:
            dict: Response dictionary with updated profile data
        """
        try:
            profile = self._repository.update_learner_profile(user_id, profile_data)
            if not profile:
                return {"success": False, "message": "Profile not found", "status_code": 404}
            return {"success": True, "data": LearnerProfileResponse.model_validate(profile), "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """
        Update a user in the repository.
        
        Args:
            user_id: ID of the user to update
            user_data: Updated user data fields
        
        Returns:
            dict: Response dictionary with updated user data
        """
        try:
            if user_data.email:
                existing_user = self._repository.get_by_email(user_data.email)
                if existing_user and existing_user.id != user_id:
                    return {"success": False, "message": "Email already registered", "status_code": 400}

            user = self._repository.update(user_id, user_data)
            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            return {
                "success": True,
                "data": UserResponse.model_validate(user),
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user from the system.
        
        Args:
            user_id: ID of the user to delete
        
        Returns:
            dict: Response dictionary with deletion status
        """
        try:
            result = self._repository.delete(user_id)
            if not result:
                return {"success": False, "message": "User not found", "status_code": 404}
            return {"success": True, "message": "User deleted successfully", "status_code": 200}
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }

    def change_user_status(self, user_id: UUID, status: str) -> Optional[UserResponse]:
        """
        Change the status of a user (activate or deactivate).
        
        Args:
            user_id: UUID of the user
            status: Status action - 'activate' or 'deactivate'
        
        Returns:
            dict: Response dictionary with updated user data
        """
        try:
            is_active = True if status.lower() == "activate" else False if status.lower() == "deactivate" else None
            
            user = self._repository.change_user_status(user_id, is_active)

            if not user:
                return {"success": False, "message": "User not found", "status_code": 404}
            return {
                "success": True, 
                "data": UserResponse.model_validate(user),
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def fetch_age_groups(self) -> List[AgeGroupResponse]:
        """
        Fetch all age groups from the database.
        
        Returns:
            dict: Response dictionary with list of age groups
        """
        try:
            age_groups = self._repository.fetch_age_groups()

            return {
                "success": True, 
                "data": [AgeGroupResponse.model_validate(ag) for ag in age_groups], 
                "status_code": 200
            }

        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_user_enrollments(self, user_id: UUID):
        """
        Get all courses a user is enrolled in.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Response dictionary with list of course enrollments
        """
        try:
            enrollments = self._repository.get_user_enrollments(user_id)
            if not enrollments:
                return {"success": False, "message": "No enrollments found for the user", "status_code": 404}
            return {
                "success": True,
                "data": enrollments,
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
        
    def get_user_public_profile(self, user_id: UUID):
        """
        Get public profile of a user including enrollments and certificates.
        
        Args:
            user_id: UUID of the user
        
        Returns:
            dict: Response dictionary with public profile data
        """
        try:
            profile = self._repository.fetch_public_profile(user_id)
            if not profile:
                return {"success": False, "message": "User not found", "status_code": 404}
            profile_data = {
                "Id": profile.Id,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "full_name": f"{profile.first_name} {profile.last_name}",
                "email": profile.email,
                "user_type": profile.user_type,
                "account_verified": profile.account_verified,
                "created_at": profile.created_at,
                "learner_profile": {
                    "bio": profile.learner_profile.bio if profile.learner_profile else None,
                    "country": profile.learner_profile.country if profile.learner_profile else None,
                    "profession": {
                        "Id": profile.learner_profile.profession.Id,
                        "name": profile.learner_profile.profession.name
                    } if profile.learner_profile and profile.learner_profile.profession else None,
                    "industry": profile.learner_profile.industry if profile.learner_profile else None,
                    "experience": profile.learner_profile.experience if profile.learner_profile else None
                },
                "enrollments": [
                    {
                        "Id": enrollment.Id,
                        "course_id": enrollment.course_id,
                        "course_title": enrollment.enrolled_course.title if enrollment.enrolled_course else None,
                        "purchased_at": enrollment.purchased_at,
                        "purchase_completed": enrollment.purchase_completed,
                        "certificate": {
                            "Id": enrollment.certificate.Id,
                            "certificate_url": enrollment.certificate.certificate_url,
                            "certificate_number": enrollment.certificate.certificate_number,
                            "issued_at": enrollment.certificate.issued_at
                        } if enrollment.certificate else None
                    } for enrollment in profile.enrollments
                ] if profile.enrollments else []
            }
            return {
                "success": True,
                "data": profile_data,
                "status_code": 200
            }
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}", exc_info=True)
            return {
                "success": False, 
                "message": "An error occurred while processing your request",
                "status_code": 500
            }
