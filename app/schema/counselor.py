from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class CounselorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = True
    push_notifications: bool = True
    lead_assignment_alerts: bool = True
    follow_up_reminders: bool = True
    performance_updates: bool = True


class WorkingHours(BaseModel):
    monday: Optional[Dict[str, str]] = Field(default={"start": "09:00", "end": "18:00"})
    tuesday: Optional[Dict[str, str]] = Field(default={"start": "09:00", "end": "18:00"})
    wednesday: Optional[Dict[str, str]] = Field(default={"start": "09:00", "end": "18:00"})
    thursday: Optional[Dict[str, str]] = Field(default={"start": "09:00", "end": "18:00"})
    friday: Optional[Dict[str, str]] = Field(default={"start": "09:00", "end": "18:00"})
    saturday: Optional[Dict[str, str]] = Field(default=None)
    sunday: Optional[Dict[str, str]] = Field(default=None)


class PerformanceMetrics(BaseModel):
    total_calls_made: int = 0
    successful_conversions: int = 0
    average_call_duration: float = 0.0
    leads_converted: int = 0
    monthly_target: int = 50
    current_month_conversions: int = 0
    conversion_rate: Optional[float] = None
    average_response_time: Optional[float] = None


# Request Schemas
class CounselorProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    phone: str = Field(..., min_length=10, max_length=15)
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[datetime] = None
    languages: List[str] = Field(default=["English"])
    specializations: List[str] = Field(default=[])
    countries_expertise: List[str] = Field(default=[])
    courses_expertise: List[str] = Field(default=[])
    max_leads_capacity: int = Field(default=50, ge=1, le=200)
    working_hours: Optional[WorkingHours] = Field(default_factory=WorkingHours)
    timezone: str = Field(default="UTC")
    notification_preferences: Optional[NotificationPreferences] = Field(default_factory=NotificationPreferences)


class CounselorProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    languages: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    countries_expertise: Optional[List[str]] = None
    courses_expertise: Optional[List[str]] = None
    max_leads_capacity: Optional[int] = Field(None, ge=1, le=200)
    working_hours: Optional[WorkingHours] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[NotificationPreferences] = None


class WorkingHoursUpdate(BaseModel):
    working_hours: WorkingHours
    timezone: str = Field(default="UTC")


class NotificationPreferencesUpdate(BaseModel):
    notification_preferences: NotificationPreferences


# Response Schemas
class CounselorProfileResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[datetime] = None
    languages: List[str]
    specializations: List[str]
    countries_expertise: List[str]
    courses_expertise: List[str]
    max_leads_capacity: int
    current_leads_count: int
    status: CounselorStatus
    is_available: bool
    working_hours: Optional[WorkingHours] = None
    timezone: str
    notification_preferences: NotificationPreferences
    performance_metrics: PerformanceMetrics
    blocked_until: Optional[datetime] = None
    block_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


# Lead related schemas
class LeadSearchFilters(BaseModel):
    status: Optional[str] = None
    quality: Optional[str] = None
    priority: Optional[str] = None
    country: Optional[str] = None
    course: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class LeadStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(new|contacted|interested|not_interested|converted|lost|follow_up|reassigned)$")


class LeadQualityUpdate(BaseModel):
    quality: str = Field(..., pattern="^(good|bad|future)$")


class LeadReassignment(BaseModel):
    new_counselor_id: str = Field(..., min_length=1)


class LeadNote(BaseModel):
    note: str = Field(..., min_length=1, max_length=1000)


class FollowUpSchedule(BaseModel):
    follow_up_date: datetime


class LeadResponse(BaseModel):
    id: str = Field(alias="_id")
    student_name: str
    student_email: str
    student_phone: str
    preferred_countries: List[str]
    preferred_courses: List[str]
    budget_range: Optional[str] = None
    academic_background: Optional[str] = None
    status: str
    quality: Optional[str] = None
    priority: str
    assigned_counselor_id: str
    assigned_at: datetime
    last_contact_date: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    notes: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


# Call Log schemas
class CallLogCreate(BaseModel):
    lead_id: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=0, le=300)  # Max 5 hours
    outcome: str = Field(..., pattern="^(successful|no_answer|busy|wrong_number|callback_requested|not_interested|interested)$")
    notes: Optional[str] = Field(None, max_length=1000)
    follow_up_required: bool = False
    next_contact_date: Optional[datetime] = None


class CallLogResponse(BaseModel):
    id: str = Field(alias="_id")
    lead_id: str
    counselor_id: str
    call_date: datetime
    duration_minutes: int
    outcome: str
    notes: Optional[str] = None
    follow_up_required: bool
    next_contact_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        populate_by_name = True


# Message Log schemas
class MessageLogCreate(BaseModel):
    lead_id: str = Field(..., min_length=1)
    message_type: str = Field(..., pattern="^(email|sms|whatsapp|system)$")
    subject: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None


class MessageLogResponse(BaseModel):
    id: str = Field(alias="_id")
    lead_id: str
    counselor_id: str
    message_type: str
    subject: Optional[str] = None
    content: str
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None
    sent_at: datetime
    delivered: bool
    read: bool
    read_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


# Dashboard schemas
class DashboardStats(BaseModel):
    status_counts: Dict[str, int]
    follow_ups_today: int
    overdue_follow_ups: int
    total_leads: int


class PerformanceStats(BaseModel):
    total_calls_today: int
    total_calls_this_week: int
    total_calls_this_month: int
    conversion_rate: float
    average_call_duration: float
    target_achievement: float
    leads_converted_today: int
    leads_converted_this_week: int
    leads_converted_this_month: int


# Notification schemas
class NotificationResponse(BaseModel):
    id: str = Field(alias="_id")
    counselor_id: str
    title: str
    message: str
    type: str
    priority: str
    read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        populate_by_name = True