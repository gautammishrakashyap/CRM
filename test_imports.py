#!/usr/bin/env python3
"""
Test script to check if the FastAPI application can start without errors.
"""
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing import of main module...")
    from app.main import app
    print("✅ Main module imported successfully!")
    
    print("Testing config imports...")
    from app.core.config import SECRET_KEY, ALGORITHM, MONGODB_URL
    print(f"✅ Config imported successfully!")
    print(f"  - SECRET_KEY: {'Set' if SECRET_KEY else 'Not set'}")
    print(f"  - ALGORITHM: {ALGORITHM}")
    print(f"  - MONGODB_URL: {MONGODB_URL}")
    
    print("Testing database connection...")
    from app.core.database import get_database
    print("✅ Database function imported successfully!")
    
    print("Testing user dependencies...")
    from app.core.dependencies import get_user_dep, get_mongodb_repo
    print("✅ Dependencies imported successfully!")
    
    print("\n🎉 All basic imports successful! Application should start.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)