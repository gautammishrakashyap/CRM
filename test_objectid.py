#!/usr/bin/env python3
"""
Test ObjectId conversion issue
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

def test_objectid_conversion():
    """Test ObjectId conversion with actual role IDs"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[MONGO_DATABASE]
        
        # Get actual roles from database
        roles_collection = db[MONGO_COLLECTION_ROLES]
        roles = list(roles_collection.find({}))
        
        print("🧪 Testing ObjectId conversion with actual role IDs")
        print("=" * 60)
        
        for role in roles:
            role_name = role.get('name')
            role_id_obj = role.get('_id')
            role_id_str = str(role_id_obj)
            
            print(f"\n🔐 Testing role: {role_name}")
            print(f"   Original ObjectId: {role_id_obj} (type: {type(role_id_obj)})")
            print(f"   String representation: {role_id_str} (type: {type(role_id_str)})")
            
            # Test 1: Direct lookup with ObjectId
            try:
                result1 = roles_collection.find_one({"_id": role_id_obj})
                if result1:
                    print(f"   ✅ Direct ObjectId lookup: SUCCESS")
                else:
                    print(f"   ❌ Direct ObjectId lookup: FAILED")
            except Exception as e:
                print(f"   ❌ Direct ObjectId lookup: ERROR - {e}")
            
            # Test 2: Lookup with string converted to ObjectId
            try:
                converted_id = ObjectId(role_id_str)
                result2 = roles_collection.find_one({"_id": converted_id})
                if result2:
                    print(f"   ✅ String->ObjectId lookup: SUCCESS")
                else:
                    print(f"   ❌ String->ObjectId lookup: FAILED")
            except Exception as e:
                print(f"   ❌ String->ObjectId lookup: ERROR - {e}")
            
            # Test 3: Check if string is valid ObjectId format
            try:
                is_valid = ObjectId.is_valid(role_id_str)
                print(f"   📝 Is valid ObjectId format: {is_valid}")
            except Exception as e:
                print(f"   ❌ ObjectId validation: ERROR - {e}")
            
            # Test 4: Check string length and format
            print(f"   📏 String length: {len(role_id_str)} (should be 24)")
            print(f"   🔤 All hex characters: {all(c in '0123456789abcdef' for c in role_id_str.lower())}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def main():
    test_objectid_conversion()

if __name__ == "__main__":
    main()