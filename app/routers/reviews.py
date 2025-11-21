from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user, get_current_admin_user
from app.models.user import User
from app.models.review import Review, ReviewStatus
from app.models.enrollment import Enrollment
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewWithUser,
    ReviewListResponse,
    ReviewStats
)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a review for the course.
    
    Requirements:
    - User must be enrolled
    - User must have completed the course
    - User can only submit one review
    
    Args:
        review_data: Review rating and text
        
    Returns:
        Created review with pending status
        
    Raises:
        403: If user is not enrolled or hasn't completed the course
        409: If user has already submitted a review
    """
    # Check if user is enrolled
    if not current_user.is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in the course to submit a review"
        )
    
    # Check if user has completed the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id
    ).first()
    
    if not enrollment or not enrollment.completed_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must complete the course before submitting a review"
        )
    
    # Check if user has already submitted a review
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a review for this course"
        )
    
    # Create review
    review = Review(
        user_id=current_user.id,
        rating=review_data.rating,
        review_text=review_data.review_text,
        status=ReviewStatus.PENDING.value
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    return review


@router.get("", response_model=ReviewListResponse)
async def get_approved_reviews(
    db: Session = Depends(get_db)
):
    """
    Get all approved reviews with aggregated statistics.
    Public endpoint - no authentication required.
    
    Returns:
        List of approved reviews with user information and rating statistics
    """
    # Get approved reviews with user information
    reviews = db.query(
        Review.id,
        Review.user_id,
        Review.rating,
        Review.review_text,
        Review.status,
        Review.created_at,
        User.full_name.label("user_name"),
        User.profile_image_url.label("user_profile_image")
    ).join(
        User, Review.user_id == User.id
    ).filter(
        Review.status == ReviewStatus.APPROVED.value
    ).order_by(
        Review.created_at.desc()
    ).all()
    
    # Convert to ReviewWithUser objects
    review_list = [
        ReviewWithUser(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user_name,
            user_profile_image=r.user_profile_image,
            rating=r.rating,
            review_text=r.review_text,
            status=r.status,
            created_at=r.created_at
        )
        for r in reviews
    ]
    
    # Calculate statistics
    all_reviews = db.query(Review).filter(
        Review.status == ReviewStatus.APPROVED.value
    ).all()
    
    total_reviews = len(all_reviews)
    average_rating = 0.0
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    if total_reviews > 0:
        total_rating = sum(r.rating for r in all_reviews)
        average_rating = round(total_rating / total_reviews, 2)
        
        for review in all_reviews:
            rating_distribution[review.rating] += 1
    
    stats = ReviewStats(
        total_reviews=total_reviews,
        average_rating=average_rating,
        rating_distribution=rating_distribution
    )
    
    return ReviewListResponse(
        reviews=review_list,
        stats=stats
    )


@router.get("/admin/pending", response_model=list[ReviewWithUser])
async def get_pending_reviews(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending reviews for moderation with user information.
    Admin only endpoint.
    
    Returns:
        List of pending reviews with user information
    """
    # Get pending reviews with user information
    reviews = db.query(
        Review.id,
        Review.user_id,
        Review.rating,
        Review.review_text,
        Review.status,
        Review.created_at,
        User.full_name.label("user_name"),
        User.profile_image_url.label("user_profile_image")
    ).join(
        User, Review.user_id == User.id
    ).filter(
        Review.status == ReviewStatus.PENDING.value
    ).order_by(
        Review.created_at.desc()
    ).all()
    
    # Convert to ReviewWithUser objects
    review_list = [
        ReviewWithUser(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user_name,
            user_profile_image=r.user_profile_image,
            rating=r.rating,
            review_text=r.review_text,
            status=r.status,
            created_at=r.created_at
        )
        for r in reviews
    ]
    
    return review_list


@router.get("/admin/all", response_model=ReviewListResponse)
async def get_all_reviews_admin(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all reviews (approved, rejected, pending) with user information.
    Admin only endpoint.
    
    Returns:
        List of all reviews with user information
    """
    # Get all reviews with user information
    reviews = db.query(
        Review.id,
        Review.user_id,
        Review.rating,
        Review.review_text,
        Review.status,
        Review.created_at,
        User.full_name.label("user_name"),
        User.profile_image_url.label("user_profile_image")
    ).join(
        User, Review.user_id == User.id
    ).order_by(
        Review.created_at.desc()
    ).all()
    
    # Convert to ReviewWithUser objects
    review_list = [
        ReviewWithUser(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user_name,
            user_profile_image=r.user_profile_image,
            rating=r.rating,
            review_text=r.review_text,
            status=r.status,
            created_at=r.created_at
        )
        for r in reviews
    ]
    
    # Calculate statistics for approved reviews only
    approved_reviews = [r for r in review_list if r.status == ReviewStatus.APPROVED.value]
    
    total_reviews = len(approved_reviews)
    average_rating = 0.0
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    if total_reviews > 0:
        total_rating = sum(r.rating for r in approved_reviews)
        average_rating = round(total_rating / total_reviews, 2)
        
        for review in approved_reviews:
            rating_distribution[review.rating] += 1
    
    stats = ReviewStats(
        total_reviews=total_reviews,
        average_rating=average_rating,
        rating_distribution=rating_distribution
    )
    
    return ReviewListResponse(
        reviews=review_list,
        stats=stats
    )


@router.put("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(
    review_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending review.
    Admin only endpoint.
    
    Args:
        review_id: ID of the review to approve
        
    Returns:
        Updated review
        
    Raises:
        404: If review not found
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Update review status
    review.status = ReviewStatus.APPROVED.value
    review.reviewed_by = current_user.id
    review.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(review)
    
    return review


@router.put("/{review_id}/reject", response_model=ReviewResponse)
async def reject_review(
    review_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending review.
    Admin only endpoint.
    
    Args:
        review_id: ID of the review to reject
        
    Returns:
        Updated review
        
    Raises:
        404: If review not found
    """
    review = db.query(Review).filter(Review.id == review_id).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Update review status
    review.status = ReviewStatus.REJECTED.value
    review.reviewed_by = current_user.id
    review.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(review)
    
    return review
