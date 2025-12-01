from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
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
    
    Returns:
        Complete dashboard analytics data
    """
    data = analytics_service.get_dashboard_analytics(db)
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
