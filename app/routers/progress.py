from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db, get_current_enrolled_user
from app.models.user import User
from app.models.content import Content
from app.models.course import Course
from app.models.module import Module
from app.schemas.progress import (
    ProgressUpdateRequest,
    ContentProgressResponse,
    OverallProgressResponse,
    ExerciseResponseRequest,
    ExerciseResponseResponse
)
from app.services.progress_service import progress_service
from app.services.certificate_service import certificate_service
from app.services.email_service import email_service

router = APIRouter(
    prefix="/api/progress",
    tags=["progress"]
)


@router.post("/{content_id}", response_model=ContentProgressResponse)
async def update_progress(
    content_id: str,
    progress_data: ProgressUpdateRequest,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Update progress for a specific content item.
    
    - **content_id**: ID of the content item
    - **is_completed**: Whether the content is completed
    - **time_spent**: Time spent in seconds
    - **last_position**: Last position (seconds for video, page for PDF)
    """
    # Verify content exists and is published
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.is_published == True
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Update progress
    progress = progress_service.update_progress(
        db=db,
        user_id=current_user.id,
        content_id=content_id,
        progress_data=progress_data
    )
    
    # Check if course is completed
    if progress_data.is_completed:
        is_course_completed = progress_service.check_course_completion(
            db=db,
            user_id=current_user.id
        )
        
        if is_course_completed:
            progress_service.mark_course_completed(
                db=db,
                user_id=current_user.id
            )
            
            # Trigger certificate generation
            # Get the course (assuming single course system)
            course = db.query(Course).first()
            
            if course:
                # Generate certificate
                certificate = await certificate_service.generate_certificate(
                    db=db,
                    user=current_user,
                    course=course
                )
                
                # Send course completion email with certificate link
                if certificate:
                    await email_service.send_course_completion_email(
                        to=current_user.email,
                        full_name=current_user.full_name,
                        certificate_url=certificate.certificate_url,
                        cert_id=certificate.certification_id
                    )
    
    # Return updated progress
    return progress_service.get_content_progress(
        db=db,
        user_id=current_user.id,
        content_id=content_id
    )


@router.get("", response_model=OverallProgressResponse)
async def get_overall_progress(
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get overall course progress for the current user.
    
    Returns:
    - Overall progress percentage
    - Module-level progress breakdown
    - Completed modules and content counts
    - Last accessed content information
    """
    return progress_service.get_overall_progress(
        db=db,
        user_id=current_user.id
    )


@router.get("/module/{module_id}", response_model=List[ContentProgressResponse])
async def get_module_progress(
    module_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get progress for all content items in a module.
    
    - **module_id**: ID of the module
    
    Returns:
    - Array of progress records for all content items in the module
    - Empty array if module has no content
    """
    # Verify module exists and is published
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.is_published == True
    ).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Get progress data for all content in the module
    progress_data = progress_service.get_module_progress(
        db=db,
        user_id=current_user.id,
        module_id=module_id
    )
    
    return progress_data


@router.get("/content/{content_id}", response_model=ContentProgressResponse)
async def get_content_progress(
    content_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get progress for a specific content item.
    
    - **content_id**: ID of the content item
    """
    # Verify content exists and is published
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.is_published == True
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    progress = progress_service.get_content_progress(
        db=db,
        user_id=current_user.id,
        content_id=content_id
    )
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress not found"
        )
    
    return progress


@router.post("/exercise", response_model=ExerciseResponseResponse)
async def submit_exercise_response(
    exercise_data: ExerciseResponseRequest,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Submit or update exercise response.
    
    - **content_id**: ID of the content containing the exercise
    - **exercise_id**: ID of the exercise within the content
    - **response_data**: User's response data (JSON object)
    """
    # Verify content exists and is published
    content = db.query(Content).filter(
        Content.id == exercise_data.content_id,
        Content.is_published == True
    ).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Submit exercise response
    response = progress_service.submit_exercise_response(
        db=db,
        user_id=current_user.id,
        exercise_data=exercise_data
    )
    
    return response
