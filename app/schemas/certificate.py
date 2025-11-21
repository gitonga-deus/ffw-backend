from pydantic import BaseModel
from datetime import datetime


class CertificateBase(BaseModel):
    """Base certificate schema."""
    student_name: str
    course_title: str


class CertificateResponse(CertificateBase):
    """Certificate response schema."""
    id: str
    user_id: str
    certification_id: str
    certificate_url: str
    issued_at: datetime
    
    class Config:
        from_attributes = True


class CertificateVerification(BaseModel):
    """Certificate verification response schema."""
    certification_id: str
    student_name: str
    course_title: str
    issued_at: datetime
    is_valid: bool
    
    class Config:
        from_attributes = True
