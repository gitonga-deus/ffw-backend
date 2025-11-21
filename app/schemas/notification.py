from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.notification import TargetAudience


class NotificationCreate(BaseModel):
    """Schema for creating and sending a notification."""
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    target_audience: TargetAudience = Field(..., description="Target audience for the notification")
    target_user_ids: Optional[list[str]] = Field(
        default=None,
        description="List of specific user IDs (required when target_audience is 'specific')"
    )


class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: str
    title: str
    message: str
    target_audience: str
    target_user_ids: Optional[str]
    sent_by: str
    sent_at: datetime
    email_sent: bool

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Schema for list of notifications."""
    notifications: list[NotificationResponse]
    total: int
