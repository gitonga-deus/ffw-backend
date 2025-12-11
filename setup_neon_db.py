"""
Neon PostgreSQL Database Setup & Seeding Script

This script handles:
1. Testing connection to Neon PostgreSQL database
2. Running database migrations (Alembic)
3. Seeding initial data (admin user, verified user, course content)

Usage:
    python setup_neon_db.py

Features:
- Validates database connection
- Shows database info (version, tables, etc.)
- Runs Alembic migrations automatically
- Seeds production-ready data
- Idempotent (safe to run multiple times)
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import bcrypt
from datetime import datetime

from app.config import settings
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.module import Module
from app.models.content import Content


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")


def test_database_connection() -> bool:
    """Test connection to the database and display info."""
    print_section("Testing Database Connection")
    
    try:
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✓ Database connection successful!")
        
        # Get database info
        with engine.connect() as conn:
            # Check if it's PostgreSQL or SQLite
            if "postgresql" in settings.database_url:
                # PostgreSQL specific queries
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                print(f"\n  Database Type: PostgreSQL")
                print(f"  Version: {version.split(',')[0]}")
                
                # Get database name
                db_result = conn.execute(text("SELECT current_database()"))
                db_name = db_result.fetchone()[0]
                print(f"  Database Name: {db_name}")
                
                # Get connection info
                host_result = conn.execute(text("SELECT inet_server_addr(), inet_server_port()"))
                host_info = host_result.fetchone()
                if host_info[0]:
                    print(f"  Host: {host_info[0]}:{host_info[1]}")
                
            elif "sqlite" in settings.database_url:
                # SQLite specific
                version_result = conn.execute(text("SELECT sqlite_version()"))
                version = version_result.fetchone()[0]
                print(f"\n  Database Type: SQLite")
                print(f"  Version: {version}")
                print(f"  File: {settings.database_url.replace('sqlite:///', '')}")
        
        # Get table count
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"  Tables: {len(tables)}")
        
        if tables:
            print(f"\n  Existing Tables:")
            for table in sorted(tables):
                print(f"    • {table}")
        else:
            print(f"\n  ⚠ No tables found - migrations need to be run")
        
        return True
        
    except OperationalError as e:
        print(f"✗ Database connection failed!")
        print(f"  Error: {str(e)}")
        print(f"\n  Connection String: {settings.database_url[:50]}...")
        print(f"\n  Troubleshooting:")
        print(f"    1. Check DATABASE_URL in .env file")
        print(f"    2. Verify Neon database is active")
        print(f"    3. Check network connectivity")
        print(f"    4. Verify SSL settings (sslmode=require)")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_migrations() -> bool:
    """Run Alembic migrations to create/update tables."""
    print_section("Running Database Migrations")
    
    try:
        import subprocess
        
        # Check if alembic is available
        result = subprocess.run(
            ["alembic", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print("✗ Alembic not found. Please install: pip install alembic")
            return False
        
        print("Running: alembic upgrade head")
        print()
        
        # Run migrations
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Migrations completed successfully!")
            return True
        else:
            print("✗ Migration failed!")
            return False
            
    except FileNotFoundError:
        print("✗ Alembic not found. Please install: pip install alembic")
        return False
    except Exception as e:
        print(f"✗ Error running migrations: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_admin_user(db: Session) -> User:
    """Create initial admin user."""
    print("\n  Creating admin user...")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == "admin@lms.com").first()
    if existing_admin:
        print("    ✓ Admin user already exists")
        return existing_admin
    
    admin = User(
        email="admin@lms.com",
        phone_number="+254700000000",
        full_name="Admin User",
        password_hash=hash_password("Admin@123"),
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_enrolled=False
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"    ✓ Admin user created: {admin.email}")
    return admin


def create_verified_user(db: Session) -> User:
    """Create the verified user (Deus Gitonga)."""
    print("\n  Creating verified user...")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "gitonga.deus@gmail.com").first()
    if existing_user:
        print(f"    ✓ User already exists: {existing_user.email}")
        return existing_user
    
    user = User(
        email="gitonga.deus@gmail.com",
        phone_number="0720158047",
        full_name="Deus Gitonga",
        password_hash=hash_password("gitonga.deus04"),
        role=UserRole.STUDENT.value,
        is_verified=True,
        is_enrolled=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"    ✓ Verified user created: {user.email}")
    return user


def create_course_with_content(db: Session) -> Course:
    """Create complete course structure with one module and content."""
    print("\n  Creating course with content...")
    
    # Check if course already exists
    existing_course = db.query(Course).first()
    if existing_course:
        print("    ✓ Course already exists")
        return existing_course
    
    # Create course
    course = Course(
        title="Financially Fit For Life - The Seven Steps",
        description="Financially Fit for life is the global leader in world class personal wealth education. This comprehensive course will teach you the seven essential steps to achieving financial freedom and building lasting wealth.",
        price=1000.00,
        currency="KES",
        instructor_name="Steven Down",
        instructor_bio="Steve Down is an entrepreneur and business maverick whose ideas about wealth creation, service to the community and personal excellence are transforming lives all over the world. His business acumen helped create the hugely successful Even Stevens chain of sandwich stores, the Financially Fit LLC, and a host of stellar business enterprises that became icons in their areas of specialization. As America's Wealth Coach, Steve went on coast-to-coast tours giving speeches and hosting seminars and helped millions change their perception and understanding of money, wealth, and how to achieve principle centered wealth.",
        is_published=True
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    print(f"    ✓ Course created: {course.title}")
    
    # Create Module 1
    module1 = Module(
        course_id=course.id,
        title="Step 1: Understanding Your Financial Foundation",
        description="Learn the fundamental principles of personal finance and wealth creation. This module covers the basics of financial literacy, mindset shifts, and setting up your financial foundation.",
        order_index=0,
        is_published=True
    )
    
    db.add(module1)
    db.commit()
    db.refresh(module1)
    
    print(f"    ✓ Module created: {module1.title}")
    
    # Create Content 1: Welcome Video
    content1 = Content(
        module_id=module1.id,
        title="Welcome to Financially Fit For Life",
        content_type="video",
        vimeo_video_id="1039206096",
        video_duration=300,
        order_index=0,
        is_published=True
    )
    
    db.add(content1)
    print(f"      ✓ Content 1: {content1.title} (Video)")
    
    # Create Content 2: Another Video
    content2 = Content(
        module_id=module1.id,
        title="The Wealth Mindset",
        content_type="video",
        vimeo_video_id="1039206096",
        video_duration=480,
        order_index=1,
        is_published=True
    )
    
    db.add(content2)
    print(f"      ✓ Content 2: {content2.title} (Video)")
    
    db.commit()
    
    return course


def seed_database() -> bool:
    """Seed the database with initial data."""
    print_section("Seeding Database")
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin = create_admin_user(db)
        
        # Create verified user (Deus Gitonga)
        user = create_verified_user(db)
        
        # Create course with content
        course = create_course_with_content(db)
        
        print("\n  ✓ Database seeding completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n  ✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def display_summary():
    """Display summary of created data."""
    print_section("Setup Summary")
    
    db = SessionLocal()
    
    try:
        # Count records
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN.value).count()
        student_count = db.query(User).filter(User.role == UserRole.STUDENT.value).count()
        course_count = db.query(Course).count()
        module_count = db.query(Module).count()
        content_count = db.query(Content).count()
        
        print(f"\n  Database Statistics:")
        print(f"    • Total Users: {user_count}")
        print(f"      - Admins: {admin_count}")
        print(f"      - Students: {student_count}")
        print(f"    • Courses: {course_count}")
        print(f"    • Modules: {module_count}")
        print(f"    • Content Items: {content_count}")
        
        print(f"\n  Login Credentials:")
        print(f"\n    Admin Account:")
        print(f"      Email: admin@lms.com")
        print(f"      Password: Admin@123")
        
        print(f"\n    Verified Student Account:")
        print(f"      Email: gitonga.deus@gmail.com")
        print(f"      Password: gitonga.deus04")
        print(f"      Phone: 0720158047")
        
        # Get course info
        course = db.query(Course).first()
        if course:
            print(f"\n  Course Information:")
            print(f"    Title: {course.title}")
            print(f"    Price: {course.price} {course.currency}")
            print(f"    Status: {'Published' if course.is_published else 'Draft'}")
        
        print(f"\n  Next Steps:")
        print(f"    1. Start backend: uvicorn app.main:app --reload")
        print(f"    2. Start frontend: cd frontend && npm run dev")
        print(f"    3. Login as Deus Gitonga to test enrollment")
        print(f"    4. Complete payment flow (demo mode)")
        print(f"    5. Test progress tracking and certificate generation")
        
    except Exception as e:
        print(f"\n  ✗ Error getting summary: {e}")
    finally:
        db.close()


def main():
    """Main setup function."""
    print_header("Neon PostgreSQL Database Setup & Seeding")
    
    print(f"\nEnvironment: {settings.environment}")
    print(f"Database URL: {settings.database_url[:50]}...")
    
    # Step 1: Test connection
    if not test_database_connection():
        print("\n✗ Setup failed: Cannot connect to database")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        print("\n✗ Setup failed: Migration errors")
        sys.exit(1)
    
    # Step 3: Seed database
    if not seed_database():
        print("\n✗ Setup failed: Seeding errors")
        sys.exit(1)
    
    # Step 4: Display summary
    display_summary()
    
    # Success!
    print_header("✓ Setup Completed Successfully!")
    print("\nYour Neon PostgreSQL database is ready to use!")
    print()


if __name__ == "__main__":
    main()
