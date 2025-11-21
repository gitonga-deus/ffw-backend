from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="KES", nullable=False)
    status = Column(String(20), nullable=False, index=True)
    ipay_transaction_id = Column(String(255))
    ipay_reference = Column(String(255))
    payment_method = Column(String(50))
    payment_metadata = Column(String)  # JSON string for SQLite compatibility
    expires_at = Column(DateTime)  # Payment expiry time (30 minutes from creation)
    webhook_attempts = Column(String, default="0")  # Number of webhook retry attempts
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def is_expired(self) -> bool:
        """Check if payment has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def can_retry_webhook(self) -> bool:
        """Check if webhook can be retried (max 5 attempts)."""
        try:
            attempts = int(self.webhook_attempts or "0")
            return attempts < 5
        except:
            return True
