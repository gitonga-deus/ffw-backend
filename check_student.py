"""Check student enrollment status."""
import requests

BACKEND_URL = "http://localhost:8000"

# Login as student1
response = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"email": "student1@test.com", "password": "Student@123"}
)

if response.status_code == 200:
    data = response.json()
    token = data["access_token"]
    user = data["user"]
    
    print(f"✅ Logged in as: {user['full_name']}")
    print(f"   Email: {user['email']}")
    print(f"   Is Enrolled: {user['is_enrolled']}")
    print(f"   Is Verified: {user['is_verified']}")
    
    if user['is_enrolled']:
        # Check enrollment status
        response = requests.get(
            f"{BACKEND_URL}/api/enrollment/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            enrollment = response.json()
            print(f"\n📋 Enrollment Status:")
            print(f"   Has Signature: {enrollment.get('has_signature', False)}")
            print(f"   Progress: {enrollment.get('progress_percentage', 0)}%")
        
        # Check course modules
        response = requests.get(
            f"{BACKEND_URL}/api/course/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            modules = response.json()
            print(f"\n📚 Course Modules: {len(modules)}")
            for module in modules:
                print(f"   - {module['title']}: {module['content_count']} items")
        else:
            print(f"\n❌ Failed to get modules: {response.status_code}")
            print(f"   {response.text}")
    else:
        print("\n⚠️ Student is not enrolled")
else:
    print(f"❌ Login failed: {response.status_code}")
    print(f"   {response.text}")
