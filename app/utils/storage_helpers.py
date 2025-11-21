"""
Helper functions for file storage operations.
Provides convenient wrappers around the storage service.
"""
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from app.services.storage_service import storage_service
from app.utils.file_validation import FileValidator
import uuid
from datetime import datetime


async def upload_profile_image(file: UploadFile) -> str:
    """
    Upload a user profile image.
    
    Args:
        file: The uploaded file
        
    Returns:
        URL of the uploaded image
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate image
    file_data, content_type = await FileValidator.validate_image(file)
    
    # Generate unique filename
    ext = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"profiles/{uuid.uuid4()}.{ext}"
    
    # Upload to storage
    url = await storage_service.upload_image(
        file_data=file_data,
        filename=filename,
        content_type=content_type
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile image"
        )
    
    return url


async def upload_signature_image(file: UploadFile, user_id: str) -> str:
    """
    Upload a digital signature image.
    
    Args:
        file: The uploaded signature file
        user_id: ID of the user
        
    Returns:
        URL of the uploaded signature
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate signature image (smaller size limit)
    file_data, content_type = await FileValidator.validate_image(
        file,
        max_size=1 * 1024 * 1024,  # 1MB for signatures
        allowed_types=['image/png', 'image/jpeg']
    )
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = file.filename.split('.')[-1] if file.filename else 'png'
    filename = f"signatures/{user_id}_{timestamp}.{ext}"
    
    # Upload to storage
    url = await storage_service.upload_image(
        file_data=file_data,
        filename=filename,
        content_type=content_type
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload signature"
        )
    
    return url


async def upload_course_pdf(file: UploadFile, content_id: str) -> Tuple[str, str]:
    """
    Upload a course PDF file.
    
    Args:
        file: The uploaded PDF file
        content_id: ID of the content
        
    Returns:
        Tuple of (url, filename)
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate PDF
    file_data, content_type = await FileValidator.validate_pdf(file)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_filename = FileValidator.validate_filename(file.filename)
    filename = f"course-pdfs/{content_id}_{timestamp}_{safe_filename}"
    
    # Upload to storage
    url = await storage_service.upload_pdf(
        file_data=file_data,
        filename=filename
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload PDF"
        )
    
    return url, safe_filename


async def upload_course_thumbnail(file: UploadFile) -> str:
    """
    Upload a course thumbnail image.
    
    Args:
        file: The uploaded thumbnail file
        
    Returns:
        URL of the uploaded thumbnail
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate image
    file_data, content_type = await FileValidator.validate_image(file)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"thumbnails/course_{timestamp}.{ext}"
    
    # Upload to storage
    url = await storage_service.upload_image(
        file_data=file_data,
        filename=filename,
        content_type=content_type
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload thumbnail"
        )
    
    return url


async def upload_instructor_image(file: UploadFile) -> str:
    """
    Upload an instructor profile image.
    
    Args:
        file: The uploaded image file
        
    Returns:
        URL of the uploaded image
        
    Raises:
        HTTPException: If upload fails
    """
    # Validate image
    file_data, content_type = await FileValidator.validate_image(file)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ext = file.filename.split('.')[-1] if file.filename else 'jpg'
    filename = f"instructors/instructor_{timestamp}.{ext}"
    
    # Upload to storage
    url = await storage_service.upload_image(
        file_data=file_data,
        filename=filename,
        content_type=content_type
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload instructor image"
        )
    
    return url


async def upload_certificate(
    pdf_data: bytes,
    user_id: str,
    cert_id: str
) -> str:
    """
    Upload a generated certificate PDF.
    
    Args:
        pdf_data: The certificate PDF as bytes
        user_id: ID of the user
        cert_id: Certification ID
        
    Returns:
        URL of the uploaded certificate
        
    Raises:
        HTTPException: If upload fails
    """
    # Generate filename
    filename = f"certificates/{user_id}_{cert_id}.pdf"
    
    # Upload to storage
    url = await storage_service.upload_pdf(
        file_data=pdf_data,
        filename=filename
    )
    
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload certificate"
        )
    
    return url


def get_signed_pdf_url(url: str, expires_in: int = 3600) -> str:
    """
    Get a signed URL for a PDF file.
    
    Args:
        url: The PDF URL
        expires_in: Expiration time in seconds (default: 1 hour)
        
    Returns:
        Signed URL
    """
    return storage_service.get_signed_url(url, expires_in)


def get_certificate_download_url(
    url: str,
    student_name: str,
    expires_in: int = 3600
) -> str:
    """
    Get a download URL for a certificate.
    
    Args:
        url: The certificate URL
        student_name: Name of the student for filename
        expires_in: Expiration time in seconds (default: 1 hour)
        
    Returns:
        Signed download URL
    """
    # Sanitize student name for filename
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_'))
    safe_name = safe_name.replace(' ', '_')
    filename = f"Certificate_{safe_name}.pdf"
    
    return storage_service.get_download_url(url, filename, expires_in)


async def delete_file_safe(url: Optional[str]) -> bool:
    """
    Safely delete a file, handling None URLs.
    
    Args:
        url: The file URL (can be None)
        
    Returns:
        True if deleted or URL was None, False if deletion failed
    """
    if not url:
        return True
    
    return await storage_service.delete_file(url)


async def replace_file(
    old_url: Optional[str],
    new_file: UploadFile,
    upload_func
) -> str:
    """
    Replace an existing file with a new one.
    
    Args:
        old_url: URL of the old file to delete
        new_file: New file to upload
        upload_func: Function to use for uploading (e.g., upload_profile_image)
        
    Returns:
        URL of the new file
    """
    # Upload new file first
    new_url = await upload_func(new_file)
    
    # Delete old file if it exists
    if old_url:
        await storage_service.delete_file(old_url)
    
    return new_url
