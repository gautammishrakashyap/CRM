from typing import List, Optional, Callable, Any
from functools import wraps
from fastapi import Depends, HTTPException, status
from jwt import InvalidTokenError
import jwt
from app.core.config import (
    SECRET_KEY, ALGORITHM, MONGO_COLLECTION_ROLES, 
    MONGO_COLLECTION_PERMISSIONS, MONGO_COLLECTION_USER_ROLES
)
from app.core.dependencies import _get_mongo_client, get_mongodb_repo
from app.repository.role import RoleRepository, PermissionRepository, UserRoleRepository
from app.schema.user import TokenData
from app.model.user import UserDB
from app.core.dependencies import get_user
from fastapi.security import HTTPAuthorizationCredentials
from app.core.security import bearer_scheme
from pymongo import MongoClient


class AuthorizationService:
    """Service for handling authorization operations"""
    
    def __init__(self, mongo_client: MongoClient):
        self.mongo_client = mongo_client
        self.role_repo = RoleRepository(mongo_client)
        self.permission_repo = PermissionRepository(mongo_client)
        self.user_role_repo = UserRoleRepository(mongo_client)
    
    def user_has_permission(self, user_id: str, permission_name: str) -> bool:
        """Check if a user has a specific permission (admins have all permissions)"""
        # First check if user is admin (admins have all permissions)
        if self.user_has_role(user_id, "admin"):
            return True
            
        # Otherwise check specific permissions
        user_permissions = self.permission_repo.get_permissions_for_user(
            MONGO_COLLECTION_USER_ROLES,
            MONGO_COLLECTION_ROLES,
            MONGO_COLLECTION_PERMISSIONS,
            user_id
        )
        return any(perm.name == permission_name for perm in user_permissions)
    
    def user_has_role(self, user_id: str, role_name: str) -> bool:
        """Check if a user has a specific role"""
        return self.user_role_repo.user_has_role(
            MONGO_COLLECTION_USER_ROLES,
            user_id,
            role_name,
            MONGO_COLLECTION_ROLES
        )
    
    def user_has_any_role(self, user_id: str, role_names: List[str]) -> bool:
        """Check if a user has any of the specified roles"""
        return any(self.user_has_role(user_id, role_name) for role_name in role_names)
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get all role names for a user"""
        user_roles = self.role_repo.get_roles_for_user(
            MONGO_COLLECTION_USER_ROLES,
            MONGO_COLLECTION_ROLES,
            user_id
        )
        return [role.name for role in user_roles]
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permission names for a user"""
        user_permissions = self.permission_repo.get_permissions_for_user(
            MONGO_COLLECTION_USER_ROLES,
            MONGO_COLLECTION_ROLES,
            MONGO_COLLECTION_PERMISSIONS,
            user_id
        )
        return [perm.name for perm in user_permissions]


def get_authorization_service(mongo_client: MongoClient = Depends(_get_mongo_client)) -> AuthorizationService:
    """Dependency to get authorization service"""
    return AuthorizationService(mongo_client)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    mongo_client: MongoClient = Depends(_get_mongo_client)
) -> UserDB:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: UserDB = Depends(get_current_user)
) -> UserDB:
    """Get current active user (alias for get_current_user with active check)"""
    return current_user


def require_permission(permission_name: str):
    """Decorator that requires a specific permission"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user = kwargs.get('current_user')
            auth_service = kwargs.get('auth_service')
            
            if not current_user or not auth_service:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization dependencies not properly injected"
                )
            
            if not auth_service.user_has_permission(str(current_user.id), permission_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission_name}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """Decorator that requires a specific role"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user = kwargs.get('current_user')
            auth_service = kwargs.get('auth_service')
            
            if not current_user or not auth_service:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization dependencies not properly injected"
                )
            
            if not auth_service.user_has_role(str(current_user.id), role_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role_name}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(role_names: List[str]):
    """Decorator that requires any of the specified roles"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user = kwargs.get('current_user')
            auth_service = kwargs.get('auth_service')
            
            if not current_user or not auth_service:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization dependencies not properly injected"
                )
            
            if not auth_service.user_has_any_role(str(current_user.id), role_names):
                roles_str = "', '".join(role_names)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: '{roles_str}'"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Permission-based dependencies
class PermissionChecker:
    """Class to create permission-checking dependencies"""
    
    def __init__(self, permission_name: str):
        self.permission_name = permission_name
    
    def __call__(
        self,
        current_user: UserDB = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service)
    ) -> UserDB:
        # Admins have all permissions
        if auth_service.user_has_role(str(current_user.id), "admin"):
            return current_user
            
        # Check specific permission for non-admin users
        if not auth_service.user_has_permission(str(current_user.id), self.permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.permission_name}' required"
            )
        return current_user


class RoleChecker:
    """Class to create role-checking dependencies"""
    
    def __init__(self, role_name: str):
        self.role_name = role_name
    
    def __call__(
        self,
        current_user: UserDB = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service)
    ) -> UserDB:
        if not auth_service.user_has_role(str(current_user.id), self.role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{self.role_name}' required"
            )
        return current_user


class AnyRoleChecker:
    """Class to create dependencies that check for any of specified roles"""
    
    def __init__(self, role_names: List[str]):
        self.role_names = role_names
    
    def __call__(
        self,
        current_user: UserDB = Depends(get_current_user),
        auth_service: AuthorizationService = Depends(get_authorization_service)
    ) -> UserDB:
        if not auth_service.user_has_any_role(str(current_user.id), self.role_names):
            roles_str = "', '".join(self.role_names)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: '{roles_str}'"
            )
        return current_user


# Convenience functions to create dependencies
def requires_permission(permission_name: str):
    """Create a dependency that requires a specific permission"""
    return PermissionChecker(permission_name)


def requires_role(role_name: str):
    """Create a dependency that requires a specific role"""
    return RoleChecker(role_name)


def requires_any_role(role_names: List[str]):
    """Create a dependency that requires any of the specified roles"""
    return AnyRoleChecker(role_names)


# Common role dependencies
requires_admin = requires_role("admin")
requires_moderator = requires_any_role(["admin", "moderator"])
requires_user = requires_any_role(["admin", "moderator", "user"])

# Common permission dependencies
requires_read_users = requires_permission("read_users")
requires_write_users = requires_permission("write_users")
requires_delete_users = requires_permission("delete_users")
requires_manage_roles = requires_permission("manage_roles")
requires_manage_profile = requires_permission("manage_profile")
requires_upload_documents = requires_permission("upload_documents")
requires_apply_colleges = requires_permission("apply_colleges")
requires_track_applications = requires_permission("track_applications")