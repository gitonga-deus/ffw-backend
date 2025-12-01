from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_verified_user
from app.models.user import User
from app.services.announcement_service import announcement_service
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse
)

router = APIRouter(prefix="", tags=["announcements"])


@router.post(
    "/admin/announcements",
    response_model=AnnouncementResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_announcement(
    announcement_data: AnnouncementCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new announcement.
    Admin only endpoint.
    
    Args:
        announcement_data: Announcement title, content, and publish status
        
    Returns:
        Created announcement
        
    Requirements: 9.1, 9.2
    """
    announcement = announcement_service.create_announcement(
        db=db,
        announcement_data=announcement_data,
        created_by=current_user.id
    )
    
    return announcement


@router.get("/announcements", response_model=AnnouncementListResponse)
async def get_announcements(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Get all published announcements for students.
    Requires authentication.
    
    Returns:
        List of published announcements ordered by created_at descending
        
    Requirements: 9.1, 9.2
    """
    announcements = announcement_service.get_announcements(
        db=db,
        published_only=True
    )
    
    return AnnouncementListResponse(
        announcements=announcements,
        total=len(announcements)
    )


@router.get(
    "/admin/announcements",
    response_model=AnnouncementListResponse
)
async def get_all_announcements_admin(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all announcements (published and unpublished).
    Admin only endpoint.
    
    Returns:
        List of all announcements ordered by created_at descending
    """
    announcements = announcement_service.get_announcements(
        db=db,
        published_only=False
    )
    
    return AnnouncementListResponse(
        announcements=announcements,
        total=len(announcements)
    )


@router.put(
    "/admin/announcements/{announcement_id}",
    response_model=AnnouncementResponse
)
async def update_announcement(
    announcement_id: str,
    announcement_data: AnnouncementUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an announcement.
    Admin only endpoint.
    
    Args:
        announcement_id: ID of the announcement to update
        announcement_data: Updated announcement data
        
    Returns:
        Updated announcement
        
    Raises:
        404: If announcement not found
    """
    announcement = announcement_service.update_announcement(
        db=db,
        announcement_id=announcement_id,
        announcement_data=announcement_data
    )
    
    return announcement


@router.delete(
    "/admin/announcements/{announcement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete an announcement.
    Admin only endpoint.
    
    Args:
        announcement_id: ID of the announcement to delete
        
    Raises:
        404: If announcement not found
    """
    announcement_service.delete_announcement(
        db=db,
        announcement_id=announcement_id
    )
    
    return None
