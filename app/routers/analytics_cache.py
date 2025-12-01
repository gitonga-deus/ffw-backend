"""
Background task to pre-compute analytics and cache them.
Call this from a cron job every hour.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.dependencies import get_db
from app.services.analytics_service import analytics_service
from app.config import settings

router = APIRouter(prefix="/cron", tags=["cron"])

# In-memory cache (in production, use Redis)
_analytics_cache = None
_cache_time = None


@router.get("/refresh-analytics")
async def refresh_analytics_cache(
    db: Session = Depends(get_db),
    cron_secret: str = None
):
    """
    Pre-compute analytics and cache them.
    Should be called by Vercel Cron every hour.
    
    Protect with cron_secret in production.
    """
    # Verify cron secret if configured
    if settings.cron_secret and cron_secret != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Invalid cron secret")
    
    global _analytics_cache, _cache_time
    
    try:
        # Compute analytics
        data = analytics_service.get_dashboard_analytics(db)
        
        # Cache it
        _analytics_cache = data
        _cache_time = datetime.utcnow()
        
        return {
            "status": "success",
            "cached_at": _cache_time.isoformat(),
            "message": "Analytics cache refreshed"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def get_cached_analytics():
    """Get cached analytics data."""
    return _analytics_cache, _cache_time
