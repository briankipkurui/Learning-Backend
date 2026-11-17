from fastapi import APIRouter, Depends, HTTPException, status, Query
from services.policy_service import PolicyService
from middleware.auth_middleware import get_current_active_user, require_admin
from models import UserModel
from schemas.policy import (
    CreatePolicyTypeRequest, UpdatePolicyTypeRequest, PolicyTypeResponse,
    CreatePolicyRequest, UpdatePolicyRequest, PolicyResponse
)
from typing import Annotated, Optional
from dependencies import get_policy_service
from utils import API_PREFIX, get_logger
from uuid import UUID

class PolicyController:
    policy_service_dependency = Annotated[PolicyService, Depends(get_policy_service)]
    current_active_user = Annotated[UserModel, Depends(get_current_active_user)]

    def __init__(self):
        self.router = APIRouter(prefix=f"{API_PREFIX}/policies", tags=["policies"])
        self.logger = get_logger("app.controllers.policy")
        self._setup_routes()

    def _setup_routes(self):
        # Policy Type routes (Admin only)
        self.router.add_api_route("/types", self.get_all_policy_types, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/types/{policy_type_id}", self.get_policy_type_by_id, methods=["GET"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/types", self.create_policy_type, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/types/{policy_type_id}", self.update_policy_type, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/types/{policy_type_id}", self.delete_policy_type, methods=["DELETE"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        
        # Policy routes
        self.router.add_api_route("", self.get_all_policies, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/{policy_id}", self.get_policy_by_id, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("/type/{policy_type_slug}/active", self.get_active_policy_by_type, methods=["GET"], status_code=status.HTTP_200_OK)
        self.router.add_api_route("", self.create_policy, methods=["POST"], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{policy_id}", self.update_policy, methods=["PUT"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        self.router.add_api_route("/{policy_id}", self.delete_policy, methods=["DELETE"], status_code=status.HTTP_200_OK, dependencies=[Depends(require_admin)])
        
        self.logger.info("PolicyController routes have been set up")

    # ========== Policy Type Endpoints ==========

    def get_all_policy_types(
        self,
        policy_service: policy_service_dependency
    ):
        """Get all policy types (Admin only)"""
        result = policy_service.get_all_policy_types()
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_policy_type_by_id(
        self,
        policy_type_id: str,
        policy_service: policy_service_dependency
    ):
        """Get a policy type by ID (Admin only)"""
        try:
            policy_type_uuid = UUID(policy_type_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy type ID format")
        
        result = policy_service.get_policy_type_by_id(policy_type_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def create_policy_type(
        self,
        policy_service: policy_service_dependency,
        policy_type_data: CreatePolicyTypeRequest
    ):
        """Create a new policy type (Admin only)"""
        result = policy_service.create_policy_type(
            name=policy_type_data.name,
            description=policy_type_data.description,
            is_required=policy_type_data.is_required
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def update_policy_type(
        self,
        policy_type_id: str,
        policy_service: policy_service_dependency,
        policy_type_data: UpdatePolicyTypeRequest
    ):
        """Update a policy type (Admin only)"""
        try:
            policy_type_uuid = UUID(policy_type_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy type ID format")
        
        result = policy_service.update_policy_type(
            policy_type_id=policy_type_uuid,
            name=policy_type_data.name,
            description=policy_type_data.description,
            is_required=policy_type_data.is_required
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def delete_policy_type(
        self,
        policy_type_id: str,
        policy_service: policy_service_dependency
    ):
        """Delete a policy type (Admin only)"""
        try:
            policy_type_uuid = UUID(policy_type_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy type ID format")
        
        result = policy_service.delete_policy_type(policy_type_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    # ========== Policy Endpoints ==========
    
    def get_all_policies(
        self,
        policy_service: policy_service_dependency,
        include_inactive: bool = Query(False, description="Include inactive policies"),
        policy_type_id: Optional[str] = Query(None, description="Filter by policy type ID")
    ):
        """Get all policies (Public)"""
        policy_type_uuid = None
        if policy_type_id:
            try:
                policy_type_uuid = UUID(policy_type_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid policy type ID format")
        
        result = policy_service.get_all_policies(include_inactive, policy_type_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_policy_by_id(
        self,
        policy_id: str,
        policy_service: policy_service_dependency
    ):
        """Get a policy by ID (Public)"""
        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy ID format")
        
        result = policy_service.get_policy_by_id(policy_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def get_active_policy_by_type(
        self,
        policy_type_slug: str,
        policy_service: policy_service_dependency
    ):
        """Get the currently active policy for a given type using slug (Public)"""
        result = policy_service.get_active_policy_by_type_slug(policy_type_slug)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def create_policy(
        self,
        policy_service: policy_service_dependency,
        policy_data: CreatePolicyRequest
    ):
        """Create a new policy (Admin only)"""
        try:
            policy_type_uuid = UUID(policy_data.policy_type_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy type ID format")
        
        # Parse replaces_policy_id if provided
        replaces_policy_uuid = None
        if policy_data.replaces_policy_id:
            try:
                replaces_policy_uuid = UUID(policy_data.replaces_policy_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid replaces_policy_id format")
        
        result = policy_service.create_policy(
            title=policy_data.title,
            version=policy_data.version,
            content=policy_data.content,
            effective_date=policy_data.effective_date,
            policy_type_id=policy_type_uuid,
            replaces_policy_id=replaces_policy_uuid
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def update_policy(
        self,
        policy_id: str,
        policy_service: policy_service_dependency,
        policy_data: UpdatePolicyRequest
    ):
        """Update a policy (Admin only)"""
        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy ID format")
        
        result = policy_service.update_policy(
            policy_id=policy_uuid,
            title=policy_data.title,
            version=policy_data.version,
            content=policy_data.content,
            effective_date=policy_data.effective_date,
            is_active=policy_data.is_active
        )
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
    
    def delete_policy(
        self,
        policy_id: str,
        policy_service: policy_service_dependency
    ):
        """Delete a policy (Admin only)"""
        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid policy ID format")
        
        result = policy_service.delete_policy(policy_uuid)
        if not result.get("success"):
            raise HTTPException(status_code=result.get("status_code"), detail=result.get("message"))
        return result
