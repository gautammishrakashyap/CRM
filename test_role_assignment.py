#!/usr/bin/env python3
"""
Test script to reproduce the role assignment issue
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8006/api/v1"

def get_auth_token():
    """Get authentication token"""
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

def list_roles(token):
    """List all available roles"""
    url = f"{BASE_URL}/admin/roles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            roles = response.json()["roles"]
            print(f"✅ Found {len(roles)} roles:")
            for role in roles:
                print(f"  - {role['name']} (ID: {role['role_id']})")
            return roles
        else:
            print(f"❌ Failed to list roles: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error listing roles: {e}")
        return []

def list_users(token):
    """List all users"""
    url = f"{BASE_URL}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            users = response.json()["users"]
            print(f"✅ Found {len(users)} users:")
            for user in users:
                print(f"  - {user['username']} (ID: {user['user_id']})")
            return users
        else:
            print(f"❌ Failed to list users: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []

def assign_role_to_user(token, user_id, role_id):
    """Assign a role to a user"""
    url = f"{BASE_URL}/admin/users/roles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "user_id": user_id,
        "role_id": role_id
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Role assignment response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Successfully assigned role: {result['message']}")
            return True
        else:
            print(f"❌ Failed to assign role: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error assigning role: {e}")
        return False

def create_test_user(token):
    """Create a test user for role assignment"""
    url = f"{BASE_URL}/users"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Created test user: {user['username']} (ID: {user['user_id']})")
            return user
        else:
            print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def main():
    print("🧪 Testing Role Assignment Issue...")
    print("=" * 50)
    
    # Step 1: Get authentication token
    print("\n1. Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Step 2: List available roles
    print("\n2. Listing available roles...")
    roles = list_roles(token)
    if not roles:
        print("❌ No roles found or error listing roles")
        sys.exit(1)
    
    # Step 3: List users or create test user
    print("\n3. Listing users...")
    users = list_users(token)
    
    # If no users other than admin, create a test user
    test_user = None
    for user in users:
        if user['username'] != 'admin':
            test_user = user
            break
    
    if not test_user:
        print("\n4. Creating test user...")
        test_user = create_test_user(token)
        if not test_user:
            print("❌ Cannot proceed without a test user")
            sys.exit(1)
    else:
        print(f"\n4. Using existing test user: {test_user['username']}")
    
    # Step 4: Try to assign a role
    print("\n5. Attempting role assignment...")
    if roles:
        student_role = None
        for role in roles:
            if role['name'] == 'student':
                student_role = role
                break
        
        if student_role:
            print(f"Assigning role '{student_role['name']}' (ID: {student_role['role_id']}) to user '{test_user['username']}' (ID: {test_user['user_id']})")
            success = assign_role_to_user(token, test_user['user_id'], student_role['role_id'])
            
            if success:
                print("✅ Role assignment successful!")
            else:
                print("❌ Role assignment failed!")
        else:
            print("❌ Student role not found")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()