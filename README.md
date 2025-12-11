# Financially Fit World Backend

FastAPI backend for the Learning Management System providing RESTful APIs for course management, user authentication, payment processing, and analytics.

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Database](#database)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The backend provides a comprehensive API for:
- 🔐 User authentication and authorization (JWT)
- 📚 Course content management
- 📊 Student enrollment and progress tracking
- 💳 Payment processing via iPay Africa
- 🎓 Automated certificate generation
- 📧 Email notifications via Resend
- 📈 Analytics and reporting
- ⭐ Course reviews and ratings

## 🛠 Tech Stack

- **Framework**: FastAPI 0.115+
- **Python**: 3.11+
- **Database**: PostgreSQL (Neon) / SQLite (development)
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.10+
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Email**: Resend API
- **Storage**: Vercel Blob
- **PDF Generation**: ReportLab
- **Migrations**: Alembic

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip
- PostgreSQL (Neon) or SQLite

### Installation

1. **Setup environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure database**
   ```bash
   cp .env.example .env
   # Edit .env and add your Neon PostgreSQL connection string
   ```

3. **Run setup script** (one command does everything!)
   ```bash
   python setup_neon_db.py
   ```
   
   This will:
   - ✅ Test database connection
   - ✅ Run migrations (create tables)
   - ✅ Seed initial data
   - ✅ Display credentials
   
   **Created Accounts:**
   - Admin: `admin@lms.com` / `Admin@123`
   - Student: `gitonga.deus@gmail.com` / `gitonga.deus04`
   
   **Created Content:**
   - Course: "Financially Fit For Life - The Seven Steps"
   - Module 1 with 2 video content items

4. **Start server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc

### Quick Commands

```bash
# Setup database (migrations + seeding)
python setup_neon_db.py

# Start development server
uvicorn app.main:app --reload

# Start with custom host/port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   └── env.py                 # Alembic config
│
├── app/
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   ├── user_progress.py
│   │   └── ...
│   │
│   ├── schemas/               # Pydantic schemas
│   │   ├── auth.py
│   │   ├── course.py
│   │   └── ...
│   │
│   ├── routers/               # API endpoints
│   │   ├── auth.py
│   │   ├── course.py
│   │   ├── admin.py
│   │   └── ...
│   │
│   ├── services/              # Business logic
│   │   ├── auth_service.py
│   │   ├── payment_service.py
│   │   ├── certificate_service.py
│   │   └── ...
│   │
│   ├── utils/                 # Utilities
│   ├── middleware/            # Custom middleware
│   ├── config.py              # Configuration
│   ├── database.py            # Database setup
│   └── main.py                # App entry point
│
├── scripts/                   # Utility scripts
├── assets/                    # Static assets (fonts, templates)
├── .env                       # Environment variables
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
├── setup_neon_db.py          # Database setup & seeding
├── alembic.ini               # Alembic configuration
├── vercel.json               # Vercel deployment config
└── README.md                  # This file
```

## 📚 API Documentation

### Interactive Docs

Once running, access:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Main Endpoints

#### Authentication (`/api/auth`)
- `POST /auth/register` - Register user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `POST /auth/verify-email` - Verify email
- `GET /auth/me` - Get current user

#### Courses (`/api/course`)
- `GET /course` - Get course details
- `GET /course/modules` - Get modules (enrolled)
- `GET /course/module/{id}` - Get module details
- `GET /course/content/{id}` - Get content

#### Progress (`/api/progress`)
- `POST /progress/{content_id}` - Update progress
- `GET /progress` - Get overall progress
- `GET /progress/module/{id}` - Get module progress

#### Payments (`/api/payments`)
- `POST /payments/initiate` - Initiate payment
- `GET /payments/status/{id}` - Check status

#### Certificates (`/api/certificates`)
- `GET /certificates/my-certificate` - Get certificate
- `GET /certificates/verify/{id}` - Verify certificate

#### Admin (`/api/admin`)
- User management
- Content management
- Analytics
- Payment tracking

### Authentication

Include JWT token in requests:
```bash
Authorization: Bearer <access_token>
```

### Example Request

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@lms.com", "password": "Admin@123"}'

# Get course (authenticated)
curl -X GET http://localhost:8000/api/course \
  -H "Authorization: Bearer <token>"
```

## 🗄️ Database

### Schema

Main tables:
- **users** - User accounts
- **course** - Course info
- **modules** - Course modules
- **content** - Module content
- **enrollments** - Student enrollments
- **user_progress** - Progress tracking
- **payments** - Transactions
- **certificates** - Generated certificates
- **reviews** - Course reviews

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

### Configuration

**Development (SQLite):**
```env
DATABASE_URL=sqlite:///./lms.db
```

**Production (PostgreSQL/Neon):**
```env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://...

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS=30

# External Services
RESEND_API_KEY=your-resend-key
VERCEL_BLOB_TOKEN=your-blob-token
IPAY_VENDOR_ID=your-vendor-id
IPAY_SECRET_KEY=your-secret

# Application
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ENVIRONMENT=development
```

See `.env.example` for all options.

## 🔧 Development

### Running Server

```bash
# Development (auto-reload)
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Database Operations

```bash
# Setup everything (recommended)
python setup_neon_db.py

# Just migrations (if needed separately)
alembic upgrade head

# Reset database (development only)
rm lms.db
python setup_neon_db.py
```

### Adding Features

1. Create model in `app/models/`
2. Create schema in `app/schemas/`
3. Create router in `app/routers/`
4. Add service in `app/services/`
5. Register router in `app/main.py`
6. Create migration: `alembic revision --autogenerate -m "msg"`
7. Apply: `alembic upgrade head`

## 🚀 Deployment

### Vercel (Recommended)

1. **Deploy**
   ```bash
   vercel --prod
   ```

2. **Set Environment Variables** in Vercel dashboard:
   - `DATABASE_URL` - Neon PostgreSQL URL
   - `SECRET_KEY` - Strong random key
   - `RESEND_API_KEY` - Email service
   - `VERCEL_BLOB_TOKEN` - File storage
   - `IPAY_VENDOR_ID` & `IPAY_SECRET_KEY` - Payments
   - `FRONTEND_URL` & `BACKEND_URL` - URLs

3. **Setup Database**
   ```bash
   # Run locally with production DATABASE_URL
   python setup_neon_db.py
   ```

### Production Checklist

- [ ] Strong `SECRET_KEY` set
- [ ] Production `DATABASE_URL` configured
- [ ] Email service (Resend) configured
- [ ] File storage (Vercel Blob) configured
- [ ] Payment gateway (iPay) configured
- [ ] CORS origins configured
- [ ] All environment variables set
- [ ] Database migrated and seeded
- [ ] Test critical flows

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check DATABASE_URL in .env
# For SQLite: DATABASE_URL=sqlite:///./lms.db
# For PostgreSQL: DATABASE_URL=postgresql://...
```

### Import Errors

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Migration Errors

```bash
# Reset database (development only)
rm lms.db
python setup_neon_db.py
```

### Email Not Sending

```bash
# Check RESEND_API_KEY in .env
# Verify domain in Resend dashboard
```

### Payment Webhook Issues

```bash
# Check IPAY_SECRET_KEY
# Verify webhook URL in iPay dashboard
# Check logs: GET /api/webhooks/diagnostics
```

### Performance Issues

1. Check database indexes
2. Review query optimization
3. Enable query logging
4. Use caching for analytics

## 📖 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)

## 🆘 Support

For issues:
1. Check troubleshooting section above
2. Review API docs at `/api/docs`
3. Check application logs
4. Contact development team

---

**Version**: 1.0.0  
**Last Updated**: December 2024
