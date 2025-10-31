from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging
from pydantic import BaseModel, Field

from app.core.dependencies import get_user_dep, get_mongodb_repo
from app.core.authorization import (
    get_current_user, requires_manage_profile, requires_any_role,
    AuthorizationService, get_authorization_service
)
from app.repository.user import UserRepository
from app.repository.student import StudentRepository
from app.schema.user import User
from app.model.user import UserDB

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Student authorization dependency - allows students, admins, and users with manage_profile permission
requires_student_access = requires_any_role(["student", "admin", "user"])

def get_student_user(
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_authorization_service)
) -> UserDB:
    """
    Get current user and check if they have student access.
    Allows: students, admins, or users with manage_profile permission
    """
    # Admin users can access everything
    if auth_service.user_has_role(str(current_user.id), "admin"):
        return current_user
    
    # Users with student role can access
    if auth_service.user_has_role(str(current_user.id), "student"):
        return current_user
    
    # Users with manage_profile permission can access
    if auth_service.user_has_permission(str(current_user.id), "manage_profile"):
        return current_user
    
    # Check what roles/permissions the user actually has for better error message
    user_roles = auth_service.get_user_roles(str(current_user.id))
    user_permissions = auth_service.get_user_permissions(str(current_user.id))
    
    error_detail = f"Student access denied. Required: 'student' role OR 'manage_profile' permission. " \
                  f"Your roles: {user_roles}. Your permissions: {user_permissions}"
    
    raise HTTPException(
        status_code=403,
        detail=error_detail
    )

# Simple Pydantic models for student endpoints
class CreateStudentProfileRequest(BaseModel):
    """Create student profile request"""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe", 
                "date_of_birth": "2000-01-15",
                "gender": "male",
                "phone": "+1234567890"
            }
        }


class AddQualificationRequest(BaseModel):
    """Request to add academic qualification"""
    level: str = Field(..., description="Education level (10th, 12th, Bachelor, etc.)")
    institution: str = Field(..., min_length=2, max_length=200)
    board_university: str = Field(..., min_length=2, max_length=200)
    subjects: List[str] = Field(default=[], max_items=20)
    percentage_cgpa: float = Field(..., ge=0, le=100)
    year_of_passing: int = Field(..., ge=1990, le=2030)
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": "12th",
                "institution": "ABC School",
                "board_university": "CBSE",
                "subjects": ["Physics", "Chemistry", "Mathematics"],
                "percentage_cgpa": 85.5,
                "year_of_passing": 2023
            }
        }


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


class UpdateInterestsRequest(BaseModel):
    """Request to update interests and career goals"""
    interests: List[str] = Field(..., min_items=1, max_items=20)
    career_goals: Optional[str] = Field(None, max_length=1000)
    current_education_level: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "interests": ["Computer Science", "Artificial Intelligence", "Web Development"],
                "career_goals": "Become a software engineer at a top tech company",
                "current_education_level": "12th"
            }
        }


class StudentProfileResponse(BaseModel):
    """Response schema for student profile"""
    success: bool
    data: Dict[str, Any]
    message: str


class QualificationResponse(BaseModel):
    """Response for qualification operations"""
    success: bool
    data: Dict[str, Any]
    message: str


class CollegePreferenceResponse(BaseModel):
    """Response for college preference operations"""
    success: bool
    data: Dict[str, Any]
    message: str

router = APIRouter(
    prefix="/student",
    dependencies=[Depends(security)]
)


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: UserDB = Depends(get_student_user),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Get current student's profile"""
    try:
        # Try to get existing profile
        profile = student_repo.get_profile_by_user_id(str(current_user.id))
        
        if profile:
            return StudentProfileResponse(
                success=True,
                data=profile,
                message="Profile retrieved successfully"
            )
        else:
            # Return empty profile structure
            return StudentProfileResponse(
                success=True,
                data={
                    "user_id": str(current_user.id),
                    "profile_completed": False,
                    "completion_percentage": 0,
                    "interests": [],
                    "career_goals": None,
                    "current_education_level": None,
                    "qualifications": [],
                    "college_preferences": [],
                    "personal_details": None,
                    "contact_details": None,
                    "address_details": None
                },
                message="No profile found, please create one"
            )
    except Exception as e:
        logger.error(f"Error getting student profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.post("/profile/create", response_model=StudentProfileResponse)
async def create_student_profile(
    profile_data: CreateStudentProfileRequest,
    current_user: UserDB = Depends(get_student_user),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Create student profile"""
    try:
        # Check if profile already exists
        existing_profile = student_repo.get_profile_by_user_id(str(current_user.id))
        if existing_profile:
            raise HTTPException(status_code=409, detail="Profile already exists")
        
        # Prepare profile data
        profile_dict = profile_data.dict(exclude_unset=True)
        profile_dict["user_id"] = str(current_user.id)
        profile_dict["profile_completed"] = False
        profile_dict["completion_percentage"] = 25  # Basic info completed
        profile_dict["created_at"] = datetime.utcnow()
        profile_dict["updated_at"] = datetime.utcnow()
        
        # Create profile
        created_profile = student_repo.create_profile(str(current_user.id), profile_dict)
        
        if created_profile:
            return StudentProfileResponse(
                success=True,
                data=created_profile,
                message="Profile created successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create profile")


@router.get("/dashboard")
async def get_student_dashboard(
    current_user: User = Depends(get_user_dep),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Get student dashboard data"""
    try:
        # Get profile
        profile = student_repo.get_profile_by_user_id(current_user.user_id)
        
        # Calculate completion percentage
        completion_percentage = 0
        missing_sections = []
        completed_sections = []
        
        if profile:
            if profile.get("personal_details"):
                completed_sections.append("personal_details")
                completion_percentage += 20
            else:
                missing_sections.append("personal_details")
                
            if profile.get("contact_details"):
                completed_sections.append("contact_details")
                completion_percentage += 15
            else:
                missing_sections.append("contact_details")
                
            if profile.get("address_details"):
                completed_sections.append("address_details")
                completion_percentage += 15
            else:
                missing_sections.append("address_details")
                
            if profile.get("qualifications") and len(profile["qualifications"]) > 0:
                completed_sections.append("qualifications")
                completion_percentage += 20
            else:
                missing_sections.append("qualifications")
                
            if profile.get("interests") and len(profile["interests"]) > 0:
                completed_sections.append("interests")
                completion_percentage += 10
            else:
                missing_sections.append("interests")
                
            if profile.get("college_preferences") and len(profile["college_preferences"]) > 0:
                completed_sections.append("college_preferences")
                completion_percentage += 10
            else:
                missing_sections.append("college_preferences")
                
            if profile.get("profile_image_url"):
                completed_sections.append("profile_image")
                completion_percentage += 10
            else:
                missing_sections.append("profile_image")
        else:
            missing_sections = ["personal_details", "contact_details", "address_details", 
                             "qualifications", "interests", "college_preferences", "profile_image"]
        
        return {
            "success": True,
            "data": {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "profile_completion": {
                    "completion_percentage": completion_percentage,
                    "profile_completed": completion_percentage >= 90,
                    "missing_sections": missing_sections,
                    "completed_sections": completed_sections,
                    "next_recommended_step": missing_sections[0] if missing_sections else "Profile completed"
                },
                "recent_activities": [
                    {"activity": "Profile viewed", "timestamp": datetime.utcnow(), "type": "view"},
                    {"activity": "Dashboard accessed", "timestamp": datetime.utcnow(), "type": "access"}
                ],
                "notifications": [
                    {"message": "Complete your profile to unlock all features", "type": "info", "priority": "medium"}
                ] if completion_percentage < 90 else [],
                "quick_stats": {
                    "applications_submitted": 0,
                    "documents_uploaded": len(profile.get("documents", {}).values()) if profile else 0,
                    "profile_completion": f"{completion_percentage}%",
                    "qualifications_added": len(profile.get("qualifications", [])) if profile else 0,
                    "college_preferences": len(profile.get("college_preferences", [])) if profile else 0
                },
                "upcoming_deadlines": [
                    {"exam_name": "Sample Entrance Exam", "date": "2025-12-01", "days_left": 72, "priority": "high"}
                ],
                "recommendations": [
                    {"title": "Complete Profile", "description": "Add missing information to improve visibility", "action": "complete_profile"},
                    {"title": "Upload Documents", "description": "Upload required certificates and transcripts", "action": "upload_docs"}
                ] if completion_percentage < 90 else []
            },
            "message": "Dashboard data retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting student dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")


@router.get("/test")
async def test_student_endpoint():
    """Test endpoint to verify student routes are working"""
    return {
        "success": True,
        "message": "Student endpoints are working!",
        "timestamp": datetime.now(),
        "endpoints": [
            "/api/v1/student/profile",
            "/api/v1/student/profile/create", 
            "/api/v1/student/dashboard",
            "/api/v1/student/qualifications/add",
            "/api/v1/student/college-preferences/add",
            "/api/v1/student/interests/update",
            "/api/v1/student/test"
        ]
    }


@router.post("/qualifications/add", response_model=QualificationResponse)
async def add_qualification(
    qualification_data: AddQualificationRequest,
    current_user: User = Depends(get_user_dep),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Add academic qualification to student profile"""
    try:
        # Get existing profile
        profile = student_repo.get_profile_by_user_id(current_user.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Please create a profile first.")
        
        # Prepare qualification data
        qual_dict = qualification_data.dict()
        qual_dict["id"] = str(datetime.utcnow().timestamp())  # Simple ID generation
        qual_dict["created_at"] = datetime.utcnow()
        
        # Update profile with new qualification
        qualifications = profile.get("qualifications", [])
        qualifications.append(qual_dict)
        
        updated_profile = student_repo.update_profile(current_user.user_id, {
            "qualifications": qualifications,
            "updated_at": datetime.utcnow()
        })
        
        if updated_profile:
            return QualificationResponse(
                success=True,
                data=qual_dict,
                message="Qualification added successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to add qualification")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding qualification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add qualification")


@router.post("/college-preferences/add", response_model=CollegePreferenceResponse)
async def add_college_preference(
    preference_data: AddCollegePreferenceRequest,
    current_user: User = Depends(get_user_dep),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Add college preference to student profile"""
    try:
        # Get existing profile
        profile = student_repo.get_profile_by_user_id(current_user.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Please create a profile first.")
        
        # Prepare preference data
        pref_dict = preference_data.dict()
        pref_dict["id"] = str(datetime.utcnow().timestamp())  # Simple ID generation
        pref_dict["application_status"] = "not_applied"
        pref_dict["created_at"] = datetime.utcnow()
        
        # Update profile with new preference
        preferences = profile.get("college_preferences", [])
        preferences.append(pref_dict)
        
        updated_profile = student_repo.update_profile(current_user.user_id, {
            "college_preferences": preferences,
            "updated_at": datetime.utcnow()
        })
        
        if updated_profile:
            return CollegePreferenceResponse(
                success=True,
                data=pref_dict,
                message="College preference added successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to add college preference")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding college preference: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add college preference")


@router.put("/interests/update", response_model=StudentProfileResponse)
async def update_interests(
    interests_data: UpdateInterestsRequest,
    current_user: User = Depends(get_user_dep),
    student_repo: StudentRepository = Depends(get_mongodb_repo(StudentRepository))
):
    """Update student interests and career goals"""
    try:
        # Get existing profile
        profile = student_repo.get_profile_by_user_id(current_user.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found. Please create a profile first.")
        
        # Update interests and career goals
        update_data = interests_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        updated_profile = student_repo.update_profile(current_user.user_id, update_data)
        
        if updated_profile:
            return StudentProfileResponse(
                success=True,
                data=updated_profile,
                message="Interests and career goals updated successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to update interests")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update interests")