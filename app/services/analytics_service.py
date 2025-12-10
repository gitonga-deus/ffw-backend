from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, desc
from decimal import Decimal

from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.payment import Payment, PaymentStatus
from app.models.review import Review, ReviewStatus
from app.models.certificate import Certificate
from app.models.content import Content
from app.models.user_progress import UserProgress


class AnalyticsService:
    """Service for calculating dashboard analytics."""
    
    def get_overview_metrics(self, db: Session) -> Dict:
        """Get overview metrics for dashboard cards - optimized with fewer queries."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        # User metrics - single query with aggregation
        user_stats = db.query(
            func.count(User.id).label('total'),
            func.sum(case((User.is_verified == True, 1), else_=0)).label('verified')
        ).first()
        
        # Enrollment metrics - single query with aggregation
        enrollment_stats = db.query(
            func.count(Enrollment.id).label('total'),
            func.sum(case((Enrollment.completed_at.is_(None), 1), else_=0)).label('active'),
            func.sum(case((Enrollment.completed_at.isnot(None), 1), else_=0)).label('completed')
        ).first()
        
        # Revenue metrics - single query with conditional sum
        revenue_stats = db.query(
            func.coalesce(
                func.sum(case(
                    (Payment.status == PaymentStatus.COMPLETED.value, Payment.amount),
                    else_=0
                )), 0
            ).label('total'),
            func.coalesce(
                func.sum(case(
                    (and_(
                        Payment.status == PaymentStatus.COMPLETED.value,
                        Payment.created_at >= month_start
                    ), Payment.amount),
                    else_=0
                )), 0
            ).label('this_month')
        ).first()
        
        # Review metrics - single query with aggregation
        review_stats = db.query(
            func.count(Review.id).label('total'),
            func.sum(case((Review.status == ReviewStatus.PENDING.value, 1), else_=0)).label('pending'),
            func.avg(case((Review.status == ReviewStatus.APPROVED.value, Review.rating), else_=None)).label('avg_rating')
        ).first()
        
        # Certificate metrics - single query with aggregation
        cert_stats = db.query(
            func.count(Certificate.id).label('total'),
            func.sum(case((Certificate.issued_at >= month_start, 1), else_=0)).label('this_month')
        ).first()
        
        return {
            "total_users": user_stats.total or 0,
            "verified_users": user_stats.verified or 0,
            "active_enrollments": enrollment_stats.active or 0,
            "completed_enrollments": enrollment_stats.completed or 0,
            "total_revenue": Decimal(str(revenue_stats.total or 0)),
            "revenue_this_month": Decimal(str(revenue_stats.this_month or 0)),
            "average_rating": round(float(review_stats.avg_rating or 0), 2),
            "total_reviews": review_stats.total or 0,
            "pending_reviews": review_stats.pending or 0,
            "certificates_issued": cert_stats.total or 0,
            "certificates_this_month": cert_stats.this_month or 0
        }
    
    def get_user_analytics(self, db: Session) -> Dict:
        """Get user analytics data - OPTIMIZED."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        days_30_ago = now - timedelta(days=30)
        
        # Single query for all user counts using aggregation
        user_stats = db.query(
            func.count(User.id).label('total'),
            func.sum(case((User.is_verified == True, 1), else_=0)).label('verified'),
            func.sum(case((User.is_enrolled == True, 1), else_=0)).label('enrolled'),
            func.sum(case((User.created_at >= month_start, 1), else_=0)).label('new_this_month')
        ).first()
        
        total_users = user_stats.total or 0
        verified_users = user_stats.verified or 0
        enrolled_users = user_stats.enrolled or 0
        new_users_this_month = user_stats.new_this_month or 0
        
        # Single query for growth data using date_trunc (PostgreSQL) or date() (SQLite)
        # This replaces 30+ individual queries with ONE query
        growth_query = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('new_users')
        ).filter(
            User.created_at >= days_30_ago
        ).group_by(
            func.date(User.created_at)
        ).all()
        
        # Convert to dict for fast lookup
        growth_dict = {str(row.date): row.new_users for row in growth_query}
        
        # Build complete 30-day array (fill missing dates with 0)
        growth_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            growth_data.append({
                "date": current_date.isoformat(),
                "new_users": growth_dict.get(str(current_date), 0),
                "verified_users": 0  # Not tracked
            })
            current_date += timedelta(days=1)
        
        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "unverified_users": total_users - verified_users,
            "enrolled_users": enrolled_users,
            "non_enrolled_users": total_users - enrolled_users,
            "new_users_this_month": new_users_this_month,
            "growth_data": growth_data
        }
    
    def get_enrollment_analytics(self, db: Session) -> Dict:
        """Get enrollment analytics data - OPTIMIZED."""
        now = datetime.utcnow()
        days_30_ago = now - timedelta(days=30)
        
        # Single query for all enrollment counts and averages
        enrollment_stats = db.query(
            func.count(Enrollment.id).label('total'),
            func.sum(case((Enrollment.completed_at.is_(None), 1), else_=0)).label('active'),
            func.sum(case((Enrollment.completed_at.isnot(None), 1), else_=0)).label('completed'),
            func.avg(Enrollment.progress_percentage).label('avg_progress'),
            func.avg(
                case(
                    (Enrollment.completed_at.isnot(None),
                     func.julianday(Enrollment.completed_at) - func.julianday(Enrollment.enrolled_at)),
                    else_=None
                )
            ).label('avg_completion_days')
        ).first()
        
        total_enrollments = enrollment_stats.total or 0
        active_enrollments = enrollment_stats.active or 0
        completed_enrollments = enrollment_stats.completed or 0
        avg_progress = enrollment_stats.avg_progress or 0.0
        average_completion_days = enrollment_stats.avg_completion_days
        
        # Completion rate
        completion_rate = 0.0
        if total_enrollments > 0:
            completion_rate = round((completed_enrollments / total_enrollments) * 100, 2)
        
        # Progress distribution - single query with CASE statements
        distribution_query = db.query(
            func.sum(case((Enrollment.progress_percentage < 26, 1), else_=0)).label('range_0_25'),
            func.sum(case((and_(Enrollment.progress_percentage >= 26, Enrollment.progress_percentage < 51), 1), else_=0)).label('range_26_50'),
            func.sum(case((and_(Enrollment.progress_percentage >= 51, Enrollment.progress_percentage < 76), 1), else_=0)).label('range_51_75'),
            func.sum(case((and_(Enrollment.progress_percentage >= 76, Enrollment.progress_percentage < 100), 1), else_=0)).label('range_76_99'),
            func.sum(case((Enrollment.progress_percentage == 100, 1), else_=0)).label('range_100')
        ).first()
        
        distribution = {
            "range_0_25": distribution_query.range_0_25 or 0,
            "range_26_50": distribution_query.range_26_50 or 0,
            "range_51_75": distribution_query.range_51_75 or 0,
            "range_76_99": distribution_query.range_76_99 or 0,
            "range_100": distribution_query.range_100 or 0
        }
        
        # Trend data - TWO queries instead of 60+
        enrollments_by_date = db.query(
            func.date(Enrollment.enrolled_at).label('date'),
            func.count(Enrollment.id).label('count')
        ).filter(
            Enrollment.enrolled_at >= days_30_ago
        ).group_by(
            func.date(Enrollment.enrolled_at)
        ).all()
        
        completions_by_date = db.query(
            func.date(Enrollment.completed_at).label('date'),
            func.count(Enrollment.id).label('count')
        ).filter(
            Enrollment.completed_at >= days_30_ago
        ).group_by(
            func.date(Enrollment.completed_at)
        ).all()
        
        # Convert to dicts for fast lookup
        enrollments_dict = {str(row.date): row.count for row in enrollments_by_date}
        completions_dict = {str(row.date): row.count for row in completions_by_date}
        
        # Build complete 30-day array
        trend_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            trend_data.append({
                "date": current_date.isoformat(),
                "enrollments": enrollments_dict.get(str(current_date), 0),
                "completions": completions_dict.get(str(current_date), 0)
            })
            current_date += timedelta(days=1)
        
        return {
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "average_progress": round(float(avg_progress), 2),
            "completion_rate": completion_rate,
            "average_completion_days": round(average_completion_days, 2) if average_completion_days else None,
            "progress_distribution": distribution,
            "trend_data": trend_data
        }
    
    def get_revenue_analytics(self, db: Session) -> Dict:
        """Get revenue analytics data - OPTIMIZED."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        days_30_ago = now - timedelta(days=30)
        
        # Single query for all revenue metrics
        revenue_stats = db.query(
            func.coalesce(
                func.sum(case((Payment.status == PaymentStatus.COMPLETED.value, Payment.amount), else_=0)), 0
            ).label('total'),
            func.coalesce(
                func.sum(case(
                    (and_(Payment.status == PaymentStatus.COMPLETED.value, Payment.created_at >= month_start), Payment.amount),
                    else_=0
                )), 0
            ).label('this_month'),
            func.coalesce(
                func.sum(case(
                    (and_(
                        Payment.status == PaymentStatus.COMPLETED.value,
                        Payment.created_at >= last_month_start,
                        Payment.created_at < month_start
                    ), Payment.amount),
                    else_=0
                )), 0
            ).label('last_month'),
            func.avg(case((Payment.status == PaymentStatus.COMPLETED.value, Payment.amount), else_=None)).label('avg_transaction'),
            func.sum(case((Payment.status == PaymentStatus.COMPLETED.value, 1), else_=0)).label('completed_count'),
            func.sum(case((Payment.status == PaymentStatus.PENDING.value, 1), else_=0)).label('pending_count'),
            func.sum(case((Payment.status == PaymentStatus.FAILED.value, 1), else_=0)).label('failed_count'),
            func.sum(case((Payment.status == PaymentStatus.REFUNDED.value, 1), else_=0)).label('refunded_count')
        ).first()
        
        total_revenue = Decimal(str(revenue_stats.total or 0))
        revenue_this_month = Decimal(str(revenue_stats.this_month or 0))
        revenue_last_month = Decimal(str(revenue_stats.last_month or 0))
        average_transaction_value = Decimal(str(revenue_stats.avg_transaction or 0))
        
        # Revenue growth percentage
        revenue_growth_percentage = None
        if revenue_last_month > 0:
            growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
            revenue_growth_percentage = round(float(growth), 2)
        
        # Payment status breakdown
        payment_status_breakdown = {
            "completed": revenue_stats.completed_count or 0,
            "pending": revenue_stats.pending_count or 0,
            "failed": revenue_stats.failed_count or 0,
            "refunded": revenue_stats.refunded_count or 0
        }
        
        # Trend data - single query instead of 30+
        trend_query = db.query(
            func.date(Payment.created_at).label('date'),
            func.sum(case((Payment.status == PaymentStatus.COMPLETED.value, Payment.amount), else_=0)).label('revenue'),
            func.sum(case((Payment.status == PaymentStatus.COMPLETED.value, 1), else_=0)).label('payment_count')
        ).filter(
            Payment.created_at >= days_30_ago
        ).group_by(
            func.date(Payment.created_at)
        ).all()
        
        # Convert to dict for fast lookup
        trend_dict = {str(row.date): {"revenue": row.revenue, "payment_count": row.payment_count} for row in trend_query}
        
        # Build complete 30-day array
        trend_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            data = trend_dict.get(str(current_date), {"revenue": Decimal('0'), "payment_count": 0})
            trend_data.append({
                "date": current_date.isoformat(),
                "revenue": data["revenue"],
                "payment_count": data["payment_count"]
            })
            current_date += timedelta(days=1)
        
        return {
            "total_revenue": total_revenue,
            "revenue_this_month": revenue_this_month,
            "revenue_last_month": revenue_last_month,
            "revenue_growth_percentage": revenue_growth_percentage,
            "average_transaction_value": average_transaction_value,
            "payment_status_breakdown": payment_status_breakdown,
            "trend_data": trend_data
        }
    
    def get_content_analytics(self, db: Session) -> Dict:
        """Get content analytics data - OPTIMIZED."""
        # Single query for content counts by type using aggregation
        content_counts = db.query(
            func.count(Content.id).label('total'),
            func.sum(case((Content.content_type == "video", 1), else_=0)).label('videos'),
            func.sum(case((Content.content_type == "pdf", 1), else_=0)).label('pdfs'),
            func.sum(case((Content.content_type == "rich_text", 1), else_=0)).label('rich_text')
        ).first()
        
        total_content_items = content_counts.total or 0
        total_videos = content_counts.videos or 0
        total_pdfs = content_counts.pdfs or 0
        total_rich_text = content_counts.rich_text or 0
        
        # Most viewed content (top 10) - optimized with single query
        content_stats = db.query(
            Content.id,
            Content.title,
            Content.content_type,
            func.count(UserProgress.id).label("view_count"),
            func.sum(case((UserProgress.is_completed == True, 1), else_=0)).label("completion_count"),
            func.avg(UserProgress.time_spent).label("avg_time_spent")
        ).outerjoin(
            UserProgress, Content.id == UserProgress.content_id
        ).group_by(
            Content.id, Content.title, Content.content_type
        ).order_by(
            desc("view_count")
        ).limit(10).all()
        
        most_viewed_content = []
        total_completion_rate = 0
        content_with_views = 0
        
        for stat in content_stats:
            view_count = stat.view_count or 0
            completion_count = stat.completion_count or 0
            avg_time = stat.avg_time_spent or 0
            
            completion_rate = 0.0
            if view_count > 0:
                completion_rate = round((completion_count / view_count) * 100, 2)
                total_completion_rate += completion_rate
                content_with_views += 1
            
            most_viewed_content.append({
                "content_id": stat.id,
                "title": stat.title,
                "content_type": stat.content_type,
                "view_count": view_count,
                "completion_count": completion_count,
                "average_time_spent": int(avg_time),
                "completion_rate": completion_rate
            })
        
        # Average completion rate
        average_completion_rate = 0.0
        if content_with_views > 0:
            average_completion_rate = round(total_completion_rate / content_with_views, 2)
        
        return {
            "total_content_items": total_content_items,
            "total_videos": total_videos,
            "total_pdfs": total_pdfs,
            "total_rich_text": total_rich_text,
            "most_viewed_content": most_viewed_content,
            "average_completion_rate": average_completion_rate
        }
    
    def get_review_analytics(self, db: Session) -> Dict:
        """Get review analytics data - OPTIMIZED."""
        # Single query for all review stats using aggregation
        review_stats = db.query(
            func.count(Review.id).label('total'),
            func.sum(case((Review.status == ReviewStatus.APPROVED.value, 1), else_=0)).label('approved'),
            func.sum(case((Review.status == ReviewStatus.PENDING.value, 1), else_=0)).label('pending'),
            func.sum(case((Review.status == ReviewStatus.REJECTED.value, 1), else_=0)).label('rejected'),
            func.avg(case((Review.status == ReviewStatus.APPROVED.value, Review.rating), else_=None)).label('avg_rating'),
            func.sum(case((Review.rating == 1, 1), else_=0)).label('rating_1'),
            func.sum(case((Review.rating == 2, 1), else_=0)).label('rating_2'),
            func.sum(case((Review.rating == 3, 1), else_=0)).label('rating_3'),
            func.sum(case((Review.rating == 4, 1), else_=0)).label('rating_4'),
            func.sum(case((Review.rating == 5, 1), else_=0)).label('rating_5')
        ).first()
        
        total_reviews = review_stats.total or 0
        approved_reviews = review_stats.approved or 0
        pending_reviews = review_stats.pending or 0
        rejected_reviews = review_stats.rejected or 0
        average_rating = round(float(review_stats.avg_rating or 0), 2)
        
        rating_distribution = {
            "rating_1": review_stats.rating_1 or 0,
            "rating_2": review_stats.rating_2 or 0,
            "rating_3": review_stats.rating_3 or 0,
            "rating_4": review_stats.rating_4 or 0,
            "rating_5": review_stats.rating_5 or 0
        }
        
        # Recent reviews (5 most recent) - single query with join
        recent = db.query(Review, User).join(
            User, Review.user_id == User.id
        ).order_by(
            desc(Review.created_at)
        ).limit(5).all()
        
        recent_reviews = []
        for review, user in recent:
            recent_reviews.append({
                "id": review.id,
                "user_name": user.full_name,
                "rating": review.rating,
                "review_text": review.review_text,
                "status": review.status,
                "created_at": review.created_at
            })
        
        return {
            "total_reviews": total_reviews,
            "approved_reviews": approved_reviews,
            "pending_reviews": pending_reviews,
            "rejected_reviews": rejected_reviews,
            "average_rating": average_rating,
            "rating_distribution": rating_distribution,
            "recent_reviews": recent_reviews
        }
    
    def get_recent_activity(self, db: Session) -> Dict:
        """Get recent activity data."""
        # Recent enrollments (5 most recent)
        recent_enrollments_data = db.query(Enrollment, User).join(
            User, Enrollment.user_id == User.id
        ).order_by(
            desc(Enrollment.enrolled_at)
        ).limit(5).all()
        
        recent_enrollments = []
        for enrollment, user in recent_enrollments_data:
            recent_enrollments.append({
                "id": enrollment.id,
                "user_name": user.full_name,
                "user_email": user.email,
                "enrolled_at": enrollment.enrolled_at,
                "progress_percentage": enrollment.progress_percentage
            })
        
        # Recent completions (5 most recent)
        recent_completions_data = db.query(Enrollment, User).join(
            User, Enrollment.user_id == User.id
        ).filter(
            Enrollment.completed_at.isnot(None)
        ).order_by(
            desc(Enrollment.completed_at)
        ).limit(5).all()
        
        recent_completions = []
        for enrollment, user in recent_completions_data:
            completion_days = (enrollment.completed_at - enrollment.enrolled_at).days
            recent_completions.append({
                "id": enrollment.id,
                "user_name": user.full_name,
                "user_email": user.email,
                "completed_at": enrollment.completed_at,
                "completion_days": completion_days
            })
        
        return {
            "recent_enrollments": recent_enrollments,
            "recent_completions": recent_completions
        }
    
    def get_dashboard_analytics(self, db: Session) -> Dict:
        """Get complete dashboard analytics."""
        return {
            "overview": self.get_overview_metrics(db),
            "user_analytics": self.get_user_analytics(db),
            "enrollment_analytics": self.get_enrollment_analytics(db),
            "revenue_analytics": self.get_revenue_analytics(db),
            "content_analytics": self.get_content_analytics(db),
            "review_analytics": self.get_review_analytics(db),
            "recent_activity": self.get_recent_activity(db)
        }


analytics_service = AnalyticsService()
