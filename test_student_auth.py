#!/usr/bin/env python3
"""
Test student authorization and role assignment
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8006/api/v1"

def get_auth_token():
    """Get authentication token for admin user"""
    url = f"{BASE_URL}/token"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Successfully obtained auth token")
            return token
        else:
            print(f"❌ Failed to get token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None

def test_student_endpoint_without_role(token):
    """Test student endpoint with admin user (should work)"""
    url = f"{BASE_URL}/student/profile"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Student profile access with admin user: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin can access student endpoints (expected)")
            return True
        else:
            print(f"❌ Admin cannot access student endpoints: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing student endpoint: {e}")
        return False

def create_test_user_without_student_role():
    """Create a test user without student role"""
    url = f"{BASE_URL}/users"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": "testuser_no_role",
        "email": "testuser_no_role@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Created test user without role: {user['username']}")
            return user
        else:
            print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def get_token_for_user(username, password):
    """Get token for specific user"""
    url = f"{BASE_URL}/token"
    data = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Got token for user: {username}")
            return token
        else:
            print(f"❌ Failed to get token for {username}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token for {username}: {e}")
        return None

def test_student_endpoint_with_unauthorized_user(token):
    """Test student endpoint with user that doesn't have student role"""
    url = f"{BASE_URL}/student/profile"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Student profile access with unauthorized user: {response.status_code}")
        if response.status_code == 403:
            error_detail = response.json().get('detail', 'No detail provided')
            print(f"✅ Proper authorization error: {error_detail}")
            return True
        elif response.status_code == 200:
            print("❌ Unauthorized user can access student endpoints (this should be blocked)")
            return False
        else:
            print(f"❌ Unexpected response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing unauthorized access: {e}")
        return False

def assign_student_role_to_user(admin_token, user_id, student_role_id):
    """Assign student role to user"""
    url = f"{BASE_URL}/admin/users/roles"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "role_id": student_role_id
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print("✅ Successfully assigned student role")
            return True
        else:
            print(f"❌ Failed to assign student role: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error assigning student role: {e}")
        return False

def get_student_role_id(admin_token):
    """Get the student role ID"""
    url = f"{BASE_URL}/admin/roles"
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            roles = response.json()["roles"]
            for role in roles:
                if role["name"] == "student":
                    print(f"✅ Found student role ID: {role['role_id']}")
                    return role["role_id"]
            print("❌ Student role not found")
            return None
        else:
            print(f"❌ Failed to get roles: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting roles: {e}")
        return None

def main():
    print("🧪 Testing Student Authorization Fix")
    print("=" * 60)
    
    # Step 1: Get admin token
    print("\n1. Getting admin authentication token...")
    admin_token = get_auth_token()
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        sys.exit(1)
    
    # Step 2: Test admin access to student endpoints
    print("\n2. Testing admin access to student endpoints...")
    admin_access = test_student_endpoint_without_role(admin_token)
    
    # Step 3: Create a user without student role
    print("\n3. Creating test user without student role...")
    test_user = create_test_user_without_student_role()
    if not test_user:
        print("❌ Cannot proceed without test user")
        sys.exit(1)
    
    # Step 4: Get token for test user
    print("\n4. Getting token for test user...")
    user_token = get_token_for_user(test_user["username"], "testpass123")
    if not user_token:
        print("❌ Cannot proceed without user token")
        sys.exit(1)
    
    # Step 5: Test unauthorized access (should fail)
    print("\n5. Testing unauthorized access to student endpoints...")
    unauthorized_access = test_student_endpoint_with_unauthorized_user(user_token)
    
    # Step 6: Get student role ID
    print("\n6. Getting student role ID...")
    student_role_id = get_student_role_id(admin_token)
    if not student_role_id:
        print("❌ Cannot proceed without student role ID")
        sys.exit(1)
    
    # Step 7: Assign student role to test user
    print("\n7. Assigning student role to test user...")
    role_assigned = assign_student_role_to_user(admin_token, test_user["user_id"], student_role_id)
    
    if role_assigned:
        # Step 8: Test authorized access (should work now)
        print("\n8. Testing authorized access after role assignment...")
        authorized_access = test_student_endpoint_without_role(user_token)
        
        if authorized_access:
            print("✅ User can access student endpoints after getting student role")
        else:
            print("❌ User still cannot access student endpoints after role assignment")
    
    print("\n" + "=" * 60)
    print("🏁 Authorization test completed!")
    
    # Summary
    print(f"\nSummary:")
    print(f"- Admin access: {'✅ PASS' if admin_access else '❌ FAIL'}")
    print(f"- Unauthorized access blocked: {'✅ PASS' if unauthorized_access else '❌ FAIL'}")
    print(f"- Role assignment: {'✅ PASS' if role_assigned else '❌ FAIL'}")

if __name__ == "__main__":
    main()