from fastapi import APIRouter, Depends, HTTPException, status, Query
from services import ProfessionService
from middleware.auth_middleware import get_current_active_user, require_admin
from models import UserModel
from schemas import CreateProfessionRequest, UpdateProfessionRequest, ProfessionResponse
from typing import Annotated
from dependencies import get_profession_service
from utils import API_PREFIX, get_logger
from uuid import UUID

class ProfessionController:
    profession_service_dependency = Annotated[ProfessionService, Depends(get_profession_service)]
    current_active_user = Annotated[UserModel, Depends(get_current_active_user)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/professions", tags=["professions"])
        self.logger = get_logger("app.controllers.profession")
        self._setup_routes()

    def _setup_routes(self):
        # Public/User routes
        self.router.add_api_route("", self.get_all_professions, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{profession_id}", self.get_profession_by_id, methods=["GET"], status_code=status.HTTP_200_OK)
        
        # Admin routes
        self.router.add_api_route("", self.create_profession, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{profession_id}", self.update_profession, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{profession_id}", self.delete_profession, methods=["DELETE"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        
        self.logger.info("ProfessionController routes have been set up")

    def get_all_professions(
        self,
        profession_service: profession_service_dependency,
        include_inactive: bool = Query(False, description="Include inactive professions")
    ):
        """Get all professions"""
        result = profession_service.get_all_professions(include_inactive=include_inactive)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_profession_by_id(
        self,
        profession_id: str,
        profession_service: profession_service_dependency,
    ):
        """Get a profession by ID"""
        try:
            profession_uuid = UUID(profession_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid profession ID format")
        
        result = profession_service.get_profession_by_id(profession_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def create_profession(
        self,
        profession_service: profession_service_dependency,
        profession_data: CreateProfessionRequest
    ):
        """Create a new profession (Admin only)"""
        result = profession_service.create_profession(
            name=profession_data.name,
            description=profession_data.description
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def update_profession(
        self,
        profession_id: str,
        profession_service: profession_service_dependency,
        profession_data: UpdateProfessionRequest
    ):
        """Update a profession (Admin only)"""
        try:
            profession_uuid = UUID(profession_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid profession ID format")
        
        result = profession_service.update_profession(
            profession_id=profession_uuid,
            name=profession_data.name,
            description=profession_data.description,
            is_active=profession_data.is_active
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def delete_profession(
        self,
        profession_id: str,
        profession_service: profession_service_dependency
    ):
        """Delete a profession (Admin only) - Soft delete"""
        try:
            profession_uuid = UUID(profession_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid profession ID format")
        
        result = profession_service.delete_profession(profession_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
