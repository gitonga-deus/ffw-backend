"""
Rate limiting middleware for API endpoints.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    For production, use Redis-based rate limiting (e.g., slowapi, fastapi-limiter).
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            "/api/enrollment/initiate": (20, 3600),  # 20 calls per hour
            "/api/enrollment/callback": (100, 60),   # 100 calls per minute
            "/api/auth/login": (20, 300),            # 20 calls per 5 minutes
            "/api/auth/register": (10, 3600),        # 10 calls per hour
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP + user if authenticated)
        client_id = self._get_client_id(request)
        
        # Get rate limit for this endpoint
        calls, period = self._get_rate_limit(request.url.path)
        
        # Check rate limit
        async with self.lock:
            now = datetime.utcnow()
            
            # Clean old entries
            self.clients[client_id] = [
                timestamp for timestamp in self.clients[client_id]
                if now - timestamp < timedelta(seconds=period)
            ]
            
            # Check if limit exceeded
            if len(self.clients[client_id]) >= calls:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": period
                    },
                    headers={"Retry-After": str(period)}
                )
            
            # Add current request
            self.clients[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = calls - len(self.clients[client_id])
        response.headers["X-RateLimit-Limit"] = str(calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(seconds=period)).timestamp()))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Use IP address as base
        client_ip = request.client.host if request.client else "unknown"
        
        # Add user ID if authenticated
        user_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Extract user ID from token (simplified - in production, decode JWT)
            try:
                from app.utils.security import decode_token
                token = auth_header.split(" ")[1]
                token_data = decode_token(token)
                if token_data:
                    user_id = token_data.user_id
            except Exception:
                pass
        
        return f"{client_ip}:{user_id or 'anonymous'}"
    
    def _get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for specific endpoint."""
        # Check for exact match
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check for prefix match
        for endpoint, limits in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limits
        
        # Default rate limit
        return self.calls, self.period


class IPBasedRateLimiter:
    """
    Simple IP-based rate limiter for specific endpoints.
    Use as a dependency in route handlers.
    """
    
    def __init__(self, calls: int = 10, period: int = 60):
        self.calls = calls
        self.period = period
        self.clients: Dict[str, list] = defaultdict(list)
    
    async def __call__(self, request: Request):
        """Check rate limit for this request."""
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        
        # Clean old entries
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if now - timestamp < timedelta(seconds=self.period)
        ]
        
        # Check limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.calls} requests per {self.period} seconds.",
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request
        self.clients[client_ip].append(now)


# Create rate limiter instances for different endpoints
payment_rate_limiter = IPBasedRateLimiter(calls=5, period=3600)  # 5 per hour
auth_rate_limiter = IPBasedRateLimiter(calls=10, period=300)     # 10 per 5 min
