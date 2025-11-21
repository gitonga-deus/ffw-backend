from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    profile_image_url = Column(String)
    role = Column(String(20), default=UserRole.STUDENT.value, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_enrolled = Column(Boolean, default=False, nullable=False, index=True)
    verification_token = Column(String(255))
    verification_token_expires_at = Column(DateTime)
    reset_password_token = Column(String(255))
    reset_password_token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime)
