from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.repository.base import BaseRepository
from app.model.counselor import (
    CounselorProfileDB, LeadDB, CallLogDB, MessageLogDB, NotificationDB,
    LeadStatus, LeadQuality, CallOutcome, MessageType
)
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class CounselorRepository(BaseRepository):
    """Repository for counselor profile operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
    
    def get_profile_by_user_id(self, collection: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get counselor profile by user ID"""
        try:
            return self.get_by_field(collection, "user_id", user_id)
        except Exception as e:
            logger.error(f"Error getting counselor profile: {str(e)}")
            return None
    
    def create_profile(self, collection: str, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new counselor profile"""
        try:
            profile_data["user_id"] = user_id
            result = self.create(profile_data, collection)
            return result
        except Exception as e:
            logger.error(f"Error creating counselor profile: {str(e)}")
            return None
    
    def update_profile(self, collection: str, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update counselor profile"""
        try:
            profile = self.get_profile_by_user_id(collection, user_id)
            if not profile:
                return None
            
            update_data["updated_at"] = datetime.utcnow()
            self.update_by_field(collection, "user_id", user_id, update_data)
            
            return self.get_profile_by_user_id(collection, user_id)
        except Exception as e:
            logger.error(f"Error updating counselor profile: {str(e)}")
            return None
    
    def get_counselor_by_id(self, collection: str, counselor_id: str) -> Optional[Dict[str, Any]]:
        """Get counselor by ID"""
        try:
            return self.get_by_id(collection, counselor_id)
        except Exception as e:
            logger.error(f"Error getting counselor by ID: {str(e)}")
            return None
    
    def get_available_counselors(self, collection: str) -> List[Dict[str, Any]]:
        """Get all available counselors for lead assignment"""
        try:
            counselors = self.database[collection].find({
                "status": "active",
                "is_available": True,
                "$expr": {"$lt": ["$current_leads_count", "$max_leads_capacity"]}
            }).sort("current_leads_count", 1)  # Sort by least leads first
            return list(counselors)
        except Exception as e:
            logger.error(f"Error getting available counselors: {str(e)}")
            return []
    
    def update_counselor_status(self, collection: str, counselor_id: str, status: str, reason: str = None) -> bool:
        """Update counselor status (active/inactive/blocked)"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == "blocked" and reason:
                update_data["block_reason"] = reason
                update_data["blocked_until"] = datetime.utcnow() + timedelta(days=30)  # Default 30 days
                update_data["is_available"] = False
            elif status == "active":
                update_data["block_reason"] = None
                update_data["blocked_until"] = None
                update_data["is_available"] = True
            
            result = self.database[collection].update_one(
                {"_id": counselor_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating counselor status: {str(e)}")
            return False
    
    def update_performance_metrics(self, collection: str, counselor_id: str, metrics: Dict[str, Any]) -> bool:
        """Update counselor performance metrics"""
        try:
            result = self.database[collection].update_one(
                {"_id": counselor_id},
                {"$set": {"performance_metrics": metrics, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
            return False


class LeadRepository(BaseRepository):
    """Repository for lead management operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
    
    def create_lead(self, collection: str, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new lead"""
        try:
            result = self.create(lead_data, collection)
            return result
        except Exception as e:
            logger.error(f"Error creating lead: {str(e)}")
            return None
    
    def get_leads_by_counselor(self, collection: str, counselor_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get leads assigned to a counselor"""
        try:
            query = {"assigned_counselor_id": counselor_id}
            if status:
                query["status"] = status
            
            leads = self.database[collection].find(query).sort("created_at", -1)
            return list(leads)
        except Exception as e:
            logger.error(f"Error getting leads by counselor: {str(e)}")
            return []
    
    def get_lead_by_id(self, collection: str, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead by ID"""
        try:
            return self.get_by_id(collection, lead_id)
        except Exception as e:
            logger.error(f"Error getting lead by ID: {str(e)}")
            return None
    
    def update_lead_status(self, collection: str, lead_id: str, status: str, counselor_id: str) -> Optional[Dict[str, Any]]:
        """Update lead status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
                "last_contact_date": datetime.utcnow()
            }
            
            result = self.database[collection].find_one_and_update(
                {"_id": lead_id, "assigned_counselor_id": counselor_id},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            return None
    
    def mark_lead_quality(self, collection: str, lead_id: str, quality: str, counselor_id: str) -> Optional[Dict[str, Any]]:
        """Mark lead quality (good/bad/future)"""
        try:
            update_data = {
                "quality": quality,
                "updated_at": datetime.utcnow()
            }
            
            result = self.database[collection].find_one_and_update(
                {"_id": lead_id, "assigned_counselor_id": counselor_id},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Error marking lead quality: {str(e)}")
            return None
    
    def reassign_lead(self, collection: str, lead_id: str, new_counselor_id: str, current_counselor_id: str) -> Optional[Dict[str, Any]]:
        """Reassign lead to another counselor"""
        try:
            update_data = {
                "assigned_counselor_id": new_counselor_id,
                "assigned_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "reassigned"
            }
            
            result = self.database[collection].find_one_and_update(
                {"_id": lead_id, "assigned_counselor_id": current_counselor_id},
                {"$set": update_data},
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Error reassigning lead: {str(e)}")
            return None
    
    def search_leads(self, collection: str, counselor_id: str, filters: Dict[str, Any], page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Search leads with filters"""
        try:
            query = {"assigned_counselor_id": counselor_id}
            
            # Apply filters
            if filters.get("status"):
                query["status"] = filters["status"]
            if filters.get("quality"):
                query["quality"] = filters["quality"]
            if filters.get("priority"):
                query["priority"] = filters["priority"]
            if filters.get("country"):
                query["preferred_countries"] = {"$in": [filters["country"]]}
            if filters.get("course"):
                query["preferred_courses"] = {"$in": [filters["course"]]}
            if filters.get("date_from"):
                query["created_at"] = {"$gte": datetime.fromisoformat(filters["date_from"])}
            if filters.get("date_to"):
                if "created_at" in query:
                    query["created_at"]["$lte"] = datetime.fromisoformat(filters["date_to"])
                else:
                    query["created_at"] = {"$lte": datetime.fromisoformat(filters["date_to"])}
            
            # Get total count
            total = self.database[collection].count_documents(query)
            
            # Get paginated results
            skip = (page - 1) * limit
            leads = self.database[collection].find(query).sort("created_at", -1).skip(skip).limit(limit)
            
            return {
                "leads": list(leads),
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"Error searching leads: {str(e)}")
            return {"leads": [], "total": 0, "page": page, "limit": limit, "pages": 0}
    
    def add_note_to_lead(self, collection: str, lead_id: str, note: str, counselor_id: str) -> bool:
        """Add note to lead"""
        try:
            result = self.database[collection].update_one(
                {"_id": lead_id, "assigned_counselor_id": counselor_id},
                {
                    "$push": {"notes": f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {note}"},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error adding note to lead: {str(e)}")
            return False
    
    def schedule_follow_up(self, collection: str, lead_id: str, follow_up_date: datetime, counselor_id: str) -> bool:
        """Schedule follow-up for lead"""
        try:
            result = self.database[collection].update_one(
                {"_id": lead_id, "assigned_counselor_id": counselor_id},
                {
                    "$set": {
                        "next_follow_up": follow_up_date,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error scheduling follow-up: {str(e)}")
            return False
    
    def get_dashboard_stats(self, collection: str, counselor_id: str) -> Dict[str, Any]:
        """Get dashboard statistics for counselor"""
        try:
            pipeline = [
                {"$match": {"assigned_counselor_id": counselor_id}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            stats = list(self.database[collection].aggregate(pipeline))
            
            # Convert to dictionary
            status_counts = {stat["_id"]: stat["count"] for stat in stats}
            
            # Get follow-ups due today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            follow_ups_today = self.database[collection].count_documents({
                "assigned_counselor_id": counselor_id,
                "next_follow_up": {"$gte": today_start, "$lt": today_end}
            })
            
            # Get overdue follow-ups
            overdue_follow_ups = self.database[collection].count_documents({
                "assigned_counselor_id": counselor_id,
                "next_follow_up": {"$lt": datetime.utcnow()}
            })
            
            return {
                "status_counts": status_counts,
                "follow_ups_today": follow_ups_today,
                "overdue_follow_ups": overdue_follow_ups,
                "total_leads": sum(status_counts.values())
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {}


class CallLogRepository(BaseRepository):
    """Repository for call log operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
    
    def create_call_log(self, collection: str, call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create call log entry"""
        try:
            result = self.create(call_data, collection)
            return result
        except Exception as e:
            logger.error(f"Error creating call log: {str(e)}")
            return None
    
    def get_call_logs_by_lead(self, collection: str, lead_id: str) -> List[Dict[str, Any]]:
        """Get call logs for a lead"""
        try:
            logs = self.database[collection].find({"lead_id": lead_id}).sort("call_date", -1)
            return list(logs)
        except Exception as e:
            logger.error(f"Error getting call logs: {str(e)}")
            return []
    
    def get_call_logs_by_counselor(self, collection: str, counselor_id: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get call logs for a counselor within date range"""
        try:
            query = {"counselor_id": counselor_id}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["call_date"] = date_filter
            
            logs = self.database[collection].find(query).sort("call_date", -1)
            return list(logs)
        except Exception as e:
            logger.error(f"Error getting counselor call logs: {str(e)}")
            return []


class MessageLogRepository(BaseRepository):
    """Repository for message log operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
    
    def create_message_log(self, collection: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create message log entry"""
        try:
            result = self.create(message_data, collection)
            return result
        except Exception as e:
            logger.error(f"Error creating message log: {str(e)}")
            return None
    
    def get_message_logs_by_lead(self, collection: str, lead_id: str) -> List[Dict[str, Any]]:
        """Get message logs for a lead"""
        try:
            logs = self.database[collection].find({"lead_id": lead_id}).sort("sent_at", -1)
            return list(logs)
        except Exception as e:
            logger.error(f"Error getting message logs: {str(e)}")
            return []
    
    def mark_message_as_read(self, collection: str, message_id: str) -> bool:
        """Mark message as read"""
        try:
            result = self.database[collection].update_one(
                {"_id": message_id},
                {"$set": {"read": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return False


class NotificationRepository(BaseRepository):
    """Repository for notification operations"""
    
    def __init__(self, mongo_client: MongoClient):
        super().__init__(mongo_client)
    
    def create_notification(self, collection: str, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create notification"""
        try:
            result = self.create(notification_data, collection)
            return result
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            return None
    
    def get_notifications_by_counselor(self, collection: str, counselor_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications for counselor"""
        try:
            query = {"counselor_id": counselor_id}
            if unread_only:
                query["read"] = False
            
            notifications = self.database[collection].find(query).sort("created_at", -1).limit(50)
            return list(notifications)
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            return []
    
    def mark_notification_as_read(self, collection: str, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            result = self.database[collection].update_one(
                {"_id": notification_id},
                {"$set": {"read": True, "read_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
    
    def get_unread_count(self, collection: str, counselor_id: str) -> int:
        """Get count of unread notifications"""
        try:
            return self.database[collection].count_documents({
                "counselor_id": counselor_id,
                "read": False
            })
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            return 0