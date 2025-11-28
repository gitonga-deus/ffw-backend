"""
Security middleware for the LMS application.
Includes CSRF protection, CSP headers, and security headers.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import secrets
import hmac
import hashlib


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    Includes Content Security Policy, X-Frame-Options, etc.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Skip adding security headers for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return response
        
        # Content Security Policy
        # Adjust these directives based on your needs
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://player.vimeo.com https://f.vimeocdn.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "media-src 'self' https://player.vimeo.com https://*.vimeocdn.com",
            "frame-src 'self' https://player.vimeo.com https://checkout.ipayafrica.com",
            "connect-src 'self' https://player.vimeo.com https://api.resend.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self' https://checkout.ipayafrica.com",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=(self)",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Strict Transport Security (HSTS) - only in production with HTTPS
        # Uncomment in production:
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware for state-changing operations.
    Uses double-submit cookie pattern.
    """
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_paths = {
            "/api/enrollment/callback",  # iPay webhook
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Validate CSRF token for state-changing requests."""
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            # Set CSRF token cookie for future requests
            if "csrf_token" not in request.cookies:
                csrf_token = self._generate_csrf_token()
                response.set_cookie(
                    key="csrf_token",
                    value=csrf_token,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="lax",
                    max_age=3600 * 24  # 24 hours
                )
            return response
        
        # Skip CSRF check for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip CSRF check for webhook endpoints (they use signature verification)
        if "/callback" in request.url.path or "/webhook" in request.url.path:
            return await call_next(request)
        
        # Validate CSRF token
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        if not csrf_cookie or not csrf_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )
        
        if not self._validate_csrf_token(csrf_cookie, csrf_header):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token invalid"
            )
        
        response = await call_next(request)
        return response
    
    def _generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)
    
    def _validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """Validate CSRF token using constant-time comparison."""
        if not cookie_token or not header_token:
            return False
        
        # Use HMAC for constant-time comparison
        return hmac.compare_digest(cookie_token, header_token)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation and sanitization.
    Checks request size, content type, and other security aspects.
    """
    
    def __init__(self, app, max_request_size: int = 20 * 1024 * 1024):  # 20MB default
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next):
        """Validate request before processing."""
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Maximum size is {self.max_request_size} bytes."
            )
        
        # Validate content type for POST/PUT/PATCH requests
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get("content-type", "")
            
            # Allow multipart/form-data, application/json, application/x-www-form-urlencoded
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            
            if not any(allowed in content_type for allowed in allowed_types):
                # Skip validation for empty body
                if content_length and int(content_length) > 0:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Unsupported content type"
                    )
        
        response = await call_next(request)
        return response
