from pymongo import MongoClient
from typing import Optional, Dict, Any
from app.repository.base import BaseRepository
from app.core.config import MONGO_COLLECTION_STUDENT_PROFILES
import logging

logger = logging.getLogger(__name__)


class StudentRepository(BaseRepository):
    """Repository for student profile operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
        self.collection_name = MONGO_COLLECTION_STUDENT_PROFILES
    
    def get_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get student profile by user ID"""
        try:
            return self.get_by_field(self.collection_name, "user_id", user_id)
        except Exception as e:
            logger.error(f"Error getting student profile: {str(e)}")
            return None
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new student profile"""
        try:
            profile_data["user_id"] = user_id
            result = self.create(profile_data, self.collection_name)
            return result
        except Exception as e:
            logger.error(f"Error creating student profile: {str(e)}")
            return None
    
    def update_profile(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update student profile"""
        try:
            # Find profile first
            profile = self.get_profile_by_user_id(user_id)
            if not profile:
                return None
            
            # Update the profile
            self.update_by_field(self.collection_name, "user_id", user_id, update_data)
            
            # Return updated profile
            return self.get_profile_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error updating student profile: {str(e)}")
            return None