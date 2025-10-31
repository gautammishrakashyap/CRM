# Authorization System Documentation

## Overview

This FastAPI application now includes a comprehensive role-based access control (RBAC) authorization system with the following features:

- **Dynamic Roles and Permissions**: Create, update, and delete roles and permissions
- **User Role Management**: Assign/remove roles to/from users dynamically
- **Fine-grained Access Control**: Permission-based and role-based endpoint protection
- **Admin Interface**: Complete admin endpoints for managing the authorization system
- **Default Setup**: Automatic initialization with default roles and permissions

## System Components

### 1. Models (`app/model/`)

#### User Model (`user.py`)
- Enhanced with `is_active` field for account status management

#### Role Models (`role.py`)
- **PermissionDB**: Individual permissions (e.g., "read_users", "delete_posts")
- **RoleDB**: Roles that contain multiple permissions (e.g., "admin", "moderator")
- **UserRoleDB**: User-role assignments with optional expiration

### 2. Repositories (`app/repository/`)

#### Role Repository (`role.py`)
- **RoleRepository**: CRUD operations for roles
- **PermissionRepository**: CRUD operations for permissions  
- **UserRoleRepository**: User-role assignment management

### 3. Authorization System (`app/core/`)

#### Authorization Service (`authorization.py`)
- **AuthorizationService**: Core service for permission checks
- **Permission Dependencies**: `requires_permission()`, `requires_role()`, `requires_any_role()`
- **Role Checkers**: Reusable dependency classes

#### Initialization (`init_auth.py`)
- Automatically creates default roles, permissions, and admin user on startup

### 4. API Endpoints

#### User Endpoints (`/api/v1/users/`)
- **POST /users** - Public registration
- **POST /token** - Public login
- **GET /users/me** - Get current user (authenticated)
- **GET /users** - List users (requires `read_users` permission)
- **GET /users/{id}** - Get user by ID (requires `read_users` permission)
- **PATCH /users/{id}** - Update user (requires `write_users` permission)
- **DELETE /users/{id}** - Delete user (requires `delete_users` permission)

#### Admin Endpoints (`/api/v1/admin/`)

**Permission Management:**
- **POST /admin/permissions** - Create permission
- **GET /admin/permissions** - List all permissions
- **PATCH /admin/permissions/{id}** - Update permission
- **DELETE /admin/permissions/{id}** - Delete permission

**Role Management:**
- **POST /admin/roles** - Create role
- **GET /admin/roles** - List all roles
- **POST /admin/roles/{id}/permissions** - Assign permissions to role
- **DELETE /admin/roles/{id}/permissions** - Remove permissions from role

**User Role Management:**
- **POST /admin/users/roles** - Assign role to user
- **DELETE /admin/users/roles** - Remove role from user
- **GET /admin/users/{id}/roles** - Get user's roles

## Default System Setup

### Default Roles

1. **admin**: Full system access with all permissions
2. **moderator**: Limited admin permissions (cannot delete users or manage roles)
3. **user**: Basic user permissions (read users, read/write posts)

### Default Permissions

- **read_users**: Read user information
- **write_users**: Create and update users
- **delete_users**: Delete users
- **read_posts**: Read posts
- **write_posts**: Create and update posts
- **delete_posts**: Delete posts
- **manage_roles**: Manage user roles and permissions
- **read_admin**: Access admin dashboard

### Default Admin User

- **Username**: `admin`
- **Email**: `admin@example.com`
- **Password**: `admin123` (⚠️ **CHANGE IN PRODUCTION!**)
- **Role**: `admin` (all permissions)

## Usage Examples

### 1. Authentication Flow

```python
# 1. Register a new user (public)
POST /api/v1/users
{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "securepassword"
}

# 2. Login to get access token
POST /api/v1/token
Form data: username=john_doe&password=securepassword

# Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer"
}

# 3. Use token in Authorization header
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 2. Admin Role Management

```python
# Assign admin role to a user
POST /api/v1/admin/users/roles
Authorization: Bearer <admin_token>
{
    "user_id": "user_id_here",
    "role_id": "admin_role_id",
    "expires_at": null  # Optional expiration
}

# Create a custom role
POST /api/v1/admin/roles
Authorization: Bearer <admin_token>
{
    "name": "content_manager",
    "description": "Can manage content but not users",
    "permission_ids": ["read_posts", "write_posts", "delete_posts"]
}
```

### 3. Permission-Based Endpoint Protection

```python
from app.core.authorization import requires_permission, requires_role

# Require specific permission
@router.get("/protected-endpoint")
def protected_endpoint(
    current_user: UserDB = Depends(requires_permission("read_admin"))
):
    return {"message": "You have admin read access!"}

# Require specific role
@router.delete("/admin-only")
def admin_only(
    current_user: UserDB = Depends(requires_role("admin"))
):
    return {"message": "Admin access confirmed!"}

# Require any of multiple roles
@router.post("/moderator-or-admin")
def moderator_or_admin(
    current_user: UserDB = Depends(requires_any_role(["admin", "moderator"]))
):
    return {"message": "You are a moderator or admin!"}
```

### 4. Custom Permission Checking

```python
from app.core.authorization import get_authorization_service

@router.get("/custom-check")
def custom_check(
    current_user: UserDB = Depends(get_current_user),
    auth_service: AuthorizationService = Depends(get_authorization_service)
):
    # Check if user has specific permission
    if auth_service.user_has_permission(str(current_user.id), "delete_posts"):
        return {"can_delete": True}
    
    # Check if user has specific role
    if auth_service.user_has_role(str(current_user.id), "moderator"):
        return {"is_moderator": True}
    
    # Get all user roles
    roles = auth_service.get_user_roles(str(current_user.id))
    return {"roles": roles}
```

## Security Features

### 1. JWT Token Authentication
- Secure token-based authentication
- Configurable token expiration
- User status validation (active/inactive)

### 2. Permission-Based Access Control
- Fine-grained permissions for different resources
- Resource and action-based permission structure
- Dynamic permission assignment

### 3. Role Hierarchy
- System roles vs custom roles
- Role-based permission inheritance
- Temporary role assignments with expiration

### 4. Admin Security
- Admin-only endpoints for system management
- Permission requirements for role management
- Audit trail for role assignments (granted_by field)

## Database Collections

The system uses these MongoDB collections:

- **user-collection**: User accounts
- **role-collection**: Available roles
- **permission-collection**: Available permissions
- **user-role-collection**: User-role assignments

## Environment Configuration

Add these to your `.env` file:

```env
# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Collections (optional, uses defaults)
MONGO_COLLECTION_USERS=user-collection
MONGO_COLLECTION_ROLES=role-collection  
MONGO_COLLECTION_PERMISSIONS=permission-collection
MONGO_COLLECTION_USER_ROLES=user-role-collection
```

## API Testing

### Using the Default Admin Account

1. **Login as admin:**
```bash
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

2. **List all permissions:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/permissions" \
  -H "Authorization: Bearer <your_admin_token>"
```

3. **Create a new role:**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/roles" \
  -H "Authorization: Bearer <your_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "editor",
    "description": "Content editor role",
    "permission_ids": ["read_posts", "write_posts"]
  }'
```

4. **Assign role to user:**
```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/roles" \
  -H "Authorization: Bearer <your_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_id_here",
    "role_id": "role_id_here"
  }'
```

## Production Considerations

1. **⚠️ Change Default Admin Password**: The default admin password is `admin123` - change this immediately in production!

2. **Secure Secret Key**: Use a strong, randomly generated SECRET_KEY

3. **Token Expiration**: Configure appropriate ACCESS_TOKEN_EXPIRE_MINUTES for your use case

4. **Database Security**: Ensure MongoDB is properly secured with authentication

5. **HTTPS**: Always use HTTPS in production for token security

6. **Role Auditing**: Monitor role assignments and changes for security

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**: Check if user has required role/permission
2. **"User not found" errors**: Ensure user exists and is active
3. **"Invalid token" errors**: Check token expiration and format
4. **Initialization failures**: Check MongoDB connection and permissions

### Debug Endpoints

Use these endpoints to debug authorization issues:

- `GET /api/v1/users/me` - Check current user info
- `GET /api/v1/admin/users/{id}/roles` - Check user's roles
- `GET /api/v1/admin/permissions` - List all available permissions

This authorization system provides a complete, production-ready RBAC solution for your FastAPI application!