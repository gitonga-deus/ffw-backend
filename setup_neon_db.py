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
import json
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
    
    # Check if tables already exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if len(tables) >= 10:  # We expect at least 10 tables
        print("✓ Database tables already exist, skipping migrations")
        return True
    
    try:
        import subprocess
        
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
            print("⚠ Migration command failed, but continuing anyway...")
            print("  (Tables may already exist)")
            return True  # Continue anyway
            
    except FileNotFoundError:
        print("⚠ Alembic not found in PATH, but continuing anyway...")
        print("  (Tables may already exist)")
        return True  # Continue anyway
    except Exception as e:
        print(f"⚠ Error running migrations: {str(e)}")
        print("  Continuing anyway (tables may already exist)...")
        return True  # Continue anyway


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


def get_course_data() -> dict:
    """Get course data structure."""
    return {
        "course": {
            "title": "Financially Fit For Life - The Seven Steps",
            "description": "Financially Fit for life is the global leader in world class personal wealth education. This comprehensive course will teach you the seven essential steps to achieving financial freedom and building lasting wealth.",
            "price": 1000.00,
            "currency": "KES",
            "instructor_name": "Steven Down",
            "instructor_bio": "Steven Down is an entrepreneur and business maverick whose ideas about wealth creation, service to the community and personal excellence are transforming lives all over the world. His business acumen helped create the hugely successful Even Stevens chain of sandwich stores, the Financially Fit LLC, and a host of stellar business enterprises that became icons in their areas of specialization. As America's Wealth Coach, Steve went on coast-to-coast tours giving speeches and hosting seminars and helped millions change their perception and understanding of money, wealth, and how to achieve principle centered wealth.",
            "is_published": True
        },
        "modules": [
            {
                "title": " Introduction to Financially Fit for Life By Steve Down",
                "description": "",
                "order_index": 0,
                "is_published": True,
                "content": [
                    {
                        "title": "Introduction to Financially Fit for Life by Steve Down Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Announcement</h2><p>I desire to empower you with the knowledge to accelerate a positive change in your financial life, a change so fast, you will mark today on your calendar as the turning point in your financial fitness. My goal is to inspire your heart in a way that can breathe new energy into your life. Once you have a healthy wealth heart, you can live a life of wealth!</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Financially Fit For Life Introduction - Part 1",
                        "content_type": "video",
                        "vimeo_video_id": "918683382",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Financially Fit For Life Introduction - Part 2",
                        "content_type": "video",
                        "vimeo_video_id": "918683993",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    },
                    {
                        "title": "Financially Fit For Life Introduction - Part 3",
                        "content_type": "video",
                        "vimeo_video_id": "918684229",
                        "video_duration": None,
                        "order_index": 3,
                        "is_published": True
                    },
                    {
                        "title": "Financially Fit For Life Introduction - Part 4",
                        "content_type": "video",
                        "vimeo_video_id": "918685087",
                        "video_duration": None,
                        "order_index": 4,
                        "is_published": True
                    },
                    {
                        "title": "Financially Fit For Life Introduction - Part 5",
                        "content_type": "video",
                        "vimeo_video_id": "918685410",
                        "video_duration": None,
                        "order_index": 5,
                        "is_published": True
                    },
                    {
                        "title": "Terms Used in Financially Fit for Life",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2><strong>Financial Freedom</strong></h2><p>A state in which an individual or household has sufficient wealth to live on without having to depend on income from some form of employment.</p><p></p><h2><strong>Freedom</strong></h2><p>Money is a tool of freedom.</p><p></p><h2>Money</h2><p>Money is a tool of purchase.</p><p></p><h2><strong>Proactive</strong></h2><p>Taking deliberate action.</p>",
                        "order_index": 6,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 1 - Wealth Awakening",
                "description": "",
                "order_index": 1,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 1 - Wealth Awakening Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Announcements</h2><p>One of the most important things I've learned from experience is that we are in life exactly where we've chosen to be. We are precisely there because of the choices we've made in the past.</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 1 Wealth Awakening - Part 1 (Wealth Is a Matter of Choice)",
                        "content_type": "video",
                        "vimeo_video_id": "918685797",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 1 Wealth Awakening - Part 2 (A Clear Passionate Wealth Vision Empowers You)",
                        "content_type": "video",
                        "vimeo_video_id": "918687371",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    },
                    {
                        "title": "Step 1 Wealth Awakening - Part 3 (Goal Setting Launches You Towards your Wealth Vision)",
                        "content_type": "video",
                        "vimeo_video_id": "918688000",
                        "video_duration": None,
                        "order_index": 3,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 2 - Psychology of Wealth",
                "description": "",
                "order_index": 2,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 2 - Psychology of Wealth Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Announcements: <strong>Psychology of Wealth</strong></h2><p>What I wish I'd learned in college but my professors didn't know</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 2 Psychology of Wealth - Part 1 (Wealth Comes From The Heart)",
                        "content_type": "video",
                        "vimeo_video_id": "918688509",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 2 Psychology of Wealth - Part 2 (The As If Principle)",
                        "content_type": "video",
                        "vimeo_video_id": "918689615",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 3 Cash Flow For Life",
                "description": "",
                "order_index": 3,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 3 Cash Flow For Life Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Announcements: Cash Flow for Life</h2><p>When it comes to managing cash flow, most of us are out of control.</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 3 Cash Flow For Life - Part 1 (Is Your Cash Flow Out Of Control)",
                        "content_type": "video",
                        "vimeo_video_id": "918692344",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 3 Cash Flow For Life - Part 2 (First Measure Then Manage)",
                        "content_type": "video",
                        "vimeo_video_id": "918692625",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    },
                    {
                        "title": "Step 3 Cash Flow For Life - Part 3 (Are You Running on a Financial Treadmill)",
                        "content_type": "video",
                        "vimeo_video_id": "918693178",
                        "video_duration": None,
                        "order_index": 3,
                        "is_published": True
                    },
                    {
                        "title": "Step 3 Cash Flow For Life - Part 4 (Work Smarter Not Harder)",
                        "content_type": "video",
                        "vimeo_video_id": "918693757",
                        "video_duration": None,
                        "order_index": 4,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 4 - Secure for Life",
                "description": "",
                "order_index": 4,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 4 - Secure for Life Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Announcements: Secure for Life</h2><blockquote><p>Money is power, freedom, a cushion, the root of all evil, the sum of blessings. - Carl Sandburg</p></blockquote><p></p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 4 Secure For Life - Part 1 (Money Is Good)",
                        "content_type": "video",
                        "vimeo_video_id": "918694913",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 4 Secure For Life - Part 2 (Are You Three Months Away From a Financial Heart Attack)",
                        "content_type": "video",
                        "vimeo_video_id": "918695869",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 5 - Debt Free for Life",
                "description": "",
                "order_index": 5,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 5 - Debt Free for Life Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Debt Free for Life</h2><p>Begin by reading a short story called \"The Puppet Master\", which is found at the end of this section.</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Part 1- Read the Puppet Master",
                        "content_type": "video",
                        "vimeo_video_id": "918696996",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Part 2- Wake Up To The Debt Free For Life Philosophy",
                        "content_type": "video",
                        "vimeo_video_id": "918697169",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    },
                    {
                        "title": "Part 3 -Debt Rate And Pulse Check Up,  Imagine That",
                        "content_type": "video",
                        "vimeo_video_id": "918696996",
                        "video_duration": None,
                        "order_index": 3,
                        "is_published": True
                    },
                    {
                        "title": "Part 4 -Run On Cash",
                        "content_type": "video",
                        "vimeo_video_id": "918698208",
                        "video_duration": None,
                        "order_index": 4,
                        "is_published": True
                    },
                    {
                        "title": "Part 5- Financial Bulimia Check Up",
                        "content_type": "video",
                        "vimeo_video_id": "918698845",
                        "video_duration": None,
                        "order_index": 5,
                        "is_published": True
                    },
                    {
                        "title": "Part 6- Being Debt Free Is Your Responsibility",
                        "content_type": "video",
                        "vimeo_video_id": "918698998",
                        "video_duration": None,
                        "order_index": 6,
                        "is_published": True
                    },
                    {
                        "title": "Part 7- Out Of The Red And In The Black",
                        "content_type": "video",
                        "vimeo_video_id": "918699208",
                        "video_duration": None,
                        "order_index": 7,
                        "is_published": True
                    },
                    {
                        "title": "Part 8- Become Totally Debt Free In Five Years",
                        "content_type": "video",
                        "vimeo_video_id": "918699480",
                        "video_duration": None,
                        "order_index": 8,
                        "is_published": True
                    },
                    {
                        "title": "Part 9- Debt Free For Life Proclamation",
                        "content_type": "video",
                        "vimeo_video_id": "918700058",
                        "video_duration": None,
                        "order_index": 9,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 6 - Wealth for Life",
                "description": "",
                "order_index": 6,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 6 - Wealth for Life Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Wealth for Life Forum</h2><p>This is the step you can mark on your journey as the most exciting as you become <strong><em>Financially Fit for Life.</em></strong></p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 6 Wealth For Life - Part 1 Take Personal Control Of Your Investments",
                        "content_type": "video",
                        "vimeo_video_id": "918712327",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 6 Wealth For Life - Part 2 (Achieve Wealth For Life In Ten Years Or Less)",
                        "content_type": "video",
                        "vimeo_video_id": "918712749",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "Step 7 - Living The Seven Steps",
                "description": "",
                "order_index": 7,
                "is_published": True,
                "content": [
                    {
                        "title": "Step 7 - Living The Seven Steps Announcement",
                        "content_type": "rich_text",
                        "rich_text_content": "<h2>Living the Seven Steps Forum</h2><p>You should now be on the fast track to becoming <em>Financially Fit for Life</em> and on to true <em>Wealth for Life</em>. Congratulations!</p>",
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "Step 7 Living The Seven Steps - Part 1 (Renew The Seven Steps)",
                        "content_type": "video",
                        "vimeo_video_id": "918713568",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "Step 7 Living The Seven Steps - Part 2 (Teach It To Retain It)",
                        "content_type": "video",
                        "vimeo_video_id": "918713858",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    }
                ]
            },
            {
                "title": "The Miracle Of Wealth -Free Gift Audio Book by Steve Down",
                "description": "",
                "order_index": 8,
                "is_published": True,
                "content": [
                    {
                        "title": "The Miracle of Wealth - Introduction",
                        "content_type": "video",
                        "vimeo_video_id": "918741569",
                        "video_duration": None,
                        "order_index": 0,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #1 10x Wealth",
                        "content_type": "video",
                        "vimeo_video_id": "918742207",
                        "video_duration": None,
                        "order_index": 1,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #2 Analysis, The Risk and Reward Paradigm",
                        "content_type": "video",
                        "vimeo_video_id": "918742850",
                        "video_duration": None,
                        "order_index": 2,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #3 Structure - The Intelligent Investor",
                        "content_type": "video",
                        "vimeo_video_id": "918745945",
                        "video_duration": None,
                        "order_index": 3,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #4 Timing - Entry and Exit",
                        "content_type": "video",
                        "vimeo_video_id": "918745966",
                        "video_duration": None,
                        "order_index": 4,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #5 Creation, Invention or Connection",
                        "content_type": "video",
                        "vimeo_video_id": "918745991",
                        "video_duration": None,
                        "order_index": 5,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #6 Attraction - Capital, Credit and Context",
                        "content_type": "video",
                        "vimeo_video_id": "918746014",
                        "video_duration": None,
                        "order_index": 6,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #7 Inside Out, The Creation and Internal Wealth",
                        "content_type": "video",
                        "vimeo_video_id": "918746032",
                        "video_duration": None,
                        "order_index": 7,
                        "is_published": True
                    },
                    {
                        "title": "The Miracle of Wealth - #8 Transcendence, Compassion Capitalism",
                        "content_type": "video",
                        "vimeo_video_id": "918746051",
                        "video_duration": None,
                        "order_index": 8,
                        "is_published": True
                    }
                ]
            }
        ]
    }


def create_course_with_content(db: Session) -> Course:
    """Create complete course structure with all modules and content."""
    print("\n  Creating course with content...")
    
    # Check if course already exists with modules
    existing_course = db.query(Course).first()
    if existing_course:
        module_count = db.query(Module).filter(Module.course_id == existing_course.id).count()
        if module_count > 0:
            print(f"    ✓ Course already exists with {module_count} modules")
            return existing_course
        else:
            print(f"    ⚠ Course exists but has no modules, deleting and recreating...")
            db.delete(existing_course)
            db.commit()
    
    # Get course data
    course_data = get_course_data()
    
    # Create course
    course_info = course_data.get("course", {})
    course = Course(
        title=course_info.get("title"),
        description=course_info.get("description"),
        price=course_info.get("price"),
        currency=course_info.get("currency", "KES"),
        instructor_name=course_info.get("instructor_name"),
        instructor_bio=course_info.get("instructor_bio"),
        instructor_image_url=course_info.get("instructor_image_url"),
        thumbnail_url=course_info.get("thumbnail_url"),
        is_published=course_info.get("is_published", True)
    )
    
    db.add(course)
    db.commit()
    db.refresh(course)
    
    print(f"    ✓ Course created: {course.title}")
    
    # Create modules and content
    modules_data = course_data.get("modules", [])
    total_content_count = 0
    
    for module_data in modules_data:
        # Create module
        module = Module(
            course_id=course.id,
            title=module_data.get("title"),
            description=module_data.get("description", ""),
            order_index=module_data.get("order_index"),
            is_published=module_data.get("is_published", True)
        )
        
        db.add(module)
        db.commit()
        db.refresh(module)
        
        print(f"    ✓ Module {module.order_index + 1}: {module.title}")
        
        # Create content for this module
        content_items = module_data.get("content", [])
        for content_data in content_items:
            content_type = content_data.get("content_type")
            
            # Prepare content fields based on type
            content_fields = {
                "module_id": module.id,
                "title": content_data.get("title"),
                "content_type": content_type,
                "order_index": content_data.get("order_index"),
                "is_published": content_data.get("is_published", True)
            }
            
            # Add type-specific fields
            if content_type == "video":
                content_fields["vimeo_video_id"] = content_data.get("vimeo_video_id")
                content_fields["video_duration"] = content_data.get("video_duration")
            elif content_type == "pdf":
                content_fields["pdf_url"] = content_data.get("pdf_url")
                content_fields["pdf_filename"] = content_data.get("pdf_filename")
            elif content_type == "rich_text":
                # Rich text content needs to be stored as JSON with 'content' and 'exercises' fields
                html_content = content_data.get("rich_text_content")
                rich_text_obj = {
                    "content": html_content,
                    "exercises": []
                }
                import json
                content_fields["rich_text_content"] = json.dumps(rich_text_obj)
            
            content = Content(**content_fields)
            db.add(content)
            total_content_count += 1
            
            print(f"      ✓ Content {content.order_index + 1}: {content.title} ({content_type})")
        
        db.commit()
    
    print(f"\n    ✓ Total: {len(modules_data)} modules, {total_content_count} content items created")
    
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
