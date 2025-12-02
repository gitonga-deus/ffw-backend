import hashlib
import hmac
import logging
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.config import settings
from app.models.payment import Payment, PaymentStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment processing with iPay Africa."""
    
    def __init__(self):
        self.vendor_id = settings.ipay_vendor_id
        self.secret_key = settings.ipay_secret_key
        self.base_url = "https://payments.ipayafrica.com/v3/ke"
        self.callback_url = f"{settings.backend_url}/enrollment/callback"
    
    def create_payment_record(
        self,
        db: Session,
        user_id: str,
        amount: float = 1000.00,
        currency: str = "KES"
    ) -> Payment:
        """Create a payment record in the database."""
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING.value,
            expires_at=expires_at,
            webhook_attempts="0"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
    
    def generate_payment_url(self, payment: Payment, user: User) -> str:
        """Generate iPay Africa payment URL based on official PHP implementation."""
        
        # Determine mode
        is_demo = self.vendor_id == "demo"
        live_mode = "0" if is_demo else "1"
        vendor_id = "demo" if is_demo else self.vendor_id
        hash_key = "demoCHANGED" if is_demo else self.secret_key
        
        # Format phone number (remove non-digits, ensure 254 prefix)
        phone = user.phone_number or ""
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif not phone.startswith("254"):
            phone = "254" + phone if phone else ""
        
        # Build fields exactly as in PHP example
        fields = {
            "live": live_mode,
            "oid": str(payment.id),
            "inv": str(payment.id),
            "ttl": str(int(payment.amount)),
            "tel": phone,
            "eml": user.email,
            "vid": vendor_id,
            "curr": payment.currency,
            "p1": str(payment.id),
            "p2": str(user.id),
            "p3": "",
            "p4": "",
            "cbk": self.callback_url,
            "cst": "1",
            "crl": "2"  # As per PHP example
        }
        
        # Generate datastring - exact order as PHP
        datastring = (
            fields['live'] +
            fields['oid'] +
            fields['inv'] +
            fields['ttl'] +
            fields['tel'] +
            fields['eml'] +
            fields['vid'] +
            fields['curr'] +
            fields['p1'] +
            fields['p2'] +
            fields['p3'] +
            fields['p4'] +
            fields['cbk'] +
            fields['cst'] +
            fields['crl']
        )
        
        # Generate hash using HMAC-SHA1 (same as PHP hash_hmac)
        generated_hash = hmac.new(
            hash_key.encode('utf-8'),
            datastring.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        fields["hsh"] = generated_hash
        
        logger.info(f"Payment URL generated for {payment.id}, amount: {fields['ttl']}")
        
        # Build URL
        query_string = "&".join([f"{k}={v}" for k, v in fields.items()])
        return f"{self.base_url}?{query_string}"
    
    def verify_callback_signature(self, callback_data: Dict[str, Any]) -> bool:
        """Verify iPay callback signature."""
        is_demo = self.vendor_id == "demo"
        
        # Demo mode: basic validation
        if is_demo:
            return "status" in callback_data
        
        # Production: verify hash
        received_hash = callback_data.get("hsh", "")
        if not received_hash:
            return False
        
        hash_key = self.secret_key
        
        # Reconstruct datastring
        datastring = (
            str(callback_data.get('live', '')) +
            str(callback_data.get('oid', '')) +
            str(callback_data.get('inv', '')) +
            str(callback_data.get('ttl', '')) +
            str(callback_data.get('tel', '')) +
            str(callback_data.get('eml', '')) +
            str(callback_data.get('vid', '')) +
            str(callback_data.get('curr', '')) +
            str(callback_data.get('p1', '')) +
            str(callback_data.get('p2', '')) +
            str(callback_data.get('p3', '')) +
            str(callback_data.get('p4', '')) +
            str(callback_data.get('cbk', '')) +
            str(callback_data.get('cst', '')) +
            str(callback_data.get('crl', ''))
        )
        
        computed_hash = hmac.new(
            hash_key.encode('utf-8'),
            datastring.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return received_hash.lower() == computed_hash.lower()
    
    def update_payment_status(
        self,
        db: Session,
        payment_id: str,
        status: str,
        ipay_transaction_id: Optional[str] = None,
        ipay_reference: Optional[str] = None,
        payment_method: Optional[str] = None,
        metadata: Optional[str] = None
    ) -> Optional[Payment]:
        """Update payment status."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            return None
        
        payment.status = status
        if ipay_transaction_id:
            payment.ipay_transaction_id = ipay_transaction_id
        if ipay_reference:
            payment.ipay_reference = ipay_reference
        if payment_method:
            payment.payment_method = payment_method
        if metadata:
            payment.payment_metadata = metadata
        
        payment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)
        return payment
    
    def get_payment_by_id(self, db: Session, payment_id: str) -> Optional[Payment]:
        """Get payment by ID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    def increment_webhook_attempts(self, db: Session, payment_id: str) -> None:
        """Increment webhook retry attempts counter."""
        if not payment_id:
            return
        
        payment = self.get_payment_by_id(db, payment_id)
        if payment:
            try:
                attempts = int(payment.webhook_attempts or "0")
                payment.webhook_attempts = str(attempts + 1)
                db.commit()
                logger.info(f"Webhook attempt {payment.webhook_attempts} for payment {payment_id}")
            except Exception as e:
                logger.error(f"Failed to increment webhook attempts: {e}")
                db.rollback()
    
    def get_failed_webhooks(self, db: Session, max_attempts: int = 5) -> list[Payment]:
        """Get payments with failed webhooks that can be retried."""
        return db.query(Payment).filter(
            Payment.status == PaymentStatus.PENDING.value,
            Payment.webhook_attempts.cast(db.Integer) < max_attempts,
            Payment.expires_at > datetime.utcnow()
        ).all()
    
    def retry_webhook(self, db: Session, payment_id: str) -> bool:
        """
        Retry webhook processing for a payment.
        Returns True if retry is allowed, False otherwise.
        """
        payment = self.get_payment_by_id(db, payment_id)
        if not payment:
            return False
        
        try:
            attempts = int(payment.webhook_attempts or "0")
            if attempts >= 5:
                logger.warning(f"Payment {payment_id} exceeded max webhook attempts")
                # Mark as failed after max attempts
                payment.status = PaymentStatus.FAILED.value
                payment.payment_metadata = json.dumps({
                    "error": "Max webhook retry attempts exceeded",
                    "attempts": attempts
                })
                db.commit()
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking webhook retry: {e}")
            return False
    
    def expire_old_payments(self, db: Session) -> int:
        """
        Expire old pending payments that are past their expiration time.
        
        Returns:
            Number of payments expired
        """
        try:
            # Find all pending payments that have expired
            expired_payments = db.query(Payment).filter(
                Payment.status == PaymentStatus.PENDING.value,
                Payment.expires_at < datetime.utcnow()
            ).all()
            
            count = 0
            for payment in expired_payments:
                payment.status = PaymentStatus.FAILED.value
                payment_metadata = json.loads(payment.payment_metadata) if payment.payment_metadata else {}
                payment_metadata['expired_at'] = datetime.utcnow().isoformat()
                payment_metadata['reason'] = 'Payment expired (30 minutes timeout)'
                payment.payment_metadata = json.dumps(payment_metadata)
                count += 1
            
            if count > 0:
                db.commit()
                logger.info(f"Expired {count} old pending payments")
            
            return count
        except Exception as e:
            logger.error(f"Error expiring old payments: {e}", exc_info=True)
            db.rollback()
            return 0


# Singleton instance
payment_service = PaymentService()
