from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ExerciseCreateRequest(BaseModel):
    """Schema for creating a new exercise."""
    content_id: str = Field(..., description="ID of the content item")
    embed_code: str = Field(..., description="123FormBuilder embed code")
    form_title: str = Field(..., description="Title of the form")
    allow_multiple_submissions: bool = Field(default=False, description="Whether to allow multiple submissions")
    
    @field_validator('embed_code', 'form_title')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class ExerciseUpdateEmbedRequest(BaseModel):
    """Schema for updating exercise embed code."""
    embed_code: str = Field(..., description="New 123FormBuilder embed code")
    form_title: Optional[str] = Field(None, description="Optional new form title")
    
    @field_validator('embed_code')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that embed code is not empty."""
        if not v or not v.strip():
            raise ValueError("Embed code cannot be empty")
        return v.strip()


class ExerciseResponse(BaseModel):
    """Schema for exercise response."""
    id: str
    content_id: str
    form_id: str
    embed_code: str
    form_title: str
    allow_multiple_submissions: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExerciseSubmissionResponse(BaseModel):
    """Schema for exercise submission response."""
    id: str
    exercise_id: str
    user_id: str
    user_name: str
    user_email: str
    form_submission_id: str
    submitted_at: datetime
    webhook_received_at: datetime
    
    class Config:
        from_attributes = True


class ExerciseSubmissionsListResponse(BaseModel):
    """Schema for list of submissions with statistics."""
    submissions: list[ExerciseSubmissionResponse]
    total_submissions: int
    unique_users: int
    completion_rate: float = Field(..., description="Percentage of enrolled users who completed")
    exercise_info: ExerciseResponse
