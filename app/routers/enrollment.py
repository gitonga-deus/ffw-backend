from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import json
import os
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.dependencies import get_current_verified_user, get_current_enrolled_user
from app.models.user import User
from app.models.payment import PaymentStatus
from app.schemas.payment import PaymentInitiateResponse
from app.schemas.enrollment import (
    EnrollmentStatusResponse,
    SignatureSubmitRequest,
    SignatureSubmitResponse
)
from app.services.payment_service import payment_service
from app.services.enrollment_service import enrollment_service
from app.services.email_service import email_service

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_enrollment(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Initiate enrollment and payment process.
    
    Creates a payment record and returns iPay Africa payment URL.
    """
    # Check if user is already enrolled
    if current_user.is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already enrolled"
        )
    
    # Check if there's already a pending payment
    existing_enrollment = enrollment_service.get_enrollment_by_user_id(
        db, current_user.id
    )
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enrollment already exists"
        )
    
    # Get course price from database
    from app.models.course import Course
    course = db.query(Course).filter(Course.is_published == True).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No published course available for enrollment"
        )
    
    # Use course price
    enrollment_price = float(course.price)
    currency = course.currency
    
    # Create payment record
    payment = payment_service.create_payment_record(
        db=db,
        user_id=current_user.id,
        amount=enrollment_price,
        currency=currency
    )
    
    # Generate iPay payment URL
    payment_url = payment_service.generate_payment_url(payment, current_user)
    
    return PaymentInitiateResponse(
        payment_id=payment.id,
        payment_url=payment_url,
        amount=payment.amount,
        currency=payment.currency
    )


@router.get("/callback")
async def payment_callback(request: Request, db: Session = Depends(get_db)):
    """iPay Africa payment callback with amount verification and retry mechanism."""
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    try:
        callback_data = dict(request.query_params)
        logger.info(f"=== iPay Callback START ===")
        logger.info(f"Callback data: {callback_data}")
        logger.info(f"Frontend URL: {frontend_url}")
        
        # Verify signature
        if not payment_service.verify_callback_signature(callback_data):
            logger.error("Invalid callback signature")
            payment_service.increment_webhook_attempts(db, callback_data.get("p1"))
            return RedirectResponse(
                url=f"{frontend_url}/enrollment/error?message=Invalid+signature",
                status_code=303
            )
        
        # Extract data - iPay truncates p1, use id or ivm as fallback
        payment_id = callback_data.get("id") or callback_data.get("ivm") or callback_data.get("p1")
        user_id = callback_data.get("p2")
        status_code = callback_data.get("status", "").lower()
        transaction_id = callback_data.get("txncd")
        callback_amount_str = callback_data.get("mc", "0")
        
        logger.info(f"Payment ID: {payment_id}, User ID: {user_id}, Status: {status_code}, Amount: {callback_amount_str}")
        
        # Get payment - try by full ID first, then by user if truncated
        payment = None
        if payment_id:
            payment = payment_service.get_payment_by_id(db, payment_id)
        
        # If not found and we have user_id, get most recent pending payment
        if not payment and user_id:
            from app.models.payment import Payment
            payment = db.query(Payment).filter(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.PENDING.value
            ).order_by(Payment.created_at.desc()).first()
            
            if payment:
                logger.info(f"Found payment by user_id: {payment.id}")
        
        if not payment:
            logger.error(f"Payment not found for ID: {payment_id}, User: {user_id}")
            return RedirectResponse(
                url=f"{frontend_url}/enrollment/error?message=Payment+not+found",
                status_code=303
            )
        
        # Increment webhook attempts
        payment_service.increment_webhook_attempts(db, payment.id)
        
        # Check if already processed
        if payment.status != PaymentStatus.PENDING.value:
            logger.info(f"Payment {payment.id} already processed")
            return RedirectResponse(
                url=f"{frontend_url}/enrollment/success?transaction_id={transaction_id}",
                status_code=303
            )
        
        # Verify amount matches (allow 1 cent tolerance for floating point)
        try:
            callback_amount = float(callback_amount_str.replace(",", ""))
            expected_amount = float(payment.amount)
            
            if abs(callback_amount - expected_amount) > 0.01:
                logger.error(f"Amount mismatch! Expected: {expected_amount}, Received: {callback_amount}")
                
                # Mark as failed due to amount mismatch
                payment_service.update_payment_status(
                    db=db,
                    payment_id=payment.id,
                    status=PaymentStatus.FAILED.value,
                    ipay_transaction_id=transaction_id,
                    ipay_reference=callback_data.get("msisdn_idnum"),
                    payment_method=callback_data.get("channel"),
                    metadata=json.dumps({
                        **callback_data,
                        "error": "Amount mismatch",
                        "expected_amount": expected_amount,
                        "received_amount": callback_amount
                    })
                )
                
                return RedirectResponse(
                    url=f"{frontend_url}/enrollment/error?message=Amount+verification+failed",
                    status_code=303
                )
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not verify amount: {e}")
            # Continue processing if amount parsing fails (demo mode may not send amount)
        
        # Determine success
        is_successful = status_code == "aei7p7yrx4ae34" or status_code in ["success", "completed"]
        
        # Update payment
        new_status = PaymentStatus.COMPLETED.value if is_successful else PaymentStatus.FAILED.value
        payment_service.update_payment_status(
            db=db,
            payment_id=payment.id,
            status=new_status,
            ipay_transaction_id=transaction_id,
            ipay_reference=callback_data.get("msisdn_idnum"),
            payment_method=callback_data.get("channel"),
            metadata=json.dumps(callback_data)
        )
        
        logger.info(f"Payment {payment.id} updated to {new_status}")
        
        # Create enrollment if successful
        if is_successful:
            logger.info(f"Creating enrollment for user {payment.user_id}")
            
            # Update user
            user = enrollment_service.update_user_enrollment_status(
                db=db,
                user_id=payment.user_id,
                is_enrolled=True
            )
            
            # Create enrollment
            enrollment_service.create_enrollment(
                db=db,
                user_id=payment.user_id,
                payment_id=payment.id
            )
            
            # Send email
            if user:
                try:
                    await email_service.send_welcome_email(
                        to=user.email,
                        full_name=user.full_name
                    )
                except Exception as email_error:
                    logger.error(f"Email send failed: {email_error}")
            
            logger.info(f"Enrollment created for user {payment.user_id}")
            
            return RedirectResponse(
                url=f"{frontend_url}/enrollment/success?transaction_id={transaction_id}",
                status_code=303
            )
        else:
            logger.info(f"Payment failed: {payment.id}")
            return RedirectResponse(
                url=f"{frontend_url}/enrollment/failed?transaction_id={transaction_id}",
                status_code=303
            )
            
    except Exception as e:
        logger.error(f"Callback error: {str(e)}", exc_info=True)
        
        # Try to increment webhook attempts even on error
        try:
            if 'payment' in locals() and payment:
                payment_service.increment_webhook_attempts(db, payment.id)
        except:
            pass
        
        return RedirectResponse(
            url=f"{frontend_url}/enrollment/error?message=Processing+failed",
            status_code=303
        )


@router.post("/signature", response_model=SignatureSubmitResponse)
async def submit_signature(
    signature_request: SignatureSubmitRequest,
    current_user: User = Depends(get_current_enrolled_user),
    db: Session = Depends(get_db)
):
    """
    Submit digital signature after enrollment.
    
    Accepts canvas signature image data and uploads to Vercel Blob.
    Sends confirmation email after successful submission.
    """
    # Check if user is enrolled
    if not current_user.is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be enrolled to submit signature"
        )
    
    # Submit signature
    enrollment = await enrollment_service.submit_signature(
        db=db,
        user_id=current_user.id,
        signature_data=signature_request.signature_data
    )
    
    if not enrollment or not enrollment.signature_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload signature"
        )
    
    # Send signature confirmation email
    try:
        await email_service.send_signature_confirmation_email(
            to=current_user.email,
            full_name=current_user.full_name
        )
        logger.info(f"Signature confirmation email sent to {current_user.email}")
    except Exception as email_error:
        logger.error(f"Failed to send signature confirmation email: {email_error}")
        # Don't fail the request if email fails
    
    return SignatureSubmitResponse(
        success=True,
        signature_url=enrollment.signature_url
    )


@router.get("/status", response_model=EnrollmentStatusResponse)
async def get_enrollment_status(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Get enrollment status for current user.
    
    Returns enrollment details, payment status, and signature status.
    """
    status_data = enrollment_service.get_enrollment_status(db, current_user.id)
    
    return EnrollmentStatusResponse(**status_data)


@router.get("/test-callback")
async def test_callback(
    payment_id: str,
    status_code: str = "aei7p7yrx4ae34",
    db: Session = Depends(get_db)
):
    """Test callback endpoint for demo mode."""
    from app.config import settings
    
    if settings.ipay_vendor_id != "demo":
        raise HTTPException(status_code=403, detail="Demo mode only")
    
    payment = payment_service.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Simulate callback
    class MockRequest:
        def __init__(self, params):
            self.query_params = params
    
    callback_params = {
        "txncd": f"TEST-{payment_id[:8]}",
        "status": status_code,
        "p1": payment_id,
        "p2": payment.user_id,
        "mc": str(float(payment.amount)),  # Include correct amount
        "channel": "test",
        "vid": "demo",
        "msisdn_idnum": "254712345678",
        "id": payment_id,  # Full payment ID
        "ivm": payment_id
    }
    
    logger.info(f"Test callback for payment {payment_id}")
    
    return await payment_callback(MockRequest(callback_params), db)


@router.post("/retry-webhook/{payment_id}")
async def retry_webhook(
    payment_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Manually retry webhook processing for a failed payment (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payment = payment_service.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Payment is not pending (current status: {payment.status})"
        )
    
    can_retry = payment_service.retry_webhook(db, payment_id)
    if not can_retry:
        raise HTTPException(
            status_code=400,
            detail="Payment has exceeded maximum retry attempts"
        )
    
    return {
        "message": "Webhook retry allowed",
        "payment_id": payment_id,
        "attempts": payment.webhook_attempts,
        "status": payment.status
    }
