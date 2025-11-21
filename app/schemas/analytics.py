from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


# Overview Cards
class OverviewMetrics(BaseModel):
    """Overview metrics for dashboard cards."""
    total_users: int = Field(..., description="Total registered users")
    verified_users: int = Field(..., description="Number of verified users")
    active_enrollments: int = Field(..., description="Number of active enrollments (not completed)")
    completed_enrollments: int = Field(..., description="Number of completed enrollments")
    total_revenue: Decimal = Field(..., description="Total revenue from completed payments")
    revenue_this_month: Decimal = Field(..., description="Revenue for current month")
    average_rating: float = Field(..., description="Average course rating")
    total_reviews: int = Field(..., description="Total number of reviews")
    pending_reviews: int = Field(..., description="Number of pending reviews")
    certificates_issued: int = Field(..., description="Total certificates issued")
    certificates_this_month: int = Field(..., description="Certificates issued this month")


# User Analytics
class UserGrowthDataPoint(BaseModel):
    """Data point for user growth chart."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    new_users: int = Field(..., description="Number of new users registered on this date")
    verified_users: int = Field(..., description="Number of users verified on this date")


class UserAnalytics(BaseModel):
    """User analytics data."""
    total_users: int
    verified_users: int
    unverified_users: int
    enrolled_users: int
    non_enrolled_users: int
    new_users_this_month: int
    growth_data: List[UserGrowthDataPoint] = Field(..., description="User growth over last 30 days")


# Enrollment Analytics
class EnrollmentProgressDistribution(BaseModel):
    """Distribution of enrollment progress."""
    range_0_25: int = Field(..., description="Enrollments with 0-25% progress")
    range_26_50: int = Field(..., description="Enrollments with 26-50% progress")
    range_51_75: int = Field(..., description="Enrollments with 51-75% progress")
    range_76_99: int = Field(..., description="Enrollments with 76-99% progress")
    range_100: int = Field(..., description="Completed enrollments (100% progress)")


class EnrollmentTrendDataPoint(BaseModel):
    """Data point for enrollment trends."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    enrollments: int = Field(..., description="Number of enrollments on this date")
    completions: int = Field(..., description="Number of completions on this date")


class EnrollmentAnalytics(BaseModel):
    """Enrollment analytics data."""
    total_enrollments: int
    active_enrollments: int
    completed_enrollments: int
    average_progress: float = Field(..., description="Average progress percentage")
    completion_rate: float = Field(..., description="Percentage of enrollments completed")
    average_completion_days: Optional[float] = Field(None, description="Average days to complete course")
    progress_distribution: EnrollmentProgressDistribution
    trend_data: List[EnrollmentTrendDataPoint] = Field(..., description="Enrollment trends over last 30 days")


# Revenue Analytics
class RevenueTrendDataPoint(BaseModel):
    """Data point for revenue trends."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    revenue: Decimal = Field(..., description="Revenue on this date")
    payment_count: int = Field(..., description="Number of payments on this date")


class PaymentStatusBreakdown(BaseModel):
    """Breakdown of payments by status."""
    completed: int
    pending: int
    failed: int
    refunded: int


class RevenueAnalytics(BaseModel):
    """Revenue analytics data."""
    total_revenue: Decimal
    revenue_this_month: Decimal
    revenue_last_month: Decimal
    revenue_growth_percentage: Optional[float] = Field(None, description="Month-over-month growth percentage")
    average_transaction_value: Decimal
    payment_status_breakdown: PaymentStatusBreakdown
    trend_data: List[RevenueTrendDataPoint] = Field(..., description="Revenue trends over last 30 days")


# Content Analytics
class ContentEngagementItem(BaseModel):
    """Content engagement statistics."""
    content_id: str
    title: str
    content_type: str
    view_count: int = Field(..., description="Number of users who viewed this content")
    completion_count: int = Field(..., description="Number of users who completed this content")
    average_time_spent: int = Field(..., description="Average time spent in seconds")
    completion_rate: float = Field(..., description="Percentage of viewers who completed")


class ContentAnalytics(BaseModel):
    """Content analytics data."""
    total_content_items: int
    total_videos: int
    total_pdfs: int
    total_rich_text: int
    most_viewed_content: List[ContentEngagementItem] = Field(..., description="Top 10 most viewed content items")
    average_completion_rate: float = Field(..., description="Average completion rate across all content")


# Review Analytics
class RatingDistribution(BaseModel):
    """Distribution of ratings."""
    rating_1: int = Field(..., description="Number of 1-star ratings")
    rating_2: int = Field(..., description="Number of 2-star ratings")
    rating_3: int = Field(..., description="Number of 3-star ratings")
    rating_4: int = Field(..., description="Number of 4-star ratings")
    rating_5: int = Field(..., description="Number of 5-star ratings")


class RecentReviewItem(BaseModel):
    """Recent review item."""
    id: str
    user_name: str
    rating: int
    review_text: str
    status: str
    created_at: datetime


class ReviewAnalytics(BaseModel):
    """Review analytics data."""
    total_reviews: int
    approved_reviews: int
    pending_reviews: int
    rejected_reviews: int
    average_rating: float
    rating_distribution: RatingDistribution
    recent_reviews: List[RecentReviewItem] = Field(..., description="5 most recent reviews")


# Recent Activity
class RecentEnrollmentItem(BaseModel):
    """Recent enrollment item."""
    id: str
    user_name: str
    user_email: str
    enrolled_at: datetime
    progress_percentage: Decimal


class RecentCompletionItem(BaseModel):
    """Recent completion item."""
    id: str
    user_name: str
    user_email: str
    completed_at: datetime
    completion_days: int = Field(..., description="Days taken to complete")


class RecentActivity(BaseModel):
    """Recent activity data."""
    recent_enrollments: List[RecentEnrollmentItem] = Field(..., description="5 most recent enrollments")
    recent_completions: List[RecentCompletionItem] = Field(..., description="5 most recent completions")


# Main Dashboard Response
class DashboardAnalyticsResponse(BaseModel):
    """Complete dashboard analytics response."""
    overview: OverviewMetrics
    user_analytics: UserAnalytics
    enrollment_analytics: EnrollmentAnalytics
    revenue_analytics: RevenueAnalytics
    content_analytics: ContentAnalytics
    review_analytics: ReviewAnalytics
    recent_activity: RecentActivity
