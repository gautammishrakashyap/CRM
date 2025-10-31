from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.authorization import AuthorizationService, get_current_user
from app.core.database import mongo_db
from app.model.user import UserDB
from app.repository.counselor import CounselorRepository, LeadRepository, NotificationRepository
from app.model.counselor import CounselorProfileDB
from app.schema.counselor import (
    CounselorProfileCreate, CounselorProfileUpdate, CounselorProfileResponse,
    WorkingHoursUpdate, NotificationPreferencesUpdate, DashboardStats, 
    PerformanceStats, NotificationResponse
)
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


async def get_counselor_user(
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_auth_service)
):
    """Dependency to get current counselor user"""
    user_id = str(current_user.id)
    
    # Check if user has counselor role or admin role
    has_access = await auth_service.check_role_permission(
        user_id=user_id,
        required_role="counselor",
        required_permission="manage_leads"
    )
    
    admin_access = await auth_service.check_role_permission(
        user_id=user_id,
        required_role="admin"
    )
    
    if not has_access and not admin_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Counselor role required."
        )
    
    return current_user


@router.get("/profile", response_model=CounselorProfileResponse)
async def get_counselor_profile(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Get counselor profile"""
    try:
        user_id = str(current_user.id)
        
        # Get counselor profile
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        return CounselorProfileResponse(**profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting counselor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile", response_model=CounselorProfileResponse)
async def update_counselor_profile(
    profile_update: CounselorProfileUpdate,
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Update counselor profile"""
    try:
        user_id = str(current_user.id)
        
        # Check if profile exists
        existing_profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not existing_profile:
            # Create new profile if doesn't exist
            profile_data = profile_update.model_dump(exclude_unset=True)
            profile_data["user_id"] = user_id
            profile_data["created_at"] = datetime.utcnow()
            profile_data["updated_at"] = datetime.utcnow()
            
            # Set default values
            profile_data.setdefault("status", "active")
            profile_data.setdefault("is_available", True)
            profile_data.setdefault("current_leads_count", 0)
            profile_data.setdefault("performance_metrics", {
                "total_calls_made": 0,
                "successful_conversions": 0,
                "average_call_duration": 0,
                "leads_converted": 0,
                "monthly_target": 50,
                "current_month_conversions": 0
            })
            
            updated_profile = counselor_repo.create_profile("counselor_profiles", user_id, profile_data)
        else:
            # Update existing profile
            update_data = profile_update.model_dump(exclude_unset=True)
            updated_profile = counselor_repo.update_profile("counselor_profiles", user_id, update_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update profile"
            )
        
        return CounselorProfileResponse(**updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating counselor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile/working-hours")
async def update_working_hours(
    working_hours_update: WorkingHoursUpdate,
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Update counselor working hours"""
    try:
        user_id = str(current_user.id)
        
        update_data = {
            "working_hours": working_hours_update.working_hours,
            "timezone": working_hours_update.timezone,
            "updated_at": datetime.utcnow()
        }
        
        updated_profile = counselor_repo.update_profile("counselor_profiles", user_id, update_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        return {"message": "Working hours updated successfully", "working_hours": updated_profile.get("working_hours")}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating working hours: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile/notifications")
async def update_notification_preferences(
    notification_prefs: NotificationPreferencesUpdate,
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Update counselor notification preferences"""
    try:
        user_id = str(current_user.id)
        
        update_data = {
            "notification_preferences": notification_prefs.notification_preferences,
            "updated_at": datetime.utcnow()
        }
        
        updated_profile = counselor_repo.update_profile("counselor_profiles", user_id, update_data)
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        return {
            "message": "Notification preferences updated successfully",
            "notification_preferences": updated_profile.get("notification_preferences")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/profile/status")
async def get_counselor_status(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Get counselor status and availability"""
    try:
        user_id = str(current_user.id)
        
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        return {
            "status": profile.get("status"),
            "is_available": profile.get("is_available"),
            "current_leads_count": profile.get("current_leads_count", 0),
            "max_leads_capacity": profile.get("max_leads_capacity", 50),
            "blocked_until": profile.get("blocked_until"),
            "block_reason": profile.get("block_reason")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting counselor status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile/availability")
async def toggle_availability(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Toggle counselor availability status"""
    try:
        user_id = str(current_user.id)
        
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        # Check if counselor is blocked
        if profile.get("status") == "blocked":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change availability. Account is blocked."
            )
        
        # Toggle availability
        new_availability = not profile.get("is_available", True)
        
        update_data = {
            "is_available": new_availability,
            "updated_at": datetime.utcnow()
        }
        
        updated_profile = counselor_repo.update_profile("counselor_profiles", user_id, update_data)
        
        return {
            "message": f"Availability {'enabled' if new_availability else 'disabled'} successfully",
            "is_available": new_availability
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Dashboard Endpoints
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Get counselor dashboard statistics"""
    try:
        user_id = str(current_user.id)
        
        # Get counselor profile to get counselor_id
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        counselor_id = profile.get("_id")
        
        # Get dashboard statistics
        stats = lead_repo.get_dashboard_stats("leads", counselor_id)
        
        return DashboardStats(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/dashboard/performance", response_model=PerformanceStats)
async def get_performance_stats(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo)
):
    """Get counselor performance statistics"""
    try:
        user_id = str(current_user.id)
        
        # Get counselor profile
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        performance_metrics = profile.get("performance_metrics", {})
        
        # Calculate additional performance stats
        total_calls = performance_metrics.get("total_calls_made", 0)
        conversions = performance_metrics.get("leads_converted", 0)
        target = performance_metrics.get("monthly_target", 50)
        current_month_conversions = performance_metrics.get("current_month_conversions", 0)
        
        conversion_rate = (conversions / total_calls * 100) if total_calls > 0 else 0
        target_achievement = (current_month_conversions / target * 100) if target > 0 else 0
        
        # For demo purposes, using static values for daily/weekly stats
        # In production, these would be calculated from actual data
        performance_stats = {
            "total_calls_today": 5,  # Would be calculated from call logs
            "total_calls_this_week": 25,  # Would be calculated from call logs
            "total_calls_this_month": total_calls,
            "conversion_rate": round(conversion_rate, 2),
            "average_call_duration": performance_metrics.get("average_call_duration", 0),
            "target_achievement": round(target_achievement, 2),
            "leads_converted_today": 2,  # Would be calculated from leads
            "leads_converted_this_week": 8,  # Would be calculated from leads
            "leads_converted_this_month": current_month_conversions
        }
        
        return PerformanceStats(**performance_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo),
    notification_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Get counselor notifications"""
    try:
        user_id = str(current_user.id)
        
        # Get counselor profile to get counselor_id
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        counselor_id = profile.get("_id")
        
        # Get notifications
        notifications = notification_repo.get_notifications_by_counselor(
            "notifications", counselor_id, unread_only
        )
        
        return [NotificationResponse(**notification) for notification in notifications]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: UserDB = Depends(get_counselor_user),
    notification_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Mark notification as read"""
    try:
        success = notification_repo.mark_notification_as_read("notifications", notification_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/notifications/unread-count")
async def get_unread_notifications_count(
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo),
    notification_repo: NotificationRepository = Depends(get_notification_repo)
):
    """Get count of unread notifications"""
    try:
        user_id = str(current_user.id)
        
        # Get counselor profile to get counselor_id
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Counselor profile not found"
            )
        
        counselor_id = profile.get("_id")
        
        # Get unread count
        unread_count = notification_repo.get_unread_count("notifications", counselor_id)
        
        return {"unread_count": unread_count}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread notifications count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )