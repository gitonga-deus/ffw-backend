# LMS Platform Backend

FastAPI backend for the Learning Management System.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and update the values:

```bash
copy .env.example .env
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   └── versions/         # Migration files
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   ├── dependencies.py  # FastAPI dependencies
│   └── main.py          # Application entry point
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment variables
├── alembic.ini          # Alembic configuration
└── requirements.txt     # Python dependencies
```

## Database

The application uses SQLite for development. The database file `lms.db` will be created automatically when you run migrations.

For production, configure the `DATABASE_URL` environment variable to point to your Neon DB PostgreSQL instance.

## API Endpoints

See `/docs` for interactive API documentation (Swagger UI).

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `ruff check .`
