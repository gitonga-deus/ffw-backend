from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)  # 'page_view', 'registration', 'enrollment', etc.
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    session_id = Column(String(255))
    event_metadata = Column(String)  # JSON string for SQLite compatibility
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
