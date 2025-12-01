"""
Cron job endpoints for scheduled tasks.
These endpoints should be called by Vercel Cron or external schedulers.
"""
from fastapi import APIRouter, Header, HTTPException, Request
from app.config import settings
from app.tasks.payment_tasks import expire_old_payments, retry_failed_webhooks
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cron", tags=["cron"])


async def verify_cron_secret(request: Request, authorization: str = Header(None)):
    """Verify that the request is from an authorized cron service."""
    # Vercel Cron sends a special header
    vercel_cron_secret = request.headers.get("x-vercel-cron-secret")
    
    if vercel_cron_secret:
        # Request is from Vercel Cron - verify the secret
        expected_secret = settings.cron_secret if settings.cron_secret else settings.secret_key
        if vercel_cron_secret != expected_secret:
            raise HTTPException(status_code=401, detail="Invalid Vercel cron secret")
        return
    
    # Otherwise, check for Bearer token (for manual/external calls)
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    
    # Use CRON_SECRET if set, otherwise fall back to SECRET_KEY
    cron_secret = settings.cron_secret if settings.cron_secret else settings.secret_key
    if token != cron_secret:
        raise HTTPException(status_code=401, detail="Invalid authorization token")


@router.post("/expire-payments")
async def cron_expire_payments(request: Request, authorization: str = Header(None)):
    """
    Expire old pending payments.
    Should be called every 5 minutes by Vercel Cron.
    """
    await verify_cron_secret(request, authorization)
    
    try:
        expire_old_payments()
        logger.info("Cron job: Expired old payments")
        return {"status": "success", "message": "Old payments expired"}
    except Exception as e:
        logger.error(f"Cron job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry-webhooks")
async def cron_retry_webhooks(request: Request, authorization: str = Header(None)):
    """
    Retry failed webhook deliveries.
    Should be called every 10 minutes by Vercel Cron.
    """
    await verify_cron_secret(request, authorization)
    
    try:
        retry_failed_webhooks()
        logger.info("Cron job: Retried failed webhooks")
        return {"status": "success", "message": "Failed webhooks retried"}
    except Exception as e:
        logger.error(f"Cron job failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
