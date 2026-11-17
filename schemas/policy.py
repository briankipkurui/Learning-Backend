from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class PolicyTypeBase(BaseModel):
    """Base schema for policy type"""
    name: str = Field(..., description="Policy type name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Policy type description")
    is_required: bool = Field(False, description="Whether this policy type is required for signup")

class CreatePolicyTypeRequest(PolicyTypeBase):
    """Request schema for creating a policy type"""
    pass

class UpdatePolicyTypeRequest(BaseModel):
    """Request schema for updating a policy type"""
    name: Optional[str] = Field(None, description="Policy type name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Policy type description")
    is_required: Optional[bool] = Field(None, description="Whether this policy type is required for signup")

class PolicyTypeResponse(PolicyTypeBase):
    """Response schema for policy type"""
    Id: str
    is_required: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class PolicyBase(BaseModel):
    """Base schema for policy"""
    title: str = Field(..., description="Policy title", min_length=1, max_length=255)
    version: str = Field(..., description="Policy version", min_length=1, max_length=50)
    content: str = Field(..., description="Policy content")
    effective_date: date = Field(..., description="Policy effective date")
    policy_type_id: str = Field(..., description="Policy type ID")

class CreatePolicyRequest(PolicyBase):
    """Request schema for creating a policy"""
    replaces_policy_id: Optional[str] = Field(None, description="ID of the policy this new policy replaces")

class UpdatePolicyRequest(BaseModel):
    """Request schema for updating a policy"""
    title: Optional[str] = Field(None, description="Policy title", min_length=1, max_length=255)
    version: Optional[str] = Field(None, description="Policy version", min_length=1, max_length=50)
    content: Optional[str] = Field(None, description="Policy content")
    effective_date: Optional[date] = Field(None, description="Policy effective date")
    is_active: Optional[bool] = Field(None, description="Whether policy is active")

class PolicyResponse(BaseModel):
    """Response schema for policy"""
    Id: str
    title: str
    version: str
    content: str
    effective_date: date
    is_active: bool
    policy_type_id: str
    replaced_by_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True
