from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./lms.db"
    
    # JWT
    secret_key: str = "CHANGE-THIS-IN-PRODUCTION-USE-SECURE-RANDOM-KEY"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # External Services
    resend_api_key: str = ""
    email_from: str = "Financially Fit World <onboarding@resend.dev>"  # Change to your verified domain
    allowed_test_email: str = ""  # Optional: Restrict registration to specific email for testing
    vercel_blob_token: str = ""
    ipay_vendor_id: str = "demo"
    ipay_secret_key: str = "demoCHANGED"
    
    # 123FormBuilder Integration
    formbuilder_api_key: str = ""
    formbuilder_webhook_secret: str = ""
    # Webhook URL format: {backend_url}/api/webhooks/123formbuilder
    # Example: https://your-domain.com/api/webhooks/123formbuilder
    # Configure this URL in your 123FormBuilder form settings
    
    # Application
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    environment: str = "development"  # development, staging, production
    
    # Security Settings
    enable_csrf: bool = False  # Enable in production
    enable_rate_limiting: bool = True
    max_request_size: int = 20 * 1024 * 1024  # 20MB
    max_image_size: int = 5 * 1024 * 1024  # 5MB
    max_pdf_size: int = 20 * 1024 * 1024  # 20MB
    cron_secret: str = ""  # Secret for authenticating cron job requests
    
    # Rate Limiting
    rate_limit_calls: int = 100  # requests per period
    rate_limit_period: int = 60  # seconds
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
