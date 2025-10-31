import requests
import json

# Test the token endpoint
def test_token_endpoint():
    url = "http://127.0.0.1:8006/api/v1/token"
    
    # Test data - only username and password as required by OAuth2PasswordRequestForm
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Token endpoint works correctly!")
            return response.json()["access_token"]
        else:
            print("❌ Token endpoint failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error testing token endpoint: {e}")
        return None

# Test protected endpoint with token
def test_protected_endpoint(token):
    if not token:
        print("❌ No token available for testing protected endpoint")
        return
        
    url = "http://127.0.0.1:8006/api/v1/users/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nProtected endpoint status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Protected endpoint works correctly!")
        else:
            print("❌ Protected endpoint failed!")
            
    except Exception as e:
        print(f"❌ Error testing protected endpoint: {e}")

if __name__ == "__main__":
    print("🧪 Testing Authorization System...")
    print("=" * 50)
    
    # Test 1: Token endpoint
    print("1. Testing token endpoint (username + password only):")
    token = test_token_endpoint()
    
    # Test 2: Protected endpoint
    print("\n2. Testing protected endpoint with token:")
    test_protected_endpoint(token)
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")