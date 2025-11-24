"""
Database seeding script for LMS platform.

This script creates initial data including:
- Admin user
- 5 verified student users for testing

Usage:
    python seed_database.py
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


def create_student_users(db: Session) -> list[User]:
    """Create 5 verified student users for testing."""
    print("\nCreating student users...")
    
    students_data = [
        {
            "email": "student1@test.com",
            "phone_number": "+254700000001",
            "full_name": "Alice Johnson",
            "password": "Student@123"
        },
        {
            "email": "student2@test.com",
            "phone_number": "+254700000002",
            "full_name": "Bob Smith",
            "password": "Student@123"
        },
        {
            "email": "student3@test.com",
            "phone_number": "+254700000003",
            "full_name": "Carol Williams",
            "password": "Student@123"
        },
        {
            "email": "student4@test.com",
            "phone_number": "+254700000004",
            "full_name": "David Brown",
            "password": "Student@123"
        },
        {
            "email": "student5@test.com",
            "phone_number": "+254700000005",
            "full_name": "Emma Davis",
            "password": "Student@123"
        }
    ]
    
    students = []
    for student_data in students_data:
        # Check if student already exists
        existing_student = db.query(User).filter(User.email == student_data["email"]).first()
        if existing_student:
            print(f"  ✓ Student already exists: {existing_student.email}")
            students.append(existing_student)
            continue
        
        student = User(
            email=student_data["email"],
            phone_number=student_data["phone_number"],
            full_name=student_data["full_name"],
            password_hash=hash_password(student_data["password"]),
            role=UserRole.STUDENT.value,
            is_verified=True,
            is_enrolled=False  # Not enrolled yet - you can enroll them manually
        )
        
        db.add(student)
        students.append(student)
        print(f"  ✓ Student created: {student_data['email']}")
    
    db.commit()
    
    for student in students:
        if student.id:  # Only refresh if it's a new student
            db.refresh(student)
    
    return students


def create_minimal_course(db: Session) -> Course:
    """Create a minimal course structure to prevent 404 errors on homepage."""
    print("\nCreating minimal course structure...")
    
    # Check if course already exists
    existing_course = db.query(Course).first()
    if existing_course:
        print("  ✓ Course already exists")
        return existing_course
    
    course = Course(
        title="Web Development Course",
        description="Learn web development from scratch. Course content will be added by the instructor.",
        price=1000.00,
        currency="KES",
        instructor_name="Instructor",
        instructor_bio="Experienced web development instructor.",
        is_published=True
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    print(f"  ✓ Minimal course created: {course.title}")
    print("    Note: No modules or content added - add them via admin panel")
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
        
        # Create student users
        students = create_student_users(db)
        
        # Create minimal course to prevent 404 errors
        course = create_minimal_course(db)
        
        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print("\nAdmin Credentials:")
        print("  Email: admin@lms.com")
        print("  Password: Admin@123")
        print("\nStudent Credentials (all use password: Student@123):")
        print("  1. student1@test.com - Alice Johnson")
        print("  2. student2@test.com - Bob Smith")
        print("  3. student3@test.com - Carol Williams")
        print("  4. student4@test.com - David Brown")
        print("  5. student5@test.com - Emma Davis")
        print("\nNote: Minimal course created with no modules/content.")
        print("You can now:")
        print("  1. Login as admin to add modules and exercises")
        print("  2. Enroll students manually")
        print("  3. Test the 123FormBuilder webhook integration")
        print("\nStart the backend server and begin testing!")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
