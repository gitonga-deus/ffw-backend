from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Exercise(Base):
    """Exercise content using 123FormBuilder forms."""
    __tablename__ = "exercises"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    form_id = Column(String(255), nullable=False, index=True)
    embed_code = Column(Text, nullable=False)
    form_title = Column(String(255), nullable=False)
    allow_multiple_submissions = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
