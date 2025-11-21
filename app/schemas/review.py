from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: str = Field(..., min_length=10, max_length=1000, description="Review text")
    
    @field_validator('review_text')
    @classmethod
    def validate_review_text(cls, v: str) -> str:
        """Validate review text length."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Review text must be at least 10 characters long")
        if len(v) > 1000:
            raise ValueError("Review text must not exceed 1000 characters")
        return v


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: str
    user_id: str
    rating: int
    review_text: str
    status: str
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReviewWithUser(BaseModel):
    """Schema for review with user information."""
    id: str
    user_id: str
    user_name: str
    user_profile_image: Optional[str] = None
    rating: int
    review_text: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewStats(BaseModel):
    """Schema for aggregated review statistics."""
    total_reviews: int
    average_rating: float
    rating_distribution: dict[int, int]  # {1: count, 2: count, ...}


class ReviewListResponse(BaseModel):
    """Schema for list of reviews with statistics."""
    reviews: list[ReviewWithUser]
    stats: ReviewStats


class ReviewModeration(BaseModel):
    """Schema for review moderation action."""
    action: str = Field(..., pattern="^(approve|reject)$")
