from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.dependencies import get_db, get_current_admin_user, get_current_enrolled_user
from app.models.user import User
from app.models.exercise import Exercise
from app.models.exercise_submission import ExerciseSubmission
from app.models.enrollment import Enrollment
from app.schemas.exercise import (
    ExerciseCreateRequest,
    ExerciseUpdateEmbedRequest,
    ExerciseResponse,
    ExerciseSubmissionResponse,
    ExerciseSubmissionsListResponse
)
from app.services.exercise_service import exercise_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["exercises"]
)


# Admin endpoints

@router.post("/admin/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new exercise with 123FormBuilder embed code.
    
    Admin only. Creates an exercise linked to a content item.
    Validates embed code and extracts form ID.
    
    Requirements: 1.3, 5.1
    """
    try:
        # Create exercise using service
        exercise = exercise_service.create_exercise(
            db=db,
            content_id=exercise_data.content_id,
            embed_code=exercise_data.embed_code,
            form_title=exercise_data.form_title,
            allow_multiple_submissions=exercise_data.allow_multiple_submissions
        )
        
        logger.info(
            "Exercise created",
            extra={
                "exercise_id": exercise.id,
                "content_id": exercise.content_id,
                "form_id": exercise.form_id,
                "admin_user_id": current_user.id
            }
        )
        
        return ExerciseResponse.model_validate(exercise)
        
    except ValueError as e:
        # Validation errors from service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to create exercise",
            extra={
                "error": str(e),
                "content_id": exercise_data.content_id,
                "admin_user_id": current_user.id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exercise"
        )


@router.get("/admin/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise_details(
    exercise_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get exercise details by ID.
    
    Admin only. Returns full exercise information including embed code.
    
    Requirements: 5.1
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    return ExerciseResponse.model_validate(exercise)


@router.put("/admin/exercises/{exercise_id}/embed", response_model=ExerciseResponse)
async def update_exercise_embed(
    exercise_id: str,
    update_data: ExerciseUpdateEmbedRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update exercise embed code.
    
    Admin only. Updates the 123FormBuilder embed code and optionally the form title.
    Preserves existing submissions. Logs the update for audit trail.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    try:
        # Get exercise to check if it exists
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exercise with ID {exercise_id} not found"
            )
        
        # Store old form_id for logging
        old_form_id = exercise.form_id
        
        # Update exercise using service
        updated_exercise = exercise_service.update_exercise_embed(
            db=db,
            exercise_id=exercise_id,
            embed_code=update_data.embed_code,
            form_title=update_data.form_title
        )
        
        # Log the update for audit trail (Requirement 5.5)
        logger.info(
            "Exercise embed code updated",
            extra={
                "exercise_id": exercise_id,
                "old_form_id": old_form_id,
                "new_form_id": updated_exercise.form_id,
                "form_id_changed": old_form_id != updated_exercise.form_id,
                "admin_user_id": current_user.id,
                "timestamp": updated_exercise.updated_at.isoformat()
            }
        )
        
        # If form_id changed, log versioning information (Requirement 5.3)
        if old_form_id != updated_exercise.form_id:
            submission_count = db.query(ExerciseSubmission).filter(
                ExerciseSubmission.exercise_id == exercise_id
            ).count()
            
            logger.info(
                "Exercise form_id changed - historical submissions preserved",
                extra={
                    "exercise_id": exercise_id,
                    "old_form_id": old_form_id,
                    "new_form_id": updated_exercise.form_id,
                    "preserved_submissions_count": submission_count,
                    "admin_user_id": current_user.id
                }
            )
        
        return ExerciseResponse.model_validate(updated_exercise)
        
    except ValueError as e:
        # Validation errors from service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update exercise embed code",
            extra={
                "error": str(e),
                "exercise_id": exercise_id,
                "admin_user_id": current_user.id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exercise"
        )


@router.delete("/admin/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete an exercise.
    
    Admin only. Deletes the exercise and all associated submissions.
    This action cannot be undone.
    
    Requirements: 5.1, 5.4
    """
    # Check if exercise exists and get submission count for logging
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    submission_count = db.query(ExerciseSubmission).filter(
        ExerciseSubmission.exercise_id == exercise_id
    ).count()
    
    # Delete exercise (submissions will be cascade deleted)
    success = exercise_service.delete_exercise(db=db, exercise_id=exercise_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    logger.info(
        "Exercise deleted",
        extra={
            "exercise_id": exercise_id,
            "deleted_submissions_count": submission_count,
            "admin_user_id": current_user.id
        }
    )
    
    return None


@router.get("/admin/exercises/{exercise_id}/submissions", response_model=ExerciseSubmissionsListResponse)
async def get_exercise_submissions(
    exercise_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all submissions for an exercise with statistics.
    
    Admin only. Returns list of submissions with user details and calculates
    completion statistics including completion rate.
    
    Requirements: 4.1, 4.2, 4.3, 4.5, 5.2
    """
    # Verify exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    # Get all submissions with user details
    submissions = db.query(ExerciseSubmission, User).join(
        User, ExerciseSubmission.user_id == User.id
    ).filter(
        ExerciseSubmission.exercise_id == exercise_id
    ).order_by(
        ExerciseSubmission.submitted_at.desc()
    ).all()
    
    # Build submission response list
    submission_responses = []
    for submission, user in submissions:
        submission_responses.append(ExerciseSubmissionResponse(
            id=submission.id,
            exercise_id=submission.exercise_id,
            user_id=submission.user_id,
            user_name=user.full_name,
            user_email=user.email,
            form_submission_id=submission.form_submission_id,
            submitted_at=submission.submitted_at,
            webhook_received_at=submission.webhook_received_at
        ))
    
    # Calculate statistics
    total_submissions = len(submission_responses)
    unique_users = len(set(s.user_id for s in submission_responses))
    
    # Calculate completion rate (unique users who submitted / total enrolled users)
    total_enrolled = db.query(User).filter(User.is_enrolled == True).count()
    completion_rate = (unique_users / total_enrolled * 100) if total_enrolled > 0 else 0.0
    
    return ExerciseSubmissionsListResponse(
        submissions=submission_responses,
        total_submissions=total_submissions,
        unique_users=unique_users,
        completion_rate=round(completion_rate, 2),
        exercise_info=ExerciseResponse.model_validate(exercise)
    )


# Student endpoints

@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Get exercise embed code for student view.
    
    Enrolled students only. Returns exercise information including embed code
    for rendering in the course interface.
    
    Requirements: 2.1
    """
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    return ExerciseResponse.model_validate(exercise)


@router.get("/exercises/{exercise_id}/status")
async def get_exercise_status(
    exercise_id: str,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Check exercise completion status for current user.
    
    Enrolled students only. Returns whether the user has completed the exercise.
    
    Requirements: 2.4
    """
    # Verify exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exercise with ID {exercise_id} not found"
        )
    
    # Check completion status
    is_completed = exercise_service.check_completion_status(
        db=db,
        exercise_id=exercise_id,
        user_id=current_user.id
    )
    
    # Get submission details if completed
    submission = None
    if is_completed:
        submission_record = exercise_service.get_user_submission(
            db=db,
            exercise_id=exercise_id,
            user_id=current_user.id
        )
        if submission_record:
            submission = {
                "submitted_at": submission_record.submitted_at,
                "form_submission_id": submission_record.form_submission_id
            }
    
    return {
        "exercise_id": exercise_id,
        "user_id": current_user.id,
        "is_completed": is_completed,
        "submission": submission
    }
