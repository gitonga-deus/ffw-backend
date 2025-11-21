"""
File upload validation utilities.
Validates file types, sizes, and content for security.
"""
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException, status
from pathlib import Path


# File size limits (in bytes)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PDF_SIZE = 20 * 1024 * 1024   # 20MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB (if needed)

# Allowed MIME types
ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif'
]

ALLOWED_PDF_TYPES = [
    'application/pdf'
]

ALLOWED_DOCUMENT_TYPES = ALLOWED_PDF_TYPES + [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
]


class FileValidator:
    """Validator for uploaded files."""
    
    @staticmethod
    async def validate_image(
        file: UploadFile,
        max_size: int = MAX_IMAGE_SIZE,
        allowed_types: Optional[List[str]] = None
    ) -> Tuple[bytes, str]:
        """
        Validate image file upload.
        
        Args:
            file: Uploaded file
            max_size: Maximum file size in bytes
            allowed_types: List of allowed MIME types
        
        Returns:
            Tuple of (file_data, content_type)
        
        Raises:
            HTTPException: If validation fails
        """
        if allowed_types is None:
            allowed_types = ALLOWED_IMAGE_TYPES
        
        # Read file data
        file_data = await file.read()
        
        # Validate size
        if len(file_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {max_size / (1024 * 1024):.1f}MB limit"
            )
        
        # Validate MIME type from header
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate actual file content (magic bytes)
        # Check for common image file signatures
        image_signatures = {
            b'\xFF\xD8\xFF': 'jpeg',  # JPEG
            b'\x89PNG\r\n\x1a\n': 'png',  # PNG
            b'RIFF': 'webp',  # WebP (followed by WEBP)
            b'GIF87a': 'gif',  # GIF87a
            b'GIF89a': 'gif',  # GIF89a
        }
        
        is_valid_image = False
        for signature, img_type in image_signatures.items():
            if file_data.startswith(signature):
                is_valid_image = True
                break
        
        if not is_valid_image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match image type"
            )
        
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check for dangerous extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.sh', '.php', '.js', '.html']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext in dangerous_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension not allowed"
            )
        
        return file_data, file.content_type
    
    @staticmethod
    async def validate_pdf(
        file: UploadFile,
        max_size: int = MAX_PDF_SIZE
    ) -> Tuple[bytes, str]:
        """
        Validate PDF file upload.
        
        Args:
            file: Uploaded file
            max_size: Maximum file size in bytes
        
        Returns:
            Tuple of (file_data, content_type)
        
        Raises:
            HTTPException: If validation fails
        """
        # Read file data
        file_data = await file.read()
        
        # Validate size
        if len(file_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {max_size / (1024 * 1024):.1f}MB limit"
            )
        
        # Validate MIME type
        if file.content_type not in ALLOWED_PDF_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF files are allowed"
            )
        
        # Validate PDF magic bytes
        if not file_data.startswith(b'%PDF'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match PDF format"
            )
        
        # Validate filename
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF filename"
            )
        
        return file_data, file.content_type
    
    @staticmethod
    async def validate_file(
        file: UploadFile,
        allowed_types: List[str],
        max_size: int
    ) -> Tuple[bytes, str]:
        """
        Generic file validation.
        
        Args:
            file: Uploaded file
            allowed_types: List of allowed MIME types
            max_size: Maximum file size in bytes
        
        Returns:
            Tuple of (file_data, content_type)
        
        Raises:
            HTTPException: If validation fails
        """
        # Read file data
        file_data = await file.read()
        
        # Validate size
        if len(file_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {max_size / (1024 * 1024):.1f}MB limit"
            )
        
        # Validate MIME type
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check for dangerous extensions
        dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.sh', '.php', '.js', '.html',
            '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
        ]
        file_ext = Path(file.filename).suffix.lower()
        if file_ext in dangerous_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension not allowed"
            )
        
        return file_data, file.content_type
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize filename.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        
        Raises:
            HTTPException: If filename is invalid
        """
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Check for directory traversal attempts
        if '..' in filename or filename.startswith('.'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Limit length
        if len(filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long (max 255 characters)"
            )
        
        return filename


# Convenience functions
async def validate_profile_image(file: UploadFile) -> Tuple[bytes, str]:
    """Validate profile image upload."""
    return await FileValidator.validate_image(file, max_size=MAX_IMAGE_SIZE)


async def validate_course_pdf(file: UploadFile) -> Tuple[bytes, str]:
    """Validate course PDF upload."""
    return await FileValidator.validate_pdf(file, max_size=MAX_PDF_SIZE)


async def validate_signature_image(file: UploadFile) -> Tuple[bytes, str]:
    """Validate signature image upload."""
    return await FileValidator.validate_image(
        file,
        max_size=1 * 1024 * 1024,  # 1MB for signatures
        allowed_types=['image/png', 'image/jpeg']
    )
