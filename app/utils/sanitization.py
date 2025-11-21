"""
Input sanitization utilities for user-generated content.
Prevents XSS, SQL injection, and other security vulnerabilities.
"""
import re
import html
from typing import Optional, Any, Dict, List
import bleach


# Allowed HTML tags for rich text content (very restrictive)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'span'
]

# Allowed HTML attributes
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': ['class'],
    'code': ['class']
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(text: str, strip: bool = False) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        text: HTML text to sanitize
        strip: If True, strip all HTML tags. If False, allow safe tags.
    
    Returns:
        Sanitized HTML string
    """
    if not text:
        return ""
    
    if strip:
        # Strip all HTML tags
        return bleach.clean(text, tags=[], strip=True)
    
    # Allow only safe HTML tags and attributes
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    return cleaned


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a plain text string.
    Removes control characters and optionally truncates.
    
    Args:
        text: Text to sanitize
        max_length: Maximum length (optional)
    
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email address.
    
    Args:
        email: Email address to sanitize
    
    Returns:
        Sanitized email address
    
    Raises:
        ValueError: If email format is invalid
    """
    if not email:
        raise ValueError("Email cannot be empty")
    
    # Remove whitespace
    email = email.strip().lower()
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    # Check for suspicious patterns
    if '..' in email or email.startswith('.') or email.endswith('.'):
        raise ValueError("Invalid email format")
    
    return email


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number.
    Removes non-numeric characters except + at the start.
    
    Args:
        phone: Phone number to sanitize
    
    Returns:
        Sanitized phone number
    """
    if not phone:
        return ""
    
    # Remove whitespace
    phone = phone.strip()
    
    # Keep only digits and + at the start
    if phone.startswith('+'):
        phone = '+' + re.sub(r'[^\d]', '', phone[1:])
    else:
        phone = re.sub(r'[^\d]', '', phone)
    
    return phone


def sanitize_url(url: str, allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Sanitize URL to prevent javascript: and data: schemes.
    
    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed URL schemes (default: http, https)
    
    Returns:
        Sanitized URL
    
    Raises:
        ValueError: If URL scheme is not allowed
    """
    if not url:
        return ""
    
    url = url.strip()
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    # Check for dangerous schemes
    dangerous_schemes = ['javascript:', 'data:', 'vbscript:', 'file:']
    url_lower = url.lower()
    
    for scheme in dangerous_schemes:
        if url_lower.startswith(scheme):
            raise ValueError(f"URL scheme '{scheme}' is not allowed")
    
    # Validate allowed schemes
    if '://' in url:
        scheme = url.split('://')[0].lower()
        if scheme not in allowed_schemes:
            raise ValueError(f"URL scheme '{scheme}' is not allowed")
    
    return url


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Filename to sanitize
    
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Keep only safe characters
    filename = re.sub(r'[^\w\s\-\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename or "unnamed"


def sanitize_json_content(data: Any) -> Any:
    """
    Recursively sanitize JSON content.
    Sanitizes strings while preserving structure.
    
    Args:
        data: JSON data to sanitize (dict, list, or primitive)
    
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return {key: sanitize_json_content(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_content(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(data)
    else:
        return data


def validate_file_type(filename: str, content_type: str, allowed_types: List[str]) -> bool:
    """
    Validate file type based on extension and MIME type.
    
    Args:
        filename: Name of the file
        content_type: MIME type from upload
        allowed_types: List of allowed MIME types
    
    Returns:
        True if file type is valid
    
    Raises:
        ValueError: If file type is not allowed
    """
    if not filename or not content_type:
        raise ValueError("Filename and content type are required")
    
    # Check MIME type
    if content_type not in allowed_types:
        raise ValueError(f"File type '{content_type}' is not allowed")
    
    # Check file extension
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Map MIME types to extensions
    mime_to_ext = {
        'image/jpeg': ['jpg', 'jpeg'],
        'image/png': ['png'],
        'image/webp': ['webp'],
        'image/gif': ['gif'],
        'application/pdf': ['pdf'],
        'video/mp4': ['mp4'],
        'video/webm': ['webm']
    }
    
    allowed_extensions = []
    for mime in allowed_types:
        allowed_extensions.extend(mime_to_ext.get(mime, []))
    
    if extension not in allowed_extensions:
        raise ValueError(f"File extension '.{extension}' is not allowed")
    
    return True


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size.
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes
    
    Returns:
        True if file size is valid
    
    Raises:
        ValueError: If file size exceeds limit
    """
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise ValueError(f"File size exceeds {max_mb:.1f}MB limit")
    
    return True


def sanitize_review_text(text: str) -> str:
    """
    Sanitize review text specifically.
    Removes HTML, limits length, and checks for spam patterns.
    
    Args:
        text: Review text to sanitize
    
    Returns:
        Sanitized review text
    """
    if not text:
        return ""
    
    # Strip all HTML
    text = sanitize_html(text, strip=True)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Check length constraints (10-1000 chars as per requirements)
    if len(text) < 10:
        raise ValueError("Review text must be at least 10 characters")
    if len(text) > 1000:
        raise ValueError("Review text must not exceed 1000 characters")
    
    # Check for spam patterns (excessive repetition)
    words = text.lower().split()
    if len(words) > 5:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            raise ValueError("Review text appears to be spam")
    
    return text


def sanitize_announcement(title: str, content: str) -> tuple[str, str]:
    """
    Sanitize announcement title and content.
    
    Args:
        title: Announcement title
        content: Announcement content
    
    Returns:
        Tuple of (sanitized_title, sanitized_content)
    """
    # Sanitize title (plain text only)
    title = sanitize_string(title, max_length=255)
    if not title:
        raise ValueError("Announcement title cannot be empty")
    
    # Sanitize content (allow some HTML formatting)
    content = sanitize_html(content, strip=False)
    if not content:
        raise ValueError("Announcement content cannot be empty")
    
    return title, content
