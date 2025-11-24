"""
Test script for 123FormBuilder webhook integration.

This script tests the webhook endpoint by sending a test payload.
"""
import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@lms.com"  # Update with your admin email
ADMIN_PASSWORD = "Admin@123"  # Update with your admin password

# Test data
TEST_PAYLOAD = {
    "form_id": "6205487",  # Your exercise form_id
    "submission_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "user_email": "student1@test.com",  # Your enrolled student email
    "submitted_at": datetime.utcnow().isoformat() + "Z",
    "responses": {
        "question_1": "Test answer for question 1",
        "question_2": "Test answer for question 2",
        "passion_killer_1": "Fear of failure",
        "passion_killer_2": "Lack of focus"
    }
}


def login_admin():
    """Login as admin and get access token."""
    print("🔐 Logging in as admin...")
    
    response = requests.post(
        f"{BACKEND_URL}/api/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful! Admin: {data['user']['full_name']}")
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_webhook(access_token):
    """Test the webhook endpoint."""
    print("\n📤 Sending test webhook payload...")
    print(f"   Form ID: {TEST_PAYLOAD['form_id']}")
    print(f"   User Email: {TEST_PAYLOAD['user_email']}")
    print(f"   Submission ID: {TEST_PAYLOAD['submission_id']}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/webhooks/123formbuilder/test",
        headers=headers,
        json=TEST_PAYLOAD
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Webhook test successful!")
        print(f"\n📊 Response Data:")
        print(json.dumps(data, indent=2))
        return True
    else:
        print(f"❌ Webhook test failed!")
        print(f"\n📊 Response:")
        print(json.dumps(response.json(), indent=2))
        return False


def check_submission(access_token, exercise_id=""):
    """Check if submission was recorded."""
    print("\n🔍 Checking submission status...")
    
    # First, get the exercise ID
    if not exercise_id:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/admin/exercises",
            headers=headers
        )
        
        if response.status_code == 200:
            exercises = response.json()
            if exercises:
                exercise_id = exercises[0]["id"]
                print(f"   Found exercise ID: {exercise_id}")
    
    if exercise_id:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/admin/exercises/{exercise_id}/submissions",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Submission Statistics:")
            print(f"   Total Submissions: {data['total_submissions']}")
            print(f"   Unique Users: {data['unique_users']}")
            print(f"   Completion Rate: {data['completion_rate']}%")
            
            if data['submissions']:
                print(f"\n📝 Recent Submissions:")
                for sub in data['submissions'][:3]:  # Show last 3
                    print(f"   - {sub['user_name']} ({sub['user_email']})")
                    print(f"     Submitted: {sub['submitted_at']}")
        else:
            print(f"   ❌ Failed to get submissions: {response.status_code}")


def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 123FormBuilder Webhook Test")
    print("=" * 60)
    
    # Step 1: Login
    access_token = login_admin()
    if not access_token:
        print("\n❌ Cannot proceed without admin access token")
        return
    
    # Step 2: Test webhook
    success = test_webhook(access_token)
    
    # Step 3: Check submission (if successful)
    if success:
        check_submission(access_token)
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
