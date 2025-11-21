from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class EnrollmentDetail(BaseModel):
    """Enrollment detail for status response."""
    id: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    progress_percentage: Decimal
    last_accessed_at: Optional[datetime] = None
    signature_url: Optional[str] = None
    signature_created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentDetail(BaseModel):
    """Payment detail for status response."""
    id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EnrollmentStatusResponse(BaseModel):
    """Enrollment status response."""
    is_enrolled: bool
    enrollment: Optional[EnrollmentDetail] = None
    payment: Optional[PaymentDetail] = None
    has_signature: bool = False
    
    class Config:
        from_attributes = True


class SignatureSubmitRequest(BaseModel):
    """Request to submit digital signature."""
    signature_data: str  # Base64 encoded image data
    

class SignatureSubmitResponse(BaseModel):
    """Response after signature submission."""
    success: bool
    signature_url: str
    message: str = "Signature submitted successfully"
