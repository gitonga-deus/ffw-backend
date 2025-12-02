from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional
from datetime import datetime
import json
import math

from app.dependencies import get_db, get_current_admin_user
from app.models.user import User
from app.models.module import Module
from app.models.content import Content
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.analytics_event import AnalyticsEvent
from app.models.course import Course
from app.schemas.course import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
    ContentReorderRequest
)
from app.schemas.user import (
    UserListResponse,
    UserListItem,
    UserDetailResponse,
    EnrollmentDetail,
    PaymentHistoryItem,
    PaymentListItem,
    ActivityLogItem,
    AdminProfileResponse,
    AdminProfileUpdate,
    CourseSettingsResponse,
    CourseSettingsUpdate
)
from app.services.storage_service import storage_service
from app.utils.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/modules", response_model=list[ModuleResponse])
async def get_modules_admin(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all modules for the course (including drafts).
    
    Admin only. Returns all modules regardless of is_published status.
    """
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    modules = (
        db.query(Module)
        .filter(Module.course_id == course.id)
        .order_by(Module.order_index)
        .all()
    )
    
    return modules


@router.get("/modules-with-content")
async def get_modules_with_content_admin(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all modules with their content in a single optimized query.
    
    Admin only. Returns all modules with content regardless of is_published status.
    Prevents N+1 query problem by fetching all data in one go.
    """
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get all modules
    modules = (
        db.query(Module)
        .filter(Module.course_id == course.id)
        .order_by(Module.order_index)
        .all()
    )
    
    # Get all content for all modules in one query
    module_ids = [m.id for m in modules]
    all_content = (
        db.query(Content)
        .filter(Content.module_id.in_(module_ids))
        .order_by(Content.module_id, Content.order_index)
        .all()
    )
    
    # Group content by module_id
    content_by_module = {}
    for content_item in all_content:
        if content_item.module_id not in content_by_module:
            content_by_module[content_item.module_id] = []
        
        # Parse rich_text_content if present
        item_dict = {
            "id": content_item.id,
            "module_id": content_item.module_id,
            "content_type": content_item.content_type,
            "title": content_item.title,
            "order_index": content_item.order_index,
            "is_published": content_item.is_published,
            "vimeo_video_id": content_item.vimeo_video_id,
            "video_duration": content_item.video_duration,
            "pdf_url": content_item.pdf_url,
            "pdf_filename": content_item.pdf_filename,
            "rich_text_content": None,
            "created_at": content_item.created_at,
            "updated_at": content_item.updated_at
        }
        
        if content_item.rich_text_content:
            try:
                item_dict["rich_text_content"] = json.loads(content_item.rich_text_content)
            except json.JSONDecodeError:
                item_dict["rich_text_content"] = None
        
        content_by_module[content_item.module_id].append(item_dict)
    
    # Build response
    result = []
    for module in modules:
        result.append({
            "id": module.id,
            "course_id": module.course_id,
            "title": module.title,
            "description": module.description,
            "order_index": module.order_index,
            "is_published": module.is_published,
            "created_at": module.created_at,
            "updated_at": module.updated_at,
            "content_items": content_by_module.get(module.id, [])
        })
    
    return result


@router.post("/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    module_data: ModuleCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new module.
    
    Admin only. Creates a module with the specified order_index.
    """
    # Check if order_index is already used
    existing = (
        db.query(Module)
        .filter(
            Module.course_id == module_data.course_id,
            Module.order_index == module_data.order_index
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module with order_index {module_data.order_index} already exists"
        )
    
    # Create module
    new_module = Module(
        course_id=module_data.course_id,
        title=module_data.title,
        description=module_data.description,
        order_index=module_data.order_index,
        is_published=module_data.is_published
    )
    
    db.add(new_module)
    db.commit()
    db.refresh(new_module)
    
    return new_module


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: str,
    module_data: ModuleUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing module.
    
    Admin only. Updates module fields.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if new order_index conflicts
    if module_data.order_index is not None and module_data.order_index != module.order_index:
        existing = (
            db.query(Module)
            .filter(
                Module.course_id == module.course_id,
                Module.order_index == module_data.order_index,
                Module.id != module_id
            )
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Module with order_index {module_data.order_index} already exists"
            )
    
    # Update fields
    if module_data.title is not None:
        module.title = module_data.title
    if module_data.description is not None:
        module.description = module_data.description
    if module_data.order_index is not None:
        module.order_index = module_data.order_index
    if module_data.is_published is not None:
        module.is_published = module_data.is_published
    
    db.commit()
    db.refresh(module)
    
    return module


@router.get("/modules/{module_id}/content", response_model=list[ContentResponse])
async def get_module_content_admin(
    module_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all content for a specific module (including drafts).
    
    Admin only. Returns all content items regardless of is_published status.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    content_items = (
        db.query(Content)
        .filter(Content.module_id == module_id)
        .order_by(Content.order_index)
        .all()
    )
    
    # Parse rich_text_content JSON strings
    result = []
    for item in content_items:
        item_dict = {
            "id": item.id,
            "module_id": item.module_id,
            "content_type": item.content_type,
            "title": item.title,
            "order_index": item.order_index,
            "is_published": item.is_published,
            "vimeo_video_id": item.vimeo_video_id,
            "video_duration": item.video_duration,
            "pdf_url": item.pdf_url,
            "pdf_filename": item.pdf_filename,
            "rich_text_content": None,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        
        if item.rich_text_content:
            try:
                item_dict["rich_text_content"] = json.loads(item.rich_text_content)
            except json.JSONDecodeError:
                item_dict["rich_text_content"] = None
        
        result.append(item_dict)
    
    return result


@router.post("/content", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create new content.
    
    Admin only. Creates content of type video, pdf, or rich_text.
    """
    # Verify module exists
    module = db.query(Module).filter(Module.id == content_data.module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if order_index is already used
    existing = (
        db.query(Content)
        .filter(
            Content.module_id == content_data.module_id,
            Content.order_index == content_data.order_index
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content with order_index {content_data.order_index} already exists in this module"
        )
    
    # Validate content type specific fields
    if content_data.content_type == "video" and not content_data.vimeo_video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vimeo_video_id is required for video content"
        )
    
    # Handle exercise content type
    if content_data.content_type == "exercise":
        # Import exercise service
        from app.services.exercise_service import exercise_service
        
        # Validate exercise data
        if not hasattr(content_data, 'exercise_data') or not content_data.exercise_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="exercise_data is required for exercise content"
            )
        
        exercise_data = content_data.exercise_data
        
        if not exercise_data.get('embed_code'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="embed_code is required for exercise content"
            )
        
        if not exercise_data.get('form_title'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="form_title is required for exercise content"
            )
        
        # Create content first
        new_content = Content(
            module_id=content_data.module_id,
            content_type=content_data.content_type,
            title=content_data.title,
            order_index=content_data.order_index,
            is_published=content_data.is_published
        )
        
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
        
        # Create exercise
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Creating exercise with embed_code length: {len(exercise_data['embed_code'])}")
            logger.info(f"Embed code preview: {exercise_data['embed_code'][:200]}")
            
            exercise = exercise_service.create_exercise(
                db=db,
                content_id=new_content.id,
                embed_code=exercise_data['embed_code'],
                form_title=exercise_data['form_title'],
                allow_multiple_submissions=exercise_data.get('allow_multiple_submissions', False)
            )
            logger.info(f"Exercise created successfully with ID: {exercise.id}")
        except ValueError as e:
            # Rollback content creation if exercise creation fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Exercise creation failed: {str(e)}")
            logger.error(f"Embed code that failed: {exercise_data['embed_code']}")
            
            db.delete(new_content)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        # Create regular content (video, pdf, rich_text)
        new_content = Content(
            module_id=content_data.module_id,
            content_type=content_data.content_type,
            title=content_data.title,
            order_index=content_data.order_index,
            vimeo_video_id=content_data.vimeo_video_id,
            video_duration=content_data.video_duration,
            pdf_filename=content_data.pdf_filename,
            rich_text_content=json.dumps(content_data.rich_text_content) if content_data.rich_text_content else None,
            is_published=content_data.is_published
        )
        
        db.add(new_content)
        db.commit()
        db.refresh(new_content)
    
    # Recalculate progress for all enrollments if content is published
    if new_content.is_published:
        from app.services.progress_service import progress_service
        progress_service.recalculate_all_enrollments(db)
    
    # Build response
    content_dict = {
        "id": new_content.id,
        "module_id": new_content.module_id,
        "content_type": new_content.content_type,
        "title": new_content.title,
        "order_index": new_content.order_index,
        "vimeo_video_id": new_content.vimeo_video_id,
        "video_duration": new_content.video_duration,
        "pdf_url": new_content.pdf_url,
        "pdf_filename": new_content.pdf_filename,
        "rich_text_content": json.loads(new_content.rich_text_content) if new_content.rich_text_content else None,
        "is_published": new_content.is_published,
        "created_at": new_content.created_at,
        "updated_at": new_content.updated_at
    }
    
    # Add exercise data if content type is exercise
    if new_content.content_type == "exercise":
        from app.services.exercise_service import exercise_service
        exercise = exercise_service.get_exercise_by_content_id(db, new_content.id)
        if exercise:
            content_dict["exercise"] = {
                "id": exercise.id,
                "form_id": exercise.form_id,
                "embed_code": exercise.embed_code,
                "form_title": exercise.form_title,
                "allow_multiple_submissions": exercise.allow_multiple_submissions
            }
    
    return ContentResponse(**content_dict)


@router.put("/content/reorder")
async def reorder_content(
    request: ContentReorderRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reorder content items within a module.
    
    Admin only. Updates order_index for multiple content items.
    Expects a request body with 'items' array containing objects with 'id' and 'order_index' fields.
    All content items must belong to the same module.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not request.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content order list cannot be empty"
            )
        
        logger.info(f"Reordering {len(request.items)} content items")
        
        # Extract content IDs
        content_ids = [item.id for item in request.items]
        
        # Fetch all content items
        content_items = db.query(Content).filter(Content.id.in_(content_ids)).all()
        
        if len(content_items) != len(content_ids):
            logger.warning(f"Found {len(content_items)} items but expected {len(content_ids)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more content items not found"
            )
        
        # Verify all content items belong to the same module
        module_ids = set(item.module_id for item in content_items)
        if len(module_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All content items must belong to the same module"
            )
        
        # Create a mapping of content_id to content object
        content_map = {item.id: item for item in content_items}
        
        # Step 1: Set all items to temporary negative order_index to avoid constraint violations
        for i, order_item in enumerate(request.items):
            content_id = order_item.id
            if content_id in content_map:
                content_map[content_id].order_index = -(i + 1)
        
        # Flush to database to apply temporary values
        db.flush()
        
        # Step 2: Update to final order_index values
        for order_item in request.items:
            content_id = order_item.id
            new_order_index = order_item.order_index
            
            if content_id in content_map:
                content_map[content_id].order_index = new_order_index
                logger.info(f"Updated {content_id} to order_index {new_order_index}")
        
        # Commit all changes
        db.commit()
        logger.info("Content reordered successfully")
        
        return {"message": "Content reordered successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering content: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder content: {str(e)}"
        )


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    content_data: ContentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update existing content.
    
    Admin only. Updates content fields.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Check if new order_index conflicts
    if content_data.order_index is not None and content_data.order_index != content.order_index:
        existing = (
            db.query(Content)
            .filter(
                Content.module_id == content.module_id,
                Content.order_index == content_data.order_index,
                Content.id != content_id
            )
            .first()
        )
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content with order_index {content_data.order_index} already exists in this module"
            )
    
    # Track if is_published changed
    is_published_changed = content_data.is_published is not None and content_data.is_published != content.is_published
    
    # Update fields
    if content_data.title is not None:
        content.title = content_data.title
    if content_data.order_index is not None:
        content.order_index = content_data.order_index
    if content_data.vimeo_video_id is not None:
        content.vimeo_video_id = content_data.vimeo_video_id
    if content_data.video_duration is not None:
        content.video_duration = content_data.video_duration
    if content_data.pdf_filename is not None:
        content.pdf_filename = content_data.pdf_filename
    if content_data.rich_text_content is not None:
        content.rich_text_content = json.dumps(content_data.rich_text_content)
    if content_data.is_published is not None:
        content.is_published = content_data.is_published
    
    db.commit()
    db.refresh(content)
    
    # Recalculate progress for all enrollments if is_published changed
    if is_published_changed:
        from app.services.progress_service import progress_service
        progress_service.recalculate_all_enrollments(db)
    
    # Build response
    content_dict = {
        "id": content.id,
        "module_id": content.module_id,
        "content_type": content.content_type,
        "title": content.title,
        "order_index": content.order_index,
        "vimeo_video_id": content.vimeo_video_id,
        "video_duration": content.video_duration,
        "pdf_url": content.pdf_url,
        "pdf_filename": content.pdf_filename,
        "rich_text_content": json.loads(content.rich_text_content) if content.rich_text_content else None,
        "is_published": content.is_published,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }
    
    return ContentResponse(**content_dict)


@router.post("/content/{content_id}/upload-pdf")
async def upload_pdf(
    content_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for content.
    
    Admin only. Uploads PDF to Vercel Blob and updates content record.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    if content.content_type != "pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content type must be 'pdf' to upload PDF files"
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Read file data
    file_data = await file.read()
    
    # Check file size (20MB limit)
    if len(file_data) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 20MB"
        )
    
    # Upload to Vercel Blob
    pdf_url = await storage_service.upload_file(
        file_data=file_data,
        filename=f"content/{content_id}/{file.filename}",
        content_type="application/pdf"
    )
    
    if not pdf_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload PDF"
        )
    
    # Update content record
    content.pdf_url = pdf_url
    content.pdf_filename = file.filename
    
    db.commit()
    
    return {
        "message": "PDF uploaded successfully",
        "pdf_url": pdf_url,
        "filename": file.filename
    }



# User Management Endpoints

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    enrollment_status: Optional[str] = Query(None, description="Filter by enrollment status: enrolled, not_enrolled"),
    registration_date_from: Optional[datetime] = Query(None, description="Filter by registration date from"),
    registration_date_to: Optional[datetime] = Query(None, description="Filter by registration date to"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of users with filtering options.
    
    Admin only. Supports filtering by enrollment status and registration date.
    """
    # Build query
    query = db.query(User).filter(User.role == "student")
    
    # Apply filters
    if enrollment_status == "enrolled":
        query = query.filter(User.is_enrolled == True)
    elif enrollment_status == "not_enrolled":
        query = query.filter(User.is_enrolled == False)
    
    if registration_date_from:
        query = query.filter(User.created_at >= registration_date_from)
    
    if registration_date_to:
        query = query.filter(User.created_at <= registration_date_to)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size)
    offset = (page - 1) * page_size
    
    # Get paginated results
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    return UserListResponse(
        users=[UserListItem.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed user profile including enrollment, progress, payment history, and activity logs.
    
    Admin only.
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get enrollment details
    enrollment = None
    if user.is_enrolled:
        enrollment_record = db.query(Enrollment).filter(Enrollment.user_id == user_id).first()
        if enrollment_record:
            enrollment = EnrollmentDetail.model_validate(enrollment_record)
    
    # Get payment history
    payments = db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()
    payment_history = [PaymentHistoryItem.model_validate(payment) for payment in payments]
    
    # Get activity logs
    activity_events = (
        db.query(AnalyticsEvent)
        .filter(AnalyticsEvent.user_id == user_id)
        .order_by(AnalyticsEvent.created_at.desc())
        .limit(50)
        .all()
    )
    
    activity_logs = []
    for event in activity_events:
        metadata = None
        if event.event_metadata:
            try:
                metadata = json.loads(event.event_metadata)
            except:
                metadata = None
        
        activity_logs.append(ActivityLogItem(
            event_type=event.event_type,
            created_at=event.created_at,
            metadata=metadata
        ))
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        profile_image_url=user.profile_image_url,
        role=user.role,
        is_verified=user.is_verified,
        is_enrolled=user.is_enrolled,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        enrollment=enrollment,
        payment_history=payment_history,
        activity_logs=activity_logs
    )


# Admin Settings Endpoints

@router.get("/settings/profile", response_model=AdminProfileResponse)
async def get_admin_profile(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get admin profile settings.
    
    Admin only. Returns admin user details and instructor information from course.
    """
    # Get course to fetch instructor bio and image
    course = db.query(Course).first()
    
    instructor_bio = None
    instructor_image_url = None
    
    if course:
        instructor_bio = course.instructor_bio
        instructor_image_url = course.instructor_image_url
    
    return AdminProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        profile_image_url=current_user.profile_image_url,
        role=current_user.role,
        instructor_bio=instructor_bio,
        instructor_image_url=instructor_image_url
    )


@router.put("/settings/profile", response_model=AdminProfileResponse)
async def update_admin_profile(
    full_name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    instructor_bio: Optional[str] = Form(None),
    instructor_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update admin profile settings.
    
    Admin only. Updates admin user details and instructor information in course.
    Supports file upload for instructor image.
    """
    # Update user fields
    if full_name is not None:
        current_user.full_name = full_name
    
    if email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(
            User.email == email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        current_user.email = email
    
    if phone_number is not None:
        current_user.phone_number = phone_number
    
    if password is not None and len(password) > 0:
        current_user.password_hash = get_password_hash(password)
    
    # Handle instructor image upload
    instructor_image_url = None
    if instructor_image is not None:
        # Validate file type
        if not instructor_image.content_type or not instructor_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Read file data
        file_data = await instructor_image.read()
        
        # Check file size (5MB limit)
        if len(file_data) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must not exceed 5MB"
            )
        
        # Upload to Vercel Blob
        instructor_image_url = await storage_service.upload_file(
            file_data=file_data,
            filename=f"instructor_images/{current_user.id}/{instructor_image.filename}",
            content_type=instructor_image.content_type
        )
        
        if not instructor_image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload instructor image"
            )
        
        current_user.profile_image_url = instructor_image_url
    
    # Update course instructor fields
    course = db.query(Course).first()
    
    if course:
        if instructor_bio is not None:
            course.instructor_bio = instructor_bio
        
        if instructor_image_url is not None:
            course.instructor_image_url = instructor_image_url
        
        # Update instructor name if full name changed
        if full_name is not None:
            course.instructor_name = full_name
    
    db.commit()
    db.refresh(current_user)
    
    if course:
        db.refresh(course)
    
    # Build response
    instructor_bio_response = course.instructor_bio if course else None
    instructor_image_url_response = course.instructor_image_url if course else None
    
    return AdminProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone_number=current_user.phone_number,
        profile_image_url=current_user.profile_image_url,
        role=current_user.role,
        instructor_bio=instructor_bio_response,
        instructor_image_url=instructor_image_url_response
    )


@router.get("/settings/course", response_model=CourseSettingsResponse)
async def get_course_settings(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get course settings.
    
    Admin only. Returns course configuration.
    """
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return CourseSettingsResponse.model_validate(course)


@router.put("/settings/course", response_model=CourseSettingsResponse)
async def update_course_settings(
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    instructor_name: Optional[str] = Form(None),
    instructor_bio: Optional[str] = Form(None),
    is_published: Optional[str] = Form(None),
    thumbnail: Optional[UploadFile] = File(None),
    instructor_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update course settings.
    
    Admin only. Updates course configuration including title, description, price, and visibility.
    Supports file uploads for thumbnail and instructor image.
    """
    course = db.query(Course).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Update fields
    if title is not None:
        course.title = title
    
    if description is not None:
        course.description = description
    
    if price is not None:
        try:
            course.price = float(price)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid price format"
            )
    
    if instructor_name is not None:
        course.instructor_name = instructor_name
    
    if instructor_bio is not None:
        course.instructor_bio = instructor_bio
    
    if is_published is not None:
        course.is_published = is_published.lower() == "true"
    
    # Handle thumbnail upload
    if thumbnail is not None:
        # Validate file type
        if not thumbnail.content_type or not thumbnail.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thumbnail must be an image"
            )
        
        # Read file data
        file_data = await thumbnail.read()
        
        # Check file size (5MB limit)
        if len(file_data) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thumbnail size must not exceed 5MB"
            )
        
        # Upload to Vercel Blob
        thumbnail_url = await storage_service.upload_file(
            file_data=file_data,
            filename=f"course_thumbnails/{course.id}/{thumbnail.filename}",
            content_type=thumbnail.content_type
        )
        
        if not thumbnail_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload thumbnail"
            )
        
        course.thumbnail_url = thumbnail_url
    
    # Handle instructor image upload
    if instructor_image is not None:
        # Validate file type
        if not instructor_image.content_type or not instructor_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instructor image must be an image"
            )
        
        # Read file data
        file_data = await instructor_image.read()
        
        # Check file size (5MB limit)
        if len(file_data) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instructor image size must not exceed 5MB"
            )
        
        # Upload to Vercel Blob
        instructor_image_url = await storage_service.upload_file(
            file_data=file_data,
            filename=f"instructor_images/{course.id}/{instructor_image.filename}",
            content_type=instructor_image.content_type
        )
        
        if not instructor_image_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload instructor image"
            )
        
        course.instructor_image_url = instructor_image_url
    
    db.commit()
    db.refresh(course)
    
    return CourseSettingsResponse.model_validate(course)



# Delete Endpoints

@router.delete("/modules/{module_id}")
async def delete_module(
    module_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a module and all its content.
    
    Admin only. Permanently deletes the module and all associated content items.
    This action cannot be undone.
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    try:
        # Clear any enrollment references to this module before deletion
        from app.models.enrollment import Enrollment
        db.query(Enrollment).filter(
            Enrollment.last_accessed_module_id == module_id
        ).update({"last_accessed_module_id": None})
        
        # Delete the module (cascade will handle content deletion)
        db.delete(module)
        db.commit()
        
        return {"message": "Module deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting module: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete module: {str(e)}"
        )


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a content item.
    
    Admin only. Permanently deletes the content item.
    This action cannot be undone.
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Track if content was published before deletion
    was_published = content.is_published
    
    # Delete the content
    db.delete(content)
    db.commit()
    
    # Recalculate progress for all enrollments if deleted content was published
    if was_published:
        from app.services.progress_service import progress_service
        progress_service.recalculate_all_enrollments(db)
    
    return {"message": "Content deleted successfully"}


# Payment Management Endpoints

@router.get("/payments", response_model=list[PaymentListItem])
async def get_payments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of payments with user information.
    
    Admin only. Returns all payments with optional status filtering.
    Optimized to avoid N+1 queries.
    """
    # Single query with JOIN to get payment and user data together
    query = (
        db.query(Payment, User)
        .join(User, Payment.user_id == User.id)
    )
    
    if status:
        query = query.filter(Payment.status == status)
    
    # Get paginated results
    offset = (page - 1) * page_size
    results = query.order_by(Payment.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Build response with user info (no additional queries needed)
    payment_list = []
    for payment, user in results:
        payment_list.append(PaymentListItem(
            id=payment.id,
            user_id=payment.user_id,
            user_name=user.full_name,
            user_email=user.email,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            payment_method=payment.payment_method or "N/A",
            ipay_transaction_id=payment.ipay_transaction_id or "Pending",
            ipay_reference=payment.ipay_reference or "N/A",
            created_at=payment.created_at
        ))
    
    return payment_list
