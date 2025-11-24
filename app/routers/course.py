from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.dependencies import get_db, get_current_enrolled_user
from app.models.course import Course
from app.models.module import Module
from app.models.content import Content
from app.models.user import User
from app.schemas.course import (
    CourseResponse,
    ModuleResponse,
    ContentResponse,
    ModuleWithContentResponse
)
from app.services.storage_service import storage_service
from app.services.progress_service import progress_service

router = APIRouter(prefix="/api", tags=["course"])


@router.get("/course", response_model=CourseResponse)
async def get_course(db: Session = Depends(get_db)):
    """
    Get course details.
    
    Returns the single course information including title, description,
    instructor details, and pricing.
    """
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return course


@router.get("/course/modules/public")
async def get_public_course_modules(
    db: Session = Depends(get_db)
):
    """
    Get all published modules for the course (public access).
    
    Returns modules ordered by order_index without progress data.
    Used for homepage display.
    """
    from sqlalchemy import func
    
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Query modules with content count
    modules_with_count = (
        db.query(
            Module,
            func.count(Content.id).label('content_count')
        )
        .outerjoin(Content, (Content.module_id == Module.id) & (Content.is_published == True))
        .filter(Module.course_id == course.id, Module.is_published == True)
        .group_by(Module.id)
        .order_by(Module.order_index)
        .all()
    )
    
    # Build result
    result = []
    for module, content_count in modules_with_count:
        result.append({
            "id": module.id,
            "course_id": module.course_id,
            "title": module.title,
            "description": module.description,
            "order_index": module.order_index,
            "is_published": module.is_published,
            "created_at": module.created_at,
            "updated_at": module.updated_at,
            "content_count": content_count or 0
        })
    
    return result


@router.get("/course/modules")
async def get_course_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_enrolled_user)
):
    """
    Get all published modules for the course with progress data.
    
    Returns modules ordered by order_index with progress information for enrolled users.
    Optimized to avoid N+1 queries.
    """
    from app.models.user_progress import UserProgress
    from sqlalchemy import func, case
    
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Single optimized query with subqueries for counts
    modules_with_progress = (
        db.query(
            Module,
            func.count(Content.id).label('content_count'),
            func.sum(
                case(
                    (UserProgress.is_completed == True, 1),
                    else_=0
                )
            ).label('completed_count')
        )
        .outerjoin(Content, (Content.module_id == Module.id) & (Content.is_published == True))
        .outerjoin(
            UserProgress,
            (UserProgress.content_id == Content.id) & (UserProgress.user_id == current_user.id)
        )
        .filter(Module.course_id == course.id, Module.is_published == True)
        .group_by(Module.id)
        .order_by(Module.order_index)
        .all()
    )
    
    # Build result
    result = []
    for module, content_count, completed_count in modules_with_progress:
        content_count = content_count or 0
        completed_count = completed_count or 0
        progress_percentage = round((completed_count / content_count * 100), 2) if content_count > 0 else 0
        
        result.append({
            "id": module.id,
            "course_id": module.course_id,
            "title": module.title,
            "description": module.description,
            "order_index": module.order_index,
            "is_published": module.is_published,
            "created_at": module.created_at,
            "updated_at": module.updated_at,
            "content_count": content_count,
            "completed_count": completed_count,
            "progress_percentage": progress_percentage
        })
    
    return result


@router.get("/modules/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details for a specific module.
    
    Returns module information including title, description, and order.
    Returns 404 if module not found or not published.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    if not module.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not available"
        )
    
    return module


@router.get("/modules/{module_id}/content", response_model=List[ContentResponse])
async def get_module_content(
    module_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all published content for a specific module.
    
    Returns content items ordered by order_index, filtered by is_published status.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    content_items = (
        db.query(Content)
        .filter(Content.module_id == module_id, Content.is_published == True)
        .order_by(Content.order_index)
        .all()
    )
    
    # Parse rich_text_content JSON strings and generate signed URLs for PDFs
    result = []
    for item in content_items:
        content_dict = {
            "id": item.id,
            "module_id": item.module_id,
            "content_type": item.content_type,
            "title": item.title,
            "order_index": item.order_index,
            "vimeo_video_id": item.vimeo_video_id,
            "video_duration": item.video_duration,
            "pdf_url": storage_service.get_signed_url(item.pdf_url) if item.pdf_url else None,
            "pdf_filename": item.pdf_filename,
            "rich_text_content": json.loads(item.rich_text_content) if item.rich_text_content else None,
            "is_published": item.is_published,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        
        # Add exercise data if content type is exercise
        if item.content_type == "exercise":
            from app.services.exercise_service import exercise_service
            exercise = exercise_service.get_exercise_by_content_id(db, item.id)
            if exercise:
                content_dict["exercise"] = {
                    "id": exercise.id,
                    "content_id": exercise.content_id,
                    "form_id": exercise.form_id,
                    "embed_code": exercise.embed_code,
                    "form_title": exercise.form_title,
                    "allow_multiple_submissions": exercise.allow_multiple_submissions,
                    "created_at": exercise.created_at,
                    "updated_at": exercise.updated_at
                }
        
        result.append(ContentResponse(**content_dict))
    
    return result



@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get specific content item by ID.
    
    Requires user to be enrolled. Returns content based on type:
    - Video: Returns Vimeo video ID
    - PDF: Returns signed Vercel Blob URL
    - Rich text: Returns structured JSONB content
    
    Sequential Access: Users must complete previous content before accessing the next.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if not content.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not available"
        )
    
    # Check if user can access this content (sequential completion check)
    can_access, reason = progress_service.can_access_content(
        db=db,
        user_id=current_user.id,
        content_id=content_id
    )
    
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason or "You must complete previous content first"
        )
    
    # Build response based on content type
    content_dict = {
        "id": content.id,
        "module_id": content.module_id,
        "content_type": content.content_type,
        "title": content.title,
        "order_index": content.order_index,
        "is_published": content.is_published,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }
    
    if content.content_type == "video":
        # Return Vimeo video ID
        content_dict["vimeo_video_id"] = content.vimeo_video_id
        content_dict["video_duration"] = content.video_duration
    
    elif content.content_type == "pdf":
        # Return signed URL for PDF
        if content.pdf_url:
            content_dict["pdf_url"] = storage_service.get_signed_url(content.pdf_url)
        content_dict["pdf_filename"] = content.pdf_filename
    
    elif content.content_type == "rich_text":
        # Return structured JSONB content
        content_dict["rich_text_content"] = json.loads(content.rich_text_content) if content.rich_text_content else None
    
    elif content.content_type == "exercise":
        # Return exercise data
        from app.services.exercise_service import exercise_service
        exercise = exercise_service.get_exercise_by_content_id(db, content.id)
        if exercise:
            content_dict["exercise"] = {
                "id": exercise.id,
                "content_id": exercise.content_id,
                "form_id": exercise.form_id,
                "embed_code": exercise.embed_code,
                "form_title": exercise.form_title,
                "allow_multiple_submissions": exercise.allow_multiple_submissions,
                "created_at": exercise.created_at,
                "updated_at": exercise.updated_at
            }
    
    return ContentResponse(**content_dict)
