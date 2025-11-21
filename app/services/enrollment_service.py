import base64
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.user import User
from app.services.storage_service import storage_service


class EnrollmentService:
    """Service for handling course enrollment."""
    
    def create_enrollment(
        self,
        db: Session,
        user_id: str,
        payment_id: str
    ) -> Enrollment:
        """
        Create an enrollment record.
        
        Args:
            db: Database session
            user_id: User ID
            payment_id: Payment ID
            
        Returns:
            Enrollment object
        """
        enrollment = Enrollment(
            user_id=user_id,
            payment_id=payment_id,
            enrolled_at=datetime.utcnow(),
            progress_percentage=0.00
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment
    
    def get_enrollment_by_user_id(
        self,
        db: Session,
        user_id: str
    ) -> Optional[Enrollment]:
        """Get enrollment by user ID."""
        return db.query(Enrollment).filter(Enrollment.user_id == user_id).first()
    
    def update_user_enrollment_status(
        self,
        db: Session,
        user_id: str,
        is_enrolled: bool
    ) -> Optional[User]:
        """
        Update user's enrollment status.
        
        Args:
            db: Database session
            user_id: User ID
            is_enrolled: Enrollment status
            
        Returns:
            Updated User object or None if not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        user.is_enrolled = is_enrolled
        db.commit()
        db.refresh(user)
        return user
    
    async def submit_signature(
        self,
        db: Session,
        user_id: str,
        signature_data: str
    ) -> Optional[Enrollment]:
        """
        Submit digital signature for enrollment.
        
        Args:
            db: Database session
            user_id: User ID
            signature_data: Base64 encoded signature image
            
        Returns:
            Updated Enrollment object or None if not found
        """
        enrollment = self.get_enrollment_by_user_id(db, user_id)
        if not enrollment:
            return None
        
        # Decode base64 signature data
        try:
            # Remove data URL prefix if present (e.g., "data:image/png;base64,")
            if "," in signature_data:
                signature_data = signature_data.split(",")[1]
            
            signature_bytes = base64.b64decode(signature_data)
            
            # Upload to Vercel Blob
            filename = f"signatures/{user_id}_{int(datetime.utcnow().timestamp())}.png"
            signature_url = await storage_service.upload_file(
                file_data=signature_bytes,
                filename=filename,
                content_type="image/png"
            )
            
            if signature_url:
                enrollment.signature_url = signature_url
                enrollment.signature_created_at = datetime.utcnow()
                db.commit()
                db.refresh(enrollment)
                return enrollment
            
        except Exception as e:
            print(f"Failed to process signature: {str(e)}")
            return None
        
        return None
    
    def get_enrollment_status(
        self,
        db: Session,
        user_id: str
    ) -> dict:
        """
        Get comprehensive enrollment status for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Dictionary with enrollment status details
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "is_enrolled": False,
                "has_signature": False
            }
        
        enrollment = self.get_enrollment_by_user_id(db, user_id)
        
        result = {
            "is_enrolled": user.is_enrolled,
            "has_signature": False,
            "enrollment": None,
            "payment": None
        }
        
        if enrollment:
            result["has_signature"] = enrollment.signature_url is not None
            result["enrollment"] = {
                "id": enrollment.id,
                "enrolled_at": enrollment.enrolled_at,
                "completed_at": enrollment.completed_at,
                "progress_percentage": enrollment.progress_percentage,
                "last_accessed_at": enrollment.last_accessed_at,
                "signature_url": enrollment.signature_url,
                "signature_created_at": enrollment.signature_created_at
            }
            
            # Get payment info if available
            if enrollment.payment_id:
                payment = db.query(Payment).filter(
                    Payment.id == enrollment.payment_id
                ).first()
                if payment:
                    result["payment"] = {
                        "id": payment.id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "status": payment.status,
                        "created_at": payment.created_at
                    }
        
        return result


# Singleton instance
enrollment_service = EnrollmentService()
