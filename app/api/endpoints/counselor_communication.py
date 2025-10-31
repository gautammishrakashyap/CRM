from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.authorization import AuthorizationService, get_current_user
from app.core.database import mongo_db
from app.model.user import UserDB
from app.repository.counselor import CounselorRepository, LeadRepository, CallLogRepository, MessageLogRepository
from app.schema.counselor import (
    CallLogCreate, CallLogResponse, MessageLogCreate, MessageLogResponse
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

def get_call_log_repo():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return CallLogRepository(mongo_db.client)

def get_message_log_repo():
    if mongo_db.client is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return MessageLogRepository(mongo_db.client)

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


async def verify_lead_access(lead_id: str, counselor_id: str) -> Dict[str, Any]:
    """Verify that counselor has access to the lead"""
    lead = lead_repo.get_lead_by_id("leads", lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.get("assigned_counselor_id") != counselor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Lead not assigned to you."
        )
    
    return lead


# Call Log Endpoints
@router.post("/{lead_id}/call-log", response_model=CallLogResponse)
async def create_call_log(
    lead_id: str,
    call_log_data: CallLogCreate,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Log a call made to a lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Verify lead access
        lead = await verify_lead_access(lead_id, counselor_id)
        
        # Create call log entry
        call_data = call_log_data.model_dump()
        call_data.update({
            "counselor_id": counselor_id,
            "call_date": datetime.utcnow(),
            "created_at": datetime.utcnow()
        })
        
        call_log = call_log_repo.create_call_log("call_logs", call_data)
        
        if not call_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create call log"
            )
        
        # Update lead's last contact date
        lead_repo.update_lead_status("leads", lead_id, lead.get("status"), counselor_id)
        
        # Update counselor performance metrics
        profile = counselor_repo.get_profile_by_user_id("counselor_profiles", user_id)
        if profile:
            metrics = profile.get("performance_metrics", {})
            metrics["total_calls_made"] = metrics.get("total_calls_made", 0) + 1
            
            # Update average call duration
            total_calls = metrics["total_calls_made"]
            current_avg = metrics.get("average_call_duration", 0)
            new_avg = ((current_avg * (total_calls - 1)) + call_log_data.duration_minutes) / total_calls
            metrics["average_call_duration"] = round(new_avg, 2)
            
            counselor_repo.update_performance_metrics("counselor_profiles", counselor_id, metrics)
        
        return CallLogResponse(**call_log)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating call log: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{lead_id}/call-logs", response_model=List[CallLogResponse])
async def get_lead_call_logs(
    lead_id: str,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Get all call logs for a specific lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Verify lead access
        await verify_lead_access(lead_id, counselor_id)
        
        # Get call logs
        call_logs = call_log_repo.get_call_logs_by_lead("call_logs", lead_id)
        
        return [CallLogResponse(**log) for log in call_logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting call logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Message Log Endpoints
@router.post("/{lead_id}/send-message", response_model=MessageLogResponse)
async def send_message_to_lead(
    lead_id: str,
    message_data: MessageLogCreate,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Send message to a lead (email/SMS/WhatsApp)"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Verify lead access
        lead = await verify_lead_access(lead_id, counselor_id)
        
        # Create message log entry
        message_log_data = message_data.model_dump()
        message_log_data.update({
            "counselor_id": counselor_id,
            "sent_at": datetime.utcnow(),
            "delivered": True,  # Assume delivery for demo
            "read": False
        })
        
        # Set recipient info from lead data
        if message_data.message_type == "email":
            message_log_data["recipient_email"] = lead.get("student_email")
        elif message_data.message_type in ["sms", "whatsapp"]:
            message_log_data["recipient_phone"] = lead.get("student_phone")
        
        message_log = message_log_repo.create_message_log("message_logs", message_log_data)
        
        if not message_log:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create message log"
            )
        
        # Update lead's last contact date
        lead_repo.update_lead_status("leads", lead_id, lead.get("status"), counselor_id)
        
        # Here you would integrate with actual email/SMS services
        # For demo purposes, we're just logging the message
        
        return MessageLogResponse(**message_log)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{lead_id}/messages", response_model=List[MessageLogResponse])
async def get_lead_messages(
    lead_id: str,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Get all messages sent to a specific lead"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Verify lead access
        await verify_lead_access(lead_id, counselor_id)
        
        # Get message logs
        message_logs = message_log_repo.get_message_logs_by_lead("message_logs", lead_id)
        
        return [MessageLogResponse(**log) for log in message_logs]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Mark a message as read"""
    try:
        success = message_log_repo.mark_message_as_read("message_logs", message_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return {"message": "Message marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Communication History Endpoints
@router.get("/{lead_id}/communication-history")
async def get_communication_history(
    lead_id: str,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Get complete communication history for a lead (calls + messages)"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Verify lead access
        await verify_lead_access(lead_id, counselor_id)
        
        # Get call logs and message logs
        call_logs = call_log_repo.get_call_logs_by_lead("call_logs", lead_id)
        message_logs = message_log_repo.get_message_logs_by_lead("message_logs", lead_id)
        
        # Combine and sort by date
        communication_history = []
        
        for call in call_logs:
            communication_history.append({
                "type": "call",
                "date": call.get("call_date"),
                "data": CallLogResponse(**call)
            })
        
        for message in message_logs:
            communication_history.append({
                "type": "message",
                "date": message.get("sent_at"),
                "data": MessageLogResponse(**message)
            })
        
        # Sort by date (most recent first)
        communication_history.sort(key=lambda x: x["date"], reverse=True)
        
        return {
            "lead_id": lead_id,
            "total_communications": len(communication_history),
            "history": communication_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communication history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Counselor Communication Statistics
@router.get("/stats/communication")
async def get_communication_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserDB = Depends(get_counselor_user)
):
    """Get communication statistics for counselor"""
    try:
        user_id = str(current_user.id)
        counselor_id = await get_counselor_id_from_user(user_id)
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Get call logs
        call_logs = call_log_repo.get_call_logs_by_counselor("call_logs", counselor_id, start_dt, end_dt)
        
        # Calculate call statistics
        total_calls = len(call_logs)
        total_duration = sum(log.get("duration_minutes", 0) for log in call_logs)
        avg_duration = total_duration / total_calls if total_calls > 0 else 0
        
        # Count outcomes
        outcomes = {}
        for log in call_logs:
            outcome = log.get("outcome")
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "call_statistics": {
                "total_calls": total_calls,
                "total_duration_minutes": total_duration,
                "average_duration_minutes": round(avg_duration, 2),
                "outcomes_breakdown": outcomes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting communication stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )