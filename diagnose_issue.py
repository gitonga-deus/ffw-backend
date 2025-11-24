"""Comprehensive diagnostic script to check course visibility issue."""
import requests
import json

BACKEND_URL = "http://localhost:8000"

def check_database_state():
    """Check what's in the database."""
    print("=" * 60)
    print("DATABASE STATE CHECK")
    print("=" * 60)
    
    # Login as admin
    response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"email": "admin@lms.com", "password": "Admin@123"}
    )
    
    if response.status_code != 200:
        print("❌ Admin login failed")
        return
    
    admin_token = response.json()["access_token"]
    
    # Check course
    response = requests.get(f"{BACKEND_URL}/api/course")
    if response.status_code == 200:
        course = response.json()
        print(f"\n✅ Course exists:")
        print(f"   Title: {course['title']}")
        print(f"   Published: {course['is_published']}")
    else:
        print(f"\n❌ No course found: {response.status_code}")
    
    # Check modules (public)
    response = requests.get(f"{BACKEND_URL}/api/course/modules/public")
    if response.status_code == 200:
        modules = response.json()
        print(f"\n✅ Public modules: {len(modules)}")
        for module in modules:
            print(f"   - {module['title']}: {module['content_count']} items (published: {module['is_published']})")
    else:
        print(f"\n❌ Failed to get public modules: {response.status_code}")

def check_student_access():
    """Check student access to course."""
    print("\n" + "=" * 60)
    print("STUDENT ACCESS CHECK")
    print("=" * 60)
    
    # Login as student1
    response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={"email": "student1@test.com", "password": "Student@123"}
    )
    
    if response.status_code != 200:
        print("❌ Student login failed")
        return
    
    data = response.json()
    token = data["access_token"]
    user = data["user"]
    
    print(f"\n✅ Student logged in:")
    print(f"   Name: {user['full_name']}")
    print(f"   Email: {user['email']}")
    print(f"   Enrolled: {user['is_enrolled']}")
    print(f"   Verified: {user['is_verified']}")
    
    if not user['is_enrolled']:
        print("\n⚠️ Student is NOT enrolled - this is the problem!")
        return
    
    # Check enrollment status
    response = requests.get(
        f"{BACKEND_URL}/api/enrollment/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        enrollment = response.json()
        print(f"\n✅ Enrollment status:")
        print(f"   Has signature: {enrollment.get('has_signature', False)}")
        print(f"   Progress: {enrollment.get('progress_percentage', 0)}%")
        
        if not enrollment.get('has_signature'):
            print("\n⚠️ Student has NO signature - will be redirected to signature page")
    else:
        print(f"\n❌ Failed to get enrollment status: {response.status_code}")
        print(f"   {response.text}")
    
    # Check course modules (enrolled endpoint)
    response = requests.get(
        f"{BACKEND_URL}/api/course/modules",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        modules = response.json()
        print(f"\n✅ Course modules accessible: {len(modules)}")
        for module in modules:
            print(f"   - {module['title']}")
            print(f"     Content: {module['content_count']} items")
            print(f"     Completed: {module['completed_count']} items")
            print(f"     Progress: {module['progress_percentage']}%")
    else:
        print(f"\n❌ Failed to get course modules: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Check progress
    response = requests.get(
        f"{BACKEND_URL}/api/progress",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        progress = response.json()
        print(f"\n✅ Progress data:")
        print(f"   Overall: {progress.get('progress_percentage', 0)}%")
        print(f"   Completed modules: {progress.get('completed_modules', 0)}/{progress.get('total_modules', 0)}")
    else:
        print(f"\n❌ Failed to get progress: {response.status_code}")

def main():
    print("\n🔍 LMS DIAGNOSTIC TOOL\n")
    
    try:
        check_database_state()
        check_student_access()
        
        print("\n" + "=" * 60)
        print("DIAGNOSIS COMPLETE")
        print("=" * 60)
        print("\nIf modules are showing in backend but not frontend:")
        print("1. Check browser console for errors")
        print("2. Verify frontend is running (npm run dev)")
        print("3. Check if student is logged in on frontend")
        print("4. Clear browser cache and localStorage")
        print("5. Check network tab for failed API calls")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
