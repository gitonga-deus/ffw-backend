"""
Database seeding script for Financially Fit World platform.

This script creates PRODUCTION data including:
- Admin user
- Verified user (Deus Gitonga)
- Complete course structure with one module and content for testing

Usage:
    python seed_database.py

IMPORTANT: This will create REAL production data. Run only once!
"""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
import bcrypt

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.module import Module
from app.models.content import Content
from app.models.exercise import Exercise


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_admin_user(db: Session) -> User:
    """Create initial admin user."""
    print("Creating admin user...")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.email == "admin@lms.com").first()
    if existing_admin:
        print("  ✓ Admin user already exists")
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
    
    print(f"  ✓ Admin user created: {admin.email}")
    print(f"    Password: Admin@123")
    return admin


def create_verified_user(db: Session) -> User:
    """Create the verified user (Deus Gitonga)."""
    print("\nCreating verified user...")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "gitonga.deus@gmail.com").first()
    if existing_user:
        print(f"  ✓ User already exists: {existing_user.email}")
        return existing_user
    
    user = User(
        email="gitonga.deus@gmail.com",
        phone_number="0720158047",
        full_name="Deus Gitonga",
        password_hash=hash_password("gitonga.deus04"),
        role=UserRole.STUDENT.value,
        is_verified=True,
        is_enrolled=False  # Will be enrolled after payment
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"  ✓ Verified user created: {user.email}")
    print(f"    Password: gitonga.deus04")
    return user


def create_course_with_content(db: Session) -> Course:
    """Create complete course structure with one module and content."""
    print("\nCreating course with content...")
    
    # Check if course already exists
    existing_course = db.query(Course).first()
    if existing_course:
        print("  ✓ Course already exists")
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
    
    print(f"  ✓ Course created: {course.title}")
    
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
    
    print(f"  ✓ Module created: {module1.title}")
    
    # Create Content 1: Welcome Video
    content1 = Content(
        module_id=module1.id,
        title="Welcome to Financially Fit For Life",
        content_type="video",
        vimeo_video_id="1039206096",
        video_duration=300,  # 5 minutes
        order_index=0,
        is_published=True
    )
    
    db.add(content1)
    print(f"    ✓ Content 1: {content1.title} (Video)")
    
    # Create Content 2: Another Video
    content2 = Content(
        module_id=module1.id,
        title="The Wealth Mindset",
        content_type="video",
        vimeo_video_id="1039206096",
        video_duration=480,  # 8 minutes
        order_index=1,
        is_published=True
    )
    
    db.add(content2)
    print(f"    ✓ Content 2: {content2.title} (Video)")
    
    db.commit()
    
    print(f"  ✓ Created 2 video content items in module")
    
    return course


def seed_database():
    """Main seeding function."""
    print("=" * 60)
    print("LMS Database Seeding Script")
    print("=" * 60)
    
    # Create tables if they don't exist
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created/verified")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create admin user
        admin = create_admin_user(db)
        
        # Create verified user (Deus Gitonga)
        user = create_verified_user(db)
        
        # Create course with content
        course = create_course_with_content(db)
        
        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print("\nAdmin Credentials:")
        print("  Email: admin@lms.com")
        print("  Password: Admin@123")
        print("\nVerified User Credentials:")
        print("  Email: gitonga.deus@gmail.com")
        print("  Full Name: Deus Gitonga")
        print("  Password: gitonga.deus04")
        print("  Phone: 0720158047")
        print("\nCourse Created:")
        print(f"  Title: {course.title}")
        print(f"  Price: {course.price} {course.currency}")
        print(f"  Modules: 1 (Step 1: Understanding Your Financial Foundation)")
        print(f"  Content Items: 2 Videos")
        print("\nNext Steps:")
        print("  1. Start the backend server: uvicorn app.main:app --reload")
        print("  2. Login as Deus Gitonga to test the course")
        print("  3. Complete payment to enroll in the course")
        print("  4. Test the progress tracking with the new fixes")
        print("  5. Add more content via admin panel as needed")
        print("\nAll content is published and ready for testing!")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
