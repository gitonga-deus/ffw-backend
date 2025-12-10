from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.dependencies import get_db, get_current_admin_user
from app.models.user import User
from app.services.analytics_service import analytics_service
from app.schemas.analytics import (
    DashboardAnalyticsResponse,
    OverviewMetrics,
    UserAnalytics,
    EnrollmentAnalytics,
    RevenueAnalytics,
    ContentAnalytics,
    ReviewAnalytics,
    RecentActivity
)

router = APIRouter(prefix="/admin/analytics", tags=["analytics"])

# Simple in-memory cache (10 minutes TTL - analytics don't need real-time updates)
_dashboard_cache: Optional[dict] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL = timedelta(minutes=10)


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    force_refresh: bool = False
):
    """
    Get complete dashboard analytics.
    
    Admin only. Returns comprehensive analytics including:
    - Overview metrics (users, revenue, ratings, certificates)
    - User analytics with growth trends
    - Enrollment analytics with progress distribution
    - Revenue analytics with trends
    - Content engagement statistics
    - Review analytics with rating distribution
    - Recent activity (enrollments and completions)
    
    Cached for 10 minutes to improve performance. Use force_refresh=true to bypass cache.
    
    Returns:
        Complete dashboard analytics data
    """
    global _dashboard_cache, _cache_timestamp
    
    # Check if cache is valid
    now = datetime.utcnow()
    if (not force_refresh and 
        _dashboard_cache is not None and 
        _cache_timestamp is not None and 
        now - _cache_timestamp < CACHE_TTL):
        return DashboardAnalyticsResponse(**_dashboard_cache)
    
    # Fetch fresh data
    data = analytics_service.get_dashboard_analytics(db)
    
    # Update cache
    _dashboard_cache = data
    _cache_timestamp = now
    
    return DashboardAnalyticsResponse(**data)


@router.get("/overview", response_model=OverviewMetrics)
async def get_overview_metrics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get overview metrics for dashboard cards.
    
    Admin only. Returns key metrics displayed in overview cards.
    
    Returns:
        Overview metrics including user counts, revenue, ratings, and certificates
    """
    data = analytics_service.get_overview_metrics(db)
    return OverviewMetrics(**data)


@router.get("/users", response_model=UserAnalytics)
async def get_user_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user analytics data.
    
    Admin only. Returns user statistics and growth trends over the last 30 days.
    
    Returns:
        User analytics with growth data
    """
    data = analytics_service.get_user_analytics(db)
    return UserAnalytics(**data)


@router.get("/enrollments", response_model=EnrollmentAnalytics)
async def get_enrollment_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get enrollment analytics data.
    
    Admin only. Returns enrollment statistics, progress distribution, and trends.
    
    Returns:
        Enrollment analytics with progress distribution and trend data
    """
    data = analytics_service.get_enrollment_analytics(db)
    return EnrollmentAnalytics(**data)


@router.get("/revenue", response_model=RevenueAnalytics)
async def get_revenue_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue analytics data.
    
    Admin only. Returns revenue statistics, payment breakdown, and trends.
    
    Returns:
        Revenue analytics with payment status breakdown and trend data
    """
    data = analytics_service.get_revenue_analytics(db)
    return RevenueAnalytics(**data)


@router.get("/content", response_model=ContentAnalytics)
async def get_content_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get content analytics data.
    
    Admin only. Returns content statistics and engagement metrics.
    
    Returns:
        Content analytics with most viewed content and completion rates
    """
    data = analytics_service.get_content_analytics(db)
    return ContentAnalytics(**data)


@router.get("/reviews", response_model=ReviewAnalytics)
async def get_review_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get review analytics data.
    
    Admin only. Returns review statistics, rating distribution, and recent reviews.
    
    Returns:
        Review analytics with rating distribution and recent reviews
    """
    data = analytics_service.get_review_analytics(db)
    return ReviewAnalytics(**data)


@router.get("/recent-activity", response_model=RecentActivity)
async def get_recent_activity(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get recent activity data.
    
    Admin only. Returns recent enrollments and completions.
    
    Returns:
        Recent activity with latest enrollments and completions
    """
    data = analytics_service.get_recent_activity(db)
    return RecentActivity(**data)


@router.get("/dashboard-with-payments")
async def get_dashboard_with_payments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    force_refresh: bool = False,
    page: int = 1,
    page_size: int = 20
):
    """
    Get complete dashboard analytics with recent payments in a single request.
    
    This endpoint combines analytics and payments data to reduce round trips.
    Optimized for dashboard loading performance.
    
    Admin only.
    
    Returns:
        Combined analytics and payments data
    """
    import time
    start_time = time.time()
    
    global _dashboard_cache, _cache_timestamp
    
    # Check if cache is valid for analytics
    now = datetime.utcnow()
    cache_hit = False
    if (not force_refresh and 
        _dashboard_cache is not None and 
        _cache_timestamp is not None and 
        now - _cache_timestamp < CACHE_TTL):
        analytics_data = _dashboard_cache
        cache_hit = True
    else:
        # Fetch fresh analytics data
        analytics_start = time.time()
        analytics_data = analytics_service.get_dashboard_analytics(db)
        analytics_duration = time.time() - analytics_start
        print(f"[PERFORMANCE] Analytics queries took {analytics_duration:.2f}s")
        
        _dashboard_cache = analytics_data
        _cache_timestamp = now
    
    # Fetch recent payments (not cached as they change frequently)
    from app.models.payment import Payment
    from app.models.user import User as UserModel
    
    payments_start = time.time()
    skip = (page - 1) * page_size
    payments_query = db.query(Payment, UserModel).join(
        UserModel, Payment.user_id == UserModel.id
    ).order_by(
        Payment.created_at.desc()
    ).offset(skip).limit(page_size).all()
    
    payments = []
    for payment, user in payments_query:
        payments.append({
            "id": payment.id,
            "user_id": payment.user_id,
            "user_name": user.full_name,
            "user_email": user.email,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "ipay_transaction_id": payment.ipay_transaction_id,
            "ipay_reference": payment.ipay_reference,
            "created_at": payment.created_at.isoformat()
        })
    
    payments_duration = time.time() - payments_start
    total_duration = time.time() - start_time
    
    print(f"[PERFORMANCE] Payments query took {payments_duration:.2f}s")
    print(f"[PERFORMANCE] Total request took {total_duration:.2f}s (cache_hit={cache_hit})")
    
    return {
        "analytics": analytics_data,
        "payments": payments,
        "payments_page": page,
        "payments_page_size": page_size
    }
