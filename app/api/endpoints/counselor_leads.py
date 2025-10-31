from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.authorization import AuthorizationService, get_current_user
from app.core.database import mongo_db
from app.model.user import UserDB
from app.repository.counselor import CounselorRepository, LeadRepository
from app.schema.counselor import (
    LeadResponse, LeadSearchFilters, LeadStatusUpdate, LeadQualityUpdate,
    LeadReassignment, LeadNote, FollowUpSchedule
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


async def get_counselor_id_from_user(user_id: str) -> str:
    """Get counselor ID from user ID"""
    profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Counselor profile not found"
        )
    return profile.get("_id")


@router.get("", response_model=Dict[str, Any])
async def get_leads(
    status_filter: Optional[str] = Query(None, alias="status"),
    quality_filter: Optional[str] = Query(None, alias="quality"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    country_filter: Optional[str] = Query(None, alias="country"),
    course_filter: Optional[str] = Query(None, alias="course"),
    date_from: Optional[str] = Query(None, alias="from_date"),
    date_to: Optional[str] = Query(None, alias="to_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: UserDB = Depends(get_counselor_user),
    counselor_repo: CounselorRepository = Depends(get_counselor_repo),
    lead_repo: LeadRepository = Depends(get_lead_repo)
):
    """Get leads assigned to counselor with filtering and pagination"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if quality_filter:
            filters["quality"] = quality_filter
        if priority_filter:
            filters["priority"] = priority_filter
        if country_filter:
            filters["country"] = country_filter
        if course_filter:
            filters["course"] = course_filter
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        # Search leads
        result = lead_repo.search_leads("leads", counselor_id, filters, page, limit)
        
        # Convert leads to response format
        leads = [LeadResponse(**lead) for lead in result["leads"]]
        
        return {
            "leads": leads,
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "limit": result["limit"],
                "pages": result["pages"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting leads: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead_details(
    lead_id: str,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Get detailed information about a specific lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Get lead
        lead = lead_repo.get_lead_by_id("leads", lead_id)
        
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )
        
        # Check if lead is assigned to this counselor
        if lead.get("assigned_counselor_id") != counselor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Lead not assigned to you."
            )
        
        return LeadResponse(**lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: str,
    status_update: LeadStatusUpdate,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Update lead status"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Update lead status
        updated_lead = lead_repo.update_lead_status("leads", lead_id, status_update.status, counselor_id)
        
        if not updated_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not assigned to you"
            )
        
        return LeadResponse(**updated_lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{lead_id}/quality", response_model=LeadResponse)
async def mark_lead_quality(
    lead_id: str,
    quality_update: LeadQualityUpdate,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Mark lead quality (good/bad/future)"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Mark lead quality
        updated_lead = lead_repo.mark_lead_quality("leads", lead_id, quality_update.quality, counselor_id)
        
        if not updated_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not assigned to you"
            )
        
        return LeadResponse(**updated_lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking lead quality: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{lead_id}/reassign", response_model=LeadResponse)
async def reassign_lead(
    lead_id: str,
    reassignment: LeadReassignment,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Reassign lead to another counselor"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Check if new counselor exists and is available
        new_counselor = counselor_repo.get_counselor_by_id("counselor_profiles", reassignment.new_counselor_id)
        
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
        
        # Check capacity
        current_leads = new_counselor.get("current_leads_count", 0)
        max_capacity = new_counselor.get("max_leads_capacity", 50)
        
        if current_leads >= max_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target counselor has reached maximum capacity"
            )
        
        # Reassign lead
        updated_lead = lead_repo.reassign_lead("leads", lead_id, reassignment.new_counselor_id, counselor_id)
        
        if not updated_lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not assigned to you"
            )
        
        # Update counselor lead counts
        # Decrease current counselor's count
        counselor_repo.update_profile("counselor_profiles", user_id, {
            "$inc": {"current_leads_count": -1}
        })
        
        # Increase new counselor's count  
        new_counselor_profile = counselor_repo.get_profile_by_user_id("counselor_profiles", new_counselor.get("user_id"))
        if new_counselor_profile:
            counselor_repo.update_profile("counselor_profiles", new_counselor.get("user_id"), {
                "$inc": {"current_leads_count": 1}
            })
        
        return LeadResponse(**updated_lead)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reassigning lead: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{lead_id}/notes")
async def add_lead_note(
    lead_id: str,
    note: LeadNote,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Add note to lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Add note to lead
        success = lead_repo.add_note_to_lead("leads", lead_id, note.note, counselor_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not assigned to you"
            )
        
        return {"message": "Note added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding lead note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{lead_id}/follow-up")
async def schedule_follow_up(
    lead_id: str,
    follow_up: FollowUpSchedule,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Schedule follow-up for lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Validate follow-up date is in the future
        if follow_up.follow_up_date <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Follow-up date must be in the future"
            )
        
        # Schedule follow-up
        success = lead_repo.schedule_follow_up("leads", lead_id, follow_up.follow_up_date, counselor_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found or not assigned to you"
            )
        
        return {
            "message": "Follow-up scheduled successfully",
            "follow_up_date": follow_up.follow_up_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling follow-up: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/summary/stats")
async def get_lead_summary_stats(current_user: UserDB = Depends(get_counselor_user)):
    """Get summary statistics for counselor's leads"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Get dashboard stats (reuse existing method)
        stats = lead_repo.get_dashboard_stats("leads", counselor_id)
        
        return {
            "total_leads": stats.get("total_leads", 0),
            "status_breakdown": stats.get("status_counts", {}),
            "follow_ups_today": stats.get("follow_ups_today", 0),
            "overdue_follow_ups": stats.get("overdue_follow_ups", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead summary stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )