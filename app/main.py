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
    docs_url="/docs",
    redoc_url="/redoc"
)

# Startup and shutdown events for background scheduler
@app.on_event("startup")
async def startup_event():
    """Start background scheduler for periodic tasks."""
    from app.scheduler import start_scheduler
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scheduler."""
    from app.scheduler import stop_scheduler
    stop_scheduler()

# Security Middleware (order matters - apply from innermost to outermost)

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

# 5. CORS configuration
# Build list of allowed origins
allowed_origins = [settings.frontend_url, "http://localhost:3000"]
# Add production frontend if different from settings
if "finfitworld.vercel.app" not in settings.frontend_url:
    allowed_origins.append("https://finfitworld.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
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

# Include routers
app.include_router(auth.router)
app.include_router(enrollment.router)
app.include_router(course.router)
app.include_router(admin.router)
app.include_router(progress.router)
app.include_router(certificates.router)
app.include_router(reviews.router)
app.include_router(analytics.router)
app.include_router(announcements.router)
app.include_router(payments.router)
app.include_router(payment_admin.router)
app.include_router(webhooks.router)
app.include_router(webhook_diagnostics.router)
app.include_router(exercises.router)
app.include_router(cron.router)


@app.get("/")
async def root():
    return {"message": "Financially Fit World API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
