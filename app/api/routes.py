from fastapi import APIRouter
from app.api.endpoints import user as user_router
from app.api.endpoints import admin as admin_router
from app.api.endpoints import student as student_router
from app.api.endpoints import counselor as counselor_router
from app.api.endpoints import counselor_leads as counselor_leads_router
from app.api.endpoints import counselor_communication as counselor_communication_router
from app.api.endpoints import admin_counselor as admin_counselor_router


router = APIRouter()

# Authentication and User endpoints (some user endpoints include auth)
router.include_router(user_router.router, prefix='/api/v1')

# Admin endpoints for role and permission management
router.include_router(admin_router.router, tags=['ADMIN V1'], prefix='/api/v1')

# Student profile management endpoints
router.include_router(student_router.router, tags=['STUDENT V1'], prefix='/api/v1')

# Counselor endpoints for profile and dashboard management
router.include_router(counselor_router.router, tags=['COUNSELOR V1'], prefix='/api/v1/counselor')

# Counselor lead management endpoints
router.include_router(counselor_leads_router.router, tags=['COUNSELOR LEADS V1'], prefix='/api/v1/counselor/leads')

# Counselor communication endpoints  
router.include_router(counselor_communication_router.router, tags=['COUNSELOR COMMUNICATION V1'], prefix='/api/v1/counselor/leads')

# Admin counselor management endpoints
router.include_router(admin_counselor_router.router, tags=['ADMIN COUNSELOR V1'], prefix='/api/v1/admin')
 