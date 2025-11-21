from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    certification_id = Column(String(50), unique=True, nullable=False, index=True)  # Public-facing ID
    certificate_url = Column(String, nullable=False)
    issued_at = Column(DateTime, default=func.now(), nullable=False)
    student_name = Column(String(255), nullable=False)
    course_title = Column(String(255), nullable=False)
