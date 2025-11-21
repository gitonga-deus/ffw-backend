"""
Database seeding script for LMS platform.

This script creates initial data including:
- Admin user
- Sample course with modules and content
- Sample announcements

Usage:
    python seed_database.py
"""

import sys
import json
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
import bcrypt

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.course import Course
from app.models.module import Module
from app.models.content import Content, ContentType
from app.models.announcement import Announcement


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


def create_sample_course(db: Session) -> Course:
    """Create sample course."""
    print("\nCreating sample course...")
    
    # Check if course already exists
    existing_course = db.query(Course).first()
    if existing_course:
        print("  ✓ Course already exists")
        return existing_course
    
    course = Course(
        title="Complete Web Development Bootcamp",
        description="""Master web development from scratch! This comprehensive course covers everything you need to become a full-stack web developer.

Learn HTML, CSS, JavaScript, React, Node.js, databases, and more. Build real-world projects and gain the skills employers are looking for.

Perfect for beginners with no prior coding experience. By the end of this course, you'll have the confidence and portfolio to start your career in web development.""",
        price=1000.00,
        currency="KES",
        instructor_name="John Doe",
        instructor_bio="""John Doe is a senior software engineer with over 10 years of experience in web development. He has worked with leading tech companies and has taught thousands of students worldwide.

His passion for teaching and making complex concepts simple has helped countless students launch successful careers in tech.""",
        is_published=True
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    print(f"  ✓ Course created: {course.title}")
    return course


def create_sample_modules(db: Session, course_id: str) -> list[Module]:
    """Create sample modules for the course."""
    print("\nCreating sample modules...")
    
    # Check if modules already exist
    existing_modules = db.query(Module).filter(Module.course_id == course_id).all()
    if existing_modules:
        print(f"  ✓ {len(existing_modules)} modules already exist")
        return existing_modules
    
    modules_data = [
        {
            "title": "Introduction to Web Development",
            "description": "Get started with web development fundamentals. Learn about how the web works, development tools, and set up your coding environment.",
            "order_index": 1
        },
        {
            "title": "HTML & CSS Fundamentals",
            "description": "Master the building blocks of web pages. Learn HTML structure, semantic markup, CSS styling, layouts, and responsive design.",
            "order_index": 2
        },
        {
            "title": "JavaScript Essentials",
            "description": "Dive into JavaScript programming. Learn variables, functions, DOM manipulation, events, and modern ES6+ features.",
            "order_index": 3
        },
        {
            "title": "React Framework",
            "description": "Build modern user interfaces with React. Learn components, hooks, state management, and best practices.",
            "order_index": 4
        },
        {
            "title": "Backend Development with Node.js",
            "description": "Create server-side applications. Learn Node.js, Express, RESTful APIs, authentication, and database integration.",
            "order_index": 5
        }
    ]
    
    modules = []
    for module_data in modules_data:
        module = Module(
            course_id=course_id,
            title=module_data["title"],
            description=module_data["description"],
            order_index=module_data["order_index"],
            is_published=True
        )
        db.add(module)
        modules.append(module)
    
    db.commit()
    
    for module in modules:
        db.refresh(module)
        print(f"  ✓ Module {module.order_index}: {module.title}")
    
    return modules


def create_sample_content(db: Session, modules: list[Module]) -> None:
    """Create sample content for modules."""
    print("\nCreating sample content...")
    
    # Check if content already exists
    existing_content = db.query(Content).first()
    if existing_content:
        print("  ✓ Content already exists")
        return
    
    # Module 1: Introduction to Web Development
    module1_content = [
        {
            "title": "Welcome to the Course",
            "content_type": ContentType.VIDEO.value,
            "order_index": 1,
            "vimeo_video_id": "123456789",
            "video_duration": 300,
            "is_published": True
        },
        {
            "title": "How the Web Works",
            "content_type": ContentType.RICH_TEXT.value,
            "order_index": 2,
            "rich_text_content": json.dumps({
                "blocks": [
                    {
                        "id": "block_1",
                        "type": "paragraph",
                        "content": "The web is built on a client-server architecture. When you type a URL in your browser, your computer (the client) sends a request to a server, which responds with the requested web page."
                    },
                    {
                        "id": "block_2",
                        "type": "heading",
                        "level": 2,
                        "content": "Key Concepts"
                    },
                    {
                        "id": "block_3",
                        "type": "paragraph",
                        "content": "HTTP (Hypertext Transfer Protocol) is the foundation of data communication on the web. It defines how messages are formatted and transmitted."
                    },
                    {
                        "id": "block_4",
                        "type": "exercise",
                        "exercise_id": "ex_001",
                        "title": "Check Your Understanding",
                        "questions": [
                            {
                                "id": "q1",
                                "type": "radio",
                                "question": "What does HTTP stand for?",
                                "options": [
                                    {"value": "a", "label": "Hypertext Transfer Protocol"},
                                    {"value": "b", "label": "High Tech Transfer Process"},
                                    {"value": "c", "label": "Hyperlink Text Protocol"}
                                ]
                            },
                            {
                                "id": "q2",
                                "type": "text",
                                "question": "In your own words, explain what happens when you visit a website:",
                                "placeholder": "Type your answer here..."
                            }
                        ]
                    }
                ]
            }),
            "is_published": True
        },
        {
            "title": "Development Tools Setup Guide",
            "content_type": ContentType.PDF.value,
            "order_index": 3,
            "pdf_url": "https://example.com/setup-guide.pdf",
            "pdf_filename": "setup-guide.pdf",
            "is_published": True
        }
    ]
    
    # Module 2: HTML & CSS Fundamentals
    module2_content = [
        {
            "title": "HTML Basics",
            "content_type": ContentType.VIDEO.value,
            "order_index": 1,
            "vimeo_video_id": "123456790",
            "video_duration": 600,
            "is_published": True
        },
        {
            "title": "CSS Styling Introduction",
            "content_type": ContentType.VIDEO.value,
            "order_index": 2,
            "vimeo_video_id": "123456791",
            "video_duration": 720,
            "is_published": True
        },
        {
            "title": "HTML & CSS Practice Exercises",
            "content_type": ContentType.RICH_TEXT.value,
            "order_index": 3,
            "rich_text_content": json.dumps({
                "blocks": [
                    {
                        "id": "block_1",
                        "type": "paragraph",
                        "content": "Now it's time to practice what you've learned! Complete the following exercises to reinforce your HTML and CSS skills."
                    },
                    {
                        "id": "block_2",
                        "type": "exercise",
                        "exercise_id": "ex_002",
                        "title": "HTML Structure Quiz",
                        "questions": [
                            {
                                "id": "q1",
                                "type": "radio",
                                "question": "Which HTML tag is used for the largest heading?",
                                "options": [
                                    {"value": "a", "label": "<h1>"},
                                    {"value": "b", "label": "<h6>"},
                                    {"value": "c", "label": "<heading>"}
                                ]
                            },
                            {
                                "id": "q2",
                                "type": "text",
                                "question": "Write the HTML code to create a link to https://example.com:",
                                "placeholder": "<a href=..."
                            }
                        ]
                    }
                ]
            }),
            "is_published": True
        }
    ]
    
    # Module 3: JavaScript Essentials
    module3_content = [
        {
            "title": "JavaScript Introduction",
            "content_type": ContentType.VIDEO.value,
            "order_index": 1,
            "vimeo_video_id": "123456792",
            "video_duration": 540,
            "is_published": True
        },
        {
            "title": "Variables and Data Types",
            "content_type": ContentType.RICH_TEXT.value,
            "order_index": 2,
            "rich_text_content": json.dumps({
                "blocks": [
                    {
                        "id": "block_1",
                        "type": "heading",
                        "level": 2,
                        "content": "JavaScript Variables"
                    },
                    {
                        "id": "block_2",
                        "type": "paragraph",
                        "content": "Variables are containers for storing data values. In JavaScript, we can declare variables using let, const, or var."
                    },
                    {
                        "id": "block_3",
                        "type": "paragraph",
                        "content": "Example: let name = 'John'; const age = 25; var city = 'Nairobi';"
                    }
                ]
            }),
            "is_published": True
        }
    ]
    
    # Create content for each module
    content_map = {
        0: module1_content,
        1: module2_content,
        2: module3_content
    }
    
    for idx, module in enumerate(modules[:3]):  # Only first 3 modules get content
        if idx in content_map:
            for content_data in content_map[idx]:
                content = Content(
                    module_id=module.id,
                    content_type=content_data["content_type"],
                    title=content_data["title"],
                    order_index=content_data["order_index"],
                    vimeo_video_id=content_data.get("vimeo_video_id"),
                    video_duration=content_data.get("video_duration"),
                    pdf_url=content_data.get("pdf_url"),
                    pdf_filename=content_data.get("pdf_filename"),
                    rich_text_content=content_data.get("rich_text_content"),
                    is_published=content_data["is_published"]
                )
                db.add(content)
                print(f"  ✓ Content: {content.title} ({content.content_type})")
    
    db.commit()


def create_sample_announcements(db: Session, admin_id: str) -> None:
    """Create sample announcements."""
    print("\nCreating sample announcements...")
    
    # Check if announcements already exist
    existing_announcements = db.query(Announcement).first()
    if existing_announcements:
        print("  ✓ Announcements already exist")
        return
    
    announcements_data = [
        {
            "title": "Welcome to the Course!",
            "content": """Welcome to the Complete Web Development Bootcamp! We're excited to have you here.

This course is designed to take you from beginner to job-ready web developer. Make sure to:
- Complete all modules in order
- Practice the exercises
- Ask questions if you get stuck
- Build your own projects alongside the course

Let's get started on your web development journey!""",
            "is_published": True
        },
        {
            "title": "New Module Released: React Framework",
            "content": """Great news! Module 4 on React Framework is now available.

In this module, you'll learn:
- React components and JSX
- State and props
- React hooks
- Building interactive UIs

This is one of the most important modules as React is widely used in the industry. Take your time and practice!""",
            "is_published": True
        },
        {
            "title": "Office Hours This Week",
            "content": """Join me for live office hours this Friday at 3 PM EAT.

We'll cover:
- Common questions from students
- Live coding session
- Career advice for web developers
- Q&A session

See you there!""",
            "is_published": True
        }
    ]
    
    for announcement_data in announcements_data:
        announcement = Announcement(
            title=announcement_data["title"],
            content=announcement_data["content"],
            created_by=admin_id,
            is_published=announcement_data["is_published"]
        )
        db.add(announcement)
        print(f"  ✓ Announcement: {announcement.title}")
    
    db.commit()


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
        
        # Create sample course
        course = create_sample_course(db)
        
        # Create sample modules
        modules = create_sample_modules(db, course.id)
        
        # Create sample content
        create_sample_content(db, modules)
        
        # Create sample announcements
        create_sample_announcements(db, admin.id)
        
        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print("\nAdmin Credentials:")
        print("  Email: admin@lms.com")
        print("  Password: Admin@123")
        print("\nYou can now start the backend server and login with these credentials.")
        
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
