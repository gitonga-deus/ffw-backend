from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import ValidationError
from datetime import datetime
import hmac
import hashlib
import logging
import json

from app.dependencies import get_db, get_current_admin_user
from app.config import settings
from app.schemas.webhook import FormBuilderWebhookPayload, WebhookResponse
from app.services.exercise_service import exercise_service
from app.services.progress_service import progress_service
from app.services.certificate_service import certificate_service
from app.services.email_service import email_service
from app.models.user import User
from app.models.exercise import Exercise
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.content import Content

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"]
)


def validate_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    """
    Validate webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body bytes
        signature: Signature from webhook header
        secret: Shared secret key
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures (constant-time comparison to prevent timing attacks)
    return hmac.compare_digest(signature, expected_signature)


async def process_exercise_submission(
    db: Session,
    payload: FormBuilderWebhookPayload
) -> dict:
    """
    Process exercise submission from 123FormBuilder webhook.
    
    This is the core business logic for handling form submissions.
    It's separated from the HTTP handler for easier testing and clarity.
    
    Steps:
    1. Validate form_id exists in database
    2. Find and validate user by email
    3. Verify user is enrolled
    4. Record submission (idempotent - won't duplicate)
    5. Update user progress for the content
    6. Recalculate enrollment progress
    7. Check for course completion and trigger certificate
    
    Args:
        db: Database session
        payload: Validated webhook payload
        
    Returns:
        dict with processing results
        
    Raises:
        HTTPException: For validation errors or business logic failures
    """
    logger.info(
        "Processing exercise submission webhook",
        extra={
            "form_id": payload.form_id,
            "submission_id": payload.submission_id,
            "user_email": payload.user_email
        }
    )
    
    # Step 1: Find exercise by form_id
    exercise = None
    
    if payload.form_id:
        exercise = db.query(Exercise).filter(Exercise.form_id == payload.form_id).first()
    
    # If form_id not provided or exercise not found, try to find from user's enrollment
    if not exercise:
        logger.info(
            "Attempting to find exercise from user's enrollment",
            extra={
                "user_email": payload.user_email,
                "form_id_provided": payload.form_id
            }
        )
        
        # Find user first
        user = db.query(User).filter(User.email == payload.user_email.lower()).first()
        if user:
            # Get user's enrollment
            enrollment = db.query(Enrollment).filter(Enrollment.user_id == user.id).first()
            if enrollment and enrollment.last_accessed_module_id:
                # Find exercises in the last accessed module
                exercises_in_module = db.query(Exercise).join(
                    Content, Exercise.content_id == Content.id
                ).filter(
                    Content.module_id == enrollment.last_accessed_module_id,
                    Content.content_type == 'exercise',
                    Content.is_published == True
                ).all()
                
                if len(exercises_in_module) == 1:
                    # Only one exercise in module, use it
                    exercise = exercises_in_module[0]
                    logger.info(
                        "Found exercise from user's last accessed module",
                        extra={
                            "exercise_id": exercise.id,
                            "form_id": exercise.form_id
                        }
                    )
    
    if not exercise:
        logger.warning(
            "Exercise not found",
            extra={
                "form_id": payload.form_id,
                "submission_id": payload.submission_id,
                "user_email": payload.user_email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No exercise found. Please ensure: 1) The exercise was created in the LMS, 2) form_id is provided in the webhook URL, or 3) The student has accessed the exercise module."
        )
    
    # Get the content associated with this exercise
    content = db.query(Content).filter(Content.id == exercise.content_id).first()
    if not content:
        logger.error(
            "Content not found for exercise",
            extra={
                "exercise_id": exercise.id,
                "content_id": exercise.content_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Exercise configuration error: associated content not found"
        )
    
    logger.info(
        "Found exercise and content",
        extra={
            "exercise_id": exercise.id,
            "content_id": content.id,
            "content_title": content.title,
            "module_id": content.module_id
        }
    )
    
    # Step 2: Find user by email
    user = db.query(User).filter(User.email == payload.user_email.lower()).first()
    if not user:
        logger.warning(
            "User not found for email",
            extra={
                "user_email": payload.user_email,
                "form_id": payload.form_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No user found with email: {payload.user_email}. Please ensure the student is registered in the LMS."
        )
    
    # Step 3: Verify user is enrolled
    enrollment = db.query(Enrollment).filter(Enrollment.user_id == user.id).first()
    if not enrollment:
        logger.warning(
            "User not enrolled",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "form_id": payload.form_id
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {payload.user_email} is not enrolled in the course. Please complete enrollment first."
        )
    
    logger.info(
        "User validated and enrolled",
        extra={
            "user_id": user.id,
            "user_email": user.email,
            "enrollment_id": enrollment.id
        }
    )
    
    # Step 4: Parse submitted_at timestamp
    try:
        submitted_at = datetime.fromisoformat(payload.submitted_at.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        logger.warning(
            "Failed to parse submitted_at timestamp, using current time",
            extra={
                "submitted_at": payload.submitted_at,
                "error": str(e)
            }
        )
        submitted_at = datetime.utcnow()
    
    # Step 5: Record submission (idempotent)
    try:
        submission = exercise_service.record_submission(
            db=db,
            exercise_id=exercise.id,
            user_id=user.id,
            form_submission_id=payload.submission_id,
            submission_data=payload.responses,
            submitted_at=submitted_at
        )
        
        logger.info(
            "Exercise submission recorded",
            extra={
                "submission_id": submission.id,
                "exercise_id": exercise.id,
                "user_id": user.id,
                "form_submission_id": payload.submission_id
            }
        )
    except Exception as e:
        logger.error(
            "Failed to record submission",
            extra={
                "error": str(e),
                "exercise_id": exercise.id,
                "user_id": user.id
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record submission: {str(e)}"
        )
    
    # Step 6: Update user progress for this content
    from app.schemas.progress import ProgressUpdateRequest
    
    try:
        progress_data = ProgressUpdateRequest(
            is_completed=True,
            time_spent=0,  # Exercise time is tracked in 123FormBuilder
            last_position=None
        )
        
        progress = progress_service.update_progress(
            db=db,
            user_id=user.id,
            content_id=content.id,
            progress_data=progress_data
        )
        
        logger.info(
            "User progress updated for exercise",
            extra={
                "user_id": user.id,
                "content_id": content.id,
                "progress_id": progress.id,
                "is_completed": progress.is_completed
            }
        )
    except Exception as e:
        logger.error(
            "Failed to update progress",
            extra={
                "error": str(e),
                "user_id": user.id,
                "content_id": content.id
            },
            exc_info=True
        )
        # Don't fail the webhook if progress update fails
        # The submission is already recorded
        logger.warning("Continuing despite progress update failure")
    
    # Step 7: Check if course is completed
    try:
        is_course_completed = progress_service.check_course_completion(
            db=db,
            user_id=user.id
        )
        
        logger.info(
            "Course completion check",
            extra={
                "user_id": user.id,
                "is_completed": is_course_completed
            }
        )
        
        if is_course_completed:
            # Mark course as completed
            progress_service.mark_course_completed(
                db=db,
                user_id=user.id
            )
            
            logger.info(
                "Course marked as completed",
                extra={
                    "user_id": user.id,
                    "enrollment_id": enrollment.id
                }
            )
            
            # Get the course
            course = db.query(Course).first()
            
            if course:
                # Check if certificate already exists
                from app.models.certificate import Certificate
                existing_cert = db.query(Certificate).filter(
                    Certificate.user_id == user.id
                ).first()
                
                if not existing_cert:
                    # Generate certificate
                    try:
                        certificate = await certificate_service.generate_certificate(
                            db=db,
                            user=user,
                            course=course
                        )
                        
                        logger.info(
                            "Certificate generated",
                            extra={
                                "user_id": user.id,
                                "certificate_id": certificate.id,
                                "certification_id": certificate.certification_id
                            }
                        )
                        
                        # Send course completion email
                        try:
                            await email_service.send_course_completion_email(
                                to=user.email,
                                full_name=user.full_name,
                                certificate_url=certificate.certificate_url,
                                cert_id=certificate.certification_id
                            )
                            
                            logger.info(
                                "Course completion email sent",
                                extra={
                                    "user_id": user.id,
                                    "email": user.email
                                }
                            )
                        except Exception as e:
                            logger.error(
                                "Failed to send completion email",
                                extra={
                                    "error": str(e),
                                    "user_id": user.id
                                },
                                exc_info=True
                            )
                            # Don't fail webhook if email fails
                    except Exception as e:
                        logger.error(
                            "Failed to generate certificate",
                            extra={
                                "error": str(e),
                                "user_id": user.id
                            },
                            exc_info=True
                        )
                        # Don't fail webhook if certificate generation fails
                else:
                    logger.info(
                        "Certificate already exists for user",
                        extra={
                            "user_id": user.id,
                            "certificate_id": existing_cert.id
                        }
                    )
    except Exception as e:
        logger.error(
            "Error during course completion check",
            extra={
                "error": str(e),
                "user_id": user.id
            },
            exc_info=True
        )
        # Don't fail webhook if completion check fails
    
    # Return success response
    return {
        "status": "success",
        "message": "Exercise submission processed successfully",
        "submission_id": submission.id,
        "user_id": user.id,
        "exercise_id": exercise.id,
        "content_id": content.id,
        "progress_updated": True,
        "course_completed": is_course_completed if 'is_course_completed' in locals() else False
    }





@router.post("/123formbuilder", response_model=WebhookResponse)
async def handle_123formbuilder_webhook(
    request: Request,
    form_id: Optional[str] = None,
    x_formbuilder_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Receive and process 123FormBuilder webhook notifications.
    
    This endpoint is called by 123FormBuilder when a student submits a form.
    It validates the webhook signature, processes the submission data,
    and updates student progress.
    
    Expected payload:
    {
        "form_id": "12345",
        "submission_id": "67890",
        "user_email": "student@example.com",
        "submitted_at": "2025-01-01T12:00:00Z",
        "responses": {...}
    }
    
    Returns:
        200 OK: Webhook processed successfully
        401 Unauthorized: Invalid webhook signature
        400 Bad Request: Invalid payload
        404 Not Found: User or exercise not found
        500 Internal Server Error: Processing error
    """
    # Read raw body for signature validation and logging
    body = await request.body()
    
    logger.info(
        "Received 123FormBuilder webhook",
        extra={
            "content_length": len(body),
            "ip_address": request.client.host if request.client else None,
            "signature_provided": bool(x_formbuilder_signature)
        }
    )
    
    # Validate webhook signature if secret is configured
    webhook_secret = getattr(settings, 'formbuilder_webhook_secret', None)
    if webhook_secret:
        if not validate_webhook_signature(body, x_formbuilder_signature, webhook_secret):
            logger.warning(
                "Webhook signature validation failed",
                extra={
                    "signature_provided": bool(x_formbuilder_signature),
                    "ip_address": request.client.host if request.client else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        logger.info("Webhook signature validated successfully")
    else:
        logger.warning("Webhook signature validation is disabled (no secret configured)")
    
    # Parse and validate JSON payload
    try:
        payload_dict = await request.json()
        
        # If form_id provided as query parameter, add it to payload
        if form_id:
            payload_dict['form_id'] = form_id
        
        # If submitted_at not provided, use current time
        if 'submitted_at' not in payload_dict or not payload_dict['submitted_at']:
            payload_dict['submitted_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Log the raw payload for debugging
        logger.debug(
            "Webhook payload received",
            extra={
                "payload": json.dumps(payload_dict, indent=2)[:500]  # Limit size
            }
        )
        
        payload = FormBuilderWebhookPayload(**payload_dict)
        
        # If form_id still not provided, try to find it from the exercise
        if not payload.form_id:
            logger.warning("form_id not provided in webhook, will attempt to find from user's exercises")
        
        logger.info(
            "Webhook payload validated",
            extra={
                "form_id": payload.form_id,
                "submission_id": payload.submission_id,
                "user_email": payload.user_email
            }
        )
        
    except ValidationError as e:
        logger.error(
            "Webhook payload validation failed",
            extra={
                "validation_errors": e.errors(),
                "payload_preview": str(payload_dict)[:200] if 'payload_dict' in locals() else None
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {e.errors()}"
        )
    except Exception as e:
        logger.error(
            "Failed to parse webhook payload",
            extra={
                "error": str(e),
                "body_preview": body[:200].decode('utf-8', errors='ignore') if body else None
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Process the webhook
    try:
        result = await process_exercise_submission(db, payload)
        
        logger.info(
            "Webhook processed successfully",
            extra={
                "form_id": payload.form_id,
                "submission_id": payload.submission_id,
                "user_email": payload.user_email,
                "result": result
            }
        )
        
        return WebhookResponse(
            status=result["status"],
            message=result["message"],
            submission_id=result["submission_id"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, not found, etc.)
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(
            "Unexpected error processing webhook",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "form_id": payload.form_id,
                "submission_id": payload.submission_id,
                "user_email": payload.user_email
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error processing webhook: {str(e)}"
        )


@router.post("/123formbuilder/test", response_model=WebhookResponse)
async def test_123formbuilder_webhook(
    payload: FormBuilderWebhookPayload,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Test endpoint for 123FormBuilder webhooks (Admin only).
    
    This endpoint allows admins to test webhook processing without
    needing to actually submit a form in 123FormBuilder.
    
    Use this to:
    - Test webhook payload structure
    - Verify form_id mapping
    - Debug submission processing
    - Test progress updates
    
    Example payload:
    {
        "form_id": "6238706",
        "submission_id": "test-123",
        "user_email": "student@example.com",
        "submitted_at": "2025-11-23T10:30:00Z",
        "responses": {
            "question_1": "Test answer 1",
            "question_2": "Test answer 2"
        }
    }
    """
    logger.info(
        "Admin testing webhook",
        extra={
            "admin_user_id": current_user.id,
            "admin_email": current_user.email,
            "test_form_id": payload.form_id,
            "test_user_email": payload.user_email
        }
    )
    
    try:
        result = await process_exercise_submission(db, payload)
        
        logger.info(
            "Test webhook processed successfully",
            extra={
                "admin_user_id": current_user.id,
                "result": result
            }
        )
        
        return WebhookResponse(
            status=result["status"],
            message=f"TEST MODE: {result['message']}",
            submission_id=result["submission_id"]
        )
        
    except HTTPException as e:
        logger.warning(
            "Test webhook failed with expected error",
            extra={
                "admin_user_id": current_user.id,
                "status_code": e.status_code,
                "detail": e.detail
            }
        )
        raise
    except Exception as e:
        logger.error(
            "Test webhook failed with unexpected error",
            extra={
                "admin_user_id": current_user.id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )
