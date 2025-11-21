from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AnnouncementCreate(BaseModel):
    """Schema for creating an announcement."""
    title: str = Field(..., min_length=1, max_length=255, description="Announcement title")
    content: str = Field(..., min_length=1, description="Announcement content")
    is_published: bool = Field(default=False, description="Whether the announcement is published")


class AnnouncementUpdate(BaseModel):
    """Schema for updating an announcement."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Announcement title")
    content: Optional[str] = Field(None, min_length=1, description="Announcement content")
    is_published: Optional[bool] = Field(None, description="Whether the announcement is published")


class AnnouncementResponse(BaseModel):
    """Schema for announcement response."""
    id: str
    title: str
    content: str
    created_by: str
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    """Schema for list of announcements."""
    announcements: list[AnnouncementResponse]
    total: int
