# Financially Fit World Backend

FastAPI backend for the Learning Management System providing RESTful APIs for course management, user authentication, payment processing, and analytics.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Authentication](#authentication)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The backend is built with FastAPI and provides a comprehensive API for:
- User authentication and authorization
- Course content management
- Student enrollment and progress tracking
- Payment processing via iPay Africa
- Certificate generation
- Email notifications
- Analytics and reporting
- Admin dashboard functionality

## ✨ Features

### Core Features
- 🔐 **JWT Authentication**: Secure token-based authentication with refresh tokens
- 👥 **User Management**: Student and admin user roles
- 📚 **Course Management**: CRUD operations for courses, modules, and content
- 📊 **Progress Tracking**: Real-time student progress tracking
- 💳 **Payment Integration**: iPay Africa payment gateway integration
- 🎓 **Certificate Generation**: Automated PDF certificate generation
- 📧 **Email Service**: Automated emails via Resend API
- ☁️ **File Storage**: Vercel Blob storage for uploads
- 📈 **Analytics**: Comprehensive analytics and reporting
- ⭐ **Review System**: Course reviews and ratings

### Technical Features
- ⚡ **High Performance**: Optimized database queries with caching
- 🔒 **Security**: CORS, rate limiting, input validation, CSRF protection
- 📝 **API Documentation**: Auto-generated OpenAPI/Swagger docs
- 🗄️ **Database Migrations**: Alembic for schema management
- 🔄 **Background Tasks**: Async task processing
- 📊 **Query Optimization**: Efficient SQL queries with aggregation
- 🎯 **Type Safety**: Pydantic models for validation

## 🛠 Tech Stack

- **Framework**: FastAPI 0.115+
- **Python**: 3.11+
- **Database**: PostgreSQL (production) / SQLite (development)
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.10+
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib with bcrypt
- **Email**: Resend API
- **Storage**: Vercel Blob
- **PDF Generation**: ReportLab
- **HTTP Client**: httpx
- **Migrations**: Alembic

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd financially-fit-world/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   - Database URL
   - JWT secret key
   - External service API keys (Resend, Vercel Blob, iPay)
   - Frontend/Backend URLs

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Seed database (optional)**
   ```bash
   python seed_database.py
   ```
   
   This creates:
   - Sample course with modules and content
   - Admin user (admin@example.com / admin123)
   - Test student user (student@example.com / student123)

8. **Start development server**
   ```bash
   uvicorn app.main:app --reload
   ```

9. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

### Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database
python seed_database.py

# Start server
uvicorn app.main:app --reload

# Run with custom host/port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run in production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
backend/
├── alembic/                          # Database migrations
│   ├── versions/                     # Migration files
│   ├── env.py                        # Alembic environment
│   └── script.py.mako               # Migration template
│
├── app/
│   ├── models/                       # SQLAlchemy models
│   │   ├── user.py                  # User model
│   │   ├── course.py                # Course model
│   │   ├── module.py                # Module model
│   │   ├── content.py               # Content model
│   │   ├── enrollment.py            # Enrollment model
│   │   ├── user_progress.py         # Progress tracking
│   │   ├── payment.py               # Payment model
│   │   ├── certificate.py           # Certificate model
│   │   ├── review.py                # Review model
│   │   ├── announcement.py          # Announcement model
│   │   ├── notification.py          # Notification model
│   │   ├── exercise.py              # Exercise model
│   │   └── analytics_event.py       # Analytics events
│   │
│   ├── schemas/                      # Pydantic schemas
│   │   ├── auth.py                  # Auth schemas
│   │   ├── user.py                  # User schemas
│   │   ├── course.py                # Course schemas
│   │   ├── enrollment.py            # Enrollment schemas
│   │   ├── progress.py              # Progress schemas
│   │   ├── payment.py               # Payment schemas
│   │   ├── certificate.py           # Certificate schemas
│   │   ├── review.py                # Review schemas
│   │   ├── analytics.py             # Analytics schemas
│   │   └── ...
│   │
│   ├── routers/                      # API endpoints
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── course.py                # Course endpoints
│   │   ├── admin.py                 # Admin endpoints
│   │   ├── enrollment.py            # Enrollment endpoints
│   │   ├── progress.py              # Progress tracking
│   │   ├── payments.py              # Payment endpoints
│   │   ├── payment_admin.py         # Payment admin
│   │   ├── webhooks.py              # Payment webhooks
│   │   ├── certificates.py          # Certificate endpoints
│   │   ├── reviews.py               # Review endpoints
│   │   ├── analytics.py             # Analytics endpoints
│   │   ├── announcements.py         # Announcement endpoints
│   │   ├── exercises.py             # Exercise endpoints
│   │   ├── cron.py                  # Cron job endpoints
│   │   └── ...
│   │
│   ├── services/                     # Business logic
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── enrollment_service.py    # Enrollment logic
│   │   ├── progress_service.py      # Progress calculations
│   │   ├── payment_service.py       # Payment processing
│   │   ├── certificate_service.py   # Certificate generation
│   │   ├── email_service.py         # Email sending
│   │   ├── email_templates.py       # Email templates
│   │   ├── analytics_service.py     # Analytics calculations
│   │   ├── storage_service.py       # File storage
│   │   └── ...
│   │
│   ├── utils/                        # Utility functions
│   │   ├── security.py              # Security utilities
│   │   ├── email.py                 # Email utilities
│   │   ├── file_validation.py       # File validation
│   │   ├── sanitization.py          # Input sanitization
│   │   ├── date_formatter.py        # Date formatting
│   │   └── ...
│   │
│   ├── middleware/                   # Custom middleware
│   │   ├── security.py              # Security headers
│   │   └── rate_limit.py            # Rate limiting
│   │
│   ├── tasks/                        # Background tasks
│   │   └── payment_tasks.py         # Payment tasks
│   │
│   ├── config.py                     # Configuration
│   ├── database.py                   # Database setup
│   ├── dependencies.py               # FastAPI dependencies
│   ├── main.py                       # Application entry
│   └── scheduler.py                  # Task scheduler
│
├── scripts/                          # Utility scripts
│   ├── recalculate_all_progress.py  # Progress recalculation
│   ├── check_db.py                  # Database checks
│   ├── test_certificate.py          # Certificate testing
│   └── README.md                    # Scripts documentation
│
├── .env                              # Environment variables (not in git)
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── alembic.ini                       # Alembic configuration
├── requirements.txt                  # Python dependencies
├── seed_database.py                  # Database seeding
├── check_db.py                       # Database checker
├── verify_content.py                 # Content verification
├── vercel.json                       # Vercel deployment config
└── README.md                         # This file
```

## 📚 API Documentation

### Interactive Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### API Endpoints Overview

#### Authentication (`/api/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/verify-email` - Verify email address
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password
- `PUT /auth/profile` - Update user profile
- `PUT /auth/change-password` - Change password
- `GET /auth/me` - Get current user

#### Courses (`/api/course`)
- `GET /course` - Get course details
- `GET /course/modules` - Get course modules (enrolled)
- `GET /course/modules/public` - Get course modules (public)
- `GET /course/module/{module_id}` - Get module details
- `GET /course/content/{content_id}` - Get content details

#### Enrollment (`/api/enrollment`)
- `POST /enrollment/enroll` - Enroll in course
- `GET /enrollment/status` - Get enrollment status
- `POST /enrollment/signature` - Submit digital signature
- `GET /enrollment/signature` - Get signature status

#### Progress (`/api/progress`)
- `POST /progress/{content_id}` - Update content progress
- `GET /progress` - Get overall progress
- `GET /progress/module/{module_id}` - Get module progress
- `GET /progress/content/{content_id}` - Get content progress

#### Payments (`/api/payments`)
- `POST /payments/initiate` - Initiate payment
- `GET /payments/status/{payment_id}` - Check payment status
- `POST /webhooks/ipay` - iPay webhook (internal)

#### Certificates (`/api/certificates`)
- `GET /certificates/my-certificate` - Get user certificate
- `GET /certificates/verify/{cert_id}` - Verify certificate

#### Reviews (`/api/reviews`)
- `POST /reviews` - Submit review
- `GET /reviews` - Get course reviews
- `GET /reviews/my-review` - Get user's review

#### Admin (`/api/admin`)
- `GET /admin/users` - List users
- `GET /admin/users/{user_id}` - Get user details
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user
- `POST /admin/content` - Create content
- `PUT /admin/content/{content_id}` - Update content
- `DELETE /admin/content/{content_id}` - Delete content
- `POST /admin/modules` - Create module
- `PUT /admin/modules/{module_id}` - Update module
- `DELETE /admin/modules/{module_id}` - Delete module

#### Analytics (`/api/admin/analytics`)
- `GET /analytics/dashboard` - Get dashboard analytics
- `GET /analytics/dashboard-with-payments` - Combined analytics + payments
- `GET /analytics/overview` - Overview metrics
- `GET /analytics/users` - User analytics
- `GET /analytics/enrollments` - Enrollment analytics
- `GET /analytics/revenue` - Revenue analytics
- `GET /analytics/content` - Content analytics
- `GET /analytics/reviews` - Review analytics

#### Announcements (`/api/announcements`)
- `GET /announcements` - Get announcements
- `POST /admin/announcements` - Create announcement
- `PUT /admin/announcements/{id}` - Update announcement
- `DELETE /admin/announcements/{id}` - Delete announcement

### Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```bash
Authorization: Bearer <access_token>
```

### Example API Calls

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "phone_number": "+254712345678"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Get course (authenticated)
curl -X GET http://localhost:8000/api/course \
  -H "Authorization: Bearer <access_token>"

# Update progress
curl -X POST http://localhost:8000/api/progress/<content_id> \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_completed": true,
    "time_spent": 300
  }'
```

## 🗄️ Database

### Database Schema

The application uses the following main tables:

- **users**: User accounts (students and admins)
- **course**: Course information
- **modules**: Course modules
- **content**: Module content (videos, PDFs, rich text)
- **enrollments**: Student enrollments
- **user_progress**: Content completion tracking
- **payments**: Payment transactions
- **certificates**: Generated certificates
- **reviews**: Course reviews
- **announcements**: Course announcements
- **notifications**: User notifications
- **exercises**: Exercise forms
- **exercise_submissions**: Exercise submissions
- **analytics_events**: Analytics tracking

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Database Configuration

**Development (SQLite):**
```env
DATABASE_URL=sqlite:///./lms.db
```

**Production (PostgreSQL):**
```env
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
```

### Database Utilities

```bash
# Check database status
python check_db.py

# Verify content integrity
python verify_content.py

# Recalculate all progress
python scripts/recalculate_all_progress.py

# Seed database with sample data
python seed_database.py
```

## 🔐 Authentication

### JWT Token Flow

1. **Registration**: User registers with email/password
2. **Email Verification**: Verification email sent
3. **Login**: User logs in with credentials
4. **Token Issuance**: Access token (24h) and refresh token (30d) issued
5. **API Access**: Access token used for authenticated requests
6. **Token Refresh**: Refresh token used to get new access token

### Token Configuration

```python
# config.py
access_token_expire_minutes = 60 * 24  # 24 hours
refresh_token_expire_days = 30  # 30 days
```

### Password Security

- Passwords hashed with bcrypt
- Minimum 8 characters required
- Password reset via email token
- Token expires after 1 hour

### Role-Based Access Control

- **Student**: Access to enrolled courses, progress, certificates
- **Admin**: Full access to all features, user management, analytics

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./lms.db

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS=30

# External Services
RESEND_API_KEY=your-resend-api-key
VERCEL_BLOB_TOKEN=your-vercel-blob-token
IPAY_VENDOR_ID=your-ipay-vendor-id
IPAY_SECRET_KEY=your-ipay-secret-key

# Application
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development

# Security
ENABLE_CSRF=false
ENABLE_RATE_LIMITING=true
CRON_SECRET=your-cron-secret

# Email
EMAIL_FROM=Financially Fit World <noreply@yourdomain.com>
```

### Configuration File

See `app/config.py` for all configuration options.

## 🔧 Development

### Running the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload

# Custom host and port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Code Quality

```bash
# Format code with Black
black .

# Lint code with Ruff
ruff check .

# Type checking with mypy
mypy app/
```

### Database Operations

```bash
# Create migration
alembic revision --autogenerate -m "add new field"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Reset database (development only)
rm lms.db
alembic upgrade head
python seed_database.py
```

### Adding New Endpoints

1. Create model in `app/models/`
2. Create schema in `app/schemas/`
3. Create router in `app/routers/`
4. Add business logic in `app/services/`
5. Register router in `app/main.py`
6. Create migration: `alembic revision --autogenerate`
7. Apply migration: `alembic upgrade head`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Manual Testing

Use the interactive API docs at http://localhost:8000/api/docs to test endpoints manually.

### Test Users

After running `seed_database.py`:

**Admin User:**
- Email: admin@example.com
- Password: admin123

**Student User:**
- Email: student@example.com
- Password: student123

## 🚀 Deployment

### Vercel Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   vercel --prod
   ```

3. **Configure Environment Variables**
   Set all required environment variables in Vercel dashboard.

4. **Database Setup**
   - Create PostgreSQL database on Neon
   - Run migrations
   - Seed initial data

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Configure production `DATABASE_URL`
- [ ] Set up Resend API for emails
- [ ] Configure Vercel Blob for storage
- [ ] Set up iPay Africa credentials
- [ ] Enable CSRF protection
- [ ] Configure CORS origins
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy
- [ ] Test all critical flows

## 🐛 Troubleshooting

### Common Issues

**Issue**: Database connection error
```bash
# Solution: Check DATABASE_URL in .env
# For SQLite: DATABASE_URL=sqlite:///./lms.db
# For PostgreSQL: DATABASE_URL=postgresql://...
```

**Issue**: Import errors
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**Issue**: Migration errors
```bash
# Solution: Reset migrations (development only)
rm lms.db
alembic upgrade head
```

**Issue**: Email not sending
```bash
# Solution: Check RESEND_API_KEY in .env
# Verify email domain is verified in Resend
```

**Issue**: Payment webhook not working
```bash
# Solution: Check IPAY_SECRET_KEY
# Verify webhook URL is configured in iPay dashboard
# Check webhook logs: GET /api/webhooks/diagnostics
```

### Debug Mode

Enable debug logging:

```python
# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

If experiencing slow queries:

1. Check database indexes
2. Review query optimization
3. Enable query logging
4. Use caching for analytics
5. See [Performance Optimizations](./PERFORMANCE_OPTIMIZATIONS.md)

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Performance Optimizations](./PERFORMANCE_OPTIMIZATIONS.md)
- [Progress Recalculation](./PROGRESS_RECALCULATION.md)
- [Scripts Documentation](./scripts/README.md)

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation
- Check application logs
- Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: December 2024
