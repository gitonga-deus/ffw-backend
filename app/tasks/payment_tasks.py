"""
Background tasks for payment processing.
"""
import logging
from app.database import SessionLocal
from app.services.payment_service import payment_service

logger = logging.getLogger(__name__)


def expire_old_payments():
    """
    Background task to expire old pending payments.
    Should be run periodically (e.g., every 5 minutes via cron or scheduler).
    """
    db = SessionLocal()
    try:
        count = payment_service.expire_old_payments(db)
        if count > 0:
            logger.info(f"Expired {count} old pending payments")
        return count
    except Exception as e:
        logger.error(f"Error expiring old payments: {str(e)}")
        return 0
    finally:
        db.close()


def retry_failed_webhooks():
    """
    Background task to retry failed webhook deliveries.
    Should be run periodically (e.g., every 10 minutes via cron or scheduler).
    """
    db = SessionLocal()
    try:
        from app.models.payment import Payment, PaymentStatus
        
        # Find payments that need webhook retry
        payments_to_retry = db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING.value,
            Payment.webhook_attempts < "5"
        ).all()
        
        retry_count = 0
        for payment in payments_to_retry:
            if payment.can_retry_webhook():
                success = payment_service.retry_failed_webhook(db, payment.id)
                if success:
                    retry_count += 1
        
        if retry_count > 0:
            logger.info(f"Retried webhooks for {retry_count} payments")
        
        return retry_count
    except Exception as e:
        logger.error(f"Error retrying webhooks: {str(e)}")
        return 0
    finally:
        db.close()
