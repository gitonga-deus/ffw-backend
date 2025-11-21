from sqlalchemy import Column, String, DateTime, Numeric, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Course(Base):
    __tablename__ = "course"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="KES", nullable=False)
    instructor_name = Column(String(255), nullable=False)
    instructor_bio = Column(String)
    instructor_image_url = Column(String)
    thumbnail_url = Column(String)
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
