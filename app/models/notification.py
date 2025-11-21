from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class TargetAudience(str, enum.Enum):
    ALL_ENROLLED = "all_enrolled"
    ALL_USERS = "all_users"
    SPECIFIC = "specific"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    target_audience = Column(String(20), nullable=False)
    target_user_ids = Column(String)  # JSON array string for SQLite compatibility
    sent_by = Column(String, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    email_sent = Column(Boolean, default=False, nullable=False)
