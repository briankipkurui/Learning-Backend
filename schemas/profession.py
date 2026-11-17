from pydantic import BaseModel, Field
from typing import Optional

class ProfessionBase(BaseModel):
    """Base schema for profession"""
    name: str = Field(..., description="Profession name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Profession description")

class CreateProfessionRequest(ProfessionBase):
    """Request schema for creating a profession"""
    pass

class UpdateProfessionRequest(BaseModel):
    """Request schema for updating a profession"""
    name: Optional[str] = Field(None, description="Profession name", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Profession description")
    is_active: Optional[bool] = Field(None, description="Whether profession is active")

class ProfessionResponse(ProfessionBase):
    """Response schema for profession"""
    Id: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True
