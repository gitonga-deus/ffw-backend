from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class ContentType(str, enum.Enum):
    VIDEO = "video"
    PDF = "pdf"
    RICH_TEXT = "rich_text"
    EXERCISE = "exercise"


class Content(Base):
    __tablename__ = "content"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id = Column(String, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)
    
    # Video specific fields
    vimeo_video_id = Column(String(255))
    video_duration = Column(Integer)  # in seconds
    
    # PDF specific fields
    pdf_url = Column(String)
    pdf_filename = Column(String(255))
    
    # Rich text specific fields
    rich_text_content = Column(String)  # JSON string for SQLite compatibility
    
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('module_id', 'order_index', name='uq_content_module_order'),
    )
