from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PaymentInitiateRequest(BaseModel):
    """Request to initiate payment and enrollment."""
    pass  # No additional fields needed, user comes from auth


class PaymentInitiateResponse(BaseModel):
    """Response with payment URL."""
    payment_id: str
    payment_url: str
    amount: Decimal
    currency: str = "KES"


class PaymentCallbackRequest(BaseModel):
    """iPay Africa webhook callback data."""
    # Based on iPay Africa C2B documentation
    txncd: str = Field(..., description="Transaction code/ID from iPay")
    msisdn: Optional[str] = Field(None, description="Customer phone number")
    mc: Optional[str] = Field(None, description="Merchant code")
    p1: Optional[str] = Field(None, description="Custom parameter 1 - payment_id")
    p2: Optional[str] = Field(None, description="Custom parameter 2")
    p3: Optional[str] = Field(None, description="Custom parameter 3")
    p4: Optional[str] = Field(None, description="Custom parameter 4")
    status: str = Field(..., description="Payment status")
    mc_gross: Optional[str] = Field(None, description="Amount paid")
    channel: Optional[str] = Field(None, description="Payment channel")


class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    payment_id: str
    status: str
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    ipay_transaction_id: Optional[str] = None
    ipay_reference: Optional[str] = None
    
    class Config:
        from_attributes = True
