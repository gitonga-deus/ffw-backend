from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin_user
from app.models.user import User
from app.services.payment_service import payment_service

router = APIRouter(prefix="/api/admin/payments", tags=["admin-payments"])


@router.post("/expire-old")
async def expire_old_payments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger expiry of old pending payments.
    
    Admin only. Marks pending payments older than 30 minutes as failed.
    """
    count = payment_service.expire_old_payments(db)
    
    return {
        "success": True,
        "message": f"Expired {count} old pending payments"
    }


@router.post("/retry-webhook/{payment_id}")
async def retry_webhook(
    payment_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manually retry webhook processing for a payment.
    
    Admin only. Attempts to reprocess a failed webhook.
    """
    success = payment_service.retry_failed_webhook(db, payment_id)
    
    if not success:
        return {
            "success": False,
            "message": "Cannot retry webhook (max attempts reached or payment not found)"
        }
    
    return {
        "success": True,
        "message": "Webhook retry initiated"
    }
