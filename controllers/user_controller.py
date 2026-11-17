from fastapi import APIRouter, HTTPException, Depends, status
from services import UserService
from schemas import UserCreate, UserUpdate, UserResponse, LearnerProfileBase, LearnerProfileResponse, UpdateUserStatus, AgeGroupResponse, PaginatedUserResponse
from dependencies import get_user_service
from middleware.auth_middleware import get_current_active_user, require_admin
from models import UserModel
from typing import List, Annotated
from utils.logger import get_logger
from utils.constants import API_PREFIX
from uuid import UUID

class UserController:
    user_service_dependency = Annotated[UserService, Depends(get_user_service)]
    current_active_user_dependency = Annotated[UserModel, Depends(get_current_active_user)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/users", tags=["users"])
        self.logger = get_logger("app.controllers.user")
        self._setup_routes()
    
    def _setup_routes(self):
        self.router.add_api_route("/", self.create_user, methods=["POST"], response_model=UserResponse, dependencies=[Depends(require_admin)], status_code=status.HTTP_201_CREATED)
        self.router.add_api_route("/", self.get_users, methods=["GET"], response_model=PaginatedUserResponse, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/me", self.get_current_user_profile, methods=["GET"], response_model=UserResponse)
        self.router.add_api_route("/me/profile", self.update_my_learner_profile, methods=["PUT"], response_model=LearnerProfileResponse, status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{user_id}", self.get_user, methods=["GET"], response_model=UserResponse, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}/status", self.change_user_status, methods=["PATCH"], response_model=UserResponse, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}/profile", self.update_learner_profile, methods=["PUT"], response_model=LearnerProfileResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}", self.update_user, methods=["PUT"], response_model=UserResponse, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}", self.delete_user, methods=["DELETE"], dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{user_id}/enrollments", self.get_user_enrollments, methods=["GET"])
        self.router.add_api_route("/{user_id}/profile/public", self.get_public_profile, methods=["GET"])
        self.router.add_api_route("/profile/age-groups", self.fetch_age_groups, methods=["GET"], response_model=List[AgeGroupResponse])
        self.logger.info("UserController routes have been set up.")
    
    def get_users(
        self, 
        user_service: user_service_dependency,
        search: str | None = None,
        limit: int = 10,
        offset: int = 0
    ):
        """Get all users with pagination and search (Admin only)"""
        result = user_service.get_all_users(limit=limit, offset=offset, search=search)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")
    
    def create_user(
        self,
        user_data: UserCreate,
        user_service: user_service_dependency
    ) -> UserResponse:
        
        """Create a new user (Public endpoint)"""

        result = user_service.create_user(user_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

    def get_current_user_profile(
        self,
        user_service: user_service_dependency,
        current_user: current_active_user_dependency
    ) -> UserResponse:
        
        """Get current user's profile"""

        result = user_service.get_user(current_user.Id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

    def update_my_learner_profile(
        self,
        profile_data: LearnerProfileBase,
        user_service: user_service_dependency,
        current_user: current_active_user_dependency
    ) -> LearnerProfileResponse:
        
        """Update current user's learner profile"""

        if current_user.user_type != "Learner":
            raise HTTPException(status_code=403, detail="Only learners can update learner profiles")
        
        result = user_service.update_learner_profile(current_user.Id, profile_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

    def update_learner_profile(
        self,
        user_id: UUID,
        profile_data: LearnerProfileBase,
        user_service: user_service_dependency
    ) -> LearnerProfileResponse:
        
        """Update any user's learner profile (Admin only)"""

        result = user_service.update_learner_profile(user_id, profile_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

    def get_user(
        self,
        user_id: UUID,
        user_service: user_service_dependency
    ) -> UserResponse:
        
        """Get specific user by ID (Admin only)"""

        result = user_service.get_user(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")
    
    def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        user_service: user_service_dependency
    ) -> UserResponse:
        
        """Update specific user (Admin only)"""

        result = user_service.update_user(user_id, user_data)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")
    
    def delete_user(
        self,
        user_id: UUID,
        user_service: user_service_dependency
    ):
        
        """Delete specific user (Admin only)"""

        result = user_service.delete_user(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return {"message": result.get("message")}

    def change_user_status(
        self,
        user_id: UUID,
        status: UpdateUserStatus,
        user_service: user_service_dependency,
        current_user: current_active_user_dependency
    ) -> UserResponse:
        
        """
            Change the status of a user (Admin only)

            :param user_id: UUID - The ID of the user whose status is to be changed
            :param status: UpdateUserStatus - The new status to be assigned to the user either 'activate' or 'deactivate'

            :returns: Updated UserResponse object
            :raises HTTPException: If the user is not found or if an admin attempts to change their own status
        """
        if current_user.Id == user_id:
            raise HTTPException(status_code=400, detail="Admins cannot change their own status")

        result = user_service.change_user_status(user_id, status.status)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")
    
    def fetch_age_groups(
        self,
        user_service: user_service_dependency
    ) -> List[AgeGroupResponse]:
        
        """Fetch all age groups"""

        result = user_service.fetch_age_groups()
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")
    
    def get_user_enrollments(
        self,
        user_id: UUID,
        user_service: user_service_dependency
    ):
        
        """Get user enrollments by user ID (Admin only)"""

        result = user_service.get_user_enrollments(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

    def get_public_profile(self, user_id: UUID, user_service: user_service_dependency) -> dict:
        """Get public profile of a user by ID"""
        result = user_service.get_user_public_profile(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result.get("data")

class HealthController:
    def __init__(self):
        self.router = APIRouter(prefix="/health", tags=["health"])
        self._setup_routes()
    
    def _setup_routes(self):
        self.router.add_api_route("/", self.health_check, methods=["GET"])
    
    def health_check(self):
        return {"status": "healthy", "message": "API is running"}
