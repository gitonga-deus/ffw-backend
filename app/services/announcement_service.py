from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


class AnnouncementService:
    """Service for handling announcement operations."""
    
    @staticmethod
    def create_announcement(
        db: Session,
        announcement_data: AnnouncementCreate,
        created_by: str
    ) -> Announcement:
        """
        Create a new announcement.
        
        Args:
            db: Database session
            announcement_data: Announcement data
            created_by: ID of the admin creating the announcement
            
        Returns:
            Created announcement
        """
        announcement = Announcement(
            title=announcement_data.title,
            content=announcement_data.content,
            is_published=announcement_data.is_published,
            created_by=created_by
        )
        
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        
        return announcement
    
    @staticmethod
    def get_announcements(
        db: Session,
        published_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Announcement]:
        """
        Get announcements.
        
        Args:
            db: Database session
            published_only: If True, only return published announcements
            limit: Maximum number of announcements to return
            
        Returns:
            List of announcements ordered by created_at descending
        """
        query = db.query(Announcement)
        
        if published_only:
            query = query.filter(Announcement.is_published == True)
        
        query = query.order_by(Announcement.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_announcement_by_id(db: Session, announcement_id: str) -> Optional[Announcement]:
        """
        Get announcement by ID.
        
        Args:
            db: Database session
            announcement_id: Announcement ID
            
        Returns:
            Announcement or None if not found
        """
        return db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    @staticmethod
    def update_announcement(
        db: Session,
        announcement_id: str,
        announcement_data: AnnouncementUpdate
    ) -> Announcement:
        """
        Update an announcement.
        
        Args:
            db: Database session
            announcement_id: Announcement ID
            announcement_data: Updated announcement data
            
        Returns:
            Updated announcement
            
        Raises:
            404: If announcement not found
        """
        announcement = db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()
        
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        # Update fields if provided
        if announcement_data.title is not None:
            announcement.title = announcement_data.title
        if announcement_data.content is not None:
            announcement.content = announcement_data.content
        if announcement_data.is_published is not None:
            announcement.is_published = announcement_data.is_published
        
        db.commit()
        db.refresh(announcement)
        
        return announcement
    
    @staticmethod
    def delete_announcement(db: Session, announcement_id: str) -> bool:
        """
        Delete an announcement.
        
        Args:
            db: Database session
            announcement_id: Announcement ID
            
        Returns:
            True if deleted
            
        Raises:
            404: If announcement not found
        """
        announcement = db.query(Announcement).filter(
            Announcement.id == announcement_id
        ).first()
        
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        db.delete(announcement)
        db.commit()
        
        return True


announcement_service = AnnouncementService()
