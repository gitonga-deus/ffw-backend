from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class UserListItem(BaseModel):
    """Schema for user in list view."""
    id: str
    email: str
    full_name: str
    phone_number: str
    profile_image_url: Optional[str] = None
    role: str
    is_verified: bool
    is_enrolled: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class PaymentHistoryItem(BaseModel):
    """Schema for payment history item."""
    id: str
    amount: Decimal
    currency: str
    status: str
    payment_method: Optional[str] = None
    ipay_transaction_id: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PaymentListItem(BaseModel):
    """Schema for payment list item with user info."""
    id: str
    user_id: str
    user_name: str
    user_email: str
    amount: Decimal
    currency: str
    status: str
    payment_method: Optional[str] = None
    ipay_transaction_id: Optional[str] = None
    ipay_reference: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class EnrollmentDetail(BaseModel):
    """Schema for enrollment details."""
    id: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: Decimal
    last_accessed_at: Optional[datetime] = None
    signature_url: Optional[str] = None
    signature_created_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class ActivityLogItem(BaseModel):
    """Schema for activity log item."""
    event_type: str
    created_at: datetime
    metadata: Optional[dict] = None


class UserDetailResponse(BaseModel):
    """Schema for detailed user profile."""
    id: str
    email: str
    full_name: str
    phone_number: str
    profile_image_url: Optional[str] = None
    role: str
    is_verified: bool
    is_enrolled: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    enrollment: Optional[EnrollmentDetail] = None
    payment_history: List[PaymentHistoryItem] = []
    activity_logs: List[ActivityLogItem] = []
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminProfileResponse(BaseModel):
    """Schema for admin profile response."""
    id: str
    email: str
    full_name: str
    phone_number: str
    profile_image_url: Optional[str] = None
    role: str
    instructor_bio: Optional[str] = None
    instructor_image_url: Optional[str] = None
    
    model_config = {"from_attributes": True}


class AdminProfileUpdate(BaseModel):
    """Schema for updating admin profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    instructor_bio: Optional[str] = None
    instructor_image_url: Optional[str] = None


class CourseSettingsResponse(BaseModel):
    """Schema for course settings response."""
    id: str
    title: str
    description: str
    price: Decimal
    currency: str
    instructor_name: str
    instructor_bio: Optional[str] = None
    instructor_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_published: bool
    
    model_config = {"from_attributes": True}


class CourseSettingsUpdate(BaseModel):
    """Schema for updating course settings."""
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    instructor_name: Optional[str] = Field(None, min_length=2, max_length=255)
    instructor_bio: Optional[str] = None
    instructor_image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None
