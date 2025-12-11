"""
Progress Router - Rebuilt with improved architecture.

This router provides clean, RESTful endpoints for progress tracking with:
- Proper authentication and authorization
- Request validation
- Comprehensive error handling
- Certificate generation integration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    OperationalError,
    IntegrityError,
    DatabaseError
)
from typing import List, Dict, Any
import logging

from app.database import get_db
from app.dependencies import get_current_enrolled_user
from app.models.user import User
from app.models.content import Content
from app.models.module import Module
from app.models.course import Course
from app.schemas.progress import (
    ProgressUpdateRequest,
    ContentProgressResponse,
    ModuleProgressResponse,
    OverallProgressResponse
)
from app.services.progress_service import progress_service
from app.services.certificate_service import certificate_service
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Consistent error response format for all endpoints."""
    
    @staticmethod
    def format_error(
        error_type: str,
        message: str,
        details: Any = None
    ) -> Dict[str, Any]:
        """
        Format error response consistently.
        
        Args:
            error_type: Type of error (e.g., "validation_error", "not_found")
            message: Human-readable error message
            details: Optional additional error details
            
        Returns:
            Formatted error dictionary
        """
        response = {
            "error": error_type,
            "message": message
        }
        if details:
            response["details"] = details
        return response

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/{content_id}", response_model=ContentProgressResponse)
async def update_progress(
    content_id: str,
    progress_data: ProgressUpdateRequest,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Update progress for a specific content item.
    
    This endpoint:
    1. Validates the content exists and is published
    2. Checks if user can access the content (sequential access)
    3. Updates or creates progress record
    4. Recalculates enrollment progress
    5. Checks for course completion and triggers certificate generation
    
    Args:
        content_id: ID of the content item
        progress_data: Progress update data (completion status, time spent, position)
        current_user: Authenticated enrolled user
        db: Database session
        
    Returns:
        Updated content progress data
        
    Raises:
        404: Content not found or not published
        403: User cannot access this content (sequential access blocked)
        409: Concurrent update conflict
        422: Invalid progress data
        503: Database connection error
    """
    try:
        # Validate progress data
        if progress_data.time_spent < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse.format_error(
                    "validation_error",
                    "Invalid progress data",
                    {"time_spent": "Time spent cannot be negative"}
                )
            )
        
        if progress_data.last_position is not None and progress_data.last_position < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse.format_error(
                    "validation_error",
                    "Invalid progress data",
                    {"last_position": "Last position cannot be negative"}
                )
            )
        
        # Validate content exists and is published
        try:
            content = db.query(Content).filter(
                Content.id == content_id,
                Content.is_published == True
            ).first()
        except OperationalError as e:
            logger.error(f"Database connection error while fetching content: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.format_error(
                    "not_found",
                    "Content not found or not published",
                    {"content_id": content_id}
                )
            )
        
        # Check if user can access this content (sequential access validation)
        try:
            can_access, reason = progress_service.can_access_content(
                db=db,
                user_id=current_user.id,
                content_id=content_id
            )
        except OperationalError as e:
            logger.error(f"Database connection error during access check: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not can_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse.format_error(
                    "access_denied",
                    reason or "You cannot access this content yet",
                    {"content_id": content_id}
                )
            )
        
        # Update progress
        try:
            progress = progress_service.update_progress(
                db=db,
                user_id=current_user.id,
                content_id=content_id,
                progress_data=progress_data
            )
        except IntegrityError as e:
            logger.warning(f"Concurrent update conflict for user {current_user.id}, content {content_id}: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse.format_error(
                    "conflict",
                    "Progress update conflict. Please retry your request.",
                    {"content_id": content_id}
                )
            )
        except OperationalError as e:
            logger.error(f"Database connection error during progress update: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        except ValueError as e:
            logger.warning(f"Validation error during progress update: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse.format_error(
                    "validation_error",
                    str(e),
                    {"content_id": content_id}
                )
            )
        
        # Check for course completion and trigger certificate generation
        if progress_data.is_completed:
            try:
                is_course_complete = progress_service.check_course_completion(
                    db=db,
                    user_id=current_user.id
                )
                
                if is_course_complete:
                    # Mark course as completed
                    progress_service.mark_course_completed(
                        db=db,
                        user_id=current_user.id
                    )
                    
                    # Check if certificate already exists
                    existing_cert = certificate_service.get_user_certificate(
                        db=db,
                        user_id=current_user.id
                    )
                    
                    # Generate certificate only if it doesn't exist
                    if not existing_cert:
                        logger.info(f"Course completed for user {current_user.id}, generating certificate")
                        
                        # Get course
                        course = db.query(Course).filter(
                            Course.is_published == True
                        ).first()
                        
                        if course:
                            # Generate certificate
                            logger.info(f"Calling certificate generation for user {current_user.id}")
                            certificate = await certificate_service.generate_certificate(
                                db=db,
                                user=current_user,
                                course=course
                            )
                            
                            if certificate:
                                logger.info(f"Certificate generated successfully: {certificate.certification_id}")
                                # Send completion email with certificate link
                                try:
                                    await email_service.send_course_completion_email(
                                        to=current_user.email,
                                        full_name=current_user.full_name,
                                        certificate_url=certificate.certificate_url,
                                        cert_id=certificate.certification_id
                                    )
                                    logger.info(f"Completion email sent to {current_user.email}")
                                except Exception as email_error:
                                    logger.error(f"Failed to send completion email: {email_error}")
                                    # Don't fail the request if email fails
                            else:
                                logger.error(f"Certificate generation returned None for user {current_user.id}")
                    else:
                        logger.info(f"Certificate already exists for user {current_user.id}, skipping generation")
            except OperationalError as e:
                logger.error(f"Database error during certificate generation: {str(e)}")
                # Don't fail the progress update if certificate generation fails
                # The progress was already saved successfully
            except Exception as e:
                logger.error(f"Error during certificate generation: {str(e)}")
                # Don't fail the progress update if certificate generation fails
        
        # Return updated progress
        return ContentProgressResponse(
            content_id=progress.content_id,
            content_title=content.title,
            content_type=content.content_type,
            is_completed=progress.is_completed,
            time_spent=progress.time_spent,
            last_position=progress.last_position,
            completed_at=progress.completed_at,
            updated_at=progress.updated_at
        )
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error updating progress: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "database_error",
                "Service temporarily unavailable. Please try again later."
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error updating progress: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )
        )


@router.get("", response_model=OverallProgressResponse)
async def get_overall_progress(
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get overall course progress for the current user.
    
    Returns comprehensive progress data including:
    - Overall progress percentage
    - Module-level progress
    - Content breakdown by type
    - Last accessed content
    
    Args:
        current_user: Authenticated enrolled user
        db: Database session
        
    Returns:
        Overall progress data with module breakdown
        
    Raises:
        503: Database connection error
    """
    try:
        progress = progress_service.get_overall_progress(
            db=db,
            user_id=current_user.id
        )
        
        return progress
        
    except OperationalError as e:
        logger.error(f"Database connection error fetching overall progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "database_error",
                "Service temporarily unavailable. Please try again later."
            )
        )
    except DatabaseError as e:
        logger.error(f"Database error fetching overall progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "database_error",
                "Service temporarily unavailable. Please try again later."
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching overall progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )
        )


@router.get("/module/{module_id}", response_model=List[ContentProgressResponse])
async def get_module_progress(
    module_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get progress for all content items in a specific module.
    
    Args:
        module_id: ID of the module
        current_user: Authenticated enrolled user
        db: Database session
        
    Returns:
        List of content progress data ordered by content order_index
        
    Raises:
        404: Module not found or not published
        503: Database connection error
    """
    try:
        # Validate module exists and is published
        try:
            module = db.query(Module).filter(
                Module.id == module_id,
                Module.is_published == True
            ).first()
        except OperationalError as e:
            logger.error(f"Database connection error while fetching module: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.format_error(
                    "not_found",
                    "Module not found or not published",
                    {"module_id": module_id}
                )
            )
        
        try:
            progress_list = progress_service.get_module_progress(
                db=db,
                user_id=current_user.id,
                module_id=module_id
            )
        except OperationalError as e:
            logger.error(f"Database connection error fetching module progress: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        return progress_list
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error fetching module progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "database_error",
                "Service temporarily unavailable. Please try again later."
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching module progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )
        )


@router.post("/access/{module_id}")
async def track_module_access(
    module_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Track when a user accesses a module (for "resume where you left off").
    
    Args:
        module_id: ID of the module being accessed
        current_user: Authenticated enrolled user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        404: Module not found
        503: Database connection error
    """
    try:
        # Validate module exists
        try:
            module = db.query(Module).filter(
                Module.id == module_id,
                Module.is_published == True
            ).first()
        except OperationalError as e:
            logger.error(f"Database connection error while fetching module: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.format_error(
                    "not_found",
                    "Module not found or not published",
                    {"module_id": module_id}
                )
            )
        
        # Update last accessed
        try:
            progress_service.update_last_accessed(
                db=db,
                user_id=current_user.id,
                module_id=module_id
            )
        except OperationalError as e:
            logger.error(f"Database connection error updating last accessed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        return {"message": "Module access tracked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error tracking module access: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )
        )


@router.get("/content/{content_id}", response_model=ContentProgressResponse)
async def get_content_progress(
    content_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get progress for a specific content item.
    
    Args:
        content_id: ID of the content item
        current_user: Authenticated enrolled user
        db: Database session
        
    Returns:
        Content progress data
        
    Raises:
        404: Content not found or not published
        503: Database connection error
    """
    try:
        # Validate content exists and is published
        try:
            content = db.query(Content).filter(
                Content.id == content_id,
                Content.is_published == True
            ).first()
        except OperationalError as e:
            logger.error(f"Database connection error while fetching content: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.format_error(
                    "not_found",
                    "Content not found or not published",
                    {"content_id": content_id}
                )
            )
        
        try:
            progress = progress_service.get_content_progress(
                db=db,
                user_id=current_user.id,
                content_id=content_id
            )
        except OperationalError as e:
            logger.error(f"Database connection error fetching content progress: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorResponse.format_error(
                    "database_error",
                    "Service temporarily unavailable. Please try again later."
                )
            )
        
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse.format_error(
                    "not_found",
                    "Content not found",
                    {"content_id": content_id}
                )
            )
        
        return progress
        
    except HTTPException:
        raise
    except DatabaseError as e:
        logger.error(f"Database error fetching content progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "database_error",
                "Service temporarily unavailable. Please try again later."
            )
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching content progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse.format_error(
                "internal_error",
                "An unexpected error occurred. Please try again later."
            )
        )
