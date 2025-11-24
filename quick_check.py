"""Quick health check for LMS system."""
import requests
import sys

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def check_backend():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend is NOT running")
        print("   Start with: cd backend && uvicorn app.main:app --reload")
        return False

def check_frontend():
    """Check if frontend is running."""
    try:
        response = requests.get(FRONTEND_URL, timeout=2)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"⚠️ Frontend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ Frontend is NOT running")
        print("   Start with: cd frontend && npm run dev")
        return False

def check_student_enrollment():
    """Check if test student is enrolled."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"email": "student1@test.com", "password": "Student@123"},
            timeout=2
        )
        
        if response.status_code == 200:
            user = response.json()["user"]
            if user["is_enrolled"]:
                print("✅ Student1 is enrolled")
                return True
            else:
                print("⚠️ Student1 is NOT enrolled")
                print("   Enroll at: http://localhost:3000/students/dashboard")
                return False
        else:
            print("⚠️ Could not verify student enrollment")
            return False
    except requests.exceptions.RequestException:
        print("⚠️ Could not check student enrollment (backend may be down)")
        return False

def check_course_content():
    """Check if course has modules."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/course/modules/public", timeout=2)
        
        if response.status_code == 200:
            modules = response.json()
            if len(modules) > 0:
                print(f"✅ Course has {len(modules)} module(s)")
                for module in modules:
                    print(f"   - {module['title']}: {module['content_count']} items")
                return True
            else:
                print("⚠️ Course has NO modules")
                print("   Add modules in admin panel")
                return False
        else:
            print("⚠️ Could not check course content")
            return False
    except requests.exceptions.RequestException:
        print("⚠️ Could not check course content (backend may be down)")
        return False

def main():
    print("=" * 60)
    print("LMS QUICK HEALTH CHECK")
    print("=" * 60)
    print()
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    
    if backend_ok:
        student_ok = check_student_enrollment()
        content_ok = check_course_content()
    else:
        student_ok = False
        content_ok = False
    
    print()
    print("=" * 60)
    
    if backend_ok and frontend_ok and student_ok and content_ok:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print()
        print("🎓 Access the LMS:")
        print(f"   Frontend: {FRONTEND_URL}")
        print(f"   Backend:  {BACKEND_URL}/docs")
        print()
        print("👤 Login as student:")
        print("   Email: student1@test.com")
        print("   Password: Student@123")
        print()
        print("📚 Course page:")
        print(f"   {FRONTEND_URL}/students/course")
        sys.exit(0)
    else:
        print("⚠️ SOME ISSUES DETECTED")
        print()
        print("Please fix the issues above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
