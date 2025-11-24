from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProgressUpdateRequest(BaseModel):
    """Request schema for updating progress."""
    is_completed: bool = Field(default=False, description="Whether the content is completed")
    time_spent: int = Field(default=0, ge=0, description="Time spent in seconds")
    last_position: Optional[int] = Field(default=None, ge=0, description="Last position (seconds for video, page for PDF)")


class ContentProgressResponse(BaseModel):
    """Response schema for content progress."""
    content_id: str
    content_title: str
    content_type: str
    is_completed: bool
    time_spent: int
    last_position: Optional[int]
    completed_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleProgressResponse(BaseModel):
    """Response schema for module progress."""
    module_id: str
    module_title: str
    total_content: int
    completed_content: int
    progress_percentage: float


class ContentBreakdown(BaseModel):
    """Breakdown of content by type."""
    videos: int = 0
    pdfs: int = 0
    rich_text: int = 0
    exercises: int = 0


class CompletedContentBreakdown(BaseModel):
    """Breakdown of completed content by type."""
    videos: int = 0
    pdfs: int = 0
    rich_text: int = 0
    exercises: int = 0


class OverallProgressResponse(BaseModel):
    """Response schema for overall course progress."""
    progress_percentage: float
    total_modules: int
    completed_modules: int
    total_content: int
    completed_content: int
    content_breakdown: Optional[ContentBreakdown] = None
    completed_breakdown: Optional[CompletedContentBreakdown] = None
    last_accessed_content_id: Optional[str]
    last_accessed_at: Optional[datetime]
    last_accessed_content: Optional[dict] = None
    modules: list[ModuleProgressResponse]


class ExerciseResponseRequest(BaseModel):
    """Request schema for submitting exercise response."""
    content_id: str = Field(..., description="Content ID containing the exercise")
    exercise_id: str = Field(..., description="Exercise ID within the content")
    response_data: dict = Field(..., description="User's response data")


class ExerciseResponseResponse(BaseModel):
    """Response schema for exercise response."""
    id: str
    content_id: str
    exercise_id: str
    response_data: str
    submitted_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
