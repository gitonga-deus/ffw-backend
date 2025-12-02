from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db, get_current_user, get_current_verified_user
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    EmailVerification,
    ForgotPassword,
    ResetPassword,
    UserProfileUpdate,
    ChangePassword,
    MessageResponse
)
from app.services.auth_service import auth_service
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    email: str = Form(...),
    phone_number: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    profile_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - Validates user data
    - Handles profile image upload to Vercel Blob
    - Creates user account with hashed password
    - Sends verification email
    - Returns success message
    """
    try:
        # Handle profile image upload if provided
        profile_image_url = None
        if profile_image:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if profile_image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
                )
            
            # Validate file size (5MB max)
            file_data = await profile_image.read()
            if len(file_data) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 5MB limit."
                )
            
            # Upload to Vercel Blob
            from app.services.storage_service import storage_service
            import uuid
            filename = f"profiles/{uuid.uuid4()}_{profile_image.filename}"
            profile_image_url = await storage_service.upload_file(
                file_data=file_data,
                filename=filename,
                content_type=profile_image.content_type
            )
        
        # Create user data object
        user_data = UserRegister(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            password=password,
            confirm_password=confirm_password,
            profile_image_url=profile_image_url
        )
        
        user, token = await auth_service.register_user(db, user_data)
        
        return MessageResponse(
            message="Registration successful. Please check your email to verify your account."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    verification: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    Verify user email with token.
    
    - Validates verification token
    - Marks user as verified
    - Returns success message
    """
    try:
        user = auth_service.verify_email(db, verification.token)
        
        return MessageResponse(
            message="Email verified successfully. You can now log in."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    - Validates credentials
    - Checks email verification status
    - Updates last login timestamp
    - Returns access and refresh tokens with user data
    """
    try:
        user, tokens = auth_service.login_user(db, login_data)
        
        # Construct complete TokenResponse with user data
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    forgot_data: ForgotPassword,
    db: Session = Depends(get_db)
):
    """
    Send password reset email.
    
    - Generates reset token
    - Sends reset email
    - Returns success message (even if email doesn't exist for security)
    """
    try:
        await auth_service.forgot_password(db, forgot_data.email)
        
        return MessageResponse(
            message="If an account exists with this email, a password reset link has been sent."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    reset_data: ResetPassword,
    db: Session = Depends(get_db)
):
    """
    Reset user password with token.
    
    - Validates reset token
    - Updates password
    - Returns success message
    """
    try:
        user = auth_service.reset_password(db, reset_data.token, reset_data.new_password)
        
        return MessageResponse(
            message="Password reset successfully. You can now log in with your new password."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get current authenticated user information.
    
    - Requires valid JWT token
    - Returns user profile data
    """
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Generates new access token
    - Returns new token pair
    """
    from app.utils.security import create_access_token, create_refresh_token
    
    token_data = {
        "sub": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    from app.config import settings
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,  # in seconds
        user=UserResponse.model_validate(current_user)
    )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    full_name: str = Form(...),
    email: str = Form(...),
    phone_number: str = Form(...),
    profile_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information.
    
    - Updates user details
    - Handles profile image upload if provided
    - Returns updated user data
    """
    try:
        # Handle profile image upload if provided
        profile_image_url = current_user.profile_image_url
        if profile_image:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if profile_image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed."
                )
            
            # Validate file size (5MB max)
            file_data = await profile_image.read()
            if len(file_data) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 5MB limit."
                )
            
            # Upload to Vercel Blob
            from app.services.storage_service import storage_service
            import uuid
            filename = f"profiles/{uuid.uuid4()}_{profile_image.filename}"
            profile_image_url = await storage_service.upload_file(
                file_data=file_data,
                filename=filename,
                content_type=profile_image.content_type
            )
        
        # Update user profile
        current_user.full_name = full_name
        current_user.email = email
        current_user.phone_number = phone_number
        if profile_image_url:
            current_user.profile_image_url = profile_image_url
        
        db.commit()
        db.refresh(current_user)
        
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    - Validates current password
    - Updates to new password
    - Returns success message
    """
    try:
        from app.utils.security import verify_password, get_password_hash
        
        # Verify current password
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Update password
        current_user.password_hash = get_password_hash(new_password)
        db.commit()
        
        return MessageResponse(
            message="Password changed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )
