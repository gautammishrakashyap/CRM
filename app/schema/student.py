from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, validator
from app.model.student import (
    AcademicQualification, CollegePreference, PersonalDetails, 
    AddressDetails, ContactDetails, StudentProfileDB, Gender
)


class StudentProfileResponse(BaseModel):
    """Response schema for student profile"""
    success: bool
    data: StudentProfileDB
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "user_id": "507f1f77bcf86cd799439011",
                    "profile_completed": False,
                    "completion_percentage": 75,
                    "interests": ["Computer Science", "Data Science"],
                    "career_goals": "Software Engineer",
                    "current_education_level": "12th"
                },
                "message": "Profile retrieved successfully"
            }
        }


class QualificationResponse(BaseModel):
    """Response for qualification operations"""
    success: bool
    data: AcademicQualification
    message: str


class CollegePreferenceResponse(BaseModel):
    """Response for college preference operations"""
    success: bool
    data: CollegePreference
    message: str


class CreateStudentProfileRequest(BaseModel):
    """Create student profile request"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    contact_details: Optional[ContactDetails] = None
    address_details: Optional[AddressDetails] = None
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe", 
                "date_of_birth": "2000-01-15",
                "gender": "male",
                "contact_details": {
                    "phone": "+1234567890",
                    "alternate_phone": "+1234567891",
                    "emergency_contact_name": "Jane Doe",
                    "emergency_contact_phone": "+1234567892",
                    "emergency_contact_relation": "Mother"
                },
                "address_details": {
                    "current_address": {
                        "street": "123 Main St",
                        "city": "New York",
                        "state": "NY",
                        "postal_code": "10001",
                        "country": "USA"
                    }
                }
            }
        }


class UpdatePersonalDetailsRequest(BaseModel):
    """Request to update personal details"""
    father_name: str = Field(..., min_length=2, max_length=100)
    mother_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: datetime
    gender: str = Field(..., regex="^(Male|Female|Other)$")
    category: str = Field(..., regex="^(General|OBC|SC|ST|EWS)$")
    nationality: str = Field(default="Indian", max_length=50)
    religion: Optional[str] = Field(None, max_length=50)
    blood_group: Optional[str] = Field(None, regex="^(A\+|A-|B\+|B-|AB\+|AB-|O\+|O-)$")
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        today = datetime.now()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 13 or age > 100:
            raise ValueError('Age must be between 13 and 100 years')
        return v


class UpdateAddressDetailsRequest(BaseModel):
    """Request to update address details"""
    permanent_address: str = Field(..., min_length=10, max_length=500)
    current_address: str = Field(..., min_length=10, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., regex="^[1-9][0-9]{5}$")
    country: str = Field(default="India", max_length=50)


class UpdateContactDetailsRequest(BaseModel):
    """Request to update contact details"""
    mobile: str = Field(..., regex="^(\+91-?)?[6-9]\d{9}$")
    alternate_mobile: Optional[str] = Field(None, regex="^(\+91-?)?[6-9]\d{9}$")
    emergency_contact: str = Field(..., regex="^(\+91-?)?[6-9]\d{9}$")
    emergency_contact_relation: str = Field(..., regex="^(Father|Mother|Guardian|Sibling|Other)$")
    
    @validator('alternate_mobile')
    def validate_alternate_mobile(cls, v, values):
        if v and 'mobile' in values and v == values['mobile']:
            raise ValueError('Alternate mobile cannot be same as primary mobile')
        return v


class AddQualificationRequest(BaseModel):
    """Request to add academic qualification"""
    level: str = Field(..., regex="^(10th|12th|Diploma|Bachelor|Master|PhD)$")
    institution: str = Field(..., min_length=2, max_length=200)
    board_university: str = Field(..., min_length=2, max_length=200)
    subjects: List[str] = Field(default=[], max_items=20)
    percentage_cgpa: float = Field(..., ge=0, le=100)
    year_of_passing: int = Field(..., ge=1990, le=2030)
    
    @validator('subjects')
    def validate_subjects(cls, v):
        if len(v) > 0:
            for subject in v:
                if len(subject.strip()) < 2:
                    raise ValueError('Each subject must be at least 2 characters long')
        return v


class UpdateQualificationRequest(BaseModel):
    """Request to update academic qualification"""
    institution: Optional[str] = Field(None, min_length=2, max_length=200)
    board_university: Optional[str] = Field(None, min_length=2, max_length=200)
    subjects: Optional[List[str]] = Field(None, max_items=20)
    percentage_cgpa: Optional[float] = Field(None, ge=0, le=100)
    year_of_passing: Optional[int] = Field(None, ge=1990, le=2030)


class AddCollegePreferenceRequest(BaseModel):
    """Request to add college preference"""
    college_name: str = Field(..., min_length=2, max_length=200)
    course_name: str = Field(..., min_length=2, max_length=200)
    location: str = Field(..., min_length=2, max_length=100)
    preference_rank: int = Field(..., ge=1, le=100)
    entrance_exam: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "college_name": "Indian Institute of Technology Delhi",
                "course_name": "Computer Science and Engineering",
                "location": "New Delhi",
                "preference_rank": 1,
                "entrance_exam": "JEE Advanced"
            }
        }


class UpdateCollegePreferenceRequest(BaseModel):
    """Request to update college preference"""
    college_name: Optional[str] = Field(None, min_length=2, max_length=200)
    course_name: Optional[str] = Field(None, min_length=2, max_length=200)
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    preference_rank: Optional[int] = Field(None, ge=1, le=100)
    entrance_exam: Optional[str] = Field(None, max_length=100)
    application_status: Optional[str] = Field(None, regex="^(not_applied|applied|accepted|rejected|waitlisted)$")


class UpdateInterestsRequest(BaseModel):
    """Request to update interests and career goals"""
    interests: List[str] = Field(..., min_items=1, max_items=20)
    career_goals: Optional[str] = Field(None, max_length=1000)
    current_education_level: Optional[str] = Field(None, regex="^(10th|12th|Diploma|Bachelor|Master|PhD)$")
    
    @validator('interests')
    def validate_interests(cls, v):
        for interest in v:
            if len(interest.strip()) < 2:
                raise ValueError('Each interest must be at least 2 characters long')
        return [interest.strip() for interest in v]


class ProfileCompletionStatusResponse(BaseModel):
    """Response for profile completion status"""
    success: bool
    data: Dict[str, Any]
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "completion_percentage": 75,
                    "profile_completed": False,
                    "missing_sections": ["address_details", "documents"],
                    "completed_sections": ["personal_details", "contact_details", "qualifications"],
                    "next_recommended_step": "Complete address details"
                },
                "message": "Profile completion status retrieved successfully"
            }
        }


class FileUploadResponse(BaseModel):
    """Response for file upload"""
    success: bool
    data: Dict[str, Any]
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "file_url": "https://s3.amazonaws.com/bucket/uploads/profile_image.jpg",
                    "file_name": "profile_image.jpg",
                    "file_size": 1024000,
                    "upload_timestamp": "2024-01-15T10:30:00",
                    "category": "profile_image"
                },
                "message": "File uploaded successfully"
            }
        }


class DocumentUploadRequest(BaseModel):
    """Request to categorize uploaded document"""
    category: str = Field(..., regex="^(profile_image|certificates|transcripts|identity_proof|other)$")
    description: Optional[str] = Field(None, max_length=200)


class StudentDashboardResponse(BaseModel):
    """Response for student dashboard"""
    profile_completion: ProfileCompletionStatusResponse
    recent_applications: List[Dict[str, Any]]
    upcoming_deadlines: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_completion": {
                    "completion_percentage": 85,
                    "profile_completed": False,
                    "missing_sections": ["documents"]
                },
                "recent_applications": [
                    {"college_name": "IIT Delhi", "status": "applied", "date": "2024-01-10"}
                ],
                "upcoming_deadlines": [
                    {"exam_name": "JEE Main", "date": "2024-04-15", "days_left": 45}
                ],
                "quick_stats": {
                    "applications_submitted": 5,
                    "colleges_shortlisted": 12,
                    "documents_uploaded": 8
                }
            }
        }