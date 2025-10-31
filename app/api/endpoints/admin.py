from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from app.core.authorization import (
    get_current_user, get_authorization_service, AuthorizationService,
    requires_admin, requires_manage_roles
)
from app.core.security import bearer_scheme
from app.core.dependencies import get_mongodb_repo
from app.repository.role import RoleRepository, PermissionRepository, UserRoleRepository
from app.repository.user import UserRepository
from app.model.user import UserDB
from app.model.role import RoleDB, PermissionDB, UserRoleDB
from app.schema.role import (
    Role, Permission, CreateRoleRequest, UpdateRoleRequest,
    CreatePermissionRequest, UpdatePermissionRequest,
    AssignRoleToUserRequest, RemoveRoleFromUserRequest,
    AssignPermissionToRoleRequest, RemovePermissionFromRoleRequest,
    ListRolesResponse, ListPermissionsResponse, ListUserRolesResponse,
    RoleAssignmentResponse, UserRole, UserWithRoles
)
from app.schema.user import User
from app.core.config import (
    MONGO_COLLECTION_ROLES, MONGO_COLLECTION_PERMISSIONS, 
    MONGO_COLLECTION_USER_ROLES, MONGO_COLLECTION_USERS
)


router = APIRouter()


# Permission Management Endpoints
@router.post(
    '/admin/permissions',
    status_code=HTTP_201_CREATED,
    response_description='Create a new permission',
    name='admin:create_permission',
    response_model=Permission,
    summary="Create permission",
    description="Create a new permission (requires Bearer token and admin access)",
    dependencies=[Depends(bearer_scheme)]
)
def create_permission(
    create_req: CreatePermissionRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Create a new permission (Admin only)"""
    # Check if permission already exists
    existing_permission = permission_repo.get_permission_by_name(
        MONGO_COLLECTION_PERMISSIONS, 
        create_req.name
    )
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission '{create_req.name}' already exists"
        )
    
    # Create new permission
    permission_db = PermissionDB(**create_req.dict())
    created_permission = permission_repo.create_permission(
        MONGO_COLLECTION_PERMISSIONS, 
        permission_db
    )
    
    return Permission(
        permission_id=str(created_permission.id),
        name=created_permission.name,
        resource=created_permission.resource,
        action=created_permission.action,
        description=created_permission.description,
        created_at=created_permission.created_at
    )


@router.get(
    '/admin/permissions',
    status_code=HTTP_200_OK,
    response_description='Get all permissions',
    name='admin:list_permissions',
    response_model=ListPermissionsResponse,
    summary="List permissions",
    description="Get all permissions (requires Bearer token and admin access)",
    dependencies=[Depends(bearer_scheme)]
)
def list_permissions(
    current_user: UserDB = Depends(requires_manage_roles),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """List all permissions (Admin only)"""
    permissions_data, total = permission_repo.get_list(
        collection=MONGO_COLLECTION_PERMISSIONS,
        sort_field='created_at',
        sort_order=-1,
        skip=0,
        limit=1000  # Get all permissions
    )
    
    permissions = [
        Permission(
            permission_id=str(perm.id),
            name=perm.name,
            resource=perm.resource,
            action=perm.action,
            description=perm.description,
            created_at=perm.created_at
        )
        for perm in permissions_data
    ]
    
    return ListPermissionsResponse(
        permissions=permissions,
        meta={"total": total}
    )


@router.patch(
    '/admin/permissions/{permission_id}',
    status_code=HTTP_200_OK,
    response_description='Update a permission',
    name='admin:update_permission',
    response_model=Permission,
)
def update_permission(
    permission_id: str,
    update_req: UpdatePermissionRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Update a permission (Admin only)"""
    updated_permission = permission_repo.update_permission(
        MONGO_COLLECTION_PERMISSIONS, 
        permission_id, 
        update_req
    )
    
    if not updated_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    return Permission(
        permission_id=str(updated_permission.id),
        name=updated_permission.name,
        resource=updated_permission.resource,
        action=updated_permission.action,
        description=updated_permission.description,
        created_at=updated_permission.created_at
    )


@router.delete(
    '/admin/permissions/{permission_id}',
    status_code=HTTP_200_OK,
    response_description='Delete a permission',
    name='admin:delete_permission',
)
def delete_permission(
    permission_id: str,
    current_user: UserDB = Depends(requires_manage_roles),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Delete a permission (Admin only)"""
    deleted = permission_repo.delete_permission(MONGO_COLLECTION_PERMISSIONS, permission_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    return {"message": f"Permission {permission_id} deleted successfully"}


# Role Management Endpoints
@router.post(
    '/admin/roles',
    status_code=HTTP_201_CREATED,
    response_description='Create a new role',
    name='admin:create_role',
    response_model=Role,
    summary="Create role",
    description="Create a new role (requires Bearer token and admin access)",
    dependencies=[Depends(bearer_scheme)]
)
def create_role(
    create_req: CreateRoleRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Create a new role (Admin only)"""
    # Check if role already exists
    existing_role = role_repo.get_role_by_name(MONGO_COLLECTION_ROLES, create_req.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{create_req.name}' already exists"
        )
    
    # Validate permission IDs
    if create_req.permission_ids:
        permissions = permission_repo.get_permissions_by_ids(
            MONGO_COLLECTION_PERMISSIONS, 
            create_req.permission_ids
        )
        if len(permissions) != len(create_req.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permission IDs are invalid"
            )
    
    # Create new role
    role_db = RoleDB(
        name=create_req.name,
        description=create_req.description,
        permissions=create_req.permission_ids,
        is_system_role=False
    )
    created_role = role_repo.create_role(MONGO_COLLECTION_ROLES, role_db)
    
    # Get permissions for response
    permissions = []
    if create_req.permission_ids:
        permissions_data = permission_repo.get_permissions_by_ids(
            MONGO_COLLECTION_PERMISSIONS, 
            create_req.permission_ids
        )
        permissions = [
            Permission(
                permission_id=str(perm.id),
                name=perm.name,
                resource=perm.resource,
                action=perm.action,
                description=perm.description,
                created_at=perm.created_at
            )
            for perm in permissions_data
        ]
    
    return Role(
        role_id=str(created_role.id),
        name=created_role.name,
        description=created_role.description,
        permissions=permissions,
        is_system_role=created_role.is_system_role,
        created_at=created_role.created_at
    )


@router.get(
    '/admin/roles',
    status_code=HTTP_200_OK,
    response_description='Get all roles',
    name='admin:list_roles',
    response_model=ListRolesResponse,
)
def list_roles(
    current_user: UserDB = Depends(requires_manage_roles),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """List all roles (Admin only)"""
    roles_data, total = role_repo.get_list(
        collection=MONGO_COLLECTION_ROLES,
        sort_field='created_at',
        sort_order=-1,
        skip=0,
        limit=1000  # Get all roles
    )
    
    roles = []
    for role in roles_data:
        # Get permissions for each role
        permissions = []
        if role.permissions:
            permissions_data = permission_repo.get_permissions_by_ids(
                MONGO_COLLECTION_PERMISSIONS, 
                role.permissions
            )
            permissions = [
                Permission(
                    permission_id=str(perm.id),
                    name=perm.name,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description,
                    created_at=perm.created_at
                )
                for perm in permissions_data
            ]
        
        roles.append(Role(
            role_id=str(role.id),
            name=role.name,
            description=role.description,
            permissions=permissions,
            is_system_role=role.is_system_role,
            created_at=role.created_at
        ))
    
    return ListRolesResponse(
        roles=roles,
        meta={"total": total}
    )


@router.post(
    '/admin/roles/{role_id}/permissions',
    status_code=HTTP_200_OK,
    response_description='Assign permissions to role',
    name='admin:assign_permissions_to_role',
)
def assign_permissions_to_role(
    role_id: str,
    assign_req: AssignPermissionToRoleRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Assign permissions to a role (Admin only)"""
    # Validate role exists
    role = role_repo.get_role_by_id(MONGO_COLLECTION_ROLES, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Validate permission IDs
    permissions = permission_repo.get_permissions_by_ids(
        MONGO_COLLECTION_PERMISSIONS, 
        assign_req.permission_ids
    )
    if len(permissions) != len(assign_req.permission_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more permission IDs are invalid"
        )
    
    # Assign permissions
    success_count = 0
    for permission_id in assign_req.permission_ids:
        if role_repo.add_permission_to_role(MONGO_COLLECTION_ROLES, role_id, permission_id):
            success_count += 1
    
    return {
        "message": f"Successfully assigned {success_count} permissions to role '{role.name}'",
        "role_id": role_id,
        "assigned_permissions": success_count
    }


@router.delete(
    '/admin/roles/{role_id}/permissions',
    status_code=HTTP_200_OK,
    response_description='Remove permissions from role',
    name='admin:remove_permissions_from_role',
)
def remove_permissions_from_role(
    role_id: str,
    remove_req: RemovePermissionFromRoleRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository))
):
    """Remove permissions from a role (Admin only)"""
    # Validate role exists
    role = role_repo.get_role_by_id(MONGO_COLLECTION_ROLES, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Remove permissions
    success_count = 0
    for permission_id in remove_req.permission_ids:
        if role_repo.remove_permission_from_role(MONGO_COLLECTION_ROLES, role_id, permission_id):
            success_count += 1
    
    return {
        "message": f"Successfully removed {success_count} permissions from role '{role.name}'",
        "role_id": role_id,
        "removed_permissions": success_count
    }


# User Role Assignment Endpoints
@router.post(
    '/admin/users/roles',
    status_code=HTTP_201_CREATED,
    response_description='Assign role to user',
    name='admin:assign_role_to_user',
    response_model=RoleAssignmentResponse,
    summary="Assign role to user",
    description="Assign a role to a user (requires Bearer token and admin access)",
    dependencies=[Depends(bearer_scheme)]
)
def assign_role_to_user(
    assign_req: AssignRoleToUserRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository)),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    user_role_repo: UserRoleRepository = Depends(get_mongodb_repo(UserRoleRepository))
):
    """Assign a role to a user (Admin only)"""
    # Validate user exists
    user = user_repo.get_by_id(MONGO_COLLECTION_USERS, assign_req.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate role exists
    role = role_repo.get_role_by_id(MONGO_COLLECTION_ROLES, assign_req.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if assignment already exists
    existing_assignment = user_role_repo.get_user_role_assignment(
        MONGO_COLLECTION_USER_ROLES,
        assign_req.user_id,
        assign_req.role_id
    )
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has role '{role.name}'"
        )
    
    # Create assignment
    user_role = UserRoleDB(
        user_id=assign_req.user_id,
        role_id=assign_req.role_id,
        granted_by=str(current_user.id),
        expires_at=assign_req.expires_at
    )
    
    created_assignment = user_role_repo.assign_role_to_user(
        MONGO_COLLECTION_USER_ROLES,
        user_role
    )
    
    return RoleAssignmentResponse(
        message=f"Successfully assigned role '{role.name}' to user '{user.username}'",
        user_id=assign_req.user_id,
        role_id=assign_req.role_id,
        assignment_id=str(created_assignment.id)
    )


@router.delete(
    '/admin/users/roles',
    status_code=HTTP_200_OK,
    response_description='Remove role from user',
    name='admin:remove_role_from_user',
)
def remove_role_from_user(
    remove_req: RemoveRoleFromUserRequest = Body(...),
    current_user: UserDB = Depends(requires_manage_roles),
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository)),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    user_role_repo: UserRoleRepository = Depends(get_mongodb_repo(UserRoleRepository))
):
    """Remove a role from a user (Admin only)"""
    # Validate user exists
    user = user_repo.get_by_id(MONGO_COLLECTION_USERS, remove_req.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate role exists
    role = role_repo.get_role_by_id(MONGO_COLLECTION_ROLES, remove_req.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Remove assignment
    removed = user_role_repo.remove_role_from_user(
        MONGO_COLLECTION_USER_ROLES,
        remove_req.user_id,
        remove_req.role_id
    )
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User does not have role '{role.name}'"
        )
    
    return {
        "message": f"Successfully removed role '{role.name}' from user '{user.username}'",
        "user_id": remove_req.user_id,
        "role_id": remove_req.role_id
    }


@router.get(
    '/admin/users/{user_id}/roles',
    status_code=HTTP_200_OK,
    response_description='Get user roles',
    name='admin:get_user_roles',
    response_model=UserWithRoles,
)
def get_user_roles(
    user_id: str,
    current_user: UserDB = Depends(requires_manage_roles),
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository)),
    role_repo: RoleRepository = Depends(get_mongodb_repo(RoleRepository)),
    permission_repo: PermissionRepository = Depends(get_mongodb_repo(PermissionRepository))
):
    """Get all roles assigned to a user (Admin only)"""
    # Validate user exists
    user = user_repo.get_by_id(MONGO_COLLECTION_USERS, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's roles
    user_roles = role_repo.get_roles_for_user(
        MONGO_COLLECTION_USER_ROLES,
        MONGO_COLLECTION_ROLES,
        user_id
    )
    
    # Convert to response format with permissions
    roles = []
    for role in user_roles:
        permissions = []
        if role.permissions:
            permissions_data = permission_repo.get_permissions_by_ids(
                MONGO_COLLECTION_PERMISSIONS,
                role.permissions
            )
            permissions = [
                Permission(
                    permission_id=str(perm.id),
                    name=perm.name,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description,
                    created_at=perm.created_at
                )
                for perm in permissions_data
            ]
        
        roles.append(Role(
            role_id=str(role.id),
            name=role.name,
            description=role.description,
            permissions=permissions,
            is_system_role=role.is_system_role,
            created_at=role.created_at
        ))
    
    return UserWithRoles(
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        roles=roles,
        created_at=user.created_at
    )