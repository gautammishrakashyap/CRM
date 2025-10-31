from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Permission Schemas
class Permission(BaseModel):
    """Schema for permission response"""
    permission_id: str
    name: str
    resource: str
    action: str
    description: Optional[str] = None
    created_at: datetime


class CreatePermissionRequest(BaseModel):
    """Schema for creating a new permission"""
    name: str = Field(..., description="Unique permission name")
    resource: str = Field(..., description="Resource this permission applies to")
    action: str = Field(..., description="Action allowed")
    description: Optional[str] = Field(None, description="Permission description")


class UpdatePermissionRequest(BaseModel):
    """Schema for updating a permission"""
    name: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None


# Role Schemas
class Role(BaseModel):
    """Schema for role response"""
    role_id: str
    name: str
    description: Optional[str] = None
    permissions: List[Permission] = []
    is_system_role: bool = False
    created_at: datetime


class CreateRoleRequest(BaseModel):
    """Schema for creating a new role"""
    name: str = Field(..., description="Unique role name")
    description: Optional[str] = Field(None, description="Role description")
    permission_ids: List[str] = Field(default=[], description="List of permission IDs to assign")


class UpdateRoleRequest(BaseModel):
    """Schema for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class AssignPermissionToRoleRequest(BaseModel):
    """Schema for assigning permissions to a role"""
    permission_ids: List[str] = Field(..., description="List of permission IDs to assign")


class RemovePermissionFromRoleRequest(BaseModel):
    """Schema for removing permissions from a role"""
    permission_ids: List[str] = Field(..., description="List of permission IDs to remove")


# User Role Assignment Schemas
class UserRole(BaseModel):
    """Schema for user role assignment response"""
    assignment_id: str
    user_id: str
    role_id: str
    role_name: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None


class AssignRoleToUserRequest(BaseModel):
    """Schema for assigning a role to a user"""
    user_id: str = Field(..., description="User ID to assign role to")
    role_id: str = Field(..., description="Role ID to assign")
    expires_at: Optional[datetime] = Field(None, description="When this role assignment expires")


class RemoveRoleFromUserRequest(BaseModel):
    """Schema for removing a role from a user"""
    user_id: str = Field(..., description="User ID to remove role from")
    role_id: str = Field(..., description="Role ID to remove")


# Enhanced User Schema with Roles
class UserWithRoles(BaseModel):
    """Enhanced user schema including role information"""
    user_id: str
    email: str
    username: str
    is_active: bool
    roles: List[Role] = []
    created_at: datetime


# List Response Schemas
class ListPermissionsResponse(BaseModel):
    """Schema for permission list response"""
    permissions: List[Permission]
    meta: dict


class ListRolesResponse(BaseModel):
    """Schema for role list response"""
    roles: List[Role]
    meta: dict


class ListUserRolesResponse(BaseModel):
    """Schema for user role assignments list response"""
    user_roles: List[UserRole]
    meta: dict


# API Response Schemas
class RoleAssignmentResponse(BaseModel):
    """Schema for role assignment operation response"""
    message: str
    user_id: str
    role_id: str
    assignment_id: str


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response"""
    has_permission: bool
    user_id: str
    permission: str
    resource: str
    action: str