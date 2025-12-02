from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    payment_id = Column(String, ForeignKey("payments.id"))
    signature_url = Column(String)
    signature_created_at = Column(DateTime)
    enrolled_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, index=True)
    progress_percentage = Column(Numeric(5, 2), default=0.00, nullable=False)
    last_accessed_module_id = Column(String, ForeignKey("modules.id", ondelete="SET NULL"))
    last_accessed_at = Column(DateTime)
