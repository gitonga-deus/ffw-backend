from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.routers import auth, enrollment, course, admin, progress, certificates, reviews, analytics, announcements, payments, payment_admin, webhooks, exercises, webhook_diagnostics, cron
from app.middleware.security import SecurityHeadersMiddleware, CSRFProtectionMiddleware, RequestValidationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="Financially Fit World API",
    description="Learning Management System API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Startup and shutdown events for background scheduler
# Note: Disabled in serverless environments (Vercel)
# Use Vercel Cron Jobs instead: https://vercel.com/docs/cron-jobs
# The /api/cron/* endpoints handle scheduled tasks

# Security Middleware (order matters - apply from innermost to outermost)
# CORS must be added LAST so it's processed FIRST

# 1. Request validation (check size, content type)
app.add_middleware(RequestValidationMiddleware, max_request_size=20 * 1024 * 1024)  # 20MB

# 2. Rate limiting (disabled for serverless - use Redis or Vercel's rate limiting)
# Note: In-memory rate limiting doesn't work in serverless environments
if settings.enable_rate_limiting and settings.environment != "production":
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 requests per minute default

# 3. CSRF protection (disabled by default - enable in production)
# Uncomment to enable CSRF protection:
# app.add_middleware(CSRFProtectionMiddleware, secret_key=settings.secret_key)

# 4. Security headers (CSP, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# 5. CORS configuration - MUST BE LAST!
# Build list of allowed origins
allowed_origins = [
    "https://finfitworld.vercel.app",  # Production frontend
    "https://ffw-frontend-ten.vercel.app",  # Production frontend (alternate)
    "http://localhost:3000",            # Local development
    "http://localhost:8000",            # Local backend (for testing)
]

# Add frontend_url from settings if not already in list
if settings.frontend_url not in allowed_origins:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# 6. Trusted host middleware (prevent host header attacks)
# Uncomment in production with actual domain:
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["yourdomain.com", "*.yourdomain.com", "localhost"]
# )

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(enrollment.router, prefix="/api")
app.include_router(course.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(certificates.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(announcements.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(payment_admin.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(webhook_diagnostics.router, prefix="/api")
app.include_router(exercises.router, prefix="/api")
app.include_router(cron.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Financially Fit World API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
