from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum, CheckConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    rating = Column(Integer, nullable=False, index=True)
    review_text = Column(String, nullable=False)
    status = Column(String(20), default=ReviewStatus.PENDING.value, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    reviewed_by = Column(String, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
        CheckConstraint('LENGTH(review_text) >= 10 AND LENGTH(review_text) <= 1000', name='check_review_text_length'),
    )
