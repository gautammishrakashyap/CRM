from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from app.model.base import PyObjectId


class AcademicQualification(BaseModel):
    """Academic qualification/education details"""
    level: str = Field(..., description="Education level (e.g., '10th', '12th', 'Bachelor', 'Master')")
    institution: str = Field(..., description="Name of the institution")
    board_university: str = Field(..., description="Board/University name")
    subjects: List[str] = Field(default=[], description="Subjects studied")
    percentage_cgpa: float = Field(..., description="Percentage or CGPA obtained")
    year_of_passing: int = Field(..., description="Year of passing/completion")
    documents: List[str] = Field(default=[], description="Document URLs in S3")
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": "12th",
                "institution": "ABC School",
                "board_university": "CBSE",
                "subjects": ["Physics", "Chemistry", "Mathematics"],
                "percentage_cgpa": 85.5,
                "year_of_passing": 2023,
                "documents": ["s3://bucket/certificates/12th_certificate.pdf"]
            }
        }


class CollegePreference(BaseModel):
    """College/University preference for admission"""
    college_name: str = Field(..., description="Name of the college/university")
    course_name: str = Field(..., description="Course/program name")
    location: str = Field(..., description="College location")
    preference_rank: int = Field(..., description="Preference ranking (1 = highest)")
    application_status: str = Field(default="not_applied", description="Application status")
    entrance_exam: Optional[str] = Field(None, description="Required entrance exam")
    
    class Config:
        json_schema_extra = {
            "example": {
                "college_name": "IIT Delhi",
                "course_name": "Computer Science Engineering",
                "location": "New Delhi",
                "preference_rank": 1,
                "application_status": "applied",
                "entrance_exam": "JEE Main"
            }
        }


class PersonalDetails(BaseModel):
    """Personal details of the student"""
    father_name: str = Field(..., description="Father's name")
    mother_name: str = Field(..., description="Mother's name")
    date_of_birth: datetime = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender")
    category: str = Field(..., description="Category (General, OBC, SC, ST, etc.)")
    nationality: str = Field(default="Indian", description="Nationality")
    religion: Optional[str] = Field(None, description="Religion")
    blood_group: Optional[str] = Field(None, description="Blood group")
    
    class Config:
        json_schema_extra = {
            "example": {
                "father_name": "John Doe Sr.",
                "mother_name": "Jane Doe",
                "date_of_birth": "2005-05-15T00:00:00",
                "gender": "Male",
                "category": "General",
                "nationality": "Indian",
                "religion": "Hindu",
                "blood_group": "O+"
            }
        }


class AddressDetails(BaseModel):
    """Address details"""
    permanent_address: str = Field(..., description="Permanent address")
    current_address: str = Field(..., description="Current address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State")
    pincode: str = Field(..., description="PIN code")
    country: str = Field(default="India", description="Country")
    
    class Config:
        json_schema_extra = {
            "example": {
                "permanent_address": "123 Main St, Sector 1",
                "current_address": "123 Main St, Sector 1",
                "city": "New Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "country": "India"
            }
        }


class ContactDetails(BaseModel):
    """Contact details"""
    mobile: str = Field(..., description="Mobile number")
    alternate_mobile: Optional[str] = Field(None, description="Alternate mobile number")
    emergency_contact: str = Field(..., description="Emergency contact number")
    emergency_contact_relation: str = Field(..., description="Emergency contact relation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mobile": "+91-9876543210",
                "alternate_mobile": "+91-9876543211",
                "emergency_contact": "+91-9876543212",
                "emergency_contact_relation": "Father"
            }
        }


class StudentProfileDB(BaseModel):
    """Student profile stored in database"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="Reference to User ID")
    
    # Profile completion status
    profile_completed: bool = Field(default=False, description="Profile completion status")
    completion_percentage: int = Field(default=0, description="Profile completion percentage")
    
    # Personal information
    personal_details: Optional[PersonalDetails] = Field(None, description="Personal details")
    address_details: Optional[AddressDetails] = Field(None, description="Address details")
    contact_details: Optional[ContactDetails] = Field(None, description="Contact details")
    
    # Academic information
    qualifications: List[AcademicQualification] = Field(default=[], description="Academic qualifications")
    current_education_level: Optional[str] = Field(None, description="Current education level")
    
    # Interests and preferences
    interests: List[str] = Field(default=[], description="Academic/career interests")
    career_goals: Optional[str] = Field(None, description="Career goals description")
    college_preferences: List[CollegePreference] = Field(default=[], description="College preferences")
    
    # Media files
    profile_image_url: Optional[str] = Field(None, description="Profile image S3 URL")
    documents: Dict[str, List[str]] = Field(default={}, description="Document URLs by category")
    
    # Application tracking
    applications_submitted: List[Dict[str, Any]] = Field(default=[], description="Submitted applications")
    entrance_exams: List[Dict[str, Any]] = Field(default=[], description="Entrance exam details")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "profile_completed": False,
                "completion_percentage": 60,
                "interests": ["Computer Science", "Artificial Intelligence", "Web Development"],
                "career_goals": "Become a software engineer at a top tech company",
                "current_education_level": "12th"
            }
        }


class StudentQualificationCreate(BaseModel):
    """Schema for creating academic qualification"""
    level: str
    institution: str
    board_university: str
    subjects: List[str] = []
    percentage_cgpa: float
    year_of_passing: int


class StudentCollegePreferenceCreate(BaseModel):
    """Schema for creating college preference"""
    college_name: str
    course_name: str
    location: str
    preference_rank: int
    entrance_exam: Optional[str] = None


class StudentPersonalDetailsCreate(BaseModel):
    """Schema for creating/updating personal details"""
    father_name: str
    mother_name: str
    date_of_birth: datetime
    gender: str
    category: str
    nationality: str = "Indian"
    religion: Optional[str] = None
    blood_group: Optional[str] = None


class StudentAddressDetailsCreate(BaseModel):
    """Schema for creating/updating address details"""
    permanent_address: str
    current_address: str
    city: str
    state: str
    pincode: str
    country: str = "India"


class StudentContactDetailsCreate(BaseModel):
    """Schema for creating/updating contact details"""
    mobile: str
    alternate_mobile: Optional[str] = None
    emergency_contact: str
    emergency_contact_relation: str