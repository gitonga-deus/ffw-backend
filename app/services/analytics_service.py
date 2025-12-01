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
        """Get user analytics data."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        days_30_ago = now - timedelta(days=30)
        
        # Basic counts
        total_users = db.query(User).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        unverified_users = total_users - verified_users
        enrolled_users = db.query(User).filter(User.is_enrolled == True).count()
        non_enrolled_users = total_users - enrolled_users
        new_users_this_month = db.query(User).filter(
            User.created_at >= month_start
        ).count()
        
        # User growth data (last 30 days)
        growth_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            new_users = db.query(User).filter(
                and_(
                    User.created_at >= datetime.combine(current_date, datetime.min.time()),
                    User.created_at < datetime.combine(next_date, datetime.min.time())
                )
            ).count()
            
            # Note: We can't track when users were verified, so we'll use 0 for now
            # In a real system, you'd want a verification_date field
            verified_count = 0
            
            growth_data.append({
                "date": current_date.isoformat(),
                "new_users": new_users,
                "verified_users": verified_count
            })
            
            current_date = next_date
        
        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "unverified_users": unverified_users,
            "enrolled_users": enrolled_users,
            "non_enrolled_users": non_enrolled_users,
            "new_users_this_month": new_users_this_month,
            "growth_data": growth_data
        }
    
    def get_enrollment_analytics(self, db: Session) -> Dict:
        """Get enrollment analytics data."""
        now = datetime.utcnow()
        days_30_ago = now - timedelta(days=30)
        
        # Basic counts
        total_enrollments = db.query(Enrollment).count()
        active_enrollments = db.query(Enrollment).filter(
            Enrollment.completed_at.is_(None)
        ).count()
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.completed_at.isnot(None)
        ).count()
        
        # Average progress
        avg_progress = db.query(
            func.avg(Enrollment.progress_percentage)
        ).scalar() or 0.0
        
        # Completion rate
        completion_rate = 0.0
        if total_enrollments > 0:
            completion_rate = round((completed_enrollments / total_enrollments) * 100, 2)
        
        # Average completion days
        completed = db.query(Enrollment).filter(
            Enrollment.completed_at.isnot(None)
        ).all()
        
        average_completion_days = None
        if completed:
            total_days = sum(
                (e.completed_at - e.enrolled_at).days for e in completed
            )
            average_completion_days = round(total_days / len(completed), 2)
        
        # Progress distribution
        enrollments = db.query(Enrollment).all()
        distribution = {
            "range_0_25": 0,
            "range_26_50": 0,
            "range_51_75": 0,
            "range_76_99": 0,
            "range_100": 0
        }
        
        for enrollment in enrollments:
            progress = float(enrollment.progress_percentage)
            if progress == 100:
                distribution["range_100"] += 1
            elif progress >= 76:
                distribution["range_76_99"] += 1
            elif progress >= 51:
                distribution["range_51_75"] += 1
            elif progress >= 26:
                distribution["range_26_50"] += 1
            else:
                distribution["range_0_25"] += 1
        
        # Trend data (last 30 days)
        trend_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            enrollments_count = db.query(Enrollment).filter(
                and_(
                    Enrollment.enrolled_at >= datetime.combine(current_date, datetime.min.time()),
                    Enrollment.enrolled_at < datetime.combine(next_date, datetime.min.time())
                )
            ).count()
            
            completions_count = db.query(Enrollment).filter(
                and_(
                    Enrollment.completed_at >= datetime.combine(current_date, datetime.min.time()),
                    Enrollment.completed_at < datetime.combine(next_date, datetime.min.time())
                )
            ).count()
            
            trend_data.append({
                "date": current_date.isoformat(),
                "enrollments": enrollments_count,
                "completions": completions_count
            })
            
            current_date = next_date
        
        return {
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "average_progress": round(float(avg_progress), 2),
            "completion_rate": completion_rate,
            "average_completion_days": average_completion_days,
            "progress_distribution": distribution,
            "trend_data": trend_data
        }
    
    def get_revenue_analytics(self, db: Session) -> Dict:
        """Get revenue analytics data."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        days_30_ago = now - timedelta(days=30)
        
        # Total revenue
        total_revenue = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            Payment.status == PaymentStatus.COMPLETED.value
        ).scalar() or Decimal('0')
        
        # Revenue this month
        revenue_this_month = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED.value,
                Payment.created_at >= month_start
            )
        ).scalar() or Decimal('0')
        
        # Revenue last month
        revenue_last_month = db.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).filter(
            and_(
                Payment.status == PaymentStatus.COMPLETED.value,
                Payment.created_at >= last_month_start,
                Payment.created_at < month_start
            )
        ).scalar() or Decimal('0')
        
        # Revenue growth percentage
        revenue_growth_percentage = None
        if revenue_last_month > 0:
            growth = ((revenue_this_month - revenue_last_month) / revenue_last_month) * 100
            revenue_growth_percentage = round(float(growth), 2)
        
        # Average transaction value
        completed_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.COMPLETED.value
        ).all()
        
        average_transaction_value = Decimal('0')
        if completed_payments:
            total = sum(p.amount for p in completed_payments)
            average_transaction_value = total / len(completed_payments)
        
        # Payment status breakdown
        payment_status_breakdown = {
            "completed": db.query(Payment).filter(Payment.status == PaymentStatus.COMPLETED.value).count(),
            "pending": db.query(Payment).filter(Payment.status == PaymentStatus.PENDING.value).count(),
            "failed": db.query(Payment).filter(Payment.status == PaymentStatus.FAILED.value).count(),
            "refunded": db.query(Payment).filter(Payment.status == PaymentStatus.REFUNDED.value).count()
        }
        
        # Trend data (last 30 days)
        trend_data = []
        current_date = days_30_ago.date()
        end_date = now.date()
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            daily_revenue = db.query(
                func.coalesce(func.sum(Payment.amount), 0)
            ).filter(
                and_(
                    Payment.status == PaymentStatus.COMPLETED.value,
                    Payment.created_at >= datetime.combine(current_date, datetime.min.time()),
                    Payment.created_at < datetime.combine(next_date, datetime.min.time())
                )
            ).scalar() or Decimal('0')
            
            payment_count = db.query(Payment).filter(
                and_(
                    Payment.status == PaymentStatus.COMPLETED.value,
                    Payment.created_at >= datetime.combine(current_date, datetime.min.time()),
                    Payment.created_at < datetime.combine(next_date, datetime.min.time())
                )
            ).count()
            
            trend_data.append({
                "date": current_date.isoformat(),
                "revenue": daily_revenue,
                "payment_count": payment_count
            })
            
            current_date = next_date
        
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
        """Get content analytics data."""
        # Content counts by type
        total_content_items = db.query(Content).count()
        total_videos = db.query(Content).filter(Content.content_type == "video").count()
        total_pdfs = db.query(Content).filter(Content.content_type == "pdf").count()
        total_rich_text = db.query(Content).filter(Content.content_type == "rich_text").count()
        
        # Most viewed content (top 10)
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
        """Get review analytics data."""
        # Review counts by status
        total_reviews = db.query(Review).count()
        approved_reviews = db.query(Review).filter(Review.status == ReviewStatus.APPROVED.value).count()
        pending_reviews = db.query(Review).filter(Review.status == ReviewStatus.PENDING.value).count()
        rejected_reviews = db.query(Review).filter(Review.status == ReviewStatus.REJECTED.value).count()
        
        # Average rating (approved only)
        approved = db.query(Review).filter(Review.status == ReviewStatus.APPROVED.value).all()
        average_rating = 0.0
        if approved:
            total_rating = sum(review.rating for review in approved)
            average_rating = round(total_rating / len(approved), 2)
        
        # Rating distribution (all reviews)
        all_reviews = db.query(Review).all()
        rating_distribution = {
            "rating_1": sum(1 for r in all_reviews if r.rating == 1),
            "rating_2": sum(1 for r in all_reviews if r.rating == 2),
            "rating_3": sum(1 for r in all_reviews if r.rating == 3),
            "rating_4": sum(1 for r in all_reviews if r.rating == 4),
            "rating_5": sum(1 for r in all_reviews if r.rating == 5)
        }
        
        # Recent reviews (5 most recent)
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
