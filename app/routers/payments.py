from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.payment import Payment
from app.schemas.user import PaymentHistoryItem

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/my-history", response_model=List[PaymentHistoryItem])
async def get_my_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get payment history for the current user.
    
    Returns all payments made by the authenticated user, ordered by date.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    
    return [PaymentHistoryItem.model_validate(payment) for payment in payments]
