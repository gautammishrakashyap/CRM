from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from app.repository.base import BaseRepository
from app.core.config import MONGO_COLLECTION_STUDENT_PROFILES


class StudentRepository(BaseRepository):
    """Repository for student profile operations"""
    
    def __init__(self, mongo: MongoClient):
        super().__init__(mongo)
        self.collection = self.database[MONGO_COLLECTION_STUDENT_PROFILES]
    
    def get_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get student profile by user ID"""
        try:
            profile = self.collection.find_one({"user_id": user_id})
            if profile:
                profile["_id"] = str(profile["_id"])
            return profile
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new student profile"""
        try:
            profile_data["user_id"] = user_id
            profile_data["created_at"] = datetime.utcnow()
            profile_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.insert_one(profile_data)
            
            # Return the created profile
            created_profile = self.collection.find_one({"_id": result.inserted_id})
            if created_profile:
                created_profile["_id"] = str(created_profile["_id"])
            return created_profile
        except Exception as e:
            print(f"Error creating profile: {e}")
            return None
    
    def update_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update student profile"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return self.get_profile_by_user_id(user_id)
            return None
        except Exception as e:
            print(f"Error updating profile: {e}")
            return None
    
    def add_qualification(self, user_id: str, qualification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add qualification to student profile"""
        try:
            result = self.collection.update_one(
                {"user_id": user_id},
                {
                    "$push": {"qualifications": qualification_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                return qualification_data
            return None
        except Exception as e:
            print(f"Error adding qualification: {e}")
            return None
    
    def add_college_preference(self, user_id: str, preference_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add college preference to student profile"""
        try:
            result = self.collection.update_one(
                {"user_id": user_id},
                {
                    "$push": {"college_preferences": preference_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                return preference_data
            return None
        except Exception as e:
            print(f"Error adding college preference: {e}")
            return None
    
    def get_all_profiles(self, page: int = 1, limit: int = 10, search: Optional[str] = None) -> Dict[str, Any]:
        """Get all student profiles with pagination"""
        try:
            skip = (page - 1) * limit
            
            # Build search query
            query = {}
            if search:
                query = {
                    "$or": [
                        {"personal_details.first_name": {"$regex": search, "$options": "i"}},
                        {"personal_details.last_name": {"$regex": search, "$options": "i"}},
                        {"contact_details.email": {"$regex": search, "$options": "i"}}
                    ]
                }
            
            # Get total count
            total = self.collection.count_documents(query)
            
            # Get profiles
            profiles = list(self.collection.find(query).skip(skip).limit(limit))
            
            # Convert ObjectIds to strings
            for profile in profiles:
                profile["_id"] = str(profile["_id"])
            
            return {
                "profiles": profiles,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            print(f"Error getting all profiles: {e}")
            return {"profiles": [], "total": 0, "page": page, "limit": limit, "pages": 0}