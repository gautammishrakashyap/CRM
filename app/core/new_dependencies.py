from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from app.core.database import get_database
from app.repository.user import UserRepository
from app.repository.student import StudentRepository
from app.core.security import decode_access_token, check_user_permission as _check_user_permission
from app.model.user import UserDB

logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_user_repository() -> UserRepository:
    """Get user repository dependency"""
    database = get_database()
    return UserRepository(database)


def get_student_repository() -> StudentRepository:
    """Get student repository dependency"""
    database = get_database()
    return StudentRepository(database)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserDB:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        payload = decode_access_token(token)
        
        if not payload:
            raise credentials_exception
            
        username = payload.get("sub")
        if not username:
            raise credentials_exception
            
        # Get user from database
        user = await user_repo.get_by_username(username)
        if not user:
            raise credentials_exception
            
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception


def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_dependency(
        current_user: UserDB = Depends(get_current_user),
        user_repo: UserRepository = Depends(get_user_repository)
    ):
        has_permission = await _check_user_permission(current_user.id, permission, user_repo)
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return True
    
    return permission_dependency


async def check_user_permission(
    permission: str,
    current_user: UserDB = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
) -> bool:
    """Check if current user has specific permission"""
    return await _check_user_permission(current_user.id, permission, user_repo)