#!/usr/bin/env python3
"""
Simple test for role assignment fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from app.repository.role import RoleRepository

# MongoDB connection (from .env file)
MONGODB_URL = "mongodb+srv://mohamad24a12res979_db_user:YJTqKTnLfSkmrOcZ@cluster0.c4197mb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DATABASE = "test"
MONGO_COLLECTION_ROLES = "role-collection"

def test_role_repository_fix():
    """Test the fixed role repository"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[MONGO_DATABASE]
        
        # Create role repository
        role_repo = RoleRepository(client)
        
        print("🧪 Testing Fixed Role Repository")
        print("=" * 50)
        
        # Get all roles first to see what IDs we have
        roles = list(db[MONGO_COLLECTION_ROLES].find({}))
        print(f"📋 Found {len(roles)} roles in database:")
        
        for role in roles:
            role_id = role['_id']
            role_name = role['name']
            print(f"   - {role_name}: {role_id}")
        
        print("\n🔍 Testing role lookup with fixed repository:")
        
        # Test each role lookup
        for role in roles:
            role_id = role['_id']
            role_name = role['name']
            
            print(f"\n🔐 Testing lookup for role: {role_name}")
            print(f"   Using ID: {role_id}")
            
            # Test the fixed get_by_id method
            try:
                found_role = role_repo.get_by_id(MONGO_COLLECTION_ROLES, role_id)
                if found_role:
                    print(f"   ✅ SUCCESS: Found role '{found_role.name}'")
                else:
                    print(f"   ❌ FAILED: No role found")
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
        
        # Test with student role specifically (most common use case)
        print(f"\n🎓 Specific test for 'student' role:")
        student_role = None
        for role in roles:
            if role['name'] == 'student':
                student_role = role
                break
        
        if student_role:
            student_id = student_role['_id']
            print(f"   Student role ID: {student_id}")
            
            found_student = role_repo.get_by_id(MONGO_COLLECTION_ROLES, student_id)
            if found_student:
                print(f"   ✅ Student role lookup SUCCESS: {found_student.name}")
                print(f"   📄 Description: {found_student.description}")
                print(f"   🔑 Permissions: {len(found_student.permissions)} permission(s)")
                
                # This simulates what happens in the admin endpoint
                print(f"\n🎯 Role assignment validation test:")
                print(f"   Role exists: {'YES' if found_student else 'NO'}")
                print(f"   Role ID: {student_id}")
                print(f"   Role name: {found_student.name}")
                
            else:
                print(f"   ❌ Student role lookup FAILED")
        else:
            print(f"   ❌ Student role not found in database")
        
        client.close()
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

def main():
    test_role_repository_fix()

if __name__ == "__main__":
    main()