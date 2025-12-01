from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.services.notification_service import notification_service
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse
)

router = APIRouter(prefix="/admin/notifications", tags=["notifications"])


@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED
)
async def send_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Send a notification to targeted users.
    Admin only endpoint.
    
    Supports targeting:
    - all_enrolled: All enrolled students
    - all_users: All verified users
    - specific: Specific users by ID list
    
    Sends emails via Resend to all targeted users.
    
    Args:
        notification_data: Notification title, message, and targeting info
        
    Returns:
        Created notification record with email status
        
    Raises:
        400: If target_user_ids is required but not provided
        
    Requirements: 9.3, 9.4, 9.5
    """
    notification = await notification_service.send_notification(
        db=db,
        notification_data=notification_data,
        sent_by=current_user.id
    )
    
    return notification


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get notification history.
    Admin only endpoint.
    
    Returns:
        List of sent notifications ordered by sent_at descending
    """
    notifications = notification_service.get_notifications(db=db)
    
    return NotificationListResponse(
        notifications=notifications,
        total=len(notifications)
    )
