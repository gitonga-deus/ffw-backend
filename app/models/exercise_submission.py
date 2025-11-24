from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class ExerciseSubmission(Base):
    """Student submissions to exercises."""
    __tablename__ = "exercise_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    form_submission_id = Column(String(255), nullable=False)
    submission_data = Column(Text, nullable=False)  # JSON string of form responses
    submitted_at = Column(DateTime, nullable=False)
    webhook_received_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'exercise_id', name='uq_user_exercise_submission'),
    )
