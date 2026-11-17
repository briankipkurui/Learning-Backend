from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class ResumeJDAnalysisResponse(BaseModel):
    """Response schema for resume/JD analysis"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    status_code: int

# ===== Interview Question Management Schemas =====

class CreateInterviewQuestionRequest(BaseModel):
    """Request schema for creating an interview question"""
    question_text: str = Field(..., description="The interview question text", min_length=1)
    category: str = Field(..., description="Question category (e.g., Icebreaker, Technical)")
    difficulty: str = Field(..., description="Difficulty level")
    framework: str = Field(..., description="Framework to use for answering")
    skills_tested: str = Field(..., description="Skills being tested")
    framework_description: Optional[str] = Field(None, description="Detailed description of the framework")
    good_answer_criteria: Optional[str] = Field(None, description="Criteria for a good answer")
    listening_guideline: Optional[str] = Field(None, description="Guidelines for listening to the answer")
    common_issues: Optional[str] = Field(None, description="Common issues to watch out for")
    notes: str = Field(..., description="Additional notes or guidance")
    time_limit: int = Field(..., description="Time limit in minutes", ge=0)
    profession_id: UUID = Field(..., description="Associated profession ID")

class UpdateInterviewQuestionRequest(BaseModel):
    """Request schema for updating an interview question"""
    question_text: Optional[str] = Field(None, description="The interview question text", min_length=1)
    category: Optional[str] = Field(None, description="Question category")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    framework: Optional[str] = Field(None, description="Framework to use for answering")
    skills_tested: Optional[str] = Field(None, description="Skills being tested")
    framework_description: Optional[str] = Field(None, description="Detailed description of the framework")
    good_answer_criteria: Optional[str] = Field(None, description="Criteria for a good answer")
    listening_guideline: Optional[str] = Field(None, description="Guidelines for listening to the answer")
    common_issues: Optional[str] = Field(None, description="Common issues to watch out for")
    notes: Optional[str] = Field(None, description="Additional notes or guidance")
    time_limit: Optional[int] = Field(None, description="Time limit in minutes", ge=0)
    profession_id: Optional[UUID] = Field(None, description="Associated profession ID")

class InterviewQuestionResponse(BaseModel):
    """Response schema for an interview question"""
    Id: UUID
    question_text: str
    category: Optional[str] = None
    difficulty: Optional[str] = None
    framework: Optional[str] = None
    skills_tested: Optional[str] = None
    framework_description: Optional[str] = None
    good_answer_criteria: Optional[str] = None
    listening_guideline: Optional[str] = None
    common_issues: Optional[str] = None
    notes: Optional[str] = None
    time_limit: Optional[int] = None
    profession_id: Optional[UUID] = None
    profession_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedInterviewQuestionsResponse(BaseModel):
    """Response schema for paginated interview questions"""
    questions: List[InterviewQuestionResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool
