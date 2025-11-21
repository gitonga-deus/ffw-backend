from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class ExerciseResponse(Base):
    __tablename__ = "exercise_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(String, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(String(255), nullable=False)  # Reference to exercise within rich_text_content
    response_data = Column(String, nullable=False)  # JSON string for SQLite compatibility
    submitted_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', 'exercise_id', name='uq_exercise_response'),
    )
