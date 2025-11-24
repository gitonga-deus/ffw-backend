from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional
from datetime import datetime


class FormBuilderWebhookPayload(BaseModel):
    """
    Schema for 123FormBuilder webhook payload.
    
    This represents the data sent by 123FormBuilder when a form is submitted.
    form_id and submitted_at are optional and can be provided via query parameters.
    """
    form_id: Optional[str] = Field(None, description="123FormBuilder form ID (can be provided via query param)")
    submission_id: str = Field(..., description="Unique submission ID from 123FormBuilder")
    user_email: str = Field(..., description="Email address of the user who submitted the form")
    submitted_at: Optional[str] = Field(None, description="ISO 8601 timestamp of when the form was submitted")
    responses: Dict[str, Any] = Field(default_factory=dict, description="Form field responses")
    
    @field_validator('submission_id', 'user_email')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('user_email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError("Invalid email format")
        return v.lower()
    
    @field_validator('submitted_at')
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate that submitted_at is a valid ISO 8601 timestamp if provided."""
        if v is None:
            return v
        try:
            # Try to parse the timestamp to ensure it's valid
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError("Invalid timestamp format. Expected ISO 8601 format.")
        return v


class WebhookResponse(BaseModel):
    """Response schema for webhook endpoint."""
    status: str = Field(..., description="Status of webhook processing")
    message: str = Field(..., description="Human-readable message")
    submission_id: Optional[str] = Field(None, description="ID of created submission record")
