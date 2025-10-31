#!/usr/bin/env python3
"""
Direct MongoDB check to see roles and permissions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime

# MongoDB connection (from .env file)
MONGODB_URL = "mongodb+srv://mohamad24a12res979_db_user:YJTqKTnLfSkmrOcZ@cluster0.c4197mb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DATABASE = "test"
MONGO_COLLECTION_ROLES = "role-collection"
MONGO_COLLECTION_PERMISSIONS = "permission-collection"
MONGO_COLLECTION_USERS = "user-collection"
MONGO_COLLECTION_USER_ROLES = "user-role-collection"

def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[MONGO_DATABASE]
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        return client, db
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return None, None

def check_collections(db):
    """Check what collections exist"""
    collections = db.list_collection_names()
    print(f"📁 Available collections: {collections}")
    return collections

def check_roles(db):
    """Check roles in database"""
    try:
        roles_collection = db[MONGO_COLLECTION_ROLES]
        roles_count = roles_collection.count_documents({})
        print(f"📊 Total roles: {roles_count}")
        
        if roles_count > 0:
            roles = list(roles_collection.find({}))
            print("🔐 Roles found:")
            for role in roles:
                role_id = str(role.get('_id', 'No ID'))
                name = role.get('name', 'No name')
                description = role.get('description', 'No description')
                permissions = role.get('permissions', [])
                print(f"  - {name} (ID: {role_id})")
                print(f"    Description: {description}")
                print(f"    Permissions: {len(permissions)} permission(s)")
        else:
            print("❌ No roles found in database")
        
        return roles_count > 0
    except Exception as e:
        print(f"❌ Error checking roles: {e}")
        return False

def check_permissions(db):
    """Check permissions in database"""
    try:
        permissions_collection = db[MONGO_COLLECTION_PERMISSIONS]
        permissions_count = permissions_collection.count_documents({})
        print(f"📊 Total permissions: {permissions_count}")
        
        if permissions_count > 0:
            permissions = list(permissions_collection.find({}))
            print("🔑 Permissions found:")
            for perm in permissions:
                perm_id = str(perm.get('_id', 'No ID'))
                name = perm.get('name', 'No name')
                resource = perm.get('resource', 'No resource')
                action = perm.get('action', 'No action')
                print(f"  - {name} (ID: {perm_id}) - {resource}:{action}")
        else:
            print("❌ No permissions found in database")
        
        return permissions_count > 0
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
        return False

def check_users(db):
    """Check users in database"""
    try:
        users_collection = db[MONGO_COLLECTION_USERS]
        users_count = users_collection.count_documents({})
        print(f"📊 Total users: {users_count}")
        
        if users_count > 0:
            users = list(users_collection.find({}))
            print("👤 Users found:")
            for user in users:
                user_id = str(user.get('_id', 'No ID'))
                username = user.get('username', 'No username')
                email = user.get('email', 'No email')
                is_active = user.get('is_active', False)
                print(f"  - {username} ({email}) (ID: {user_id}) - Active: {is_active}")
        else:
            print("❌ No users found in database")
        
        return users_count > 0
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        return False

def check_user_roles(db):
    """Check user role assignments"""
    try:
        user_roles_collection = db[MONGO_COLLECTION_USER_ROLES]
        user_roles_count = user_roles_collection.count_documents({})
        print(f"📊 Total user-role assignments: {user_roles_count}")
        
        if user_roles_count > 0:
            user_roles = list(user_roles_collection.find({}))
            print("🔗 User-role assignments found:")
            for assignment in user_roles:
                assignment_id = str(assignment.get('_id', 'No ID'))
                user_id = assignment.get('user_id', 'No user_id')
                role_id = assignment.get('role_id', 'No role_id')
                granted_by = assignment.get('granted_by', 'No granted_by')
                created_at = assignment.get('created_at', 'No date')
                print(f"  - Assignment {assignment_id}: User {user_id} -> Role {role_id} (by {granted_by})")
        else:
            print("❌ No user-role assignments found in database")
        
        return user_roles_count > 0
    except Exception as e:
        print(f"❌ Error checking user roles: {e}")
        return False

def test_role_lookup(db):
    """Test role lookup by ID"""
    try:
        roles_collection = db[MONGO_COLLECTION_ROLES]
        roles = list(roles_collection.find({}))
        
        if roles:
            # Test with first role
            test_role = roles[0]
            role_id = str(test_role['_id'])
            print(f"\n🧪 Testing role lookup with ID: {role_id}")
            
            # Test ObjectId conversion
            try:
                object_id = ObjectId(role_id)
                found_role = roles_collection.find_one({"_id": object_id})
                if found_role:
                    print(f"✅ Role lookup successful: {found_role['name']}")
                else:
                    print("❌ Role lookup failed: No role found with ObjectId")
            except Exception as e:
                print(f"❌ ObjectId conversion failed: {e}")
            
            # Test string ID lookup (this should fail)
            found_role_str = roles_collection.find_one({"_id": role_id})
            if found_role_str:
                print(f"✅ String ID lookup successful: {found_role_str['name']}")
            else:
                print("❌ String ID lookup failed (this is expected)")
        
    except Exception as e:
        print(f"❌ Error testing role lookup: {e}")

def main():
    print("🔍 Direct MongoDB Investigation")
    print("=" * 50)
    
    # Connect to MongoDB
    client, db = connect_to_mongo()
    if not client:
        sys.exit(1)
    
    try:
        # Check collections
        print("\n1. Checking available collections...")
        collections = check_collections(db)
        
        # Check permissions
        print("\n2. Checking permissions...")
        check_permissions(db)
        
        # Check roles
        print("\n3. Checking roles...")
        check_roles(db)
        
        # Check users
        print("\n4. Checking users...")
        check_users(db)
        
        # Check user role assignments
        print("\n5. Checking user-role assignments...")
        check_user_roles(db)
        
        # Test role lookup
        print("\n6. Testing role lookup...")
        test_role_lookup(db)
        
    finally:
        client.close()
        print("\n✅ MongoDB connection closed")
    
    print("\n" + "=" * 50)
    print("🏁 Investigation completed!")

if __name__ == "__main__":
    main()