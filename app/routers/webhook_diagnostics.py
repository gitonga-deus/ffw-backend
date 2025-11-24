"""
Diagnostic endpoints for 123FormBuilder webhook integration.

These endpoints help admins diagnose and troubleshoot webhook issues.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import logging

from app.dependencies import get_db, get_current_admin_user
from app.models.user import User
from app.models.exercise import Exercise
from app.models.exercise_submission import ExerciseSubmission
from app.models.enrollment import Enrollment
from app.models.content import Content
from app.models.user_progress import UserProgress

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webhooks/diagnostics",
    tags=["webhook-diagnostics"]
)


@router.get("/form/{form_id}")
async def diagnose_form(
    form_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Diagnose a specific form_id configuration.
    
    Returns detailed information about:
    - Whether the exercise exists
    - Associated content and module
    - Submission count
    - Common issues
    """
    logger.info(
        "Admin diagnosing form",
        extra={
            "admin_user_id": current_user.id,
            "form_id": form_id
        }
    )
    
    # Find exercise
    exercise = db.query(Exercise).filter(Exercise.form_id == form_id).first()
    
    if not exercise:
        return {
            "status": "error",
            "form_id": form_id,
            "exercise_found": False,
            "message": f"No exercise found with form_id: {form_id}",
            "suggestions": [
                "Verify the form_id is correct",
                "Check if the exercise was created in the LMS",
                "Ensure the embed code was properly parsed",
                "Try creating the exercise again with the correct embed code"
            ]
        }
    
    # Get associated content
    content = db.query(Content).filter(Content.id == exercise.content_id).first()
    
    if not content:
        return {
            "status": "error",
            "form_id": form_id,
            "exercise_found": True,
            "exercise_id": exercise.id,
            "content_found": False,
            "message": "Exercise exists but associated content not found (data integrity issue)",
            "suggestions": [
                "This is a database integrity issue",
                "Contact system administrator",
                "The exercise may need to be recreated"
            ]
        }
    
    # Get submission count
    submission_count = db.query(func.count(ExerciseSubmission.id)).filter(
        ExerciseSubmission.exercise_id == exercise.id
    ).scalar()
    
    # Get unique users who submitted
    unique_submitters = db.query(func.count(ExerciseSubmission.user_id.distinct())).filter(
        ExerciseSubmission.exercise_id == exercise.id
    ).scalar()
    
    # Get progress records for this content
    progress_count = db.query(func.count(UserProgress.id)).filter(
        UserProgress.content_id == content.id,
        UserProgress.is_completed == True
    ).scalar()
    
    return {
        "status": "success",
        "form_id": form_id,
        "exercise_found": True,
        "exercise": {
            "id": exercise.id,
            "form_id": exercise.form_id,
            "form_title": exercise.form_title,
            "allow_multiple_submissions": exercise.allow_multiple_submissions,
            "created_at": exercise.created_at.isoformat(),
            "updated_at": exercise.updated_at.isoformat()
        },
        "content": {
            "id": content.id,
            "title": content.title,
            "content_type": content.content_type,
            "module_id": content.module_id,
            "order_index": content.order_index,
            "is_published": content.is_published
        },
        "statistics": {
            "total_submissions": submission_count,
            "unique_submitters": unique_submitters,
            "progress_records": progress_count
        },
        "health_check": {
            "content_published": content.is_published,
            "submissions_match_progress": submission_count == progress_count,
            "has_submissions": submission_count > 0
        },
        "message": "Exercise configuration looks good" if content.is_published else "Warning: Content is not published"
    }


@router.get("/user/{email}")
async def diagnose_user(
    email: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Diagnose a specific user's webhook eligibility.
    
    Returns detailed information about:
    - Whether the user exists
    - Enrollment status
    - Submission history
    - Common issues
    """
    logger.info(
        "Admin diagnosing user",
        extra={
            "admin_user_id": current_user.id,
            "target_email": email
        }
    )
    
    # Find user
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user:
        return {
            "status": "error",
            "email": email,
            "user_found": False,
            "message": f"No user found with email: {email}",
            "suggestions": [
                "Verify the email address is correct",
                "Check if the user has registered in the LMS",
                "Ensure the email in the form matches the LMS registration email exactly",
                "Check for typos or case sensitivity issues"
            ]
        }
    
    # Check enrollment
    enrollment = db.query(Enrollment).filter(Enrollment.user_id == user.id).first()
    
    if not enrollment:
        return {
            "status": "error",
            "email": email,
            "user_found": True,
            "user_id": user.id,
            "enrolled": False,
            "message": f"User {email} exists but is not enrolled in the course",
            "user_details": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_verified": user.is_verified,
                "is_enrolled": user.is_enrolled,
                "role": user.role
            },
            "suggestions": [
                "User needs to complete payment and enrollment",
                "Check payment status",
                "Verify enrollment was processed correctly"
            ]
        }
    
    # Get submission count
    submission_count = db.query(func.count(ExerciseSubmission.id)).filter(
        ExerciseSubmission.user_id == user.id
    ).scalar()
    
    # Get completed content count
    completed_content = db.query(func.count(UserProgress.id)).filter(
        UserProgress.user_id == user.id,
        UserProgress.is_completed == True
    ).scalar()
    
    # Get total published content
    total_content = db.query(func.count(Content.id)).filter(
        Content.is_published == True
    ).scalar()
    
    return {
        "status": "success",
        "email": email,
        "user_found": True,
        "enrolled": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "is_enrolled": user.is_enrolled,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        },
        "enrollment": {
            "id": enrollment.id,
            "enrolled_at": enrollment.enrolled_at.isoformat(),
            "progress_percentage": float(enrollment.progress_percentage),
            "completed_at": enrollment.completed_at.isoformat() if enrollment.completed_at else None,
            "last_accessed_at": enrollment.last_accessed_at.isoformat() if enrollment.last_accessed_at else None
        },
        "statistics": {
            "exercise_submissions": submission_count,
            "completed_content": completed_content,
            "total_content": total_content,
            "progress_percentage": float(enrollment.progress_percentage)
        },
        "health_check": {
            "can_receive_webhooks": True,
            "has_submissions": submission_count > 0,
            "has_progress": completed_content > 0
        },
        "message": "User is properly configured to receive webhooks"
    }


@router.get("/submission/{submission_id}")
async def diagnose_submission(
    submission_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Diagnose a specific submission by form_submission_id.
    
    Returns detailed information about:
    - Whether the submission was recorded
    - Associated user and exercise
    - Progress update status
    """
    logger.info(
        "Admin diagnosing submission",
        extra={
            "admin_user_id": current_user.id,
            "submission_id": submission_id
        }
    )
    
    # Find submission
    submission = db.query(ExerciseSubmission).filter(
        ExerciseSubmission.form_submission_id == submission_id
    ).first()
    
    if not submission:
        return {
            "status": "error",
            "submission_id": submission_id,
            "submission_found": False,
            "message": f"No submission found with form_submission_id: {submission_id}",
            "suggestions": [
                "The webhook may not have been received",
                "Check 123FormBuilder webhook logs for delivery status",
                "Verify the webhook URL is correct",
                "Check backend logs for webhook errors",
                "Try resubmitting the form"
            ]
        }
    
    # Get associated data
    exercise = db.query(Exercise).filter(Exercise.id == submission.exercise_id).first()
    user = db.query(User).filter(User.id == submission.user_id).first()
    
    if not exercise or not user:
        return {
            "status": "error",
            "submission_id": submission_id,
            "submission_found": True,
            "message": "Submission exists but associated data is missing (data integrity issue)",
            "submission": {
                "id": submission.id,
                "exercise_id": submission.exercise_id,
                "user_id": submission.user_id,
                "submitted_at": submission.submitted_at.isoformat(),
                "webhook_received_at": submission.webhook_received_at.isoformat()
            }
        }
    
    # Get content
    content = db.query(Content).filter(Content.id == exercise.content_id).first()
    
    # Check if progress was updated
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == user.id,
        UserProgress.content_id == exercise.content_id
    ).first()
    
    return {
        "status": "success",
        "submission_id": submission_id,
        "submission_found": True,
        "submission": {
            "id": submission.id,
            "form_submission_id": submission.form_submission_id,
            "submitted_at": submission.submitted_at.isoformat(),
            "webhook_received_at": submission.webhook_received_at.isoformat(),
            "processing_delay_seconds": (submission.webhook_received_at - submission.submitted_at).total_seconds()
        },
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        },
        "exercise": {
            "id": exercise.id,
            "form_id": exercise.form_id,
            "form_title": exercise.form_title
        },
        "content": {
            "id": content.id if content else None,
            "title": content.title if content else None,
            "content_type": content.content_type if content else None
        } if content else None,
        "progress": {
            "exists": progress is not None,
            "is_completed": progress.is_completed if progress else False,
            "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None
        },
        "health_check": {
            "submission_recorded": True,
            "progress_updated": progress is not None and progress.is_completed,
            "content_exists": content is not None
        },
        "message": "Submission processed successfully" if (progress and progress.is_completed) else "Warning: Progress may not have been updated"
    }


@router.get("/overview")
async def webhook_overview(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get an overview of webhook system health.
    
    Returns statistics about:
    - Total exercises configured
    - Total submissions received
    - Recent webhook activity
    - System health indicators
    """
    logger.info(
        "Admin viewing webhook overview",
        extra={"admin_user_id": current_user.id}
    )
    
    # Count exercises
    total_exercises = db.query(func.count(Exercise.id)).scalar()
    
    # Count submissions
    total_submissions = db.query(func.count(ExerciseSubmission.id)).scalar()
    
    # Count unique users who submitted
    unique_submitters = db.query(func.count(ExerciseSubmission.user_id.distinct())).scalar()
    
    # Get recent submissions (last 10)
    recent_submissions = db.query(
        ExerciseSubmission,
        User.email,
        User.full_name,
        Exercise.form_title
    ).join(
        User, ExerciseSubmission.user_id == User.id
    ).join(
        Exercise, ExerciseSubmission.exercise_id == Exercise.id
    ).order_by(
        ExerciseSubmission.webhook_received_at.desc()
    ).limit(10).all()
    
    recent_list = []
    for submission, email, full_name, form_title in recent_submissions:
        recent_list.append({
            "submission_id": submission.id,
            "form_submission_id": submission.form_submission_id,
            "user_email": email,
            "user_name": full_name,
            "form_title": form_title,
            "submitted_at": submission.submitted_at.isoformat(),
            "webhook_received_at": submission.webhook_received_at.isoformat()
        })
    
    # Count enrolled users
    total_enrolled = db.query(func.count(Enrollment.id)).scalar()
    
    # Calculate completion rate
    completion_rate = (unique_submitters / total_enrolled * 100) if total_enrolled > 0 else 0
    
    return {
        "status": "success",
        "statistics": {
            "total_exercises": total_exercises,
            "total_submissions": total_submissions,
            "unique_submitters": unique_submitters,
            "total_enrolled_users": total_enrolled,
            "completion_rate": round(completion_rate, 2)
        },
        "recent_submissions": recent_list,
        "health_check": {
            "exercises_configured": total_exercises > 0,
            "receiving_webhooks": total_submissions > 0,
            "users_submitting": unique_submitters > 0
        },
        "message": "Webhook system is operational" if total_submissions > 0 else "No submissions received yet"
    }
