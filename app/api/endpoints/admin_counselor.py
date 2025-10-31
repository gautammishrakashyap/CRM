from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.core.authorization import AuthorizationService, get_current_user
from app.core.database import mongo_db
from app.model.user import UserDB
from app.repository.counselor import CounselorRepository, LeadRepository, NotificationRepository
from app.schema.counselor import CounselorProfileResponse, PerformanceStats
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Lazy initialization functions
def get_counselor_repo():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return CounselorRepository(mongo_db.client)

def get_lead_repo():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return LeadRepository(mongo_db.client)

def get_notification_repo():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return NotificationRepository(mongo_db.client)

def get_auth_service():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return AuthorizationService(mongo_db.client)


async def get_admin_user(
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service)
):
    """Dependency to get current admin user"""
    user_id = str(current_user.id)
    
    # Check if user has admin role
    has_access = await auth_service.check_role_permission(
        user_id=user_id,
        required_role="admin"
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin role required."
        )
    
    return current_user


# Request/Response Models
class CounselorStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive|blocked)$")
    reason: Optional[str] = Field(None, max_length=500)
    block_duration_days: Optional[int] = Field(None, ge=1, le=365)


class CounselorAssignment(BaseModel):
    counselor_id: str = Field(..., min_length=1)


class PerformanceUpdate(BaseModel):
    total_calls_made: Optional[int] = Field(None, ge=0)
    successful_conversions: Optional[int] = Field(None, ge=0)
    average_call_duration: Optional[float] = Field(None, ge=0)
    leads_converted: Optional[int] = Field(None, ge=0)
    monthly_target: Optional[int] = Field(None, ge=1)
    current_month_conversions: Optional[int] = Field(None, ge=0)


class BulkNotification(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    counselor_ids: Optional[List[str]] = Field(None, description="If None, sends to all counselors")


# Admin Counselor Management Endpoints
@router.get("/counselors", response_model=List[CounselorProfileResponse])
async def get_all_counselors(
    status_filter: Optional[str] = Query(None, alias="status"),
    availability_filter: Optional[bool] = Query(None, alias="available"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserDB = Depends(get_admin_user)
):
    """Get all counselors with filtering (Admin only)"""
    try:
        # Build query
        query = {}
        if status_filter:
            query["status"] = status_filter
        if availability_filter is not None:
            query["is_available"] = availability_filter
        
        # Get counselors with pagination
        skip = (page - 1) * limit
        counselors = counselor_repo.database["counselor_profiles"].find(query).skip(skip).limit(limit)
        
        counselor_list = []
        for counselor in counselors:
            counselor_list.append(CounselorProfileResponse(**counselor))
        
        return counselor_list
        
    except Exception as e:
        logger.error(f"Error getting counselors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/counselors/{counselor_id}", response_model=CounselorProfileResponse)
async def get_counselor_details(
    counselor_id: str,
    current_user: UserDB = Depends(get_admin_user)
):
    """Get detailed counselor information (Admin only)"""
    try:
        counselor = counselor_repo.get_counselor_by_id("counselor_profiles", counselor_id)
        
        if not counselor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor not found"
            )
        
        return CounselorProfileResponse(**counselor)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting counselor details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/counselors/{counselor_id}/status")
async def update_counselor_status(
    counselor_id: str,
    status_update: CounselorStatusUpdate,
    current_user: UserDB = Depends(get_admin_user)
):
    """Update counselor status - block/unblock/activate (Admin only)"""
    try:
        admin_user_id = str(current_user.id)
        
        # Calculate block duration if blocking
        blocked_until = None
        if status_update.status == "blocked" and status_update.block_duration_days:
            blocked_until = datetime.utcnow() + timedelta(days=status_update.block_duration_days)
        
        # Update counselor status
        success = counselor_repo.update_counselor_status(
            "counselor_profiles", 
            counselor_id, 
            status_update.status, 
            status_update.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor not found"
            )
        
        # Create notification for counselor
        counselor = counselor_repo.get_counselor_by_id("counselor_profiles", counselor_id)
        if counselor:
            notification_data = {
                "counselor_id": counselor_id,
                "title": f"Account Status Updated",
                "message": f"Your account status has been changed to {status_update.status}",
                "type": "status_update",
                "priority": "high" if status_update.status == "blocked" else "medium",
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            if status_update.reason:
                notification_data["message"] += f". Reason: {status_update.reason}"
            
            notification_repo.create_notification("notifications", notification_data)
        
        return {
            "message": f"Counselor status updated to {status_update.status}",
            "counselor_id": counselor_id,
            "status": status_update.status,
            "updated_by": admin_user_id,
            "blocked_until": blocked_until.isoformat() if blocked_until else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating counselor status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/counselors/{counselor_id}/performance")
async def update_counselor_performance(
    counselor_id: str,
    performance_update: PerformanceUpdate,
    current_user: UserDB = Depends(get_admin_user)
):
    """Update counselor performance metrics (Admin only)"""
    try:
        # Get current performance metrics
        counselor = counselor_repo.get_counselor_by_id("counselor_profiles", counselor_id)
        
        if not counselor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor not found"
            )
        
        current_metrics = counselor.get("performance_metrics", {})
        
        # Update only provided fields
        update_data = performance_update.model_dump(exclude_unset=True)
        current_metrics.update(update_data)
        
        # Calculate conversion rate
        total_calls = current_metrics.get("total_calls_made", 0)
        conversions = current_metrics.get("leads_converted", 0)
        if total_calls > 0:
            current_metrics["conversion_rate"] = round((conversions / total_calls) * 100, 2)
        
        success = counselor_repo.update_performance_metrics("counselor_profiles", counselor_id, current_metrics)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update performance metrics"
            )
        
        # Create notification for counselor
        notification_data = {
            "counselor_id": counselor_id,
            "title": "Performance Metrics Updated",
            "message": "Your performance metrics have been updated by admin",
            "type": "performance_update",
            "priority": "medium",
            "read": False,
            "created_at": datetime.utcnow()
        }
        
        notification_repo.create_notification("notifications", notification_data)
        
        return {
            "message": "Performance metrics updated successfully",
            "counselor_id": counselor_id,
            "updated_metrics": current_metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating performance metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/leads/{lead_id}/reassign")
async def admin_reassign_lead(
    lead_id: str,
    assignment: CounselorAssignment,
    current_user: UserDB = Depends(get_admin_user)
):
    """Admin reassign lead to different counselor"""
    try:
        admin_user_id = str(current_user.id)
        
        # Get current lead
        lead = lead_repo.get_lead_by_id("leads", lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        current_counselor_id = lead.get("assigned_counselor_id")
        
        # Check if new counselor exists and is available
        new_counselor = counselor_repo.get_counselor_by_id("counselor_profiles", assignment.counselor_id)
        
        if not new_counselor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target counselor not found"
            )
        
        if not new_counselor.get("is_available") or new_counselor.get("status") != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target counselor is not available"
            )
        
        # Perform reassignment
        updated_lead = lead_repo.reassign_lead("leads", lead_id, assignment.counselor_id, current_counselor_id)
        
        if not updated_lead:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reassign lead"
            )
        
        # Update counselor lead counts
        if current_counselor_id:
            # Decrease previous counselor's count
            current_counselor = counselor_repo.get_counselor_by_id("counselor_profiles", current_counselor_id)
            if current_counselor:
                new_count = max(0, current_counselor.get("current_leads_count", 0) - 1)
                counselor_repo.update_profile("counselor_profiles", current_counselor.get("user_id"), {
                    "current_leads_count": new_count
                })
        
        # Increase new counselor's count
        new_count = new_counselor.get("current_leads_count", 0) + 1
        counselor_repo.update_profile("counselor_profiles", new_counselor.get("user_id"), {
            "current_leads_count": new_count
        })
        
        # Create notifications
        notifications = [
            {
                "counselor_id": assignment.counselor_id,
                "title": "New Lead Assigned",
                "message": f"Lead {lead.get('student_name')} has been assigned to you by admin",
                "type": "lead_assignment",
                "priority": "medium",
                "read": False,
                "created_at": datetime.utcnow()
            }
        ]
        
        if current_counselor_id and current_counselor_id != assignment.counselor_id:
            notifications.append({
                "counselor_id": current_counselor_id,
                "title": "Lead Reassigned",
                "message": f"Lead {lead.get('student_name')} has been reassigned by admin",
                "type": "lead_reassignment",
                "priority": "medium",
                "read": False,
                "created_at": datetime.utcnow()
            })
        
        for notification in notifications:
            notification_repo.create_notification("notifications", notification)
        
        return {
            "message": "Lead reassigned successfully",
            "lead_id": lead_id,
            "previous_counselor_id": current_counselor_id,
            "new_counselor_id": assignment.counselor_id,
            "reassigned_by": admin_user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reassigning lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/notifications/broadcast")
async def send_bulk_notification(
    notification: BulkNotification,
    current_user: UserDB = Depends(get_admin_user)
):
    """Send notification to multiple counselors (Admin only)"""
    try:
        admin_user_id = str(current_user.id)
        
        # Get target counselors
        if notification.counselor_ids:
            # Send to specific counselors
            target_counselors = []
            for counselor_id in notification.counselor_ids:
                counselor = counselor_repo.get_counselor_by_id("counselor_profiles", counselor_id)
                if counselor:
                    target_counselors.append(counselor)
        else:
            # Send to all active counselors
            target_counselors = counselor_repo.database["counselor_profiles"].find({"status": "active"})
            target_counselors = list(target_counselors)
        
        if not target_counselors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No target counselors found"
            )
        
        # Create notifications
        notifications_created = 0
        for counselor in target_counselors:
            notification_data = {
                "counselor_id": counselor.get("_id"),
                "title": notification.title,
                "message": notification.message,
                "type": "broadcast",
                "priority": notification.priority,
                "read": False,
                "created_at": datetime.utcnow()
            }
            
            result = notification_repo.create_notification("notifications", notification_data)
            if result:
                notifications_created += 1
        
        return {
            "message": f"Bulk notification sent successfully",
            "notifications_sent": notifications_created,
            "target_counselors": len(target_counselors),
            "sent_by": admin_user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/analytics/overview")
async def get_counselor_analytics_overview(current_user: UserDB = Depends(get_admin_user)):
    """Get overall counselor system analytics (Admin only)"""
    try:
        # Get counselor statistics
        total_counselors = counselor_repo.database["counselor_profiles"].count_documents({})
        active_counselors = counselor_repo.database["counselor_profiles"].count_documents({"status": "active"})
        available_counselors = counselor_repo.database["counselor_profiles"].count_documents({
            "status": "active", 
            "is_available": True
        })
        blocked_counselors = counselor_repo.database["counselor_profiles"].count_documents({"status": "blocked"})
        
        # Get lead statistics
        total_leads = lead_repo.database["leads"].count_documents({})
        assigned_leads = lead_repo.database["leads"].count_documents({"assigned_counselor_id": {"$exists": True, "$ne": None}})
        unassigned_leads = total_leads - assigned_leads
        
        # Get performance statistics
        pipeline = [
            {"$group": {
                "_id": None,
                "total_calls": {"$sum": "$performance_metrics.total_calls_made"},
                "total_conversions": {"$sum": "$performance_metrics.leads_converted"},
                "avg_conversion_rate": {"$avg": "$performance_metrics.conversion_rate"}
            }}
        ]
        
        performance_stats = list(counselor_repo.database["counselor_profiles"].aggregate(pipeline))
        perf_data = performance_stats[0] if performance_stats else {}
        
        return {
            "counselor_overview": {
                "total_counselors": total_counselors,
                "active_counselors": active_counselors,
                "available_counselors": available_counselors,
                "blocked_counselors": blocked_counselors,
                "utilization_rate": round((active_counselors / total_counselors) * 100, 2) if total_counselors > 0 else 0
            },
            "lead_overview": {
                "total_leads": total_leads,
                "assigned_leads": assigned_leads,
                "unassigned_leads": unassigned_leads,
                "assignment_rate": round((assigned_leads / total_leads) * 100, 2) if total_leads > 0 else 0
            },
            "performance_overview": {
                "total_calls_system_wide": perf_data.get("total_calls", 0),
                "total_conversions_system_wide": perf_data.get("total_conversions", 0),
                "average_conversion_rate": round(perf_data.get("avg_conversion_rate", 0), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )