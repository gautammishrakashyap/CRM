from typing import Optional, List, Dict, Any
from datetime import datetime, time
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.model.base import PyObjectId
from enum import Enum


class WorkingHours(BaseModel):
    """Working hours configuration"""
    monday: Optional[Dict[str, str]] = Field(None, description="Monday working hours")
    tuesday: Optional[Dict[str, str]] = Field(None, description="Tuesday working hours")
    wednesday: Optional[Dict[str, str]] = Field(None, description="Wednesday working hours")
    thursday: Optional[Dict[str, str]] = Field(None, description="Thursday working hours")
    friday: Optional[Dict[str, str]] = Field(None, description="Friday working hours")
    saturday: Optional[Dict[str, str]] = Field(None, description="Saturday working hours")
    sunday: Optional[Dict[str, str]] = Field(None, description="Sunday working hours")
    timezone: str = Field(default="UTC", description="Timezone")
    
    class Config:
        json_schema_extra = {
            "example": {
                "monday": {"start": "09:00", "end": "17:00"},
                "tuesday": {"start": "09:00", "end": "17:00"},
                "wednesday": {"start": "09:00", "end": "17:00"},
                "thursday": {"start": "09:00", "end": "17:00"},
                "friday": {"start": "09:00", "end": "17:00"},
                "saturday": None,
                "sunday": None,
                "timezone": "Asia/Kolkata"
            }
        }


class CounselorSpecialization(BaseModel):
    """Counselor specialization areas"""
    countries: List[str] = Field(default=[], description="Countries of expertise")
    courses: List[str] = Field(default=[], description="Course specializations")
    universities: List[str] = Field(default=[], description="University partnerships")
    languages: List[str] = Field(default=[], description="Languages spoken")
    
    class Config:
        json_schema_extra = {
            "example": {
                "countries": ["USA", "Canada", "UK", "Australia"],
                "courses": ["Engineering", "Business", "Computer Science"],
                "universities": ["MIT", "Harvard", "Stanford"],
                "languages": ["English", "Hindi", "Spanish"]
            }
        }


class CounselorPerformanceMetrics(BaseModel):
    """Performance metrics for counselor"""
    total_leads: int = Field(default=0, description="Total leads assigned")
    active_leads: int = Field(default=0, description="Currently active leads")
    converted_leads: int = Field(default=0, description="Successfully converted leads")
    conversion_rate: float = Field(default=0.0, description="Conversion percentage")
    avg_response_time: float = Field(default=0.0, description="Average response time in hours")
    calls_made: int = Field(default=0, description="Total calls made")
    emails_sent: int = Field(default=0, description="Total emails sent")
    follow_ups_completed: int = Field(default=0, description="Follow-ups completed")
    rating: float = Field(default=0.0, description="Average rating from students")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_leads": 150,
                "active_leads": 25,
                "converted_leads": 45,
                "conversion_rate": 30.0,
                "avg_response_time": 2.5,
                "calls_made": 200,
                "emails_sent": 350,
                "follow_ups_completed": 120,
                "rating": 4.5
            }
        }


class CounselorStatus(str, Enum):
    """Counselor status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    BLOCKED = "blocked"


class CounselorProfileDB(BaseModel):
    """Counselor profile stored in database"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference to User ID")
    
    # Personal Information
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    phone: str = Field(..., description="Phone number")
    emergency_contact: Optional[str] = Field(None, description="Emergency contact")
    
    # Professional Information
    designation: str = Field(default="Counselor", description="Job designation")
    department: str = Field(default="Counseling", description="Department")
    experience_years: float = Field(default=0.0, description="Years of experience")
    specialization: CounselorSpecialization = Field(default_factory=CounselorSpecialization)
    
    # Work Configuration
    working_hours: WorkingHours = Field(default_factory=WorkingHours)
    max_leads_capacity: int = Field(default=50, description="Maximum leads capacity")
    current_leads_count: int = Field(default=0, description="Current active leads")
    
    # Status and Access
    status: CounselorStatus = Field(default=CounselorStatus.ACTIVE)
    is_available: bool = Field(default=True, description="Available for new leads")
    blocked_until: Optional[datetime] = Field(None, description="Blocked until this date")
    block_reason: Optional[str] = Field(None, description="Reason for blocking")
    
    # Performance
    performance_metrics: CounselorPerformanceMetrics = Field(default_factory=CounselorPerformanceMetrics)
    
    # Profile completion
    profile_completed: bool = Field(default=False)
    completion_percentage: int = Field(default=0)
    
    # Media
    profile_image_url: Optional[str] = Field(None, description="Profile image S3 URL")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(None, description="Last login time")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "first_name": "John",
                "last_name": "Doe",
                "employee_id": "EMP001",
                "phone": "+1234567890",
                "designation": "Senior Counselor",
                "experience_years": 5.5,
                "max_leads_capacity": 75,
                "status": "active",
                "is_available": True
            }
        }


# Lead Management Models
class LeadStatus(str, Enum):
    """Lead status"""
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    FOLLOW_UP = "follow_up"
    CONVERTED = "converted"
    CLOSED = "closed"
    REASSIGNED = "reassigned"


class LeadQuality(str, Enum):
    """Lead quality assessment"""
    GOOD = "good"
    BAD = "bad"
    FUTURE = "future"
    EXCELLENT = "excellent"


class LeadPriority(str, Enum):
    """Lead priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CallOutcome(str, Enum):
    """Call outcome"""
    CONNECTED = "connected"
    NOT_REACHABLE = "not_reachable"
    BUSY = "busy"
    CALL_BACK = "call_back"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CONVERTED = "converted"


class MessageType(str, Enum):
    """Message type"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    CALL = "call"
    NOTE = "note"


class LeadDB(BaseModel):
    """Lead information in database"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Student Information
    student_id: PyObjectId = Field(..., description="Reference to Student ID")
    student_name: str = Field(..., description="Student name")
    student_email: str = Field(..., description="Student email")
    student_phone: str = Field(..., description="Student phone")
    
    # Lead Information
    status: LeadStatus = Field(default=LeadStatus.NEW)
    quality: Optional[LeadQuality] = Field(None, description="Lead quality assessment")
    priority: LeadPriority = Field(default=LeadPriority.MEDIUM)
    source: str = Field(default="website", description="Lead source")
    
    # Assignment Information
    assigned_counselor_id: Optional[PyObjectId] = Field(None, description="Assigned counselor")
    assigned_at: Optional[datetime] = Field(None, description="Assignment time")
    assigned_by: Optional[PyObjectId] = Field(None, description="Assigned by user")
    
    # Student Preferences
    preferred_countries: List[str] = Field(default=[], description="Preferred countries")
    preferred_courses: List[str] = Field(default=[], description="Preferred courses")
    preferred_cities: List[str] = Field(default=[], description="Preferred cities")
    budget_range: Optional[Dict[str, float]] = Field(None, description="Budget range")
    intake_term: Optional[str] = Field(None, description="Preferred intake term")
    
    # Communication History
    last_contact_date: Optional[datetime] = Field(None)
    next_follow_up: Optional[datetime] = Field(None)
    total_calls: int = Field(default=0)
    total_emails: int = Field(default=0)
    total_messages: int = Field(default=0)
    
    # Notes and Comments
    notes: List[str] = Field(default=[], description="General notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CallLogDB(BaseModel):
    """Call log entry"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    lead_id: PyObjectId = Field(..., description="Reference to Lead")
    counselor_id: PyObjectId = Field(..., description="Reference to Counselor")
    
    call_date: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: int = Field(default=0, description="Call duration in minutes")
    outcome: CallOutcome = Field(..., description="Call outcome")
    notes: str = Field(default="", description="Call notes")
    follow_up_required: bool = Field(default=False)
    next_call_scheduled: Optional[datetime] = Field(None)
    
    # Call details
    phone_number: str = Field(..., description="Phone number called")
    call_type: str = Field(default="outbound", description="Call type")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MessageLogDB(BaseModel):
    """Message/communication log"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    lead_id: PyObjectId = Field(..., description="Reference to Lead")
    counselor_id: PyObjectId = Field(..., description="Reference to Counselor")
    
    message_type: MessageType = Field(..., description="Type of message")
    subject: Optional[str] = Field(None, description="Message subject")
    content: str = Field(..., description="Message content")
    recipient: str = Field(..., description="Recipient (email/phone)")
    
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = Field(default=False)
    read: bool = Field(default=False)
    response_received: bool = Field(default=False)
    
    # Template information
    template_used: Optional[str] = Field(None, description="Template ID used")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class NotificationDB(BaseModel):
    """Notification for counselor"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    counselor_id: PyObjectId = Field(..., description="Reference to Counselor")
    
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: str = Field(..., description="Notification type")
    priority: str = Field(default="medium", description="Priority level")
    
    # Related objects
    related_lead_id: Optional[PyObjectId] = Field(None, description="Related lead")
    related_object_type: Optional[str] = Field(None, description="Type of related object")
    related_object_id: Optional[PyObjectId] = Field(None, description="Related object ID")
    
    # Status
    read: bool = Field(default=False)
    read_at: Optional[datetime] = Field(None)
    
    # Action
    action_required: bool = Field(default=False)
    action_url: Optional[str] = Field(None, description="URL for action")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Notification expiry")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}