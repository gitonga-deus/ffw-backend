from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserLogin
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_verification_token,
    generate_reset_token
)
from app.services.email_service import email_service


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    async def register_user(db: Session, user_data: UserRegister) -> Tuple[User, str]:
        """
        Register a new user.
        
        Returns:
            Tuple of (User, verification_token)
        """
        # In development mode with Resend, only allow specific test email
        from app.config import settings
        if settings.allowed_test_email and user_data.email != settings.allowed_test_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration is currently limited to {settings.allowed_test_email} for testing. Please use this email or contact support."
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            or_(
                User.email == user_data.email,
                User.phone_number == user_data.phone_number
            )
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already registered"
                )
        
        # Generate verification token
        verification_token = generate_verification_token()
        token_expiry = datetime.utcnow() + timedelta(hours=24)
        
        # Create new user
        new_user = User(
            email=user_data.email,
            phone_number=user_data.phone_number,
            full_name=user_data.full_name,
            password_hash=hash_password(user_data.password),
            profile_image_url=user_data.profile_image_url,
            role=UserRole.STUDENT.value,
            is_verified=False,
            is_enrolled=False,
            verification_token=verification_token,
            verification_token_expires_at=token_expiry
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send verification email (non-blocking - don't fail registration if email fails)
        try:
            email_result = await email_service.send_verification_email(
                to=new_user.email,
                full_name=new_user.full_name,
                token=verification_token
            )
            if not email_result.get("success"):
                print(f"Warning: Verification email failed for {new_user.email}: {email_result.get('error')}")
        except Exception as e:
            # Log the error but don't fail registration
            print(f"Error sending verification email to {new_user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            # User is still created, they can request a new verification email later
        
        return new_user, verification_token
    
    @staticmethod
    def verify_email(db: Session, token: str) -> User:
        """Verify user email with token."""
        user = db.query(User).filter(User.verification_token == token).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        if user.verification_token_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Update user
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> Tuple[User, dict]:
        """
        Authenticate user and generate tokens.
        
        Returns:
            Tuple of (User, tokens_dict)
        """
        # Find user by email
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if email is verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in"
            )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Generate tokens
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        from app.config import settings
        
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60  # in seconds
        }
        
        return user, tokens
    
    @staticmethod
    async def forgot_password(db: Session, email: str) -> bool:
        """Send password reset email."""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Don't reveal if email exists
            return True
        
        # Generate reset token
        reset_token = generate_reset_token()
        token_expiry = datetime.utcnow() + timedelta(hours=1)
        
        user.reset_password_token = reset_token
        user.reset_password_token_expires_at = token_expiry
        
        db.commit()
        
        # Send reset email
        await email_service.send_password_reset_email(
            to=user.email,
            full_name=user.full_name,
            token=reset_token
        )
        
        return True
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> User:
        """Reset user password with token."""
        user = db.query(User).filter(User.reset_password_token == token).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        if user.reset_password_token_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired"
            )
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.reset_password_token = None
        user.reset_password_token_expires_at = None
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()


auth_service = AuthService()
